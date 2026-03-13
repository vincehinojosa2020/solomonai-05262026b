"""
Authentication helpers for Solomon AI.
"""
from fastapi import Request, HTTPException
from datetime import datetime, timezone
from database import db, serialize_doc


async def get_current_user(request: Request):
    """Get current user from session cookie or Authorization header."""
    session_token = request.cookies.get("session_token")

    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]

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
    if user.get("role") not in ("church_admin", "platform_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def get_current_member_user(request: Request):
    """Get current user — any authenticated role."""
    return await get_current_user(request)
