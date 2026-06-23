"""
Phoenix AI - JWT Authentication & RBAC System
Implements:
- JWT access/refresh tokens
- Password hashing (bcrypt)
- Role-based access control (Admin, Developer, Operator, User)
- Token verification middleware
"""
import time
import uuid
import hashlib
import hmac
import json
import base64
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ai_project.api.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_REFRESH_TOKEN_EXPIRE_DAYS

logger = logging.getLogger("PhoenixAuth")

# ══════════════════════════════════════════════════════════════
#  Role Definitions
# ══════════════════════════════════════════════════════════════

class Roles:
    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    USER = "user"

# Role hierarchy: higher roles inherit lower role permissions
ROLE_HIERARCHY = {
    Roles.ADMIN: 4,
    Roles.DEVELOPER: 3,
    Roles.OPERATOR: 2,
    Roles.USER: 1,
}

# Route permission matrix
ROUTE_PERMISSIONS: Dict[str, str] = {
    # Admin only
    "/api/admin/backup": Roles.ADMIN,
    "/api/memory/clear": Roles.ADMIN,
    "/api/model/quantize": Roles.ADMIN,
    "/api/memory/consolidate": Roles.ADMIN,
    # Developer+
    "/api/sandbox/run": Roles.DEVELOPER,
    "/api/agent/debug/scan": Roles.DEVELOPER,
    "/api/agent/debug/repair": Roles.DEVELOPER,
    "/api/agent/refactor": Roles.DEVELOPER,
    "/api/agent/orchestrate": Roles.DEVELOPER,
    "/api/evaluate": Roles.DEVELOPER,
    "/api/evaluate/benchmarks": Roles.DEVELOPER,
    # Operator+
    "/api/memory/upload": Roles.OPERATOR,
    "/api/ai_explorer/add": Roles.OPERATOR,
    # User (default, all authenticated users)
    "/api/chat": Roles.USER,
    "/api/chat/stream": Roles.USER,
    "/api/memory": Roles.USER,
    "/api/memory/add": Roles.USER,
    "/api/memory/search": Roles.USER,
    "/api/ai_explorer/search": Roles.USER,
    "/api/monitoring/metrics": Roles.USER,
}

# Public routes (no authentication required)
PUBLIC_ROUTES = {
    "/api/health",
    "/api/health/liveness",
    "/api/health/readiness",
    "/metrics",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/docs",
    "/openapi.json",
    "/redoc",
}


# ══════════════════════════════════════════════════════════════
#  Password Hashing (PBKDF2-SHA256 — no bcrypt dependency needed)
# ══════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-SHA256 with random salt."""
    salt = uuid.uuid4().hex
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${pwd_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its stored hash."""
    try:
        salt, pwd_hash = stored_hash.split("$", 1)
        check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return hmac.compare_digest(check.hex(), pwd_hash)
    except (ValueError, AttributeError):
        return False


# ══════════════════════════════════════════════════════════════
#  JWT Token Management (Pure Python — no jose dependency)
# ══════════════════════════════════════════════════════════════

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def create_access_token(user_id: str, username: str, role: str) -> str:
    """Create a JWT access token."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + (JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        "jti": uuid.uuid4().hex,
    }
    return _encode_jwt(payload)


def create_refresh_token(user_id: str, username: str, role: str) -> str:
    """Create a JWT refresh token."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "type": "refresh",
        "iat": now,
        "exp": now + (JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400),
        "jti": uuid.uuid4().hex,
    }
    return _encode_jwt(payload)


def _encode_jwt(payload: dict) -> str:
    """Encode a JWT token using HMAC-SHA256."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(JWT_SECRET_KEY.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_jwt(token: str) -> dict:
    """Decode and verify a JWT token. Raises HTTPException on failure."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid token format")

        header_b64, payload_b64, sig_b64 = parts

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(JWT_SECRET_KEY.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise HTTPException(status_code=401, detail="Invalid token signature")

        # Decode payload
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))

        # Check expiration
        if payload.get("exp", 0) < int(time.time()):
            raise HTTPException(status_code=401, detail="Token has expired")

        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")


# ══════════════════════════════════════════════════════════════
#  In-Memory User Store (Enterprise: replace with DB)
# ══════════════════════════════════════════════════════════════

_users_store: Dict[str, Dict[str, Any]] = {}


def _init_default_admin():
    """Initialize default admin user if store is empty."""
    if not _users_store:
        admin_id = str(uuid.uuid4())
        _users_store[admin_id] = {
            "id": admin_id,
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "role": Roles.ADMIN,
            "created_at": int(time.time()),
        }
        logger.info("Default admin user created (username: admin)")


_init_default_admin()


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    for user in _users_store.values():
        if user["username"] == username:
            return user
    return None


def create_user(username: str, password: str, role: str = Roles.USER) -> Dict[str, Any]:
    if get_user_by_username(username):
        raise HTTPException(status_code=409, detail="Username already exists")
    if role not in ROLE_HIERARCHY:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "username": username,
        "password_hash": hash_password(password),
        "role": role,
        "created_at": int(time.time()),
    }
    _users_store[user_id] = user
    return user


# ══════════════════════════════════════════════════════════════
#  FastAPI Dependencies
# ══════════════════════════════════════════════════════════════

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[Dict[str, Any]]:
    """
    Extract and validate the JWT token from the request.
    Returns None for public routes.
    """
    path = request.url.path

    # Allow public routes without auth
    if path in PUBLIC_ROUTES:
        return None

    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required. Provide a Bearer token.")

    payload = decode_jwt(credentials.credentials)

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type. Use an access token.")

    return payload


def require_role(minimum_role: str):
    """
    Dependency factory: ensures the authenticated user has at least the specified role.
    Uses role hierarchy for comparison.
    """
    async def role_checker(user: dict = Depends(get_current_user)):
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        user_role = user.get("role", Roles.USER)
        if ROLE_HIERARCHY.get(user_role, 0) < ROLE_HIERARCHY.get(minimum_role, 0):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {minimum_role}, your role: {user_role}"
            )
        return user
    return role_checker


def check_route_permission(path: str, user_role: str) -> bool:
    """Check if a user role has permission to access a route."""
    required_role = ROUTE_PERMISSIONS.get(path, Roles.USER)
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)
