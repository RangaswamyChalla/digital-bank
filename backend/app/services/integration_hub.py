"""
Service integration layer for coordinating communication between modules.
Implements the integration architecture for fraud detection, analytics, and admin services.
"""

import asyncio
import json
import logging
from typing import Dict, Optional, List, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Optional Redis dependency - gracefully degrade if not available
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - pub/sub will be local only")


class ProcessingStatus(str, Enum):
    """Processing status for transactions and alerts"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    FRAUD_DETECTED = "fraud_detected"


@dataclass
class ServiceContext:
    """Context for service communication"""

    request_id: str
    user_id: str
    timestamp: datetime
    endpoint: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context for Redis pub/sub"""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "endpoint": self.endpoint,
            "metadata": self.metadata or {},
        }


class RedisEventBus:
    """Redis pub/sub event bus for multi-instance communication"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._listeners: Dict[str, List[Callable]] = {}
        self._subscription_task: Optional[asyncio.Task] = None
        self._instance_id = f"instance_{id(self)}"

    async def connect(self) -> None:
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - event bus will be local only")
            return

        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as exc:
            logger.warning(f"Failed to connect to Redis: {exc} - event bus will be local only")
            self._redis = None

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self._subscription_task:
            self._subscription_task.cancel()
            try:
                await self._subscription_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.close()

        if self._redis:
            await self._redis.close()
            self._redis = None

    async def publish(self, channel: str, data: Dict[str, Any]) -> None:
        """Publish event to Redis channel"""
        if not self._redis:
            return

        try:
            message = json.dumps(data)
            await self._redis.publish(channel, message)
            logger.debug(f"Published to {channel}: {message[:100]}...")
        except Exception as exc:
            logger.error(f"Failed to publish to Redis: {exc}")

    def subscribe(self, channel: str, callback: Callable) -> None:
        """Subscribe to a Redis channel (local listeners only)"""
        if channel not in self._listeners:
            self._listeners[channel] = []
        self._listeners[channel].append(callback)

    async def _start_subscription(self, channels: List[str]) -> None:
        """Start listening to Redis subscriptions"""
        if not self._redis:
            return

        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(*channels)

        async for message in self._pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"]
                try:
                    data = json.loads(message["data"])
                    if channel in self._listeners:
                        for callback in self._listeners[channel]:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(data)
                                else:
                                    callback(data)
                            except Exception as exc:
                                logger.error(f"Listener error for {channel}: {exc}")
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in Redis message: {message['data']}")


class ServiceIntegrationHub:
    """
    Central hub for service integration.
    Coordinates between fraud detection, analytics, transactions, and admin services.
    Supports Redis pub/sub for multi-instance WebSocket support.
    """

    def __init__(self, redis_url: str = None):
        self.services: Dict[str, Any] = {}
        self.event_listeners: Dict[str, List[callable]] = {}
        self._redis_bus: Optional[RedisEventBus] = None
        self._redis_url = redis_url
        logger.info("ServiceIntegrationHub initialized")

    async def initialize_redis(self, redis_url: str = None) -> None:
        """Initialize Redis event bus for multi-instance pub/sub"""
        if self._redis_bus is None:
            url = redis_url or self._redis_url or "redis://localhost:6379"
            self._redis_bus = RedisEventBus(url)
            await self._redis_bus.connect()

            # Subscribe to cross-instance event channels
            channels = ["fraud.detected", "transaction.completed", "admin.alert"]
            for channel in channels:
                self._redis_bus.subscribe(channel, self._handle_redis_event)

            # Start Redis listener if connected
            if self._redis_bus._redis:
                asyncio.create_task(
                    self._redis_bus._start_subscription(channels)
                )
                logger.info("Redis event bus initialized for multi-instance support")

    def register_service(self, name: str, service: Any) -> None:
        """Register a service module"""
        self.services[name] = service
        logger.info(f"Service registered: {name}")

    def on_event(self, event_type: str, callback: callable) -> None:
        """Register event listener for service events"""
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        self.event_listeners[event_type].append(callback)
        logger.debug(f"Event listener registered: {event_type}")

    async def emit_event(self, event_type: str, data: Any, context: ServiceContext) -> None:
        """Emit an event to all registered listeners"""
        logger.info(f"Emitting event: {event_type}", extra={"request_id": context.request_id})

        # Publish to Redis for cross-instance communication
        if self._redis_bus:
            redis_data = {
                "event_type": event_type,
                "data": data if isinstance(data, dict) else asdict(data) if hasattr(data, '__dict__') else str(data),
                "context": context.to_dict() if hasattr(context, 'to_dict') else str(context),
            }
            await self._redis_bus.publish(event_type, redis_data)

        # Local event handlers
        if event_type in self.event_listeners:
            tasks = [
                callback(data, context)
                for callback in self.event_listeners[event_type]
            ]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _handle_redis_event(self, data: Dict[str, Any]) -> None:
        """Handle events received from Redis pub/sub"""
        try:
            event_type = data.get("event_type")
            event_data = data.get("data")
            logger.debug(f"Received Redis event: {event_type}")
            # Redis events are already published to local listeners via emit_event
            # This is just for logging/monitoring
        except Exception as exc:
            logger.error(f"Error handling Redis event: {exc}")

    # ===== TRANSACTION FLOW =====

    async def process_transaction(
        self, transaction_data: Dict[str, Any], context: ServiceContext
    ) -> Dict[str, Any]:
        """
        Main transaction processing flow:
        1. Validate transaction
        2. Run fraud detection
        3. Process transaction
        4. Log activity
        5. Notify admin (if fraud detected)
        """
        try:
            logger.info(f"Processing transaction", extra={"request_id": context.request_id})

            # Step 1: Validate
            await self.emit_event("transaction.validating", transaction_data, context)

            # Step 2: Run fraud detection
            fraud_result = await self._run_fraud_detection(transaction_data, context)

            if fraud_result.get("is_suspicious", False):
                logger.warning(
                    f"Fraud detected in transaction by user {context.user_id}",
                    extra={"request_id": context.request_id},
                )
                await self.emit_event("fraud.detected", fraud_result, context)

                return {
                    "status": ProcessingStatus.FRAUD_DETECTED,
                    "fraud_alert": fraud_result,
                    "transaction": transaction_data,
                }

            # Step 3: Process transaction
            await self.emit_event("transaction.processing", transaction_data, context)

            # Step 4: Log activity
            await self.emit_event("audit.log",
                {
                    "action": "transaction_processed",
                    "user_id": context.user_id,
                    "transaction": transaction_data,
                },
                context,
            )

            # Step 5: Emit completion event for Redis subscribers
            await self.emit_event("transaction.completed", transaction_data, context)

            logger.info(f"Transaction processed successfully", extra={"request_id": context.request_id})

            return {
                "status": ProcessingStatus.COMPLETED,
                "transaction": transaction_data,
                "fraud_check": fraud_result,
            }

        except Exception as exc:
            logger.exception(f"Transaction processing failed", extra={"request_id": context.request_id})
            await self.emit_event(
                "error.occurred",
                {
                    "error": str(exc),
                    "type": type(exc).__name__,
                },
                context,
            )
            return {"status": ProcessingStatus.FAILED, "error": str(exc)}

    # ===== FRAUD DETECTION FLOW =====

    async def _run_fraud_detection(
        self, transaction_data: Dict[str, Any], context: ServiceContext
    ) -> Dict[str, Any]:
        """
        Run fraud detection internally.
        Calls fraud detection service if available.
        """
        try:
            fraud_service = self.services.get("fraud_detection")
            if not fraud_service:
                logger.warning("Fraud detection service not available")
                return {"is_suspicious": False, "risk_score": 0}

            # Run fraud analysis
            fraud_result = await fraud_service.analyze_transaction(
                transaction_data, context
            )

            logger.debug(
                f"Fraud analysis completed: risk_score={fraud_result.get('risk_score')}",
                extra={"request_id": context.request_id},
            )

            return fraud_result

        except Exception as exc:
            logger.error(
                f"Fraud detection service error: {str(exc)}",
                extra={"request_id": context.request_id},
            )
            return {"is_suspicious": False, "risk_score": 0, "error": str(exc)}

    # ===== ANALYTICS FLOW =====

    async def record_transaction_for_analytics(
        self, transaction_data: Dict[str, Any], context: ServiceContext
    ) -> None:
        """Record transaction in analytics"""
        try:
            analytics_service = self.services.get("analytics")
            if analytics_service:
                await analytics_service.record(transaction_data, context)
        except Exception as exc:
            logger.error(f"Analytics recording failed: {str(exc)}")

    # ===== ADMIN NOTIFICATION FLOW =====

    async def notify_admin_fraud_alert(
        self, fraud_alert: Dict[str, Any], context: ServiceContext
    ) -> None:
        """Notify admins of fraud alert"""
        try:
            websocket_service = self.services.get("websocket")
            if websocket_service:
                await websocket_service.broadcast_admin_alert(fraud_alert, context)
                logger.info(
                    "Admin notified of fraud alert",
                    extra={"request_id": context.request_id},
                )

            # Also broadcast via Redis for multi-instance support
            await self.emit_event("admin.alert", fraud_alert, context)

        except Exception as exc:
            logger.error(f"Admin notification failed: {str(exc)}")

    # ===== USER ACTIVITY LOGGING =====

    async def log_user_activity(
        self,
        action: str,
        user_id: str,
        details: Dict[str, Any],
        context: ServiceContext,
    ) -> None:
        """Log user activity for audit trail"""
        try:
            await self.emit_event(
                "audit.activity_logged",
                {
                    "action": action,
                    "user_id": user_id,
                    "details": details,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                context,
            )
        except Exception as exc:
            logger.error(f"Activity logging failed: {str(exc)}")

    # ===== ADMIN ACTION FLOW =====

    async def execute_admin_action(
        self, action: str, target_id: str, context: ServiceContext, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute admin actions:
        - Block account
        - Unblock account
        - Escalate fraud alert
        - Mark transaction as safe
        """
        try:
            logger.info(
                f"Admin action executed: {action} on {target_id}",
                extra={"request_id": context.request_id},
            )

            # Log the admin action
            await self.log_user_activity(
                action=f"admin_{action}",
                user_id=context.user_id,
                details={"target_id": target_id, **kwargs},
                context=context,
            )

            # Emit admin action event
            await self.emit_event(
                f"admin.{action}",
                {"target_id": target_id, **kwargs},
                context,
            )

            return {"status": "success", "action": action}

        except Exception as exc:
            logger.error(f"Admin action failed: {str(exc)}")
            return {"status": "failed", "error": str(exc)}


# Global service hub instance
_service_hub: Optional[ServiceIntegrationHub] = None


def get_service_hub() -> ServiceIntegrationHub:
    """Get or create the global service integration hub"""
    global _service_hub
    if _service_hub is None:
        _service_hub = ServiceIntegrationHub()
    return _service_hub


def initialize_service_hub(redis_url: str = None) -> ServiceIntegrationHub:
    """Initialize the service hub with all registered services"""
    hub = get_service_hub()
    logger.info("Service integration hub ready")
    return hub


async def initialize_service_hub_async(redis_url: str = None) -> ServiceIntegrationHub:
    """Async initialize the service hub with Redis pub/sub support"""
    hub = get_service_hub()
    await hub.initialize_redis(redis_url)
    logger.info("Service integration hub ready with Redis pub/sub")
    return hub
