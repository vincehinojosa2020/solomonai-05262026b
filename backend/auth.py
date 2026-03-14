"""
Authentication helpers for Solomon AI.
Shared across all route modules.
"""
from fastapi import Request, HTTPException
from datetime import datetime, timezone
from typing import Optional
from database import db, serialize_doc


def get_session_token_from_request(request: Request) -> Optional[str]:
    """Resolve auth token from cookie (web) or Authorization Bearer header (mobile).
    Prefers explicit Authorization header so API clients can override stale browser cookies.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header:
        parts = auth_header.strip().split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
            if token:
                return token
    session_token = request.cookies.get("session_token")
    if session_token:
        return session_token
    return None


async def get_current_user(request: Request):
    """Get current user from session cookie or Authorization header."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_doc = await db.user_sessions.find_one(
        {"session_token": session_token}, {"_id": 0}
    )
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")

    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    user_doc = await db.users.find_one(
        {"user_id": session_doc["user_id"]}, {"_id": 0}
    )
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")

    result = serialize_doc(user_doc)
    result["role"] = user_doc.get("role", "admin")
    return result


async def get_current_admin_user(request: Request):
    """Get current user and verify admin role."""
    user = await get_current_user(request)
    if user.get("role") not in ("admin", "church_admin", "platform_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def get_current_member_user(request: Request):
    """Get current user for portal access: member + church/platform admins."""
    user = await get_current_user(request)
    if user.get("role") not in ("member", "admin", "church_admin", "platform_admin"):
        raise HTTPException(status_code=403, detail="Portal access required")
    return user
