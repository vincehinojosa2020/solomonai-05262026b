"""Solomon AI — Admin Meetings Routes"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import (
    serialize_doc, transcribe_audio_with_whisper,
    summarize_meeting_with_claude, notify_meeting_event,
)
from core.seed import ensure_demo_meetings_data
from models.schemas import (
    PastorMeetingSlot, PastorMeetingSlotCreate,
    PastorMeetingUpdate, Tenant,
)

router = APIRouter()

@router.get("/admin/meetings/slots")
async def get_admin_meeting_slots(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_meetings_data(tenant_id)
    slots = await db.pastor_meeting_slots.find({"tenant_id": tenant_id}, {"_id": 0}).sort("start_time", 1).to_list(200)
    return {"slots": [serialize_doc(slot) for slot in slots]}


@router.post("/admin/meetings/slots")
async def create_admin_meeting_slot(request: Request, payload: PastorMeetingSlotCreate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    slot = PastorMeetingSlot(
        tenant_id=tenant_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        location=payload.location
    ).model_dump()
    await db.pastor_meeting_slots.insert_one(slot)
    return {"slot": serialize_doc(slot)}


@router.get("/admin/meetings")
async def get_admin_meetings(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    meetings = await db.pastor_meetings.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
    slot_ids = [m.get("slot_id") for m in meetings]
    slots = await db.pastor_meeting_slots.find({"id": {"$in": slot_ids}}, {"_id": 0}).to_list(200)
    slot_map = {s["id"]: s for s in slots}

    response = []
    for meeting in meetings:
        slot = slot_map.get(meeting.get("slot_id"), {})
        response.append({
            **serialize_doc(meeting),
            "slot": serialize_doc(slot) if slot else None
        })

    return {"meetings": response}


@router.patch("/admin/meetings/{meeting_id}")
async def update_admin_meeting(request: Request, meeting_id: str, payload: PastorMeetingUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.pastor_meetings.update_one({"id": meeting_id, "tenant_id": tenant_id}, {"$set": update_data})

    meeting = await db.pastor_meetings.find_one({"id": meeting_id, "tenant_id": tenant_id}, {"_id": 0})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return {"meeting": serialize_doc(meeting)}


@router.post("/admin/meetings/{meeting_id}/recording")
async def upload_meeting_recording(request: Request, meeting_id: str, file: UploadFile = File(...)):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    meeting = await db.pastor_meetings.find_one({"id": meeting_id, "tenant_id": tenant_id}, {"_id": 0})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    uploads_dir = ROOT_DIR / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    file_suffix = Path(file.filename or "recording").suffix or ".webm"
    file_path = uploads_dir / f"meeting_{meeting_id}{file_suffix}"

    with file_path.open("wb") as buffer:
        content = await file.read()
        buffer.write(content)

    transcript_text = await transcribe_audio_with_whisper(file_path)
    summary_text = await summarize_meeting_with_claude(transcript_text, meeting.get("topic"))

    update_data = {
        "transcript": transcript_text,
        "summary": summary_text,
        "recording_filename": file_path.name,
        "status": "completed",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    await db.pastor_meetings.update_one({"id": meeting_id}, {"$set": update_data})
    notifications = await notify_meeting_event("meeting_summary_ready", meeting)

    return {"transcript": transcript_text, "summary": summary_text, "notifications": notifications}

# ============== LEADERSHIP NOTES ROUTES ==============

