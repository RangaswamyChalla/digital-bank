"""
WebSocket handlers for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, status
from typing import Set
import json
from datetime import datetime
from app.database import get_db
from app.services.auth import AuthService
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.user_connections: dict = {}  # user_id -> list of WebSockets
        self.admin_connections: Set[WebSocket] = set()  # admin users

    async def connect(self, websocket: WebSocket, user_id: str, is_admin: bool = False):
        """Add a new connection"""
        await websocket.accept()
        self.active_connections.add(websocket)

        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

        if is_admin:
            self.admin_connections.add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str, is_admin: bool = False):
        """Remove a connection"""
        self.active_connections.discard(websocket)

        if user_id in self.user_connections:
            self.user_connections[user_id] = [
                ws for ws in self.user_connections[user_id] if ws != websocket
            ]
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        if is_admin:
            self.admin_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")
                self.active_connections.discard(connection)

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user's connections"""
        if user_id in self.user_connections:
            for connection in list(self.user_connections[user_id]):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending message to user {user_id}: {e}")
                    self.disconnect(connection, user_id)

    async def send_to_admins(self, message: dict):
        """Send message to admin users"""
        for connection in list(self.admin_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message to admin: {e}")
                self.admin_connections.discard(connection)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/transactions/{user_id}")
async def websocket_transactions(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(...)
):
    """WebSocket endpoint for real-time transaction updates - user can only access their own data"""
    # Verify token and extract user info
    try:
        payload = AuthService.decode_token(token)
        token_user_id = payload.get("user_id")
        user_role = payload.get("role", "customer")

        # Users can only subscribe to their own transactions
        # Admins can subscribe to any user's transactions
        if token_user_id != user_id and user_role != "admin":
            await websocket.close(code=4001, reason="Unauthorized")
            return

    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    is_admin = user_role == "admin"
    await manager.connect(websocket, user_id, is_admin)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now, can be enhanced for specific handlers
            message = {
                "type": "ping",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            await manager.send_to_user(user_id, message)
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, is_admin)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id, is_admin)


@router.websocket("/admin/alerts/{admin_user_id}")
async def websocket_fraud_alerts(
    websocket: WebSocket,
    admin_user_id: str,
    token: str = Query(...)
):
    """WebSocket endpoint for fraud alerts (admin only)"""
    # Verify token and admin role
    try:
        payload = AuthService.decode_token(token)
        token_user_id = payload.get("user_id")
        user_role = payload.get("role", "customer")

        if user_role != "admin":
            await websocket.close(code=4001, reason="Admin access required")
            return

        # Admin can only subscribe to their own alerts stream
        if token_user_id != admin_user_id:
            await websocket.close(code=4001, reason="Unauthorized")
            return

    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await manager.connect(websocket, admin_user_id, is_admin=True)
    try:
        while True:
            # Receive heartbeat/control messages
            data = await websocket.receive_text()

            # Parse message
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "ping")

                if msg_type == "ping":
                    # Send pong back
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, admin_user_id, is_admin=True)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, admin_user_id, is_admin=True)


@router.websocket("/admin/dashboard/{admin_user_id}")
async def websocket_admin_dashboard(
    websocket: WebSocket,
    admin_user_id: str,
    token: str = Query(...)
):
    """WebSocket endpoint for admin dashboard live updates"""
    # Verify token and admin role
    try:
        payload = AuthService.decode_token(token)
        token_user_id = payload.get("user_id")
        user_role = payload.get("role", "customer")

        if user_role != "admin":
            await websocket.close(code=4001, reason="Admin access required")
            return

        if token_user_id != admin_user_id:
            await websocket.close(code=4001, reason="Unauthorized")
            return

    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await manager.connect(websocket, admin_user_id, is_admin=True)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()

            try:
                msg = json.loads(data)

                if msg.get("type") == "subscribe":
                    # Handle subscription to specific updates
                    await websocket.send_json({
                        "type": "subscribed",
                        "channels": msg.get("channels", [])
                    })

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, admin_user_id, is_admin=True)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, admin_user_id, is_admin=True)


async def notify_fraud_alert(alert_data: dict):
    """Notify admins of new fraud alert"""
    message = {
        "type": "fraud_alert",
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.send_to_admins(message)


async def notify_transaction(user_id: str, transaction_data: dict):
    """Notify user of transaction update"""
    message = {
        "type": "transaction_update",
        "data": transaction_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.send_to_user(user_id, message)


async def notify_admin_update(update_data: dict):
    """Notify admins of system updates"""
    message = {
        "type": "system_update",
        "data": update_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.send_to_admins(message)
