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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # STARTUP
    logger.info("Application starting up")
    await init_db()
    logger.info("Database initialized")
    
    # Import and initialize service hub after app is fully configured
    from app.services.integration_hub import initialize_service_hub
    initialize_service_hub()
    logger.info("Service integration hub initialized")
    
    yield
    
    # SHUTDOWN
    logger.info("Application shutting down")


# ===== CREATE FASTAPI APP =====
app = FastAPI(
    title="Digital Banking Platform",
    description="Production-grade banking application with fraud detection and real-time analytics",
    version="1.0.0",
    lifespan=lifespan,
    redoc_url="/api/docs/redoc",
    swagger_ui_parameters={"syntaxHighlight": "monokai"}
)

# ===== MIDDLEWARE STACK =====
# Order matters! Apply from innermost to outermost

# 1. Rate Limiting (outermost - first to execute)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    burst_size=10
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
    """Health Check Endpoint"""
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
        "status": "healthy" if db_connected else "degraded",
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": "connected" if db_connected else "disconnected",
            "fraud_detection": True,
            "websocket": "active",
            "cache": "disabled"
        }
    }


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
    logger.exception(f"Unhandled exception: {type(exc).__name__}")
    
    import uuid
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

