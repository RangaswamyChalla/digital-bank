"""
Per-user rate limiting using Redis.
Provides application-level rate limiting per authenticated user.
"""
import time
from typing import Dict, Tuple, Optional
from fastapi import HTTPException, status, Depends
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.routers.users import get_current_user


class PerUserRateLimiter:
    """
    Per-user rate limiter using Redis sliding window.

    Provides granular rate limiting per authenticated user,
    complementing the global IP-based rate limiting.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        requests_per_minute: int = 120,
        requests_per_hour: int = 1000,
        requests_per_day: int = 5000,
        burst_size: int = 20,
    ):
        self.redis_url = redis_url
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self.burst_size = burst_size
        self._redis: Optional[redis.Redis] = None

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

    def _get_key(self, user_id: str, window: str) -> str:
        """Generate Redis key for rate limit."""
        return f"rate_limit:user:{user_id}:{window}"

    async def _check_window(
        self,
        redis_client: redis.Redis,
        user_id: str,
        window_seconds: int,
        limit: int,
        window_name: str,
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit for a specific window.

        Returns:
            (allowed, remaining, retry_after)
        """
        key = self._get_key(user_id, window_name)
        current_time = time.time()
        window_start = current_time - window_seconds

        try:
            pipe = redis_client.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)

            # Count requests in window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiry
            pipe.expire(key, window_seconds + 1)

            results = await pipe.execute()
            request_count = results[1]

            if request_count >= limit:
                oldest = await redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int(window_seconds - (current_time - oldest_time)) + 1
                else:
                    retry_after = window_seconds
                return False, 0, max(1, retry_after)

            remaining = limit - request_count - 1
            return True, max(0, remaining), 0

        except Exception:
            return True, limit, 0

    async def check_rate_limit(self, user_id: str) -> Tuple[bool, int, int]:
        """
        Check all rate limit windows for a user.

        Returns:
            (allowed, remaining_requests, retry_after_seconds)
        """
        redis_client = await self._get_redis()

        # If Redis unavailable, fail open
        if redis_client is None:
            return True, self.requests_per_minute, 0

        try:
            # Check minute window
            allowed, remaining, retry_after = await self._check_window(
                redis_client, user_id, 60, self.requests_per_minute, "minute"
            )
            if not allowed:
                return False, 0, retry_after

            # Check hour window
            allowed, remaining_hour, retry_after = await self._check_window(
                redis_client, user_id, 3600, self.requests_per_hour, "hour"
            )
            if not allowed:
                return False, 0, retry_after
            remaining = min(remaining, remaining_hour)

            # Check day window
            allowed, remaining_day, retry_after = await self._check_window(
                redis_client, user_id, 86400, self.requests_per_day, "day"
            )
            if not allowed:
                return False, 0, retry_after
            remaining = min(remaining, remaining_day)

            return True, remaining, 0

        except Exception:
            return True, self.requests_per_minute, 0

    async def get_user_usage(self, user_id: str) -> Dict[str, Dict[str, int]]:
        """Get current usage statistics for a user."""
        redis_client = await self._get_redis()

        if redis_client is None:
            return {}

        usage = {}
        windows = [
            ("minute", 60),
            ("hour", 3600),
            ("day", 86400),
        ]

        for window_name, window_seconds in windows:
            key = self._get_key(user_id, window_name)
            current_time = time.time()
            cutoff = current_time - window_seconds

            try:
                # Count requests in window
                count = await redis_client.zcount(key, cutoff, current_time)

                # Get oldest request timestamp
                oldest = await redis_client.zrange(key, 0, 0, withscores=True)
                oldest_time = oldest[0][1] if oldest else current_time

                usage[window_name] = {
                    "used": count,
                    "limit": getattr(self, f"requests_per_{window_name}"),
                    "reset_in_seconds": int(
                        window_seconds - (current_time - oldest_time)
                    ) if oldest else window_seconds,
                }
            except Exception:
                usage[window_name] = {"used": 0, "limit": 0, "reset_in_seconds": 0}

        return usage


# Global rate limiter instance
_per_user_rate_limiter: Optional[PerUserRateLimiter] = None


def get_per_user_rate_limiter() -> PerUserRateLimiter:
    """Get the global per-user rate limiter instance."""
    global _per_user_rate_limiter
    if _per_user_rate_limiter is None:
        _per_user_rate_limiter = PerUserRateLimiter(
            redis_url=settings.REDIS_URL,
            requests_per_minute=120,
            requests_per_hour=1000,
            requests_per_day=5000,
            burst_size=20,
        )
    return _per_user_rate_limiter


async def check_user_rate_limit(user_id: str) -> Tuple[bool, int, int]:
    """Check rate limit for a user."""
    limiter = get_per_user_rate_limiter()
    return await limiter.check_rate_limit(user_id)


async def get_current_user_rate_limit_status(user_id: str) -> Dict[str, Dict[str, int]]:
    """Get rate limit status for a user."""
    limiter = get_per_user_rate_limiter()
    return await limiter.get_user_usage(user_id)
