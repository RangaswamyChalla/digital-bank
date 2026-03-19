"""
Rate limiting middleware for API protection
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiting middleware.

    Limits requests per IP address using a sliding window algorithm.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        exempt_paths: tuple = ("/health", "/docs", "/openapi.json", "/redoc")
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.exempt_paths = exempt_paths

        # Sliding window storage: {ip: [(timestamp, count), ...]}
        self._requests: Dict[str, list] = defaultdict(list)

        # Cleanup old entries every minute
        self._last_cleanup = time.time()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxies"""
        # Check X-Forwarded-For header first (for proxied requests)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to client host
        if request.client:
            return request.client.host

        return "unknown"

    def _cleanup_old_entries(self):
        """Remove entries older than 60 seconds"""
        current_time = time.time()
        if current_time - self._last_cleanup < 60:
            return

        cutoff = current_time - 60
        for ip in list(self._requests.keys()):
            self._requests[ip] = [
                (ts, count) for ts, count in self._requests[ip] if ts > cutoff
            ]
            if not self._requests[ip]:
                del self._requests[ip]

        self._last_cleanup = current_time

    def _check_rate_limit(self, ip: str) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Returns:
            (allowed, remaining, retry_after)
        """
        current_time = time.time()
        self._cleanup_old_entries()

        # Get requests in current window
        window_requests = [
            ts for ts, _ in self._requests[ip] if current_time - ts < 60
        ]

        if len(window_requests) >= self.requests_per_minute:
            # Calculate retry-after
            oldest = min(window_requests) if window_requests else current_time
            retry_after = int(60 - (current_time - oldest)) + 1
            return False, 0, retry_after

        # Add current request
        self._requests[ip].append((current_time, 1))
        remaining = self.requests_per_minute - len(window_requests) - 1

        return True, remaining, 0

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        ip = self._get_client_ip(request)
        allowed, remaining, retry_after = self._check_rate_limit(ip)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response


def get_rate_limit_exempt_paths() -> tuple:
    """Return paths exempt from rate limiting"""
    return ("/health", "/docs", "/openapi.json", "/redoc", "/api/v1/auth/login", "/api/v1/auth/register")
