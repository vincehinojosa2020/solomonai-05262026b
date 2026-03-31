"""Solomon AI — Admin Kids Check-In Routes"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import random
import logging

from core import db, DEFAULT_TENANT_ID, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc, generate_pickup_code
from models.schemas import Child, Checkin, Group, KidsCheckoutRequest, RegisterFamilyPayload, SermonCreate, SermonUpdate

router = APIRouter()

@router.get("/admin/kids/checkins")
async def get_all_checkins(request: Request, status: str = None):
    """Get all check-ins for admin view"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    
    checkins = await db.checkins.find(query, {"_id": 0}).sort("checked_in_at", -1).to_list(200)
    return {"checkins": [serialize_doc(c) for c in checkins]}


@router.post("/admin/kids/checkins/{checkin_id}/checkout")
async def checkout_child(request: Request, checkin_id: str):
    """Admin: Check out a child"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    checkin = await db.checkins.find_one({"id": checkin_id, "tenant_id": tenant_id}, {"_id": 0})
    if not checkin:
        raise HTTPException(status_code=404, detail="Check-in not found")
    
    if checkin.get("status") == "checked_out":
        raise HTTPException(status_code=400, detail="Child is already checked out")
    
    await db.checkins.update_one(
        {"id": checkin_id},
        {"$set": {
            "status": "checked_out",
            "checked_out_at": datetime.now(timezone.utc).isoformat(),
            "checked_out_by": user.get("name", "Admin")
        }}
    )
    
    updated = await db.checkins.find_one({"id": checkin_id}, {"_id": 0})
    
    # Notify parent via push
    try:
        child = await db.children.find_one({"id": checkin.get("child_id")}, {"_id": 0})
        if child and child.get("parent_id"):
            await send_push_notification(
                child["parent_id"], user.get("tenant_id", ""),
                "Pickup Time!",
                f"{child.get('name', 'Your child')} is ready for pickup.",
                "/portal/kids"
            )
    except Exception:
        pass
    
    return {"message": "Child checked out", "checkin": serialize_doc(updated)}


@router.get("/admin/kids/checkins/history")
async def get_checkin_history(request: Request, days: int = 30):
    """Get check-in history for reporting"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    checkins = await db.checkins.find({
        "tenant_id": tenant_id,
        "checked_in_at": {"$gte": cutoff.isoformat()}
    }, {"_id": 0}).sort("checked_in_at", -1).to_list(500)
    
    return {"checkins": [serialize_doc(c) for c in checkins], "days": days}


@router.get("/admin/kids/all")
async def get_all_kids_admin(request: Request):
    """Get all registered children for admin view"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Get all children with parent info
    children = await db.children.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(500)
    
    # Enrich with parent info
    enriched = []
    for child in children:
        parent = await db.users.find_one({"id": child.get("parent_user_id")}, {"_id": 0, "password_hash": 0})
        enriched.append({
            **serialize_doc(child),
            "parent_name": parent.get("name") if parent else "Unknown",
            "parent_phone": parent.get("phone") if parent else None,
            "parent_email": parent.get("email") if parent else None
        })
    
    return {"children": enriched}


@router.post("/admin/kids/{child_id}/checkin")
async def admin_checkin_child(request: Request, child_id: str, payload: dict = None):
    """Admin: Check in a child directly"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Get child
    child = await db.children.find_one({"id": child_id, "tenant_id": tenant_id}, {"_id": 0})
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    # Check if already checked in
    existing = await db.checkins.find_one({
        "child_id": child_id,
        "status": "checked_in"
    }, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Child is already checked in")
    
    # Generate pickup code
    pickup_code = generate_pickup_code()
    
    # Get parent info
    parent = await db.users.find_one({"user_id": child.get("parent_user_id")}, {"_id": 0})
    parent_name = parent.get("name", "Unknown Parent") if parent else "Unknown Parent"
    parent_phone = parent.get("phone") if parent else None
    
    checkin = Checkin(
        tenant_id=tenant_id,
        child_id=child_id,
        child_name=child.get("name", "Unknown Child"),
        parent_user_id=child.get("parent_user_id"),
        parent_name=parent_name,
        parent_phone=parent_phone,
        pickup_code=pickup_code,
        classroom=payload.get("classroom", "Sunday School") if payload else "Sunday School"
    ).model_dump()
    checkin["checked_in_at"] = datetime.now(timezone.utc).isoformat()
    checkin["checked_in_by"] = user.get("name", "Admin")
    
    await db.checkins.insert_one(checkin)
    
    # Mock SMS notification (parent info already retrieved above)
    print(f"[MOCK SMS] To: {parent_phone or 'No phone'}")
    print(f"[MOCK SMS] Message: Hi {parent_name}! {child.get('name')} has been checked into Sunday School by {user.get('name', 'Staff')}. Pickup code: {pickup_code}")
    
    return {
        "message": f"{child.get('name')} checked in successfully",
        "pickup_code": pickup_code,
        "checkin": serialize_doc(checkin)
    }


@router.post("/admin/kids/verify-pickup")
async def verify_pickup_code(request: Request, payload: dict):
    """Admin: Verify a pickup code and get child info"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    code = payload.get("code", "").upper().strip()
    if not code:
        raise HTTPException(status_code=400, detail="Pickup code required")
    
    # Find active check-in with this code
    checkin = await db.checkins.find_one({
        "tenant_id": tenant_id,
        "pickup_code": code,
        "status": "checked_in"
    }, {"_id": 0})
    
    if not checkin:
        return {"valid": False, "message": "Invalid or expired pickup code"}
    
    # Get child info
    child = await db.children.find_one({"id": checkin.get("child_id")}, {"_id": 0})
    
    # Get parent info
    parent = await db.users.find_one({"id": checkin.get("parent_user_id")}, {"_id": 0, "password_hash": 0})
    
    return {
        "valid": True,
        "checkin": serialize_doc(checkin),
        "child": serialize_doc(child) if child else None,
        "parent": {
            "name": parent.get("name") if parent else "Unknown",
            "phone": parent.get("phone") if parent else None,
            "email": parent.get("email") if parent else None
        }
    }

class RegisterFamilyPayload(BaseModel):
    parentName: str
    parentEmail: str
    parentPhone: str = ""
    childName: str
    childBirthdate: str = ""
    childAllergies: str = ""
    childNotes: str = ""


@router.post("/admin/kids/register-family")
async def register_new_family(request: Request, payload: RegisterFamilyPayload):
    """Admin: Register a new family (walk-in) directly from front desk"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Check if parent already exists
    existing_user = await db.users.find_one({"email": payload.parentEmail.lower()})
    
    if existing_user:
        parent_user_id = existing_user.get("user_id")
        # Check if child already exists for this parent
        existing_child = await db.children.find_one({
            "parent_user_id": parent_user_id,
            "name": payload.childName
        })
        if existing_child:
            raise HTTPException(status_code=400, detail=f"{payload.childName} is already registered for this parent")
    else:
        # Create new parent user
        parent_user_id = f"member_{str(uuid.uuid4())[:8]}"
        temp_password = secrets.token_urlsafe(12)
        import bcrypt as _bc; password_hash = _bc.hashpw(temp_password.encode("utf-8"), _bc.gensalt()).decode("utf-8")
        new_user = {
            "user_id": parent_user_id,
            "email": payload.parentEmail.lower(),
            "name": payload.parentName,
            "phone": payload.parentPhone,
            "role": "member",
            "tenant_id": tenant_id,
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "registered_by_admin": True
        }
        await db.users.insert_one(new_user)
        
        # Log temporary password for staff to share
        print(f"[NEW FAMILY] Created parent: {payload.parentEmail} | Temp Password: {temp_password}")
    
    # Create child
    child_id = str(uuid.uuid4())
    child = {
        "id": child_id,
        "tenant_id": tenant_id,
        "parent_user_id": parent_user_id,
        "parent_name": payload.parentName,
        "parent_phone": payload.parentPhone,
        "name": payload.childName,
        "birthdate": payload.childBirthdate if payload.childBirthdate else None,
        "allergies": payload.childAllergies,
        "special_needs": payload.childNotes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.children.insert_one(child)
    
    return {
        "message": f"Family registered successfully! Welcome {payload.parentName} & {payload.childName}",
        "parent_email": payload.parentEmail,
        "child_id": child_id,
        "new_user": not existing_user
    }

# ============== PHASE 6: CHECK-IN ENHANCEMENT ==============

# --- Check-in Locations ---
@router.get("/admin/checkin/locations")
async def get_checkin_locations(request: Request):
    """Get all check-in locations/rooms"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        return {"locations": []}
    locations = await db.checkin_locations.find({"tenant_id": tenant_id}, {"_id": 0}).sort("name", 1).to_list(100)
    if not locations:
        # Seed default locations
        defaults = [
            {"name": "Nursery", "room": "Room 100", "age_range": "0-2", "capacity": 15, "folder": "Early Childhood"},
            {"name": "Toddlers", "room": "Room 101", "age_range": "2-3", "capacity": 20, "folder": "Early Childhood"},
            {"name": "Pre-K", "room": "Room 102", "age_range": "3-5", "capacity": 25, "folder": "Preschool"},
            {"name": "K-1st Grade", "room": "Room 201", "age_range": "5-7", "capacity": 30, "folder": "Elementary"},
            {"name": "2nd-3rd Grade", "room": "Room 202", "age_range": "7-9", "capacity": 30, "folder": "Elementary"},
            {"name": "4th-5th Grade", "room": "Room 203", "age_range": "9-11", "capacity": 30, "folder": "Elementary"},
            {"name": "Middle School", "room": "Youth Center", "age_range": "11-14", "capacity": 40, "folder": "Youth"},
            {"name": "Special Needs", "room": "Room 105", "age_range": "All", "capacity": 10, "folder": "Specialized"},
        ]
        for loc in defaults:
            loc["id"] = str(uuid.uuid4())
            loc["tenant_id"] = tenant_id
            loc["is_active"] = True
            loc["created_at"] = datetime.now(timezone.utc).isoformat()
            await db.checkin_locations.insert_one(loc)
        locations = await db.checkin_locations.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(100)
    return {"locations": locations}


@router.post("/admin/checkin/locations")
async def create_checkin_location(request: Request, payload: dict):
    """Create a check-in location"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    location = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": payload.get("name", ""),
        "room": payload.get("room", ""),
        "age_range": payload.get("age_range", ""),
        "capacity": payload.get("capacity", 30),
        "folder": payload.get("folder", "General"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.checkin_locations.insert_one(location)
    return {"location": {k: v for k, v in location.items() if k != "_id"}}


@router.put("/admin/checkin/locations/{location_id}")
async def update_checkin_location(request: Request, location_id: str, payload: dict):
    """Update a check-in location"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    updates = {}
    for f in ["name", "room", "age_range", "capacity", "folder", "is_active"]:
        if f in payload:
            updates[f] = payload[f]
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.checkin_locations.update_one({"id": location_id, "tenant_id": tenant_id}, {"$set": updates})
    return {"message": "Location updated"}


@router.delete("/admin/checkin/locations/{location_id}")
async def delete_checkin_location(request: Request, location_id: str):
    """Delete a check-in location"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    await db.checkin_locations.delete_one({"id": location_id, "tenant_id": tenant_id})
    return {"message": "Location deleted"}

# --- Check-in Station Config ---
@router.get("/admin/checkin/stations")
async def get_checkin_stations(request: Request):
    """Get check-in station configurations"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        return {"stations": []}
    stations = await db.checkin_stations.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(20)
    if not stations:
        defaults = [
            {"name": "Main Lobby Kiosk", "mode": "self", "location_ids": [], "description": "Self check-in at lobby entrance"},
            {"name": "Front Desk", "mode": "manned", "location_ids": [], "description": "Staffed check-in station"},
        ]
        for st in defaults:
            st["id"] = str(uuid.uuid4())
            st["tenant_id"] = tenant_id
            st["is_active"] = True
            st["created_at"] = datetime.now(timezone.utc).isoformat()
            await db.checkin_stations.insert_one(st)
        stations = await db.checkin_stations.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(20)
    return {"stations": stations}


@router.post("/admin/checkin/stations")
async def create_checkin_station(request: Request, payload: dict):
    """Create a check-in station"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    station = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": payload.get("name", ""),
        "mode": payload.get("mode", "self"),
        "location_ids": payload.get("location_ids", []),
        "description": payload.get("description", ""),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.checkin_stations.insert_one(station)
    return {"station": {k: v for k, v in station.items() if k != "_id"}}


@router.put("/admin/checkin/stations/{station_id}")
async def update_checkin_station(request: Request, station_id: str, payload: dict):
    """Update a check-in station"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    updates = {}
    for f in ["name", "mode", "location_ids", "description", "is_active"]:
        if f in payload:
            updates[f] = payload[f]
    await db.checkin_stations.update_one({"id": station_id, "tenant_id": tenant_id}, {"$set": updates})
    return {"message": "Station updated"}


@router.delete("/admin/checkin/stations/{station_id}")
async def delete_checkin_station(request: Request, station_id: str):
    """Delete a check-in station"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    await db.checkin_stations.delete_one({"id": station_id, "tenant_id": tenant_id})
    return {"message": "Station deleted"}

# --- Label Templates ---
@router.get("/admin/checkin/labels")
async def get_label_templates(request: Request):
    """Get label templates"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    templates = await db.checkin_labels.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(50)
    if not templates:
        defaults = [
            {
                "name": "Standard Name Tag",
                "type": "name_tag",
                "width": 4, "height": 2,
                "fields": ["child_name", "classroom", "allergies_icon", "security_code"],
                "layout": {"font_size": 18, "show_allergies": True, "show_barcode": True, "show_logo": True},
                "is_default": True,
            },
            {
                "name": "Security Label (Parent)",
                "type": "security",
                "width": 4, "height": 1,
                "fields": ["child_name", "security_code", "classroom"],
                "layout": {"font_size": 14, "show_allergies": False, "show_barcode": True, "show_logo": False},
                "is_default": False,
            },
            {
                "name": "Allergy Alert Tag",
                "type": "allergy",
                "width": 4, "height": 2,
                "fields": ["child_name", "classroom", "allergies_detail", "medical_notes", "security_code"],
                "layout": {"font_size": 16, "show_allergies": True, "show_barcode": True, "show_logo": True, "allergy_highlight": True},
                "is_default": False,
            },
        ]
        for t in defaults:
            t["id"] = str(uuid.uuid4())
            t["tenant_id"] = tenant_id
            t["created_at"] = datetime.now(timezone.utc).isoformat()
            await db.checkin_labels.insert_one(t)
        templates = await db.checkin_labels.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(50)
    return {"templates": templates}


@router.post("/admin/checkin/labels")
async def create_label_template(request: Request, payload: dict):
    """Create a label template"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    template = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": payload.get("name", ""),
        "type": payload.get("type", "name_tag"),
        "width": payload.get("width", 4),
        "height": payload.get("height", 2),
        "fields": payload.get("fields", ["child_name", "classroom", "security_code"]),
        "layout": payload.get("layout", {}),
        "is_default": payload.get("is_default", False),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.checkin_labels.insert_one(template)
    return {"template": {k: v for k, v in template.items() if k != "_id"}}


@router.put("/admin/checkin/labels/{label_id}")
async def update_label_template(request: Request, label_id: str, payload: dict):
    """Update a label template"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    updates = {}
    for f in ["name", "type", "width", "height", "fields", "layout", "is_default"]:
        if f in payload:
            updates[f] = payload[f]
    await db.checkin_labels.update_one({"id": label_id, "tenant_id": tenant_id}, {"$set": updates})
    return {"message": "Label template updated"}


@router.delete("/admin/checkin/labels/{label_id}")
async def delete_label_template(request: Request, label_id: str):
    """Delete a label template"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    await db.checkin_labels.delete_one({"id": label_id, "tenant_id": tenant_id})
    return {"message": "Label template deleted"}

# --- Medical/Allergy Alerts ---
@router.get("/admin/checkin/medical-alerts")
async def get_medical_alerts(request: Request):
    """Get all children with medical/allergy alerts"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    children = await db.children.find(
        {"tenant_id": tenant_id, "$or": [
            {"allergies": {"$exists": True, "$ne": ""}},
            {"medical_notes": {"$exists": True, "$ne": ""}},
        ]}, {"_id": 0}
    ).to_list(500)
    return {"alerts": children, "total": len(children)}


@router.put("/admin/checkin/children/{child_id}/medical")
async def update_child_medical(request: Request, child_id: str, payload: dict):
    """Update medical/allergy info for a child"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    updates = {}
    for f in ["allergies", "medical_notes", "medical_severity", "authorized_guardians"]:
        if f in payload:
            updates[f] = payload[f]
    updates["medical_updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.children.update_one({"id": child_id, "tenant_id": tenant_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Child not found")
    return {"message": "Medical info updated"}

# --- Guardian Verification ---
@router.get("/admin/checkin/children/{child_id}/guardians")
async def get_child_guardians(request: Request, child_id: str):
    """Get authorized guardians for a child"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    child = await db.children.find_one({"id": child_id, "tenant_id": tenant_id}, {"_id": 0})
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    return {"guardians": child.get("authorized_guardians", []), "child_name": child.get("name")}


@router.post("/admin/checkin/children/{child_id}/guardians")
async def add_guardian(request: Request, child_id: str, payload: dict):
    """Add an authorized guardian for a child"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    guardian = {
        "id": str(uuid.uuid4()),
        "name": payload.get("name", ""),
        "relationship": payload.get("relationship", ""),
        "phone": payload.get("phone", ""),
        "photo_url": payload.get("photo_url", ""),
        "pin_code": payload.get("pin_code", ""),
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.children.update_one(
        {"id": child_id, "tenant_id": tenant_id},
        {"$push": {"authorized_guardians": guardian}}
    )
    return {"guardian": guardian}


@router.delete("/admin/checkin/children/{child_id}/guardians/{guardian_id}")
async def remove_guardian(request: Request, child_id: str, guardian_id: str):
    """Remove an authorized guardian"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    await db.children.update_one(
        {"id": child_id, "tenant_id": tenant_id},
        {"$pull": {"authorized_guardians": {"id": guardian_id}}}
    )
    return {"message": "Guardian removed"}

# --- Check-in Reports ---
@router.get("/admin/checkin/reports/trends")
async def get_checkin_trends(request: Request, days: int = 30):
    """Get check-in attendance trends"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    checkins = await db.checkins.find(
        {"tenant_id": tenant_id, "checked_in_at": {"$gte": cutoff}}, {"_id": 0, "checked_in_at": 1, "classroom": 1}
    ).to_list(5000)
    # Group by date
    daily = {}
    by_room = {}
    for c in checkins:
        date = c.get("checked_in_at", "")[:10]
        daily[date] = daily.get(date, 0) + 1
        room = c.get("classroom", "Unknown")
        by_room[room] = by_room.get(room, 0) + 1
    sorted_daily = sorted(daily.items(), key=lambda x: x[0])
    return {
        "daily_trend": [{"date": d, "count": c} for d, c in sorted_daily],
        "by_room": [{"room": r, "count": c} for r, c in sorted(by_room.items(), key=lambda x: -x[1])],
        "total_checkins": len(checkins),
        "period_days": days,
    }


@router.get("/admin/checkin/reports/first-timers")
async def get_first_time_visitors(request: Request, days: int = 30):
    """Get first-time check-in visitors"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    # Find children who had their first check-in within the period
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {"_id": "$child_id", "first_checkin": {"$min": "$checked_in_at"}, "child_name": {"$first": "$child_name"}, "total_checkins": {"$sum": 1}}},
        {"$match": {"first_checkin": {"$gte": cutoff}}},
        {"$sort": {"first_checkin": -1}},
        {"$limit": 100},
    ]
    results = await db.checkins.aggregate(pipeline).to_list(100)
    first_timers = [{"child_id": r["_id"], "child_name": r.get("child_name", "Unknown"), "first_checkin": r["first_checkin"], "total_checkins": r["total_checkins"]} for r in results]
    return {"first_timers": first_timers, "total": len(first_timers)}

# ============== CAFE ROUTES ==============


@router.get("/admin/kids/checkins/today")
async def get_admin_kids_checkins_today(request: Request):
    """Get ALL children checked in today for this tenant."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    # Use UTC start/end of today for reliable matching
    now_utc = datetime.now(timezone.utc)
    today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_end = now_utc.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
    checkins = await db.checkins.find(
        {"tenant_id": tenant_id, "checked_in_at": {"$gte": today_start, "$lte": today_end}},
        {"_id": 0}
    ).sort("checked_in_at", -1).to_list(500)
    # Also include any still checked_in from previous days (edge case: overnight)
    still_checked_in = await db.checkins.find(
        {"tenant_id": tenant_id, "status": "checked_in", "checked_in_at": {"$lt": today_start}},
        {"_id": 0}
    ).to_list(100)
    all_checkins = checkins + still_checked_in
    enriched = []
    for c in all_checkins:
        child = await db.children.find_one({"id": c.get("child_id")}, {"_id": 0})
        enriched.append({
            "child_id": c.get("child_id"),
            "child_name": c.get("child_name"),
            "parent_name": c.get("parent_name"),
            "parent_phone": c.get("parent_phone", ""),
            "pickup_code": c.get("pickup_code"),
            "checkin_time": c.get("checked_in_at"),
            "checkout_time": c.get("checked_out_at"),
            "status": c.get("status"),
            "allergies": (child or {}).get("allergies", ""),
            "emergency_contact": (child or {}).get("emergency_contact", ""),
            "checkin_id": c.get("id"),
        })
    return {"checkins": enriched, "total": len(enriched)}


@router.post("/admin/kids/checkout")
async def admin_kids_checkout(request: Request, payload: KidsCheckoutRequest):
    """Admin verifies pickup code and checks out a child."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    checkin = await db.checkins.find_one(
        {"tenant_id": tenant_id, "child_id": payload.child_id, "status": "checked_in"},
        {"_id": 0}
    )
    if not checkin:
        raise HTTPException(status_code=404, detail="No active check-in found")
    if checkin.get("pickup_code") != payload.pickup_code:
        raise HTTPException(status_code=400, detail="Invalid pickup code")
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.checkins.update_one(
        {"id": checkin["id"]},
        {"$set": {"status": "checked_out", "checked_out_at": now_iso, "checked_out_by": user.get("name", "Admin")}}
    )
    return {"success": True, "child_name": checkin.get("child_name"), "checkout_time": now_iso}


@router.post("/admin/kids/checkout-by-code")
async def admin_kids_checkout_by_code(request: Request, payload: dict):
    """Admin scans QR or enters code — checkout without knowing child_id."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    code = payload.get("pickup_code", "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Pickup code required")
    
    # Parse QR code format: SOLOMON_PICKUP_{child_id}_{code}_{date}
    actual_code = code
    if code.startswith("SOLOMON_PICKUP_"):
        parts = code.split("_")
        if len(parts) >= 4:
            actual_code = parts[3]
    
    checkin = await db.checkins.find_one(
        {"tenant_id": tenant_id, "pickup_code": actual_code, "status": "checked_in"},
        {"_id": 0}
    )
    if not checkin:
        raise HTTPException(status_code=404, detail="No active check-in found for this code")
    
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.checkins.update_one(
        {"id": checkin["id"]},
        {"$set": {"status": "checked_out", "checked_out_at": now_iso, "checked_out_by": user.get("name", "Admin")}}
    )
    child = await db.children.find_one({"id": checkin.get("child_id")}, {"_id": 0})
    return {
        "success": True, 
        "child_name": checkin.get("child_name"), 
        "child": serialize_doc(child) if child else None,
        "checkout_time": now_iso,
        "checkin_id": checkin.get("id")
    }

# --- Admin Media Sermons CRUD ---
class SermonCreate(BaseModel):
    title: str
    description: str = ""
    video_url: str = ""
    thumbnail_url: str = ""
    pastor: str = ""
    series_name: str = ""
    duration_seconds: int = 0
    category: str = "sermon"
    published: bool = True

class SermonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    pastor: Optional[str] = None
    series_name: Optional[str] = None
    duration_seconds: Optional[int] = None
    category: Optional[str] = None
    published: Optional[bool] = None

