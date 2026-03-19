# Routers exports
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.accounts import router as accounts_router
from app.routers.transactions import router as transactions_router
from app.routers.kyc import router as kyc_router
from app.routers.notifications import router as notifications_router
from app.routers.admin import router as admin_router
from app.routers import transactions_history
from app.routers import fraud
from app.routers import analytics
from app.routers import websocket

__all__ = [
    "auth_router",
    "users_router",
    "accounts_router",
    "transactions_router",
    "kyc_router",
    "notifications_router",
    "admin_router",
    "transactions_history",
    "fraud",
    "analytics",
    "websocket"
]