"""
Announcements routes for Solomon AI — Admin CRUD + Portal read.
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from database import db, serialize_doc, DEFAULT_TENANT_ID
from auth import get_current_admin_user, get_current_member_user
import uuid

router = APIRouter()


class AnnouncementCreate(BaseModel):
    title: str
    body: str
    priority: str = "normal"
    expires_at: Optional[str] = None
    send_push: bool = False

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    priority: Optional[str] = None
    expires_at: Optional[str] = None


@router.get("/portal/announcements")
async def get_portal_announcements(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    now_iso = datetime.now(timezone.utc).isoformat()
    announcements = await db.announcements.find(
        {"tenant_id": tenant_id, "$or": [
            {"expires_at": {"$gte": now_iso}},
            {"expires_at": {"$exists": False}},
            {"expires_at": None}
        ]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return {"announcements": [serialize_doc(item) for item in announcements]}


@router.get("/admin/announcements")
async def get_admin_announcements(request: Request, limit: int = 100):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    announcements = await db.announcements.find(
        {"tenant_id": tenant_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    return {"announcements": [serialize_doc(a) for a in announcements]}


@router.post("/admin/announcements")
async def create_admin_announcement(request: Request, payload: AnnouncementCreate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    announcement = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "title": payload.title,
        "body": payload.body,
        "priority": payload.priority,
        "expires_at": payload.expires_at,
        "created_by": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.announcements.insert_one(announcement)

    if payload.send_push:
        try:
            from routes.push import send_push_notification
            subs = await db.push_subscriptions.find({"tenant_id": tenant_id}, {"_id": 0, "user_id": 1}).to_list(1000)
            for sub in subs:
                try:
                    await send_push_notification(
                        sub["user_id"], tenant_id,
                        payload.title, payload.body, "/portal/announcements"
                    )
                except Exception:
                    pass
        except Exception:
            pass

    return {"message": "Announcement created", "announcement": serialize_doc(announcement)}


@router.put("/admin/announcements/{announcement_id}")
async def update_admin_announcement(request: Request, announcement_id: str, payload: AnnouncementUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.announcements.update_one(
        {"id": announcement_id, "tenant_id": tenant_id}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"message": "Announcement updated"}


@router.delete("/admin/announcements/{announcement_id}")
async def delete_admin_announcement(request: Request, announcement_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    result = await db.announcements.delete_one({"id": announcement_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"message": "Announcement deleted"}
