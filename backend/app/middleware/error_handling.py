"""
Centralized error handling and logging middleware for the banking application.
Ensures consistent error responses and structured logging across all services.
"""

import logging
import traceback
import json
from typing import Callable, Any
from datetime import datetime
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uuid


# Configure structured logging
class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint

        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exc(),
            }

        return json.dumps(log_data)


def setup_logging(log_level=logging.INFO):
    """Configure structured logging for the application"""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    return logger


# Custom exception classes
class BankingException(Exception):
    """Base exception for banking application"""

    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationException(BankingException):
    """Raised when authentication fails"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR", 401)


class AuthorizationException(BankingException):
    """Raised when user lacks required permissions"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHZ_ERROR", 403)


class FraudDetectedException(BankingException):
    """Raised when fraud is detected"""

    def __init__(self, message: str = "Transaction flagged as fraudulent"):
        super().__init__(message, "FRAUD_DETECTED", 403)


class DatabaseException(BankingException):
    """Raised when database operation fails"""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DB_ERROR", 500)


class ValidationException(BankingException):
    """Raised when input validation fails"""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, "VALIDATION_ERROR", 422)


class ServiceException(BankingException):
    """Raised when external service fails"""

    def __init__(self, message: str = "External service unavailable"):
        super().__init__(message, "SERVICE_ERROR", 503)


# Error response models
class ErrorResponse:
    """Standardized error response format"""

    def __init__(
        self, code: str, message: str, details: dict = None, request_id: str = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.request_id = request_id
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "request_id": self.request_id,
                "timestamp": self.timestamp,
            }
        }


# Request/Response logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses"""

    def __init__(self, app, logger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log incoming request
        log_record = logging.LogRecord(
            name=__name__,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"Incoming {request.method} {request.url.path}",
            args=(),
            exc_info=None,
        )
        log_record.request_id = request_id
        log_record.endpoint = f"{request.method} {request.url.path}"

        # Process request
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            log_record.exc_info = (type(exc), exc, exc.__traceback__)
            self.logger.handle(log_record)
            raise


# Error handling middleware
class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Centralized error handling middleware"""

    def __init__(self, app, logger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        try:
            return await call_next(request)

        except BankingException as exc:
            error_response = ErrorResponse(
                code=exc.code,
                message=exc.message,
                request_id=getattr(request.state, "request_id", None),
            )
            self.logger.error(f"Banking error: {exc.code} - {exc.message}")
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response.to_dict(),
            )

        except ValueError as exc:
            import traceback
            print(f"[DEBUG ValueError] {exc}", flush=True)
            print(traceback.format_exc(), flush=True)
            error_response = ErrorResponse(
                code="VALIDATION_ERROR",
                message=str(exc),
                request_id=getattr(request.state, "request_id", None),
            )
            return JSONResponse(
                status_code=422,
                content=error_response.to_dict(),
            )

        except Exception as exc:
            import traceback
            print(f"[DEBUG Exception] {type(exc).__name__}: {exc}", flush=True)
            print(traceback.format_exc(), flush=True)
            request_id = getattr(request.state, "request_id", "unknown")
            self.logger.exception(f"Unhandled exception in request {request_id}")

            error_response = ErrorResponse(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred. Please try again later.",
                request_id=request_id,
            )
            return JSONResponse(
                status_code=500,
                content=error_response.to_dict(),
            )
