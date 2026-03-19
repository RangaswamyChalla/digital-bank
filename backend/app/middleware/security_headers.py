"""
Security headers middleware for API protection.
Adds security-related HTTP headers to all responses.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Headers added:
    - Strict-Transport-Security (HSTS): Enforces HTTPS connections
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: XSS filter for older browsers
    - Referrer-Policy: Controls referrer information
    - Content-Security-Policy: Mitigates XSS and injection attacks
    - Permissions-Policy: Controls browser features
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Strict-Transport-Security (HSTS)
        # Forces HTTPS for 1 year (31536000 seconds)
        # includeSubDomains means all subdomains also use HTTPS
        # preload allows inclusion in browser HSTS preload lists
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # X-Content-Type-Options
        # Prevents browsers from MIME-sniffing a response away from the declared content-type
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options
        # Prevents the page from being displayed in an iframe (clickjacking protection)
        # DENY: Page cannot be displayed in a frame at all
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection
        # Enables XSS filter in older browsers (modern browsers use CSP instead)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy
        # Controls how much referrer information is sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content-Security-Policy (CSP)
        # Helps prevent XSS, clickjacking, and other code injection attacks
        # This is a restrictive policy - adjust based on your needs
        csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests"
        )
        response.headers["Content-Security-Policy"] = csp

        # Permissions-Policy
        # Controls which browser features and APIs can be used
        # Disables features that could be abused
        permissions = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        response.headers["Permissions-Policy"] = permissions

        return response
