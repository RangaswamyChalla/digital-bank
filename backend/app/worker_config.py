"""
ARQ Worker configuration for Digital Bank.
"""
from arq import cron
from arq.connections import RedisSettings

from app.config import settings
from app.workers import (
    process_fraud_alert_email,
    send_transaction_notification,
    send_admin_alert_notification,
    cleanup_expired_tokens,
    generate_monthly_statement,
    retry_failed_transaction,
)


class WorkerSettings:
    """Settings for ARQ worker."""

    redis_settings = RedisSettings.from_url(settings.REDIS_URL)

    # Functions that can be called as jobs
    functions = [
        process_fraud_alert_email,
        send_transaction_notification,
        send_admin_alert_notification,
        cleanup_expired_tokens,
        generate_monthly_statement,
        retry_failed_transaction,
    ]

    # Job retry settings
    max_retries = 3
    retry_delay = 60  # seconds

    # Job timeout (seconds)
    job_timeout = 300  # 5 minutes

    # Cron jobs (scheduled tasks)
    cron_jobs = [
        # Run expired token cleanup daily at 3 AM
        cron(cleanup_expired_tokens, hour=3, minute=0),
    ]

    # On startup, run these
    on_startup = []
    # On shutdown, run these
    on_shutdown = []
