"""
Solomon AI — Auth Helpers
Session management, rate limiting, tenant validation.
"""
from fastapi import HTTPException, Request
import time as _time

# In-memory rate limiting (single-instance)
RATE_LIMITS = {}

def check_rate_limit_v2(bucket: str, max_requests: int, window_seconds: int) -> bool:
    """Check if request is within rate limit. Returns True if allowed."""
    now = _time.time()
    if bucket not in RATE_LIMITS:
        RATE_LIMITS[bucket] = {"count": 0, "window_start": now}
    entry = RATE_LIMITS[bucket]
    if now - entry["window_start"] > window_seconds:
        RATE_LIMITS[bucket] = {"count": 1, "window_start": now}
        return True
    entry["count"] += 1
    return entry["count"] <= max_requests


def get_session_token_from_request(request: Request) -> str:
    """Extract session token from cookie or Authorization header."""
    token = request.cookies.get("session_token")
    if token:
        return token
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def get_current_admin_user(request: Request, db):
    """Get current admin user with tenant validation."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if user.get("role") not in ["admin", "church_admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    if user.get("role") != "platform_admin" and not user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Tenant context required for admin access")
    return user


async def get_current_portal_user(request: Request, db):
    """Get current portal/member user."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_tenant(user: dict) -> str:
    """Extract and validate tenant_id from user. Raises 403 if missing."""
    tenant_id = user.get("tenant_id")
    if not tenant_id and user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Tenant context required")
    return tenant_id
