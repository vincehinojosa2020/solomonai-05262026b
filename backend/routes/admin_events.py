"""Solomon AI — Admin Events, Calendar, Registrations Routes"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc
from models.schemas import Event, Tenant, AdminRegisterRequest, ApprovalDecision, EventCreate, FormCreate, RoomBookingRequest, WorkflowCreate

router = APIRouter()

@router.get("/admin/registrations/events")
async def get_registration_events(request: Request):
    """Get all events that have registration enabled"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    events = await db.events.find(
        {"tenant_id": tenant_id, "registration_required": True}, {"_id": 0}
    ).sort("start_datetime", -1).to_list(200)
    # Enrich with registration counts and config
    for evt in events:
        reg_count = await db.event_registrations.count_documents({"event_id": evt["id"], "status": {"$ne": "waitlisted"}})
        waitlist_count = await db.event_registrations.count_documents({"event_id": evt["id"], "status": "waitlisted"})
        config = await db.registration_configs.find_one({"event_id": evt["id"]}, {"_id": 0})
        evt["confirmed_count"] = reg_count
        evt["waitlist_count"] = waitlist_count
        evt["has_config"] = config is not None
        evt["pricing"] = config.get("pricing", {}) if config else {}
    return {"events": events, "total": len(events)}


@router.get("/admin/registrations/configs/{event_id}")
async def get_registration_config(request: Request, event_id: str):
    """Get registration configuration for an event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    config = await db.registration_configs.find_one({"event_id": event_id, "tenant_id": tenant_id}, {"_id": 0})
    if not config:
        return {"config": None}
    return {"config": config}


@router.post("/admin/registrations/configs/{event_id}")
async def save_registration_config(request: Request, event_id: str, payload: dict):
    """Create or update registration configuration for an event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    # Verify event exists
    event = await db.events.find_one({"id": event_id, "tenant_id": tenant_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    # Mark event as registration-required
    await db.events.update_one({"id": event_id}, {"$set": {"registration_required": True}})
    existing = await db.registration_configs.find_one({"event_id": event_id, "tenant_id": tenant_id})
    config_data = {
        "event_id": event_id,
        "tenant_id": tenant_id,
        "pricing": payload.get("pricing", {"enabled": False, "amount": 0, "currency": "USD"}),
        "add_ons": payload.get("add_ons", []),
        "custom_questions": payload.get("custom_questions", []),
        "promo_codes": payload.get("promo_codes", []),
        "confirmation_message": payload.get("confirmation_message", "Thank you for registering!"),
        "max_registrants_per_order": payload.get("max_registrants_per_order", 10),
        "require_payment": payload.get("require_payment", False),
        "auto_confirm": payload.get("auto_confirm", True),
        "waitlist_enabled": payload.get("waitlist_enabled", True),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user.get("user_id"),
    }
    if existing:
        await db.registration_configs.update_one({"event_id": event_id, "tenant_id": tenant_id}, {"$set": config_data})
        return {"message": "Registration config updated", "config": config_data}
    else:
        config_data["id"] = str(uuid.uuid4())
        config_data["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.registration_configs.insert_one(config_data)
        return {"message": "Registration config created", "config": {k: v for k, v in config_data.items() if k != "_id"}}


@router.get("/admin/registrations/{event_id}/registrants")
async def get_event_registrants(request: Request, event_id: str, status: Optional[str] = None):
    """Get all registrants for a registration event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    query = {"event_id": event_id, "tenant_id": tenant_id}
    if status:
        query["status"] = status
    registrants = await db.event_registrations.find(query, {"_id": 0}).sort("registered_at", -1).to_list(500)
    totals = {
        "confirmed": len([r for r in registrants if r.get("status") != "waitlisted" and r.get("status") != "cancelled"]),
        "waitlisted": len([r for r in registrants if r.get("status") == "waitlisted"]),
        "cancelled": len([r for r in registrants if r.get("status") == "cancelled"]),
    }
    return {"registrants": registrants, "totals": totals}


@router.put("/admin/registrations/{event_id}/registrants/{registration_id}")
async def update_registrant_status(request: Request, event_id: str, registration_id: str, payload: dict):
    """Update a registrant's status (confirm waitlisted, cancel, etc)"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    new_status = payload.get("status", "confirmed")
    result = await db.event_registrations.update_one(
        {"id": registration_id, "event_id": event_id, "tenant_id": tenant_id},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user.get("user_id")}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Registration not found")
    if new_status == "confirmed":
        await db.events.update_one({"id": event_id}, {"$inc": {"registration_count": 1}})
    return {"message": f"Registration updated to {new_status}"}


@router.post("/admin/registrations/{event_id}/promo-codes")
async def add_promo_code(request: Request, event_id: str, payload: dict):
    """Add a promo code to a registration event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    code = {
        "id": str(uuid.uuid4()),
        "code": payload.get("code", "").upper(),
        "discount_type": payload.get("discount_type", "percentage"),
        "discount_value": payload.get("discount_value", 0),
        "max_uses": payload.get("max_uses"),
        "uses_count": 0,
        "is_active": True,
    }
    await db.registration_configs.update_one(
        {"event_id": event_id, "tenant_id": tenant_id},
        {"$push": {"promo_codes": code}}
    )
    return {"promo_code": code}


@router.get("/admin/events/{event_id}/registrations")
async def get_event_registrations(request: Request, event_id: str):
    """Get all registrations for an event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Verify event exists
    query = {"id": event_id, "tenant_id": tenant_id}
    
    event = await db.events.find_one(query, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get registrations
    registrations = await db.event_registrations.find(
        {"event_id": event_id},
        {"_id": 0}
    ).to_list(500)
    
    return {
        "event": event,
        "registrations": registrations,
        "total": len(registrations)
    }

class AdminRegisterRequest(BaseModel):
    user_id: Optional[str] = None
    person_id: Optional[str] = None
    name: str
    email: Optional[str] = None


@router.post("/admin/events/{event_id}/registrations")
async def admin_register_for_event(request: Request, event_id: str, reg_data: AdminRegisterRequest):
    """Admin registers someone for an event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Verify event exists
    query = {"id": event_id, "tenant_id": tenant_id}
    
    event = await db.events.find_one(query, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check capacity
    if event.get("capacity"):
        current_count = await db.event_registrations.count_documents({"event_id": event_id})
        if current_count >= event["capacity"]:
            raise HTTPException(status_code=400, detail="This event is full")
    
    # Create registration
    registration = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id or event.get("tenant_id"),
        "event_id": event_id,
        "user_id": reg_data.user_id,
        "person_id": reg_data.person_id,
        "user_name": reg_data.name,
        "user_email": reg_data.email,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "registered_by_admin": True
    }
    
    await db.event_registrations.insert_one(registration)
    await db.events.update_one({"id": event_id}, {"$inc": {"registration_count": 1}})
    
    logger.info("admin_event_registration_created", extra={"tenant_id": tenant_id, "event_id": event_id, "registration_id": registration["id"]})
    
    return {"message": f"Registered {reg_data.name} for {event['name']}", "registration_id": registration["id"]}


@router.delete("/admin/events/{event_id}/registrations/{registration_id}")
async def admin_cancel_registration(request: Request, event_id: str, registration_id: str):
    """Admin cancels a registration"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Verify event exists
    query = {"id": event_id, "tenant_id": tenant_id}
    
    event = await db.events.find_one(query, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete registration
    result = await db.event_registrations.delete_one({"id": registration_id, "event_id": event_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    await db.events.update_one({"id": event_id}, {"$inc": {"registration_count": -1}})
    
    return {"message": "Registration cancelled"}

# ============== MEMBER PORTAL - MY REGISTRATIONS ==============


@router.get("/admin/events")
async def get_admin_events(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    upcoming_only: bool = True
):
    """Get all events for admin management"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    
    if upcoming_only:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        query["event_date"] = {"$gte": today}
    
    events = await db.events.find(
        query, {"_id": 0}
    ).sort("event_date", 1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.events.count_documents(query)
    
    # Get registration counts
    for event in events:
        reg_count = await db.event_registrations.count_documents({"event_id": event["id"]})
        event["registration_count"] = reg_count
    
    return {
        "events": events,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/admin/events")
async def create_event(request: Request, event_data: EventCreate):
    """Create a new event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    new_event = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": event_data.name,
        "description": event_data.description,
        "event_date": event_data.event_date,
        "start_time": event_data.start_time,
        "end_time": event_data.end_time,
        "location": event_data.location,
        "capacity": event_data.capacity,
        "is_public": event_data.is_public,
        "requires_registration": event_data.requires_registration,
        "registration_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.events.insert_one(new_event)
    
    logger.info("event_created", extra={"tenant_id": tenant_id, "event_id": new_event.get("id")})
    
    return {
        "message": "Event created successfully",
        "event": {k: v for k, v in new_event.items() if k != "_id"}
    }


@router.put("/admin/events/{event_id}")
async def update_event(request: Request, event_id: str, updates: dict):
    """Update an event's details"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": event_id, "tenant_id": tenant_id}
    
    allowed_fields = [
        "name", "description", "event_date", "start_time", "end_time",
        "location", "capacity", "is_public", "requires_registration",
        "category", "is_featured", "ticket_tiers"
    ]
    
    update_data = {k: v for k, v in updates.items() if k in allowed_fields}
    
    result = await db.events.update_one(query, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"message": "Event updated successfully"}


@router.delete("/admin/events/{event_id}")
async def delete_event(request: Request, event_id: str):
    """Delete an event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": event_id, "tenant_id": tenant_id}
    
    result = await db.events.delete_one(query)
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Also delete registrations
    await db.event_registrations.delete_many({"event_id": event_id})
    
    return {"message": "Event deleted successfully"}


# ============== PHASE 2: CALENDAR APPROVALS ==============

class RoomBookingRequest(BaseModel):
    event_name: str
    description: Optional[str] = None
    event_date: str
    start_time: str
    end_time: str
    room_id: str
    room_name: Optional[str] = None
    campus_id: Optional[str] = None
    requested_by: Optional[str] = None
    notes: Optional[str] = None
    recurrence: Optional[str] = None

class ApprovalDecision(BaseModel):
    decision: str  # "approved" or "rejected"
    notes: Optional[str] = None


@router.post("/admin/calendar/booking-requests")
async def create_booking_request(request: Request, payload: RoomBookingRequest):
    """Create a room booking request that needs approval"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    booking = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "event_name": payload.event_name,
        "description": payload.description,
        "event_date": payload.event_date,
        "start_time": payload.start_time,
        "end_time": payload.end_time,
        "room_id": payload.room_id,
        "room_name": payload.room_name or "Main Room",
        "campus_id": payload.campus_id,
        "requested_by": user.get("name", "Unknown"),
        "requested_by_id": user.get("user_id"),
        "notes": payload.notes,
        "status": "pending",
        "conflicts": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    # Check for conflicts
    conflicts = await db.booking_requests.find({
        "tenant_id": tenant_id,
        "room_id": payload.room_id,
        "event_date": payload.event_date,
        "status": {"$in": ["pending", "approved"]},
    }, {"_id": 0}).to_list(100)
    conflict_list = []
    for existing in conflicts:
        if (payload.start_time < existing.get("end_time", "24:00") and
            payload.end_time > existing.get("start_time", "00:00")):
            conflict_list.append({
                "id": existing["id"],
                "event_name": existing["event_name"],
                "start_time": existing["start_time"],
                "end_time": existing["end_time"],
                "status": existing["status"]
            })
    booking["conflicts"] = conflict_list
    booking["has_conflicts"] = len(conflict_list) > 0
    await db.booking_requests.insert_one(booking)
    return {
        "id": booking["id"],
        "status": "pending",
        "has_conflicts": booking["has_conflicts"],
        "conflicts": conflict_list,
        "message": "Booking request submitted for approval" + (" (conflicts detected)" if conflict_list else "")
    }


@router.get("/admin/calendar/approvals")
async def get_calendar_approvals(request: Request, status: Optional[str] = None, campus_id: Optional[str] = None):
    """Get room booking requests pending approval"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    if campus_id:
        query["campus_id"] = campus_id
    bookings = await db.booking_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    counts = {
        "pending": await db.booking_requests.count_documents({"tenant_id": tenant_id, "status": "pending"}),
        "approved": await db.booking_requests.count_documents({"tenant_id": tenant_id, "status": "approved"}),
        "rejected": await db.booking_requests.count_documents({"tenant_id": tenant_id, "status": "rejected"}),
    }
    return {"bookings": bookings, "counts": counts}


@router.post("/admin/calendar/approvals/{booking_id}")
async def decide_booking(request: Request, booking_id: str, payload: ApprovalDecision):
    """Approve or reject a booking request"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if payload.decision not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")
    result = await db.booking_requests.update_one(
        {"id": booking_id, "tenant_id": tenant_id},
        {"$set": {
            "status": payload.decision,
            "decided_by": user.get("name", "Admin"),
            "decided_at": datetime.now(timezone.utc).isoformat(),
            "decision_notes": payload.notes,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Booking request not found")
    if payload.decision == "approved":
        booking = await db.booking_requests.find_one({"id": booking_id}, {"_id": 0})
        if booking:
            event = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "name": booking["event_name"],
                "description": booking.get("description", ""),
                "event_date": booking["event_date"],
                "start_time": booking.get("start_time"),
                "end_time": booking.get("end_time"),
                "location": booking.get("room_name", ""),
                "room_id": booking.get("room_id"),
                "capacity": 100,
                "is_public": True,
                "requires_registration": False,
                "registration_count": 0,
                "booking_id": booking_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.events.insert_one(event)
    return {"message": f"Booking {payload.decision}", "status": payload.decision}


@router.post("/admin/calendar/approvals/bulk")
async def bulk_decide_bookings(request: Request, payload: dict):
    """Bulk approve or reject multiple booking requests"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    booking_ids = payload.get("booking_ids", [])
    decision = payload.get("decision", "")
    if decision not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")
    updated = 0
    for bid in booking_ids:
        r = await db.booking_requests.update_one(
            {"id": bid, "tenant_id": tenant_id, "status": "pending"},
            {"$set": {
                "status": decision,
                "decided_by": user.get("name", "Admin"),
                "decided_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        if r.modified_count > 0:
            updated += 1
            if decision == "approved":
                bk = await db.booking_requests.find_one({"id": bid}, {"_id": 0})
                if bk:
                    await db.events.insert_one({
                        "id": str(uuid.uuid4()), "tenant_id": tenant_id,
                        "name": bk["event_name"], "description": bk.get("description", ""),
                        "event_date": bk["event_date"], "start_time": bk.get("start_time"),
                        "end_time": bk.get("end_time"), "location": bk.get("room_name", ""),
                        "room_id": bk.get("room_id"), "capacity": 100,
                        "is_public": True, "requires_registration": False,
                        "registration_count": 0, "booking_id": bid,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
    return {"message": f"{updated} bookings {decision}", "updated": updated}


@router.get("/admin/calendar/conflicts")
async def get_calendar_conflicts(request: Request, date: Optional[str] = None):
    """Detect room booking conflicts"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    query = {"tenant_id": tenant_id, "status": {"$in": ["pending", "approved"]}}
    if date:
        query["event_date"] = date
    bookings = await db.booking_requests.find(query, {"_id": 0}).to_list(500)
    conflicts = []
    for i, a in enumerate(bookings):
        for b in bookings[i+1:]:
            if (a["room_id"] == b["room_id"] and a["event_date"] == b["event_date"] and
                a["start_time"] < b.get("end_time", "24:00") and
                a["end_time"] > b.get("start_time", "00:00")):
                conflicts.append({
                    "room_id": a["room_id"],
                    "room_name": a.get("room_name", ""),
                    "date": a["event_date"],
                    "booking_a": {"id": a["id"], "event_name": a["event_name"], "start_time": a["start_time"], "end_time": a["end_time"], "status": a["status"]},
                    "booking_b": {"id": b["id"], "event_name": b["event_name"], "start_time": b["start_time"], "end_time": b["end_time"], "status": b["status"]},
                })
    return {"conflicts": conflicts, "total": len(conflicts)}


@router.get("/admin/calendar/rooms")
async def get_rooms(request: Request):
    """Get available rooms for the tenant"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    rooms = await db.rooms.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(100)
    if not rooms:
        default_rooms = [
            {"id": "sanctuary", "name": "Sanctuary", "capacity": 500, "campus": "Main Campus"},
            {"id": "fellowship-hall", "name": "Fellowship Hall", "capacity": 200, "campus": "Main Campus"},
            {"id": "room-101", "name": "Room 101", "capacity": 30, "campus": "Main Campus"},
            {"id": "room-102", "name": "Room 102", "capacity": 30, "campus": "Main Campus"},
            {"id": "room-103", "name": "Room 103", "capacity": 25, "campus": "Main Campus"},
            {"id": "youth-room", "name": "Youth Room", "capacity": 75, "campus": "Main Campus"},
            {"id": "nursery", "name": "Nursery", "capacity": 20, "campus": "Main Campus"},
            {"id": "conference-room", "name": "Conference Room", "capacity": 12, "campus": "Main Campus"},
            {"id": "gym", "name": "Gymnasium", "capacity": 300, "campus": "Main Campus"},
            {"id": "outdoor-pavilion", "name": "Outdoor Pavilion", "capacity": 150, "campus": "Main Campus"},
        ]
        for r in default_rooms:
            r["tenant_id"] = tenant_id
        await db.rooms.insert_many(default_rooms)
        rooms = default_rooms
    return {"rooms": [{k: v for k, v in r.items() if k not in ["_id", "tenant_id"]} for r in rooms]}


# ─── Full Calendar API ────────────────────────────────────────────────────────

@router.get("/admin/events/calendar")
async def get_calendar_events(
    request: Request,
    start: str = None,
    end: str = None,
    event_type: str = None,
):
    """Return events in FullCalendar-compatible format with date range filtering."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")

    query: dict = {"tenant_id": tenant_id}
    if start or end:
        date_filter = {}
        if start:
            date_filter["$gte"] = start[:10]
        if end:
            date_filter["$lte"] = end[:10]
        if date_filter:
            query["event_date"] = date_filter
    if event_type:
        query["event_type"] = event_type

    events = await db.events.find(query, {"_id": 0}).sort("event_date", 1).limit(500).to_list(500)

    EVENT_COLORS = {
        "service": "#1e40af",
        "community": "#16a34a",
        "conference": "#7c3aed",
        "youth": "#db2777",
        "group": "#d97706",
        "training": "#0891b2",
        "other": "#64748b",
    }

    fc_events = []
    for e in events:
        date = e.get("event_date", "")
        start_time = e.get("start_time", "")
        end_time = e.get("end_time", "")
        etype = e.get("event_type", "other")

        fc_event = {
            "id": e.get("id"),
            "title": e.get("name", "Event"),
            "backgroundColor": EVENT_COLORS.get(etype, EVENT_COLORS["other"]),
            "borderColor": EVENT_COLORS.get(etype, EVENT_COLORS["other"]),
            "extendedProps": {
                "description": e.get("description", ""),
                "location": e.get("location", ""),
                "capacity": e.get("capacity"),
                "event_type": etype,
                "requires_registration": e.get("requires_registration", False),
                "is_public": e.get("is_public", True),
                "price": e.get("price", 0),
                "ticket_tiers": e.get("ticket_tiers", []),
                "recurring": e.get("recurring", False),
                "rrule": e.get("rrule", ""),
            }
        }

        if start_time:
            fc_event["start"] = f"{date}T{start_time}"
            fc_event["end"] = f"{date}T{end_time}" if end_time else None
        else:
            fc_event["start"] = date
            fc_event["allDay"] = True

        fc_events.append(fc_event)

    return {"events": fc_events}


@router.post("/admin/events/{event_id}/clone")
async def clone_event(request: Request, event_id: str):
    """Clone an event for quick duplication."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    original = await db.events.find_one({"id": event_id, "tenant_id": tenant_id}, {"_id": 0})
    if not original:
        raise HTTPException(status_code=404, detail="Event not found")

    new_event = {**original, "id": str(uuid.uuid4()), "name": f"Copy of {original.get('name','')}",
                 "created_at": datetime.now(timezone.utc).isoformat()}
    await db.events.insert_one(new_event)
    return {"message": "Event cloned", "event_id": new_event["id"]}



# ============== PHASE 2: PEOPLE WORKFLOWS ==============

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger: Optional[str] = "manual"
    steps: Optional[List[Dict[str, Any]]] = None

class FormCreate(BaseModel):
    name: str
    description: Optional[str] = None
    fields: Optional[List[Dict[str, Any]]] = None
    is_public: bool = True
    auto_create_profile: bool = False
    redirect_url: Optional[str] = None

