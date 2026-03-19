"""
Rate limiting dependency for FastAPI routes.
Provides per-user rate limiting on specific endpoints.
"""
from fastapi import HTTPException, status, Header
from typing import Optional
import logging

from app.middleware.per_user_rate_limit import check_user_rate_limit

logger = logging.getLogger(__name__)


async def rate_limit_dependency(
    authorization: Optional[str] = Header(None)
) -> None:
    """
    FastAPI dependency that enforces per-user rate limiting.

    Use this on routes that need per-user rate limiting:
        @router.post("/transfer")
        async def transfer(
            ...,
            _: None = Depends(rate_limit_dependency)
        ):
            ...

    Note: This requires a valid Authorization header.
    """
    if not authorization:
        # No auth header - skip rate limiting (auth middleware will handle this)
        return

    try:
        # Extract user ID from the authorization header
        # Format: "Bearer <token>"
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization

        # Decode token to get user_id (without full validation)
        from app.services.auth import AuthService
        payload = AuthService.decode_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            return

        # Check rate limit
        allowed, remaining, retry_after = await check_user_rate_limit(user_id)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOTAL_REQUESTS,
                detail=f"User rate limit exceeded. Retry after {retry_after} seconds.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Remaining": "0"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        # On any error, fail open (allow request)
        logger.warning(f"Rate limit check failed: {e}")
        return
