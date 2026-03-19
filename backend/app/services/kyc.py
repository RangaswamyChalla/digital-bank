import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.user import KYCSubmit


class KYCService:
    @staticmethod
    async def submit_kyc(db: AsyncSession, user_id: uuid.UUID, kyc_data: KYCSubmit) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.kyc_status in ["submitted", "approved"]:
            raise HTTPException(
                status_code=400,
                detail="KYC already submitted or approved"
            )

        # Update user KYC info
        user.kyc_document_type = kyc_data.document_type
        user.kyc_document_number = kyc_data.document_number
        user.kyc_document_file = kyc_data.document_file
        user.kyc_address = kyc_data.address
        user.kyc_status = "submitted"
        user.kyc_submitted_at = datetime.utcnow()

        # Create audit log
        audit_log = AuditLog(
            user_id=user_id,
            action="kyc_submitted",
            entity_type="user",
            entity_id=user_id,
            details={
                "document_type": kyc_data.document_type,
                "document_number": kyc_data.document_number[-4:]  # Only last 4 digits
            }
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_kyc_status(db: AsyncSession, user_id: uuid.UUID) -> dict:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "kyc_level": user.kyc_level,
            "kyc_status": user.kyc_status,
            "kyc_submitted_at": user.kyc_submitted_at,
            "kyc_reviewed_at": user.kyc_reviewed_at,
            "kyc_rejection_reason": user.kyc_rejection_reason
        }

    @staticmethod
    async def get_pending_kyc_applications(db: AsyncSession) -> List[User]:
        result = await db.execute(
            select(User).where(
                User.kyc_status == "submitted"
            ).order_by(User.kyc_submitted_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def review_kyc(
        db: AsyncSession,
        admin_user_id: uuid.UUID,
        user_id: uuid.UUID,
        approved: bool,
        reason: Optional[str] = None
    ) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.kyc_status != "submitted":
            raise HTTPException(
                status_code=400,
                detail="KYC application not in submitted status"
            )

        if approved:
            user.kyc_status = "approved"
            user.kyc_level = 2
            user.kyc_reviewed_at = datetime.utcnow()
            user.kyc_reviewed_by = admin_user_id
            status_action = "kyc_approved"
        else:
            user.kyc_status = "rejected"
            user.kyc_reviewed_at = datetime.utcnow()
            user.kyc_reviewed_by = admin_user_id
            user.kyc_rejection_reason = reason
            status_action = "kyc_rejected"

        # Create audit log
        audit_log = AuditLog(
            user_id=admin_user_id,
            action=status_action,
            entity_type="user",
            entity_id=user_id,
            details={"reason": reason} if reason else None
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(user)
        return user