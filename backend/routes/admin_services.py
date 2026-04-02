"""Solomon AI — Admin Services, Songs, Volunteers, Templates Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import logging

from core import (
    db, DEFAULT_TENANT_ID,
    require_permission, get_current_admin_user, require_tenant,
    logger,
)
from core.helpers import serialize_doc
from models.schemas import Service

router = APIRouter()

@router.get("/admin/volunteers")
async def get_volunteer_teams(request: Request):
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id")
    teams = await db.volunteer_teams.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(100)
    for team in teams:
        members = await db.volunteer_assignments.find({"team_id": team["id"], "tenant_id": tenant_id}, {"_id": 0}).to_list(200)
        for m in members:
            u = await db.users.find_one({"user_id": m.get("user_id")}, {"_id": 0, "name": 1, "email": 1, "picture": 1})
            m["user"] = u
        team["members"] = members
    return {"teams": teams, "total": len(teams)}


@router.post("/admin/volunteers/teams")
async def create_volunteer_team(request: Request, payload: dict):
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id")
    team = {"id": str(uuid.uuid4()), "tenant_id": tenant_id, "team_name": payload.get("team_name"), "ministry": payload.get("ministry", ""), "description": payload.get("description", ""), "created_at": datetime.now(timezone.utc).isoformat(), "created_by": user.get("user_id")}
    await db.volunteer_teams.insert_one(team)
    return {"success": True, "team": {k: v for k, v in team.items() if k != "_id"}}


@router.post("/admin/volunteers/assign")
async def assign_volunteer(request: Request, payload: dict):
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id")
    assignment = {"id": str(uuid.uuid4()), "tenant_id": tenant_id, "user_id": payload.get("user_id"), "team_id": payload.get("team_id"), "role_title": payload.get("role_title", "Volunteer"), "assigned_at": datetime.now(timezone.utc).isoformat(), "assigned_by": user.get("user_id")}
    await db.volunteer_assignments.update_one({"user_id": payload.get("user_id"), "team_id": payload.get("team_id"), "tenant_id": tenant_id}, {"$set": assignment}, upsert=True)
    return {"success": True, "assignment": {k: v for k, v in assignment.items() if k != "_id"}}


@router.get("/admin/volunteers/user/{user_id}")
async def get_user_volunteer_teams(request: Request, user_id: str):
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id")
    assignments = await db.volunteer_assignments.find({"user_id": user_id, "tenant_id": tenant_id}, {"_id": 0}).to_list(50)
    for a in assignments:
        team = await db.volunteer_teams.find_one({"id": a.get("team_id")}, {"_id": 0})
        a["team"] = team
    return {"assignments": assignments}

# ============== HEALTH ENDPOINTS ==============


@router.get("/admin/services/plans")
async def get_service_plans(request: Request, week: str = None):
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    query = {"tenant_id": tenant_id}
    if week:
        from datetime import timedelta
        week_start = week
        week_end_dt = datetime.fromisoformat(week) + timedelta(days=7)
        query["date"] = {"$gte": week_start, "$lte": week_end_dt.strftime("%Y-%m-%d")}
    plans = await db.service_plans.find(query, {"_id": 0}).sort("date", -1).to_list(100)
    return {"plans": plans}


@router.post("/admin/services/plans")
async def create_service_plan(request: Request, payload: dict):
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    plan = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "date": payload.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "service_type": payload.get("service_type", "sunday_morning"),
        "title": payload.get("title", "Sunday Service"),
        "items": payload.get("items", []),
        "team_assignments": payload.get("team_assignments", []),
        "status": "draft",
        "created_by": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.service_plans.insert_one({**plan})
    return plan


@router.put("/admin/services/plans/{plan_id}")
async def update_service_plan(request: Request, plan_id: str, payload: dict):
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    updates = {}
    for field in ["date", "service_type", "title", "items", "team_assignments", "status"]:
        if field in payload:
            updates[field] = payload[field]
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.service_plans.update_one({"id": plan_id, "tenant_id": tenant_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    updated = await db.service_plans.find_one({"id": plan_id}, {"_id": 0})
    return updated


# ============== VOLUNTEER SCHEDULING ==============


@router.post("/admin/volunteers/schedule")
async def create_volunteer_schedule(request: Request, payload: dict):
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    entry = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "date": payload.get("date"),
        "role": payload.get("role"),
        "user_id": payload.get("user_id"),
        "user_name": payload.get("user_name", ""),
        "service_plan_id": payload.get("service_plan_id"),
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.volunteer_schedule.insert_one({**entry})
    return entry


@router.get("/admin/volunteers/schedule")
async def get_volunteer_schedule(request: Request, week: str = None):
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    query = {"tenant_id": tenant_id}
    if week:
        from datetime import timedelta
        week_end = (datetime.fromisoformat(week) + timedelta(days=7)).strftime("%Y-%m-%d")
        query["date"] = {"$gte": week, "$lte": week_end}
    entries = await db.volunteer_schedule.find(query, {"_id": 0}).sort("date", 1).to_list(500)
    roles = list(set(e.get("role", "") for e in entries))
    return {"schedule": entries, "roles": roles}


@router.get("/admin/songs")
async def get_songs(request: Request, search: Optional[str] = None):
    """Get song library"""
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    query = {"tenant_id": tenant_id}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"artist": {"$regex": search, "$options": "i"}},
        ]
    songs = await db.songs.find(query, {"_id": 0}).sort("title", 1).to_list(500)
    return {"songs": songs, "total": len(songs)}


@router.post("/admin/songs")
async def create_song(request: Request, payload: dict):
    """Add a song to the library"""
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    song = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "title": payload.get("title", ""),
        "artist": payload.get("artist", ""),
        "ccli_number": payload.get("ccli_number", ""),
        "default_key": payload.get("default_key", "C"),
        "bpm": payload.get("bpm"),
        "duration": payload.get("duration", ""),
        "arrangements": payload.get("arrangements", [
            {"id": str(uuid.uuid4()), "name": "Default", "key": payload.get("default_key", "C"), "is_default": True}
        ]),
        "lyrics": payload.get("lyrics", ""),
        "tags": payload.get("tags", []),
        "usage_count": 0,
        "last_used": None,
        "created_by": user.get("name", "Admin"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.songs.insert_one(song)
    return {"song": {k: v for k, v in song.items() if k != "_id"}}


@router.put("/admin/songs/{song_id}")
async def update_song(request: Request, song_id: str, payload: dict):
    """Update a song"""
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    allowed = ["title", "artist", "ccli_number", "default_key", "bpm", "duration", "arrangements", "lyrics", "tags"]
    updates = {k: v for k, v in payload.items() if k in allowed}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.songs.update_one({"id": song_id, "tenant_id": tenant_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Song not found")
    return {"message": "Song updated"}


@router.delete("/admin/songs/{song_id}")
async def delete_song(request: Request, song_id: str):
    """Delete a song"""
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    result = await db.songs.delete_one({"id": song_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Song not found")
    return {"message": "Song deleted"}

# ============== PHASE 3: SERVICE TYPES MANAGEMENT ==============


@router.post("/admin/service-types")
async def create_service_type(request: Request, payload: dict):
    """Create a new service type"""
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    st = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": payload.get("name", ""),
        "description": payload.get("description", ""),
        "default_day": payload.get("default_day", "sunday"),
        "default_time": payload.get("default_time", "09:00"),
        "default_items": payload.get("default_items", []),
        "teams": payload.get("teams", []),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.service_types_config.insert_one(st)
    return {"service_type": {k: v for k, v in st.items() if k != "_id"}}


@router.get("/admin/service-types")
async def get_admin_service_types(request: Request):
    """Get configurable service types"""
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    types = await db.service_types_config.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(50)
    if not types:
        defaults = [
            {"id": "sunday_morning", "name": "Sunday Morning", "default_day": "sunday", "default_time": "09:00"},
            {"id": "sunday_evening", "name": "Sunday Evening", "default_day": "sunday", "default_time": "18:00"},
            {"id": "wednesday", "name": "Wednesday Night", "default_day": "wednesday", "default_time": "19:00"},
            {"id": "special", "name": "Special Service", "default_day": "", "default_time": ""},
        ]
        for d in defaults:
            d["tenant_id"] = tenant_id
            d["is_active"] = True
            d["teams"] = []
            d["default_items"] = []
            d["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.service_types_config.insert_many(defaults)
        types = defaults
    return {"service_types": [{k: v for k, v in t.items() if k not in ["_id", "tenant_id"]} for t in types]}

# ============== PHASE 3: PLAN TEMPLATES ==============


@router.post("/admin/services/templates")
async def save_plan_as_template(request: Request, payload: dict):
    """Save a service plan as a reusable template"""
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    template = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": payload.get("name", "Untitled Template"),
        "description": payload.get("description", ""),
        "service_type": payload.get("service_type", "sunday_morning"),
        "items": payload.get("items", []),
        "team_positions": payload.get("team_positions", []),
        "created_by": user.get("name", "Admin"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.plan_templates.insert_one(template)
    return {"template": {k: v for k, v in template.items() if k != "_id"}}


@router.get("/admin/services/templates")
async def get_plan_templates(request: Request):
    """Get saved plan templates"""
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    templates = await db.plan_templates.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"templates": templates}


@router.post("/admin/services/plans/from-template")
async def create_plan_from_template(request: Request, payload: dict):
    """Create a new plan from a template"""
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    template_id = payload.get("template_id")
    template = await db.plan_templates.find_one({"id": template_id, "tenant_id": tenant_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    items = []
    for item in template.get("items", []):
        items.append({**item, "id": str(uuid.uuid4())})
    plan = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "date": payload.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "service_type": template.get("service_type", "sunday_morning"),
        "title": payload.get("title", template.get("name", "Service")),
        "items": items,
        "team_assignments": [],
        "status": "draft",
        "template_id": template_id,
        "created_by": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.service_plans.insert_one(plan)
    return {k: v for k, v in plan.items() if k != "_id"}


@router.post("/admin/services/plans/{plan_id}/duplicate")
async def duplicate_plan(request: Request, plan_id: str, payload: dict = None):
    """Duplicate an existing plan to a new date"""
    if payload is None:
        payload = {}
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    source = await db.service_plans.find_one({"id": plan_id, "tenant_id": tenant_id}, {"_id": 0})
    if not source:
        raise HTTPException(status_code=404, detail="Plan not found")
    items = []
    for item in source.get("items", []):
        items.append({**item, "id": str(uuid.uuid4())})
    new_plan = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "date": payload.get("date", source["date"]),
        "service_type": source.get("service_type"),
        "title": payload.get("title", f"{source.get('title', 'Service')} (Copy)"),
        "items": items,
        "team_assignments": [],
        "status": "draft",
        "created_by": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.service_plans.insert_one(new_plan)
    return {k: v for k, v in new_plan.items() if k != "_id"}

# ============== PHASE 3: BLOCKOUT DATES ==============


@router.post("/admin/volunteers/blockout-dates")
async def create_blockout_date(request: Request, payload: dict):
    """Create a blockout date for a volunteer"""
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    blockout = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "user_id": payload.get("user_id"),
        "user_name": payload.get("user_name", ""),
        "start_date": payload.get("start_date"),
        "end_date": payload.get("end_date", payload.get("start_date")),
        "reason": payload.get("reason", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.blockout_dates.insert_one(blockout)
    return {"blockout": {k: v for k, v in blockout.items() if k != "_id"}}


@router.get("/admin/volunteers/blockout-dates")
async def get_blockout_dates(request: Request, user_id: Optional[str] = None):
    """Get blockout dates"""
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    query = {"tenant_id": tenant_id}
    if user_id:
        query["user_id"] = user_id
    blockouts = await db.blockout_dates.find(query, {"_id": 0}).sort("start_date", 1).to_list(500)
    return {"blockout_dates": blockouts}


@router.delete("/admin/volunteers/blockout-dates/{blockout_id}")
async def delete_blockout_date(request: Request, blockout_id: str):
    """Delete a blockout date"""
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    await db.blockout_dates.delete_one({"id": blockout_id, "tenant_id": tenant_id})
    return {"message": "Blockout date removed"}

