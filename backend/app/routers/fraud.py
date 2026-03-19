"""
Fraud Detection and Alert Management Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.database import get_db
from app.models.fraud_alert import FraudAlert
from app.models.user import User
from app.routers.users import get_current_user
from app.services.fraud_detection import FraudDetectionService, FraudAlertRequest, FraudAlertResponse
import json

router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])


@router.get("/alerts")
async def get_fraud_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    status_filter: str = None
):
    """
    Get fraud alerts (admin only)
    Can filter by status: open, escalated, blocked, verified_safe
    """
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view fraud alerts"
        )
    
    query = select(FraudAlert)
    
    if status_filter:
        query = query.where(FraudAlert.status == status_filter)
    
    query = query.order_by(desc(FraudAlert.created_at)).limit(limit).offset(offset)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [
        {
            "id": str(alert.id),
            "user_id": str(alert.user_id),
            "transaction_id": str(alert.transaction_id) if alert.transaction_id else None,
            "risk_score": alert.risk_score,
            "risk_level": alert.risk_level,
            "reasons": json.loads(alert.reasons) if alert.reasons else [],
            "recommended_action": alert.recommended_action,
            "status": alert.status,
            "admin_action": alert.admin_action,
            "created_at": alert.created_at.isoformat(),
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
        }
        for alert in alerts
    ]


@router.get("/alerts/{alert_id}")
async def get_alert_details(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed fraud alert information"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    
    result = await db.execute(
        select(FraudAlert).where(FraudAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Get user info
    user_result = await db.execute(
        select(User).where(User.id == alert.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    return {
        "alert": {
            "id": str(alert.id),
            "risk_score": alert.risk_score,
            "risk_level": alert.risk_level,
            "reasons": json.loads(alert.reasons) if alert.reasons else [],
            "status": alert.status,
            "created_at": alert.created_at.isoformat()
        },
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "kyc_status": user.kyc_status,
            "is_active": user.is_active
        }
    }


@router.post("/alerts/{alert_id}/action")
async def take_fraud_action(
    alert_id: str,
    action: str,  # block, verify_safe, escalate
    notes: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Take action on a fraud alert
    Actions: block, verify_safe, escalate
    """
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    
    result = await db.execute(
        select(FraudAlert).where(FraudAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Update alert
    if action == "block":
        alert.status = "blocked"
        alert.admin_action = "ACCOUNT_BLOCKED"
        # Block user account
        user_result = await db.execute(
            select(User).where(User.id == alert.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.is_active = False
    
    elif action == "verify_safe":
        alert.status = "verified_safe"
        alert.admin_action = "VERIFIED_SAFE"
    
    elif action == "escalate":
        alert.status = "escalated"
        alert.admin_action = "ESCALATED_TO_SECURITY"
    
    alert.admin_notes = notes
    alert.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(alert)
    
    return {
        "message": f"Alert {alert_id} marked as {action}",
        "status": alert.status
    }


@router.get("/user-risk/{user_id}")
async def get_user_fraud_risk(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get fraud risk profile for a user"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    
    risk_profile = await FraudDetectionService.get_user_risk_profile(db, user_id)
    
    # Get recent fraud alerts
    alerts_result = await db.execute(
        select(FraudAlert).where(
            and_(
                FraudAlert.user_id == user_id,
                FraudAlert.status == "open"
            )
        ).order_by(desc(FraudAlert.created_at)).limit(5)
    )
    recent_alerts = alerts_result.scalars().all()
    
    return {
        "profile": risk_profile,
        "recent_alerts": [
            {
                "id": str(a.id),
                "risk_level": a.risk_level,
                "risk_score": a.risk_score,
                "created_at": a.created_at.isoformat()
            }
            for a in recent_alerts
        ]
    }


@router.get("/statistics")
async def get_fraud_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get fraud detection statistics"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    
    # Count alerts by status
    total_result = await db.execute(select(FraudAlert))
    total_alerts = len(total_result.scalars().all())
    
    open_result = await db.execute(
        select(FraudAlert).where(FraudAlert.status == "open")
    )
    open_alerts = len(open_result.scalars().all())
    
    high_risk_result = await db.execute(
        select(FraudAlert).where(FraudAlert.risk_level == "high")
    )
    high_risk = len(high_risk_result.scalars().all())
    
    blocked_result = await db.execute(
        select(FraudAlert).where(FraudAlert.status == "blocked")
    )
    blocked_accounts = len(blocked_result.scalars().all())
    
    return {
        "total_alerts": total_alerts,
        "open_alerts": open_alerts,
        "high_risk_alerts": high_risk,
        "blocked_accounts": blocked_accounts,
        "alert_resolution_rate": f"{((total_alerts - open_alerts) / total_alerts * 100) if total_alerts > 0 else 0:.2f}%"
    }


# Import datetime at the top for update_at
from datetime import datetime
