from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.services.notification import NotificationService
from app.routers.users import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str | None
    is_read: bool
    created_at: str

    class Config:
        from_attributes = True


class NotificationCount(BaseModel):
    unread_count: int


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all notifications for current user"""
    notifications = await NotificationService.get_user_notifications(
        db,
        current_user.id,
        limit
    )
    return [
        NotificationResponse(
            id=str(n.id),
            type=n.type,
            title=n.title,
            message=n.message,
            is_read=n.is_read,
            created_at=n.created_at.isoformat()
        )
        for n in notifications
    ]


@router.get("/unread-count", response_model=NotificationCount)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    count = await NotificationService.get_unread_count(db, current_user.id)
    return NotificationCount(unread_count=count)


@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    from uuid import UUID
    await NotificationService.mark_as_read(db, current_user.id, UUID(notification_id))
    return {"message": "Notification marked as read"}


@router.put("/read-all")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read"""
    await NotificationService.mark_all_as_read(db, current_user.id)
    return {"message": "All notifications marked as read"}