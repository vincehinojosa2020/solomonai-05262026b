"""
Volunteer routes for Solomon AI — Leaderboard, Hours Tracker, Admin Management.
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from database import db, serialize_doc, DEFAULT_TENANT_ID
from auth import get_current_admin_user, get_current_member_user
import uuid
import random

router = APIRouter()

VOLUNTEER_BADGE_TIERS = [
    {"name": "Helping Hand", "icon": "hands-helping", "threshold": 5, "color": "#60A5FA"},
    {"name": "Faithful Servant", "icon": "heart", "threshold": 15, "color": "#A78BFA"},
    {"name": "Ministry Champion", "icon": "trophy", "threshold": 30, "color": "#FBBF24"},
    {"name": "Church Pillar", "icon": "landmark", "threshold": 50, "color": "#F97316"},
    {"name": "Kingdom Builder", "icon": "crown", "threshold": 100, "color": "#EF4444"},
]


def compute_volunteer_badge(signup_count: int) -> Dict[str, Any]:
    current_badge = None
    next_badge = VOLUNTEER_BADGE_TIERS[0]
    for tier in VOLUNTEER_BADGE_TIERS:
        if signup_count >= tier["threshold"]:
            current_badge = tier
        else:
            next_badge = tier
            break
    else:
        next_badge = None
    progress = 0.0
    if next_badge:
        floor = current_badge["threshold"] if current_badge else 0
        progress = round((signup_count - floor) / (next_badge["threshold"] - floor) * 100, 1)
    return {
        "current_badge": current_badge,
        "next_badge": next_badge,
        "progress_to_next": min(progress, 100.0),
        "signups_to_next": (next_badge["threshold"] - signup_count) if next_badge else 0,
    }


# === Pydantic Models ===

class VolunteerSignupRequest(BaseModel):
    opportunity_id: str

class VolunteerOpportunityCreate(BaseModel):
    title: str
    description: str = ""
    schedule: str = ""
    location: str = ""
    spots_available: int = 10
    ministry_area: str = "General"

class VolunteerOpportunityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    schedule: Optional[str] = None
    location: Optional[str] = None
    spots_available: Optional[int] = None
    ministry_area: Optional[str] = None
    is_active: Optional[bool] = None

class LogVolunteerHoursRequest(BaseModel):
    user_id: str
    opportunity_id: Optional[str] = None
    hours: float
    date: Optional[str] = None
    notes: Optional[str] = ""

class SelfLogHoursRequest(BaseModel):
    hours: float
    opportunity_id: Optional[str] = None
    date: Optional[str] = None
    notes: Optional[str] = ""


# === Portal: Member Volunteer Routes ===

@router.get("/portal/volunteer/opportunities")
async def get_portal_volunteer_opportunities(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    opportunities = await db.volunteer_opportunities.find(
        {"tenant_id": tenant_id, "is_active": True}, {"_id": 0}
    ).sort("title", 1).to_list(200)
    return {"opportunities": [serialize_doc(item) for item in opportunities]}


@router.post("/portal/volunteer/signup")
async def signup_portal_volunteer(request: Request, payload: VolunteerSignupRequest):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    opportunity = await db.volunteer_opportunities.find_one(
        {"tenant_id": tenant_id, "id": payload.opportunity_id, "is_active": True}, {"_id": 0}
    )
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    existing = await db.volunteer_signups.find_one(
        {"tenant_id": tenant_id, "opportunity_id": payload.opportunity_id, "user_id": user.get("user_id")}, {"_id": 0}
    )
    if existing:
        return {"message": "Already signed up", "signup": serialize_doc(existing)}
    signup = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "opportunity_id": payload.opportunity_id,
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "status": "signed_up",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.volunteer_signups.insert_one(signup)
    await db.volunteer_opportunities.update_one(
        {"tenant_id": tenant_id, "id": payload.opportunity_id}, {"$inc": {"spots_available": -1}}
    )
    return {"message": "Signed up successfully", "signup": serialize_doc(signup)}


@router.get("/portal/volunteer/leaderboard")
async def get_volunteer_leaderboard(request: Request, limit: int = 20):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {
            "_id": "$user_id",
            "user_name": {"$first": "$user_name"},
            "signup_count": {"$sum": 1},
            "total_hours": {"$sum": {"$ifNull": ["$hours", 0]}},
            "ministry_areas": {"$addToSet": "$ministry_area"},
            "last_signup": {"$max": "$created_at"},
        }},
        {"$sort": {"signup_count": -1, "total_hours": -1}},
        {"$limit": limit},
    ]
    results = await db.volunteer_signups.aggregate(pipeline).to_list(limit)
    leaderboard = []
    for rank, entry in enumerate(results, 1):
        badge_info = compute_volunteer_badge(entry["signup_count"])
        leaderboard.append({
            "rank": rank,
            "user_id": entry["_id"],
            "user_name": entry.get("user_name") or "Volunteer",
            "signup_count": entry["signup_count"],
            "total_hours": round(entry.get("total_hours", 0), 1),
            "ministry_areas": [m for m in (entry.get("ministry_areas") or []) if m],
            "last_signup": entry.get("last_signup"),
            "badge": badge_info["current_badge"],
        })
    return {"leaderboard": leaderboard, "badge_tiers": VOLUNTEER_BADGE_TIERS}


@router.get("/portal/volunteer/my-stats")
async def get_my_volunteer_stats(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    user_id = user["user_id"]
    signups = await db.volunteer_signups.find(
        {"tenant_id": tenant_id, "user_id": user_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    signup_count = len(signups)
    total_hours = sum(s.get("hours", 0) for s in signups)
    ministry_areas = list({s.get("ministry_area") for s in signups if s.get("ministry_area")})
    badge_info = compute_volunteer_badge(signup_count)
    higher_count = await db.volunteer_signups.aggregate([
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {"_id": "$user_id", "cnt": {"$sum": 1}}},
        {"$match": {"cnt": {"$gt": signup_count}}},
        {"$count": "total"},
    ]).to_list(1)
    rank = (higher_count[0]["total"] if higher_count else 0) + 1
    return {
        "user_id": user_id,
        "user_name": user.get("name", ""),
        "signup_count": signup_count,
        "total_hours": round(total_hours, 1),
        "ministry_areas": ministry_areas,
        "rank": rank,
        "last_signup": signups[0]["created_at"] if signups else None,
        "badge": badge_info["current_badge"],
        "next_badge": badge_info["next_badge"],
        "progress_to_next": badge_info["progress_to_next"],
        "signups_to_next": badge_info["signups_to_next"],
        "badge_tiers": VOLUNTEER_BADGE_TIERS,
    }


@router.post("/portal/volunteer/log-hours")
async def self_log_volunteer_hours(request: Request, payload: SelfLogHoursRequest):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    if payload.hours <= 0 or payload.hours > 24:
        raise HTTPException(status_code=400, detail="Hours must be between 0 and 24")
    log_date = payload.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ministry_area = ""
    if payload.opportunity_id:
        opp = await db.volunteer_opportunities.find_one(
            {"tenant_id": tenant_id, "id": payload.opportunity_id}, {"_id": 0, "ministry_area": 1}
        )
        ministry_area = (opp or {}).get("ministry_area", "")
    entry = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "user_id": user["user_id"],
        "user_name": user.get("name", ""),
        "opportunity_id": payload.opportunity_id,
        "ministry_area": ministry_area,
        "hours": payload.hours,
        "date": log_date,
        "notes": payload.notes,
        "status": "self_logged",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.volunteer_signups.insert_one(entry)
    return {"message": f"Logged {payload.hours}h", "entry": serialize_doc(entry)}


@router.get("/portal/volunteer/hours-summary")
async def get_volunteer_hours_summary(request: Request, period: str = "monthly"):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    user_id = user["user_id"]
    all_entries = await db.volunteer_signups.find(
        {"tenant_id": tenant_id, "user_id": user_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    now = datetime.now(timezone.utc)
    buckets = {}
    for entry in all_entries:
        ts = entry.get("date") or entry.get("created_at", "")
        try:
            dt = datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            continue
        if period == "weekly":
            key = f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
        else:
            key = dt.strftime("%Y-%m")
        if key not in buckets:
            buckets[key] = {"period": key, "hours": 0.0, "count": 0}
        buckets[key]["hours"] = round(buckets[key]["hours"] + entry.get("hours", 0), 1)
        buckets[key]["count"] += 1
    sorted_buckets = sorted(buckets.values(), key=lambda b: b["period"], reverse=True)
    if period == "weekly":
        current_key = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}"
    else:
        current_key = now.strftime("%Y-%m")
    current = buckets.get(current_key, {"period": current_key, "hours": 0.0, "count": 0})
    total_hours = round(sum(e.get("hours", 0) for e in all_entries), 1)
    return {
        "user_id": user_id,
        "period_type": period,
        "current_period": current,
        "breakdown": sorted_buckets[:12],
        "total_hours": total_hours,
        "total_sessions": len(all_entries),
    }


@router.get("/portal/volunteer/hours-log")
async def get_volunteer_hours_log(request: Request, limit: int = 50):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    entries = await db.volunteer_signups.find(
        {"tenant_id": tenant_id, "user_id": user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    return {"entries": [serialize_doc(e) for e in entries], "total": len(entries)}


# === Admin: Volunteer Management ===

@router.get("/admin/volunteer/opportunities")
async def get_admin_volunteer_opportunities(request: Request, limit: int = 200):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    opportunities = await db.volunteer_opportunities.find(
        {"tenant_id": tenant_id}, {"_id": 0}
    ).sort("title", 1).to_list(limit)
    return {"opportunities": [serialize_doc(o) for o in opportunities]}


@router.post("/admin/volunteer/opportunities")
async def create_admin_volunteer_opportunity(request: Request, payload: VolunteerOpportunityCreate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    opportunity = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "title": payload.title,
        "description": payload.description,
        "schedule": payload.schedule,
        "location": payload.location,
        "spots_available": payload.spots_available,
        "ministry_area": payload.ministry_area,
        "is_active": True,
        "created_by": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.volunteer_opportunities.insert_one(opportunity)
    return {"message": "Opportunity created", "opportunity": serialize_doc(opportunity)}


@router.put("/admin/volunteer/opportunities/{opportunity_id}")
async def update_admin_volunteer_opportunity(request: Request, opportunity_id: str, payload: VolunteerOpportunityUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.volunteer_opportunities.update_one(
        {"id": opportunity_id, "tenant_id": tenant_id}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {"message": "Opportunity updated"}


@router.delete("/admin/volunteer/opportunities/{opportunity_id}")
async def delete_admin_volunteer_opportunity(request: Request, opportunity_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    result = await db.volunteer_opportunities.delete_one({"id": opportunity_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {"message": "Opportunity deleted"}


@router.get("/admin/volunteer/signups")
async def get_admin_volunteer_signups(request: Request, opportunity_id: Optional[str] = None, limit: int = 200):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    if opportunity_id:
        query["opportunity_id"] = opportunity_id
    signups = await db.volunteer_signups.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return {"signups": [serialize_doc(s) for s in signups]}


@router.put("/admin/volunteer/signups/{signup_id}")
async def update_admin_volunteer_signup(request: Request, signup_id: str, payload: dict):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    allowed = ["status", "admin_notes"]
    update_data = {k: v for k, v in payload.items() if k in allowed}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.volunteer_signups.update_one(
        {"id": signup_id, "tenant_id": tenant_id}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Signup not found")
    return {"message": "Signup updated"}


@router.post("/admin/volunteer/log-hours")
async def admin_log_volunteer_hours(request: Request, payload: LogVolunteerHoursRequest):
    admin = await get_current_admin_user(request)
    tenant_id = admin.get("tenant_id") or DEFAULT_TENANT_ID
    target_user = await db.users.find_one({"user_id": payload.user_id}, {"_id": 0, "name": 1, "user_id": 1})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    log_entry = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "user_id": payload.user_id,
        "user_name": target_user.get("name", ""),
        "opportunity_id": payload.opportunity_id,
        "hours": payload.hours,
        "date": payload.date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "notes": payload.notes,
        "logged_by": admin.get("user_id"),
        "status": "logged",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.volunteer_signups.insert_one(log_entry)
    return {"message": f"Logged {payload.hours}h for {target_user.get('name', payload.user_id)}", "entry": serialize_doc(log_entry)}


# === Seed Data ===

async def seed_volunteer_leaderboard_data():
    tenant_id = DEFAULT_TENANT_ID
    member = await db.users.find_one({"email": "member@abundant.church"}, {"_id": 0})
    if not member:
        return
    user_id = member["user_id"]
    user_name = member.get("name", "Maria Garcia")
    existing = await db.volunteer_signups.count_documents({"tenant_id": tenant_id, "user_id": user_id})
    if existing >= 8:
        return
    opportunities = await db.volunteer_opportunities.find({"tenant_id": tenant_id, "is_active": True}, {"_id": 0}).to_list(10)
    ministry_map = {o["id"]: o.get("ministry_area", "General") for o in opportunities}
    now = datetime.now(timezone.utc)
    seed_signups = []
    for i in range(8):
        opp = opportunities[i % len(opportunities)] if opportunities else None
        seed_signups.append({
            "id": f"vol_seed_{user_id}_{i}",
            "tenant_id": tenant_id,
            "user_id": user_id,
            "user_name": user_name,
            "opportunity_id": opp["id"] if opp else f"opp_seed_{i}",
            "ministry_area": ministry_map.get(opp["id"], "General") if opp else "General",
            "hours": round(random.uniform(1.5, 4.0), 1),
            "status": "signed_up",
            "created_at": (now - timedelta(days=random.randint(1, 90))).isoformat(),
        })
    fake_volunteers = [
        ("vol_demo_sarah", "Sarah Johnson", 22),
        ("vol_demo_james", "James Williams", 17),
        ("vol_demo_emily", "Emily Davis", 12),
        ("vol_demo_michael", "Michael Brown", 35),
        ("vol_demo_rachel", "Rachel Martinez", 9),
    ]
    for fake_id, fake_name, count in fake_volunteers:
        existing_fake = await db.volunteer_signups.count_documents({"tenant_id": tenant_id, "user_id": fake_id})
        if existing_fake >= count:
            continue
        for j in range(count - existing_fake):
            opp = opportunities[j % len(opportunities)] if opportunities else None
            seed_signups.append({
                "id": f"vol_seed_{fake_id}_{j}",
                "tenant_id": tenant_id,
                "user_id": fake_id,
                "user_name": fake_name,
                "opportunity_id": opp["id"] if opp else f"opp_seed_{j}",
                "ministry_area": ministry_map.get(opp["id"], "General") if opp else "General",
                "hours": round(random.uniform(1.0, 3.5), 1),
                "status": "signed_up",
                "created_at": (now - timedelta(days=random.randint(1, 120))).isoformat(),
            })
    for s in seed_signups:
        await db.volunteer_signups.update_one({"id": s["id"]}, {"$set": s}, upsert=True)
