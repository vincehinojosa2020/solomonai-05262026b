"""
Geofence routes for Solomon AI — Location-based attendance check-in.
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from database import db, serialize_doc, DEFAULT_TENANT_ID
from auth import get_current_admin_user, get_current_member_user
import uuid
import math

router = APIRouter()


class GeofenceCheckinRequest(BaseModel):
    latitude: float
    longitude: float


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


@router.get("/admin/geofence/config")
async def get_geofence_config(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    config = await db.geofence_config.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not config:
        config = {
            "tenant_id": tenant_id,
            "zones": [{"id": "zone_main", "name": "Main Campus", "latitude": 31.7619, "longitude": -106.4850, "radius_meters": 200.0, "is_enabled": True}],
            "auto_checkin_enabled": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.geofence_config.insert_one({**config})
    return {"config": serialize_doc(config)}


@router.put("/admin/geofence/config")
async def update_geofence_config(request: Request, payload: dict):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    allowed = ["zones", "auto_checkin_enabled"]
    update_data = {k: v for k, v in payload.items() if k in allowed}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.geofence_config.update_one({"tenant_id": tenant_id}, {"$set": update_data}, upsert=True)
    updated = await db.geofence_config.find_one({"tenant_id": tenant_id}, {"_id": 0})
    return {"message": "Geofence config updated", "config": serialize_doc(updated)}


@router.post("/portal/attendance/geofence-checkin")
async def geofence_checkin(request: Request, payload: GeofenceCheckinRequest):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    config = await db.geofence_config.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not config or not config.get("auto_checkin_enabled"):
        raise HTTPException(status_code=400, detail="Geofence check-in is not enabled")

    matched_zone = None
    for zone in config.get("zones", []):
        if not zone.get("is_enabled"):
            continue
        dist = haversine(payload.latitude, payload.longitude, zone["latitude"], zone["longitude"])
        if dist <= zone.get("radius_meters", 200):
            matched_zone = zone
            break

    if not matched_zone:
        return {"checked_in": False, "message": "You are not within any church campus zone"}

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = await db.attendance_checkins.find_one(
        {"tenant_id": tenant_id, "user_id": user["user_id"], "date": today}, {"_id": 0}
    )
    if existing:
        return {"checked_in": True, "message": "Already checked in today", "zone": matched_zone["name"]}

    checkin = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "user_id": user["user_id"],
        "user_name": user.get("name", ""),
        "check_in_type": "geofence",
        "zone_name": matched_zone["name"],
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "date": today,
        "checked_in_at": datetime.now(timezone.utc).isoformat()
    }
    await db.attendance_checkins.insert_one(checkin)
    return {"checked_in": True, "message": f"Checked in at {matched_zone['name']}", "zone": matched_zone["name"]}
