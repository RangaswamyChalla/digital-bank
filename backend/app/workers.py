"""
Background tasks for Digital Bank.
Tasks are processed asynchronously by ARQ workers.
"""
import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.notification import Notification
from app.models.user import User
from app.models.fraud_alert import FraudAlert

logger = logging.getLogger(__name__)


async def process_fraud_alert_email(ctx: dict, alert_id: str, user_id: str) -> dict:
    """
    Send email notification for fraud alert to admin.
    In production, this would integrate with an email service (SendGrid, SES, etc.)
    """
    logger.info(f"Processing fraud alert email for alert {alert_id}")

    async with AsyncSessionLocal() as db:
        try:
            # Get fraud alert
            result = await db.execute(
                select(FraudAlert).where(FraudAlert.id == alert_id)
            )
            alert = result.scalar_one_or_none()

            if not alert:
                return {"status": "error", "message": "Alert not found"}

            # Get user
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                return {"status": "error", "message": "User not found"}

            # In production: Send email to admins
            # email_service.send(
            #     to=admin_emails,
            #     subject=f"Fraud Alert: User {user.email}",
            #     body=f"High-risk transaction detected. Risk score: {alert.risk_score}"
            # )

            logger.info(f"Fraud alert email processed for alert {alert_id}")
            return {
                "status": "success",
                "alert_id": alert_id,
                "user_email": user.email,
                "risk_score": alert.risk_score
            }

        except Exception as e:
            logger.error(f"Failed to process fraud alert email: {e}")
            return {"status": "error", "message": str(e)}


async def send_transaction_notification(
    ctx: dict,
    user_id: str,
    notification_type: str,
    title: str,
    message: str
) -> dict:
    """
    Send in-app notification to user.
    This is called after transaction processing to notify the user.
    """
    logger.info(f"Sending notification to user {user_id}: {title}")

    async with AsyncSessionLocal() as db:
        try:
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                is_read=False
            )
            db.add(notification)
            await db.commit()

            logger.info(f"Notification sent to user {user_id}")
            return {
                "status": "success",
                "notification_id": str(notification.id)
            }

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return {"status": "error", "message": str(e)}


async def send_admin_alert_notification(
    ctx: dict,
    alert_data: dict
) -> dict:
    """
    Notify admins about a new fraud alert via in-app notification.
    """
    logger.info(f"Sending admin alert notification: {alert_data.get('id', 'unknown')}")

    async with AsyncSessionLocal() as db:
        try:
            # Get all admin users
            result = await db.execute(
                select(User).where(User.role.in_(["admin", "super_admin"]))
            )
            admins = result.scalars().all()

            notifications_created = 0
            for admin in admins:
                notification = Notification(
                    user_id=admin.id,
                    type="fraud_alert",
                    title="New Fraud Alert",
                    message=f"High-risk transaction detected. Risk score: {alert_data.get('risk_score', 0)}",
                    is_read=False
                )
                db.add(notification)
                notifications_created += 1

            await db.commit()

            logger.info(f"Admin alerts sent to {notifications_created} admins")
            return {
                "status": "success",
                "admins_notified": notifications_created
            }

        except Exception as e:
            logger.error(f"Failed to send admin notifications: {e}")
            return {"status": "error", "message": str(e)}


async def cleanup_expired_tokens(ctx: dict) -> dict:
    """
    Periodic cleanup of expired refresh tokens.
    Should be scheduled to run daily.
    """
    logger.info("Running expired token cleanup")

    async with AsyncSessionLocal() as db:
        try:
            from app.models.refresh_token import RefreshToken

            # Delete expired tokens
            result = await db.execute(
                select(RefreshToken).where(RefreshToken.expires_at < datetime.utcnow())
            )
            expired_tokens = result.scalars().all()
            count = len(expired_tokens)

            for token in expired_tokens:
                await db.delete(token)

            await db.commit()

            logger.info(f"Cleaned up {count} expired tokens")
            return {
                "status": "success",
                "tokens_cleaned": count
            }

        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            return {"status": "error", "message": str(e)}


async def generate_monthly_statement(
    ctx: dict,
    user_id: str,
    account_id: str,
    month: str
) -> dict:
    """
    Generate monthly account statement.
    In production, this would generate a PDF and store/send it.
    """
    logger.info(f"Generating monthly statement for user {user_id}, account {account_id}, month {month}")

    async with AsyncSessionLocal() as db:
        try:
            from app.models.transaction import Transaction
            from app.models.account import Account

            # Get account
            result = await db.execute(
                select(Account).where(Account.id == account_id)
            )
            account = result.scalar_one_or_none()

            if not account:
                return {"status": "error", "message": "Account not found"}

            # In production: Query transactions for the month, generate PDF
            # statement = statement_generator.generate(
            #     account=account,
            #     transactions=transactions,
            #     month=month
            # )

            logger.info(f"Monthly statement generated for account {account_id}")
            return {
                "status": "success",
                "account_id": account_id,
                "month": month
            }

        except Exception as e:
            logger.error(f"Failed to generate monthly statement: {e}")
            return {"status": "error", "message": str(e)}


async def retry_failed_transaction(ctx: dict, transaction_id: str) -> dict:
    """
    Retry a failed transaction.
    Used for automatic retry of transient failures.
    """
    logger.info(f"Retrying failed transaction {transaction_id}")

    async with AsyncSessionLocal() as db:
        try:
            from app.models.transaction import Transaction

            result = await db.execute(
                select(Transaction).where(Transaction.id == transaction_id)
            )
            transaction = result.scalar_one_or_none()

            if not transaction:
                return {"status": "error", "message": "Transaction not found"}

            if transaction.status != "failed":
                return {"status": "error", "message": "Transaction is not in failed state"}

            # In production: Re-attempt the transaction
            # This would involve re-running the payment logic

            logger.info(f"Transaction {transaction_id} marked for retry")
            return {
                "status": "success",
                "transaction_id": transaction_id,
                "message": "Transaction queued for retry"
            }

        except Exception as e:
            logger.error(f"Failed to retry transaction: {e}")
            return {"status": "error", "message": str(e)}
