"""
Analytics and Reporting Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.database import get_replica_db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.fraud_alert import FraudAlert
from app.routers.users import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/transactions-summary")
async def get_transactions_summary(
    days: int = 30,
    db: AsyncSession = Depends(get_replica_db),
    current_user: User = Depends(get_current_user)
):
    """Get transaction summary for the last N days (uses read replica)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return await _get_transactions_summary_db(db, days)


async def _get_transactions_summary_db(db: AsyncSession, days: int) -> dict:
    """Internal function to get transaction summary with provided session."""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Total transactions
    total_result = await db.execute(
        select(func.count(Transaction.id)).where(Transaction.created_at >= start_date)
    )
    total_transactions = total_result.scalar() or 0

    # Successful transactions
    success_result = await db.execute(
        select(func.count(Transaction.id)).where(
            (Transaction.created_at >= start_date) &
            (Transaction.status == "completed")
        )
    )
    successful = success_result.scalar() or 0

    # Failed transactions
    failed = total_transactions - successful

    # Total amount
    amount_result = await db.execute(
        select(func.sum(Transaction.amount)).where(Transaction.created_at >= start_date)
    )
    total_amount = float(amount_result.scalar() or 0)

    # Average transaction
    avg_result = await db.execute(
        select(func.avg(Transaction.amount)).where(Transaction.created_at >= start_date)
    )
    avg_amount = float(avg_result.scalar() or 0)

    return {
        "period": f"Last {days} days",
        "total_transactions": total_transactions,
        "successful_transactions": successful,
        "failed_transactions": failed,
        "success_rate": f"{(successful / total_transactions * 100) if total_transactions > 0 else 0:.2f}%",
        "total_amount": round(total_amount, 2),
        "average_amount": round(avg_amount, 2)
    }


@router.get("/daily-transactions")
async def get_daily_transactions(
    days: int = 30,
    db: AsyncSession = Depends(get_replica_db),
    current_user: User = Depends(get_current_user)
):
    """Get daily transaction breakdown (uses read replica)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    start_date = datetime.utcnow() - timedelta(days=days)

    # Get transactions grouped by day
    result = await db.execute(
        select(
            func.date(Transaction.created_at).label("date"),
            func.count(Transaction.id).label("count"),
            func.sum(Transaction.amount).label("total_amount")
        ).where(Transaction.created_at >= start_date)
        .group_by(func.date(Transaction.created_at))
        .order_by(func.date(Transaction.created_at))
    )

    data = []
    for row in result:
        data.append({
            "date": row[0].isoformat(),
            "transactions": row[1],
            "total_amount": round(float(row[2] or 0), 2)
        })

    return {"data": data}


@router.get("/user-growth")
async def get_user_growth(
    days: int = 30,
    db: AsyncSession = Depends(get_replica_db),
    current_user: User = Depends(get_current_user)
):
    """Get user growth metrics (uses read replica)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    start_date = datetime.utcnow() - timedelta(days=days)

    # New users
    new_users_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= start_date)
    )
    new_users = new_users_result.scalar() or 0

    # Total users
    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar() or 0

    # Active users (with transactions)
    active_result = await db.execute(
        select(func.count(func.distinct(Transaction.from_account_id))).where(
            Transaction.created_at >= start_date
        )
    )
    active_users = active_result.scalar() or 0

    # KYC approved
    kyc_result = await db.execute(
        select(func.count(User.id)).where(User.kyc_status == "approved")
    )
    kyc_approved = kyc_result.scalar() or 0

    return {
        "total_users": total_users,
        "new_users_period": new_users,
        "active_users": active_users,
        "kyc_approved": kyc_approved,
        "kyc_approval_rate": f"{(kyc_approved / total_users * 100) if total_users > 0 else 0:.2f}%"
    }


@router.get("/fraud-metrics")
async def get_fraud_metrics(
    days: int = 30,
    db: AsyncSession = Depends(get_replica_db),
    current_user: User = Depends(get_current_user)
):
    """Get fraud detection metrics (uses read replica)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    start_date = datetime.utcnow() - timedelta(days=days)

    # Total alerts
    total_result = await db.execute(
        select(func.count(FraudAlert.id)).where(FraudAlert.created_at >= start_date)
    )
    total_alerts = total_result.scalar() or 0

    # High risk
    high_result = await db.execute(
        select(func.count(FraudAlert.id)).where(
            (FraudAlert.created_at >= start_date) &
            (FraudAlert.risk_level == "high")
        )
    )
    high_risk = high_result.scalar() or 0

    # Blocked accounts
    blocked_result = await db.execute(
        select(func.count(FraudAlert.id)).where(
            (FraudAlert.created_at >= start_date) &
            (FraudAlert.status == "blocked")
        )
    )
    blocked = blocked_result.scalar() or 0

    # Average risk score
    avg_result = await db.execute(
        select(func.avg(FraudAlert.risk_score)).where(FraudAlert.created_at >= start_date)
    )
    avg_risk = float(avg_result.scalar() or 0)

    return {
        "total_alerts": total_alerts,
        "high_risk_alerts": high_risk,
        "blocked_accounts": blocked,
        "average_risk_score": round(avg_risk, 2),
        "high_risk_ratio": f"{(high_risk / total_alerts * 100) if total_alerts > 0 else 0:.2f}%"
    }


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_replica_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive dashboard statistics (uses read replica)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Get all metrics using the same replica db session
    trans_summary = await _get_transactions_summary_db(db, 7)
    user_growth = await _get_user_growth_db(db, 30)
    fraud_metrics = await _get_fraud_metrics_db(db, 7)

    return {
        "transactions": trans_summary,
        "users": user_growth,
        "fraud": fraud_metrics,
        "timestamp": datetime.utcnow().isoformat()
    }


async def _get_user_growth_db(db: AsyncSession, days: int) -> dict:
    """Internal function to get user growth with provided session."""
    start_date = datetime.utcnow() - timedelta(days=days)

    new_users_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= start_date)
    )
    new_users = new_users_result.scalar() or 0

    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(func.distinct(Transaction.from_account_id))).where(
            Transaction.created_at >= start_date
        )
    )
    active_users = active_result.scalar() or 0

    kyc_result = await db.execute(
        select(func.count(User.id)).where(User.kyc_status == "approved")
    )
    kyc_approved = kyc_result.scalar() or 0

    return {
        "total_users": total_users,
        "new_users_period": new_users,
        "active_users": active_users,
        "kyc_approved": kyc_approved,
        "kyc_approval_rate": f"{(kyc_approved / total_users * 100) if total_users > 0 else 0:.2f}%"
    }


async def _get_fraud_metrics_db(db: AsyncSession, days: int) -> dict:
    """Internal function to get fraud metrics with provided session."""
    start_date = datetime.utcnow() - timedelta(days=days)

    total_result = await db.execute(
        select(func.count(FraudAlert.id)).where(FraudAlert.created_at >= start_date)
    )
    total_alerts = total_result.scalar() or 0

    high_result = await db.execute(
        select(func.count(FraudAlert.id)).where(
            (FraudAlert.created_at >= start_date) &
            (FraudAlert.risk_level == "high")
        )
    )
    high_risk = high_result.scalar() or 0

    blocked_result = await db.execute(
        select(func.count(FraudAlert.id)).where(
            (FraudAlert.created_at >= start_date) &
            (FraudAlert.status == "blocked")
        )
    )
    blocked = blocked_result.scalar() or 0

    avg_result = await db.execute(
        select(func.avg(FraudAlert.risk_score)).where(FraudAlert.created_at >= start_date)
    )
    avg_risk = float(avg_result.scalar() or 0)

    return {
        "total_alerts": total_alerts,
        "high_risk_alerts": high_risk,
        "blocked_accounts": blocked,
        "average_risk_score": round(avg_risk, 2),
        "high_risk_ratio": f"{(high_risk / total_alerts * 100) if total_alerts > 0 else 0:.2f}%"
    }
