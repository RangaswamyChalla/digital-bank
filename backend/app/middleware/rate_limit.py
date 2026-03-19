"""
Rate limiting middleware for API protection.
Redis-backed for horizontal scaling support.
"""
import time
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis.asyncio as redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiting middleware using Redis.

    Limits requests per IP address using a sliding window algorithm.
    Redis-backed so rate limits are shared across all instances.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        exempt_paths: tuple = ("/health", "/docs", "/openapi.json", "/redoc"),
        redis_url: str = "redis://localhost:6379",
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.exempt_paths = exempt_paths
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self._window_seconds = 60

    async def _get_redis(self) -> Optional[redis.Redis]:
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    async def _close_redis(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxies."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    async def _check_rate_limit_redis(self, ip: str) -> Tuple[bool, int, int]:
        """
        Check rate limit using Redis sliding window.

        Returns:
            (allowed, remaining, retry_after)
        """
        redis_client = await self._get_redis()

        # If Redis unavailable, fall back to allowing (fail open)
        if redis_client is None:
            return True, self.requests_per_minute, 0

        key = f"rate_limit:{ip}"
        current_time = time.time()
        window_start = current_time - self._window_seconds

        try:
            # Use Redis pipeline for atomic operations
            pipe = redis_client.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            pipe.zcard(key)

            # Add current request with timestamp as score
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiry on the key
            pipe.expire(key, self._window_seconds + 1)

            results = await pipe.execute()
            request_count = results[1]

            if request_count >= self.requests_per_minute:
                # Get oldest request timestamp to calculate retry_after
                oldest = await redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int(self._window_seconds - (current_time - oldest_time)) + 1
                else:
                    retry_after = self._window_seconds

                return False, 0, max(1, retry_after)

            remaining = self.requests_per_minute - request_count - 1
            return True, max(0, remaining), 0

        except Exception:
            # On Redis error, fail open (allow request)
            return True, self.requests_per_minute, 0

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        ip = self._get_client_ip(request)
        allowed, remaining, retry_after = await self._check_rate_limit_redis(ip)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self._window_seconds)

        return response


def get_rate_limit_exempt_paths() -> tuple:
    """Return paths exempt from rate limiting."""
    return (
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/metrics",
    )
