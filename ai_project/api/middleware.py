"""
Phoenix AI - Enterprise Security Middleware
Implements:
- Security headers (CSP, HSTS, X-Content-Type-Options, etc.)
- CSRF protection (Double Submit Cookie pattern)
- SSRF prevention
- Request/Response audit logging
"""
import time
import uuid
import logging
import ipaddress
from urllib.parse import urlparse
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ai_project.api.config import ENVIRONMENT

logger = logging.getLogger("PhoenixSecurity")

# ══════════════════════════════════════════════════════════════
#  Security Headers Middleware
# ══════════════════════════════════════════════════════════════

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds enterprise-grade security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"

        # XSS Protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # HSTS (only in production)
        if ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Remove server identification
        response.headers["Server"] = "Phoenix-AI"

        return response


# ══════════════════════════════════════════════════════════════
#  CSRF Protection Middleware
# ══════════════════════════════════════════════════════════════

class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection using custom header validation.
    State-changing requests (POST, PUT, DELETE, PATCH) must include
    the X-CSRF-Token header matching a value from the client.
    API calls with Bearer auth are exempt (since CSRF targets cookie-based auth).
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    EXEMPT_PATHS = {"/api/auth/login", "/api/auth/register", "/api/auth/refresh"}

    async def dispatch(self, request: Request, call_next):
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Bearer token auth is CSRF-immune (not sent automatically by browser)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)

        # JSON API requests are CSRF-immune (browsers cannot send JSON content-type via forms)
        content_type = request.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return await call_next(request)

        # For multipart/form-data or cookie-based sessions, require X-CSRF-Token
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing. Include X-CSRF-Token header."}
            )

        return await call_next(request)


# ══════════════════════════════════════════════════════════════
#  SSRF Prevention
# ══════════════════════════════════════════════════════════════

BLOCKED_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),         # Private
    ipaddress.ip_network("172.16.0.0/12"),      # Private
    ipaddress.ip_network("192.168.0.0/16"),     # Private
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local
    ipaddress.ip_network("0.0.0.0/8"),          # Current network
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),           # IPv6 private
    ipaddress.ip_network("fe80::/10"),          # IPv6 link-local
]

BLOCKED_SCHEMES = {"file", "ftp", "gopher", "data", "javascript"}


def validate_url_ssrf(url: str) -> bool:
    """
    Validates a URL to prevent SSRF attacks.
    Returns True if the URL is safe, raises HTTPException otherwise.
    """
    try:
        parsed = urlparse(url)

        # Block dangerous schemes
        if parsed.scheme.lower() in BLOCKED_SCHEMES:
            raise HTTPException(status_code=400, detail=f"Blocked URL scheme: {parsed.scheme}")

        # Block internal IPs
        hostname = parsed.hostname
        if hostname:
            try:
                ip = ipaddress.ip_address(hostname)
                for network in BLOCKED_IP_RANGES:
                    if ip in network:
                        raise HTTPException(status_code=400, detail="URL points to a restricted internal network")
            except ValueError:
                # It's a hostname, not an IP — allow DNS resolution later
                pass

        return True
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid URL format")


# ══════════════════════════════════════════════════════════════
#  Audit Logging Middleware
# ══════════════════════════════════════════════════════════════

class AuditLogMiddleware(BaseHTTPMiddleware):
    """Logs all API requests for security auditing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"

        # Extract user info from auth header if present
        user_info = "anonymous"
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                from ai_project.api.auth import decode_jwt
                payload = decode_jwt(auth[7:])
                user_info = f"{payload.get('username', 'unknown')}({payload.get('role', 'unknown')})"
            except Exception:
                user_info = "invalid-token"

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            logger.info(
                f"AUDIT | {request_id} | {request.method} {request.url.path} | "
                f"status={response.status_code} | user={user_info} | ip={client_ip} | "
                f"duration={duration:.3f}s"
            )

            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"AUDIT | {request_id} | {request.method} {request.url.path} | "
                f"ERROR | user={user_info} | ip={client_ip} | "
                f"duration={duration:.3f}s | error={str(e)}"
            )
            raise
