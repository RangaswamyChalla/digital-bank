"""
Background job service for enqueueing async tasks.
Provides an interface for the main application to enqueue background jobs.
"""
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Global job queue connection pool
_job_pool = None


async def get_job_pool():
    """Get or create the ARQ job pool."""
    global _job_pool
    if _job_pool is None:
        try:
            from arq import asyncio_pool
            _job_pool = asyncio_pool.from_url(settings.ARQ_REDIS_URL)
        except Exception as e:
            logger.warning(f"ARQ pool not available: {e}")
            return None
    return _job_pool


async def close_job_pool():
    """Close the job pool connection."""
    global _job_pool
    if _job_pool:
        try:
            await _job_pool.close()
        except:
            pass
        _job_pool = None


async def enqueue_fraud_alert_email(alert_id: str, user_id: str) -> bool:
    """Enqueue a fraud alert email notification."""
    try:
        pool = await get_job_pool()
        if pool is None:
            logger.warning("ARQ pool not available, skipping job enqueue")
            return False
        await pool.enqueue_job("process_fraud_alert_email", alert_id, user_id)
        logger.info(f"Enqueued fraud alert email job for alert {alert_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to enqueue fraud alert email: {e}")
        return False


async def enqueue_transaction_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str
) -> bool:
    """Enqueue a transaction notification."""
    try:
        pool = await get_job_pool()
        if pool is None:
            logger.warning("ARQ pool not available, skipping job enqueue")
            return False
        await pool.enqueue_job(
            "send_transaction_notification",
            user_id,
            notification_type,
            title,
            message
        )
        logger.info(f"Enqueued transaction notification for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to enqueue transaction notification: {e}")
        return False


async def enqueue_admin_alert(alert_data: dict) -> bool:
    """Enqueue an admin alert notification."""
    try:
        pool = await get_job_pool()
        if pool is None:
            logger.warning("ARQ pool not available, skipping job enqueue")
            return False
        await pool.enqueue_job("send_admin_alert_notification", alert_data)
        logger.info(f"Enqueued admin alert notification")
        return True
    except Exception as e:
        logger.error(f"Failed to enqueue admin alert: {e}")
        return False


async def enqueue_monthly_statement(user_id: str, account_id: str, month: str) -> bool:
    """Enqueue a monthly statement generation."""
    try:
        pool = await get_job_pool()
        if pool is None:
            logger.warning("ARQ pool not available, skipping job enqueue")
            return False
        await pool.enqueue_job("generate_monthly_statement", user_id, account_id, month)
        logger.info(f"Enqueued monthly statement for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to enqueue monthly statement: {e}")
        return False


async def enqueue_transaction_retry(transaction_id: str) -> bool:
    """Enqueue a failed transaction retry."""
    try:
        pool = await get_job_pool()
        if pool is None:
            logger.warning("ARQ pool not available, skipping job enqueue")
            return False
        await pool.enqueue_job("retry_failed_transaction", transaction_id)
        logger.info(f"Enqueued transaction retry for {transaction_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to enqueue transaction retry: {e}")
        return False
