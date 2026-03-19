"""
Prometheus metrics for Digital Bank.
Provides observability for transactions, fraud detection, and API performance.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from typing import Callable

# Application info
APP_INFO = Info("digital_bank", "Digital Bank application info")
APP_INFO.info({"version": "1.0.0", "service": "digital-bank-api"})

# Transaction metrics
TRANSACTIONS_TOTAL = Counter(
    "digital_bank_transactions_total",
    "Total number of transactions processed",
    ["transaction_type", "transfer_type", "status"]
)

TRANSACTION_AMOUNT = Histogram(
    "digital_bank_transaction_amount",
    "Transaction amount distribution",
    ["transaction_type", "transfer_type"],
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
)

TRANSACTION_DURATION = Histogram(
    "digital_bank_transaction_duration_seconds",
    "Transaction processing duration in seconds",
    ["transaction_type"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Fraud detection metrics
FRAUD_CHECKS_TOTAL = Counter(
    "digital_bank_fraud_checks_total",
    "Total number of fraud checks performed",
    ["risk_level", "decision"]
)

FRAUD_RISK_SCORE = Histogram(
    "digital_bank_fraud_risk_score",
    "Fraud risk score distribution",
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
)

FRAUD_ALERTS_ACTIVE = Gauge(
    "digital_bank_fraud_alerts_active",
    "Number of active fraud alerts"
)

# API metrics
API_REQUESTS_TOTAL = Counter(
    "digital_bank_api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status_code"]
)

API_REQUEST_DURATION = Histogram(
    "digital_bank_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Account metrics
ACCOUNTS_TOTAL = Gauge(
    "digital_bank_accounts_total",
    "Total number of accounts",
    ["account_type", "status"]
)

ACCOUNT_BALANCE = Histogram(
    "digital_bank_account_balance",
    "Account balance distribution",
    ["account_type"],
    buckets=[100, 1000, 5000, 10000, 50000, 100000, 500000]
)

# User metrics
USERS_TOTAL = Gauge(
    "digital_bank_users_total",
    "Total number of users",
    ["role", "kyc_status"]
)

# Database metrics
DB_QUERY_DURATION = Histogram(
    "digital_bank_db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)


def track_transaction_metrics(transaction_type: str, transfer_type: str):
    """Decorator to track transaction metrics"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                TRANSACTION_DURATION.labels(
                    transaction_type=transaction_type
                ).observe(duration)
                if status == "success":
                    TRANSACTIONS_TOTAL.labels(
                        transaction_type=transaction_type,
                        transfer_type=transfer_type,
                        status="completed"
                    ).inc()
                else:
                    TRANSACTIONS_TOTAL.labels(
                        transaction_type=transaction_type,
                        transfer_type=transfer_type,
                        status="failed"
                    ).inc()
        return wrapper
    return decorator


def track_api_request(method: str, endpoint: str):
    """Decorator to track API request metrics"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                API_REQUEST_DURATION.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                API_REQUESTS_TOTAL.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=str(status_code)
                ).inc()
        return wrapper
    return decorator
