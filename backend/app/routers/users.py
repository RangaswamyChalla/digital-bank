import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth import AuthService

router = APIRouter(prefix="/users", tags=["Users"])


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
) -> User:
    """Dependency to get current authenticated user from JWT token"""
    token = None

    # Try Authorization header first
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    # Fall back to cookie
    elif access_token:
        token = access_token
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = AuthService.decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user information"""
    if user_update.full_name:
        current_user.full_name = user_update.full_name
    if user_update.phone:
        current_user.phone = user_update.phone

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/me/rate-limit-status")
async def get_rate_limit_status(
    current_user: User = Depends(get_current_user)
):
    """Get current user's rate limit status"""
    from app.middleware.per_user_rate_limit import get_current_user_rate_limit_status

    usage = await get_current_user_rate_limit_status(str(current_user.id))

    return {
        "user_id": str(current_user.id),
        "rate_limits": usage
    }
