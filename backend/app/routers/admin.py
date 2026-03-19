from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.routers.users import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminStats(BaseModel):
    total_users: int
    total_accounts: int
    total_transactions: int
    pending_kyc: int


class UserListItem(BaseModel):
    id: str
    email: str
    full_name: str
    kyc_level: int
    kyc_status: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get admin dashboard statistics"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Count total users
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar() or 0

    # Count total accounts
    result = await db.execute(select(func.count(Account.id)))
    total_accounts = result.scalar() or 0

    # Count total transactions
    result = await db.execute(select(func.count(Transaction.id)))
    total_transactions = result.scalar() or 0

    # Count pending KYC
    result = await db.execute(
        select(func.count(User.id)).where(User.kyc_status == "submitted")
    )
    pending_kyc = result.scalar() or 0

    return AdminStats(
        total_users=total_users,
        total_accounts=total_accounts,
        total_transactions=total_transactions,
        pending_kyc=pending_kyc
    )


@router.get("/users", response_model=List[UserListItem])
async def get_all_users(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    )
    users = result.scalars().all()

    return [
        UserListItem(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            kyc_level=u.kyc_level,
            kyc_status=u.kyc_status,
            is_active=u.is_active,
            created_at=u.created_at.isoformat()
        )
        for u in users
    ]


class LockUserRequest(BaseModel):
    locked: bool


@router.put("/users/{user_id}/lock")
async def lock_user(
    user_id: str,
    request: LockUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lock or unlock a user account (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from uuid import UUID

    # Prevent admin from locking themselves
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="Cannot lock or unlock your own account")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not request.locked
    await db.commit()

    return {"message": f"User {'locked' if request.locked else 'unlocked'} successfully"}