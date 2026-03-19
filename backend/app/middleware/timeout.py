"""
Request timeout middleware for API protection.
Ensures requests don't hang indefinitely.
"""
import asyncio
from typing import Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces a timeout on request processing.

    Prevents requests from hanging indefinitely by timing out
    after a configured number of seconds.
    """

    def __init__(
        self,
        app,
        timeout_seconds: int = 30,
        exempt_paths: tuple = ("/health", "/metrics", "/docs", "/openapi.json", "/redoc")
    ):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
        self.exempt_paths = exempt_paths

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with timeout enforcement."""
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        try:
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
            return response
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Request timed out after {self.timeout_seconds} seconds"
            )
