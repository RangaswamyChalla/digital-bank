from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.schemas.user import KYCSubmit, UserResponse
from app.services.kyc import KYCService
from app.routers.users import get_current_user

router = APIRouter(prefix="/kyc", tags=["KYC"])


class KYCStatusResponse(BaseModel):
    kyc_level: int
    kyc_status: str
    kyc_submitted_at: str | None
    kyc_reviewed_at: str | None
    kyc_rejection_reason: str | None


@router.post("/submit", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def submit_kyc(
    kyc_data: KYCSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit KYC documents for verification"""
    return await KYCService.submit_kyc(db, current_user.id, kyc_data)


@router.get("/status", response_model=KYCStatusResponse)
async def get_kyc_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current KYC status for current user"""
    status = await KYCService.get_kyc_status(db, current_user.id)
    return KYCStatusResponse(
        kyc_level=status["kyc_level"],
        kyc_status=status["kyc_status"],
        kyc_submitted_at=status["kyc_submitted_at"].isoformat() if status["kyc_submitted_at"] else None,
        kyc_reviewed_at=status["kyc_reviewed_at"].isoformat() if status["kyc_reviewed_at"] else None,
        kyc_rejection_reason=status["kyc_rejection_reason"]
    )


# Admin KYC endpoints
admin_router = APIRouter(prefix="/admin/kyc", tags=["Admin KYC"])


@admin_router.get("/list", response_model=List[UserResponse])
async def list_pending_kyc(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all pending KYC applications (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return await KYCService.get_pending_kyc_applications(db)


class KYCReviewRequest(BaseModel):
    approved: bool
    reason: str | None = None


@admin_router.put("/review/{user_id}", response_model=UserResponse)
async def review_kyc(
    user_id: str,
    review: KYCReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject a KYC application (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from uuid import UUID
    return await KYCService.review_kyc(
        db,
        current_user.id,
        UUID(user_id),
        review.approved,
        review.reason
    )