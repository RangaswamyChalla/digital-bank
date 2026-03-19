from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import traceback
import logging

from app.config import settings
from app.database import init_db
from app.middleware.error_handling import (
    setup_logging,
    ErrorHandlingMiddleware,
    RequestLoggingMiddleware,
)
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import (
    auth_router,
    users_router,
    accounts_router,
    transactions_router,
    transactions_history,
    kyc_router,
    notifications_router,
    admin_router,
    fraud,
    analytics,
    websocket
)

# ===== INITIALIZE LOGGING =====
logger = setup_logging()


def setup_sentry():
    """Initialize Sentry if DSN is configured"""
    import os
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlAlchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            environment=settings.ENVIRONMENT,
            release="digital-bank@1.0.0",
        )
        logger.info("Sentry error tracking initialized")
    else:
        logger.info("Sentry DSN not configured - error tracking disabled")


def setup_opentelemetry():
    """Initialize OpenTelemetry tracing if configured"""
    import os
    otlp_endpoint = os.getenv("OTLP_ENDPOINT")

    if otlp_endpoint:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        # Create resource with service name
        resource = Resource(attributes={
            SERVICE_NAME: "digital-bank-api"
        })

        # Set up tracer provider
        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        logger.info(f"OpenTelemetry tracing initialized - exporting to {otlp_endpoint}")
        return True
    else:
        logger.info("OTLP_ENDPOINT not configured - OpenTelemetry tracing disabled")
        return False


def instrument_app():
    """Instrument FastAPI and SQLAlchemy with OpenTelemetry"""
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from app.database import engine

    # Instrument FastAPI (after app is created)
    # Note: This is called after app creation below
    logger.info("OpenTelemetry instrumentation configured")


setup_sentry()
otel_enabled = setup_opentelemetry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("Application starting up")
    await init_db()
    logger.info("Database initialized")

    yield

    logger.info("Application shutting down")
    try:
        from app.database import engine
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# ===== CREATE FASTAPI APP =====
app = FastAPI(
    title="Digital Banking Platform",
    description="Production-grade banking application with fraud detection and real-time analytics",
    version="1.0.0",
    lifespan=lifespan,
    redoc_url="/api/docs/redoc",
    swagger_ui_parameters={"syntaxHighlight": "monokai"}
)

# Instrument FastAPI with OpenTelemetry (if enabled)
if otel_enabled:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from app.database import engine
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

# ===== MIDDLEWARE STACK =====
# Order matters! Apply from innermost to outermost

# 1. Rate Limiting (outermost - first to execute)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    burst_size=10,
    redis_url=settings.REDIS_URL
)

# 2. Error Handling Middleware (catches all errors)
app.add_middleware(ErrorHandlingMiddleware, logger=logger)

# 2. Request/Response Logging Middleware
app.add_middleware(RequestLoggingMiddleware, logger=logger)

# 3. CORS Middleware (security)
cors_origins = settings.BACKEND_CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# 4. Security Headers Middleware
from app.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# 5. Request Timeout Middleware
from app.middleware.timeout import TimeoutMiddleware
app.add_middleware(TimeoutMiddleware, timeout_seconds=30)

# ===== ROUTERS =====
# Authentication
app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])

# User Management
app.include_router(users_router, prefix="/api/v1", tags=["Users"])

# Accounts
app.include_router(accounts_router, prefix="/api/v1", tags=["Accounts"])

# Transactions
app.include_router(transactions_router, prefix="/api/v1", tags=["Transactions"])
app.include_router(transactions_history.router, prefix="/api/v1", tags=["Transaction History"])

# KYC
app.include_router(kyc_router, prefix="/api/v1", tags=["KYC"])

# Notifications
app.include_router(notifications_router, prefix="/api/v1", tags=["Notifications"])

# Admin
app.include_router(admin_router, prefix="/api/v1", tags=["Admin"])

# Fraud Detection
app.include_router(fraud.router, prefix="/api/v1", tags=["Fraud Detection"])

# Analytics
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])

# WebSocket (Real-time)
app.include_router(websocket.router, tags=["Real-time"])


# ===== HEALTH & STATUS ENDPOINTS =====

@app.get("/", tags=["System"])
async def root():
    """API Root - System Information"""
    return {
        "name": "Digital Banking Platform",
        "version": "1.0.0",
        "environment": "development",
        "status": "operational"
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Basic health check - returns overall status."""
    from app.database import engine
    from sqlalchemy import text

    # Check database connectivity
    db_connected = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_connected = True
    except Exception:
        db_connected = False

    # Check Redis connectivity
    redis_connected = False
    try:
        from app.services.integration_hub import get_service_hub
        hub = get_service_hub()
        if hub._redis_bus and hub._redis_bus._redis:
            await hub._redis_bus._redis.ping()
            redis_connected = True
    except Exception:
        redis_connected = False

    # Check WebSocket manager
    from app.routers.websocket import manager
    websocket_active = manager is not None

    overall_status = "healthy" if db_connected else "degraded"

    return {
        "status": overall_status,
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": "connected" if db_connected else "disconnected",
            "redis": "connected" if redis_connected else "disconnected",
            "websocket": "active" if websocket_active else "inactive",
        }
    }


@app.get("/health/ready", tags=["System"])
async def readiness_check():
    """
    Readiness probe - checks if the app is ready to receive traffic.
    Used by Kubernetes to determine when to route traffic to this instance.
    """
    from app.database import engine
    from sqlalchemy import text

    checks = {}
    all_ready = True

    # Database check
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "ready"}
    except Exception as e:
        checks["database"] = {"status": "not_ready", "error": str(e)}
        all_ready = False

    # Redis check (optional - app can work without Redis)
    try:
        from app.services.integration_hub import get_service_hub
        hub = get_service_hub()
        if hub._redis_bus and hub._redis_bus._redis:
            await hub._redis_bus._redis.ping()
            checks["redis"] = {"status": "ready"}
        else:
            checks["redis"] = {"status": "not_configured"}
    except Exception as e:
        checks["redis"] = {"status": "degraded", "error": str(e)}
        # Redis is not critical - don't fail readiness

    status_code = 200 if all_ready else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_ready,
            "checks": checks
        }
    )


@app.get("/health/live", tags=["System"])
async def liveness_check():
    """
    Liveness probe - checks if the app is alive.
    Used by Kubernetes to determine if the container should be restarted.
    Returns 200 if the app is running, regardless of dependencies.
    """
    return {"alive": True, "timestamp": __import__('datetime').datetime.utcnow().isoformat()}


@app.get("/metrics", tags=["System"])
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/api/v1/system/status", tags=["System"])
async def system_status():
    """Detailed System Status"""
    from app.database import engine
    from sqlalchemy import text

    # Actually check database connectivity
    db_connected = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_connected = True
    except Exception:
        db_connected = False

    return {
        "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
        "application": {
            "name": "Digital Banking Platform",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG
        },
        "services": {
            "database": {
                "enabled": True,
                "connected": db_connected,
                "url_configured": bool(settings.DATABASE_URL)
            },
            "fraud_detection": {
                "enabled": True,
                "timeout_seconds": 30
            },
            "cache": {
                "enabled": False,
                "host": None
            },
            "logging": {
                "level": "INFO",
                "format": "json"
            }
        },
        "security": {
            "cors_origins": len(settings.BACKEND_CORS_ORIGINS),
            "jwt_algorithm": settings.ALGORITHM,
            "token_expiry_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES
        }
    }


# ===== ERROR HANDLERS =====

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Fallback global exception handler (for non-BankingException errors)"""
    import traceback
    print(f"[ERROR] Unhandled exception: {type(exc).__name__}", flush=True)
    print(traceback.format_exc(), flush=True)

    request_id = str(uuid.uuid4())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request_id
            }
        }
    )


# ===== STARTUP/SHUTDOWN EVENTS =====

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("FastAPI application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("FastAPI application shutdown")

