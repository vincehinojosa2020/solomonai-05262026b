"""
Group messaging routes for Solomon AI.
"""
from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timezone
import uuid

from database import db
from auth import get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("/{group_id}/messages")
async def get_group_messages(request: Request, group_id: str, before: str = None, limit: int = 50):
    """Get messages for a group."""
    user = await get_current_user(request)
    tenant_id = user.get("tenant_id", "")

    query = {"group_id": group_id, "tenant_id": tenant_id}
    if before:
        query["created_at"] = {"$lt": before}

    messages = await db.group_messages.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    messages.reverse()
    return {"messages": messages}


@router.post("/{group_id}/messages")
async def send_group_message(request: Request, group_id: str):
    """Send a message to a group chat."""
    user = await get_current_user(request)
    tenant_id = user.get("tenant_id", "")
    body = await request.json()
    text = (body.get("text") or "").strip()

    if not text:
        raise HTTPException(status_code=400, detail="Message text is required")

    message = {
        "id": str(uuid.uuid4()),
        "group_id": group_id,
        "tenant_id": tenant_id,
        "sender_id": user.get("user_id") or user.get("id", ""),
        "sender_name": user.get("name", "Unknown"),
        "sender_email": user.get("email", ""),
        "sender_role": user.get("role", "member"),
        "text": text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.group_messages.insert_one(message)

    # Push notifications to other group members
    try:
        from routes.push import send_push_notification
        group_members = await db.group_members.find(
            {"group_id": group_id, "tenant_id": tenant_id},
            {"_id": 0, "person_id": 1, "user_id": 1}
        ).to_list(100)
        sender_id = user.get("user_id") or user.get("id", "")
        for m in group_members:
            member_uid = m.get("user_id") or m.get("person_id", "")
            if member_uid and member_uid != sender_id:
                await send_push_notification(
                    member_uid, tenant_id,
                    f"New message in {group_id[:8]}",
                    f"{message['sender_name']}: {text[:80]}",
                    "/portal/groups"
                )
    except Exception:
        pass

    return {k: v for k, v in message.items() if k != "_id"}


@router.delete("/{group_id}/messages/{message_id}")
async def delete_group_message(request: Request, group_id: str, message_id: str):
    """Delete a message (sender or admin only)."""
    user = await get_current_user(request)
    tenant_id = user.get("tenant_id", "")

    msg = await db.group_messages.find_one(
        {"id": message_id, "group_id": group_id, "tenant_id": tenant_id}, {"_id": 0}
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    user_id = user.get("user_id") or user.get("id", "")
    if msg["sender_id"] != user_id and user.get("role") not in ("church_admin", "platform_admin"):
        raise HTTPException(status_code=403, detail="Cannot delete this message")

    await db.group_messages.delete_one({"id": message_id})
    return {"message": "Deleted"}
