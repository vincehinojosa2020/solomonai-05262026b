"""Solomon AI — Admin Settings, Branding, API Keys, Dashboard, War Room Routes"""
from fastapi import APIRouter, HTTPException, Request, Query
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import uuid
import json
import io
import logging

from core import (
    db, DEFAULT_TENANT_ID,
    get_current_admin_user, require_permission, require_tenant,
    audit_log,
    logger,
)
from core.helpers import (
    serialize_doc, generate_api_key, get_tenant_giving_metrics,
    AGENT_PERMISSIONS,
)
from core.seed import ensure_abundant_go_live_portal_content
from models.schemas import (
    AgentAPIKey, AgentAPIKeyCreate,
    Fund, Group, Service, Tenant,
)

router = APIRouter()

@router.get("/admin/dashboard/aggregate")
async def get_aggregate_dashboard(request: Request):
    """Return aggregate stats across all accessible campuses for multi-campus admins."""
    user = await get_current_admin_user(request)
    accessible = user.get("accessible_campuses") or []
    campus_ids = [c.get("id") for c in accessible if c.get("id")]

    if not campus_ids:
        campus_ids = [user.get("tenant_id") or DEFAULT_TENANT_ID]

    total_members = 0
    total_groups = 0
    total_kids_today = 0
    total_giving_mtd = 0
    campus_breakdown = []

    for cid in campus_ids:
        members = await db.users.count_documents({"tenant_id": cid, "role": "member"})
        groups = await db.groups.count_documents({"tenant_id": cid, "is_active": True})
        kids = await db.checkins.count_documents({"tenant_id": cid, "status": "checked_in"})

        cached = await db.dashboard_stats_cache.find_one({"tenant_id": cid}, {"_id": 0})
        mtd_giving = cached.get("mtd_giving", 0) if cached else 0

        tenant_doc = await db.tenants.find_one({"id": cid}, {"_id": 0, "name": 1})
        campus_name = tenant_doc.get("name", cid) if tenant_doc else cid

        total_members += members
        total_groups += groups
        total_kids_today += kids
        total_giving_mtd += mtd_giving

        campus_breakdown.append({
            "id": cid,
            "name": campus_name,
            "members": members,
            "groups": groups,
            "kids_checked_in": kids,
            "mtd_giving": mtd_giving,
        })

    return {
        "total_members": total_members,
        "total_groups": total_groups,
        "total_kids_today": total_kids_today,
        "total_giving_mtd": total_giving_mtd,
        "campuses": campus_breakdown,
        "campus_count": len(campus_ids),
    }

# ============== COMMUNICATIONS ENHANCED ==============


@router.get("/admin/attendance/today")
async def get_admin_attendance_today(request: Request, tenant_id: Optional[str] = None):
    """Admin summary of today's attendance across member and kids check-ins."""
    user = await get_current_admin_user(request)
    effective_tenant_id = tenant_id or user.get("tenant_id") or DEFAULT_TENANT_ID

    today = datetime.now(timezone.utc).date().isoformat()
    day_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    member_checkins = await db.member_checkins.find(
        {"tenant_id": effective_tenant_id, "service_date": today},
        {"_id": 0}
    ).to_list(5000)

    kids_checkins = await db.checkins.find(
        {
            "tenant_id": effective_tenant_id,
            "checked_in_at": {"$gte": day_start.isoformat()}
        },
        {"_id": 0}
    ).to_list(5000)

    return {
        "date": today,
        "tenant_id": effective_tenant_id,
        "member_checkins_total": len(member_checkins),
        "member_checkins_online": len([c for c in member_checkins if c.get("check_in_type") == "online"]),
        "member_checkins_in_person": len([c for c in member_checkins if c.get("check_in_type") != "online"]),
        "kids_checkins_total": len(kids_checkins),
        "kids_checked_in_now": len([c for c in kids_checkins if c.get("status") == "checked_in"])
    }


@router.get("/admin/qr/generate")
async def generate_admin_qr(
    request: Request,
    action: str = "attendance_checkin",
    expires_in_minutes: int = 60
):
    """Generate a QR payload and image URL for mobile scanning flows."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    expires_in_minutes = max(1, min(expires_in_minutes, 1440))
    now = datetime.now(timezone.utc)
    payload = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "action": action,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=expires_in_minutes)).isoformat()
    }

    qr_data = quote(json.dumps(payload))
    qr_url = f"https://quickchart.io/qr?size=300&text={qr_data}"

    return {
        "qr": {
            "image_url": qr_url,
            "payload": payload,
            "format": "quickchart"
        }
    }


@router.get("/admin/dashboard")
async def get_admin_dashboard(request: Request):
    """Tenant-scoped admin dashboard summary for web/mobile admin apps."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_abundant_go_live_portal_content()

    giving = await get_tenant_giving_metrics(tenant_id)
    total_members = await db.users.count_documents({"tenant_id": tenant_id, "role": "member"})
    active_groups = await db.groups.count_documents({"tenant_id": tenant_id, "is_active": True})
    active_members = await db.users.count_documents({"tenant_id": tenant_id, "role": "member", "is_active": True})

    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    month_start = datetime.now(timezone.utc).replace(day=1).isoformat()

    new_this_week = await db.users.count_documents(
        {
            "tenant_id": tenant_id,
            "role": "member",
            "created_at": {"$gte": week_start}
        }
    )

    today = datetime.now(timezone.utc).date()
    days_since_sunday = (today.weekday() - 6) % 7
    last_sunday = today - timedelta(days=days_since_sunday)
    last_sunday_attendance = await db.member_checkins.count_documents(
        {"tenant_id": tenant_id, "service_date": last_sunday.isoformat()}
    )

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    upcoming_events_count = await db.events.count_documents(
        {
            "tenant_id": tenant_id,
            "$or": [
                {"start_datetime": {"$gte": today_str}},
                {"event_date": {"$gte": today_str}}
            ]
        }
    )

    recent_activity_docs = await db.activity_log.find(
        {"tenant_id": tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)

    recurring_donors = giving["recurring_count"]
    cafe_orders_this_week = await db.cafe_orders.count_documents(
        {"tenant_id": tenant_id, "created_at": {"$gte": week_start}}
    )
    merch_sales_docs = await db.merch_orders.find(
        {"tenant_id": tenant_id, "created_at": {"$gte": week_start}},
        {"_id": 0, "total": 1}
    ).to_list(5000)
    merch_sales_this_week = round(sum(float(item.get("total", 0) or 0) for item in merch_sales_docs), 2)
    event_signups_this_month = await db.event_registrations.count_documents(
        {"tenant_id": tenant_id, "registered_at": {"$gte": month_start}}
    )
    small_groups_count = active_groups
    at_risk_members = await db.people.count_documents(
        {"tenant_id": tenant_id, "engagement_level": "at_risk"}
    )

    return {
        "active_members": active_members,
        "new_this_week": new_this_week,
        "total_members": total_members,
        "active_groups": active_groups,
        "mtd_giving": giving["mtd_total"],
        "ytd_giving": giving["ytd_total"],
        "recurring_count": giving["recurring_count"],
        "recurring_donors": recurring_donors,
        "cafe_orders_this_week": cafe_orders_this_week,
        "merch_sales_this_week": merch_sales_this_week,
        "event_signups_this_month": event_signups_this_month,
        "small_groups_count": small_groups_count,
        "at_risk_members": at_risk_members,
        "last_sunday_attendance": last_sunday_attendance,
        "upcoming_events_count": upcoming_events_count,
        "recent_activity": [serialize_doc(item) for item in recent_activity_docs]
    }


@router.get("/admin/war-room")
async def war_room_data(request: Request):
    """Real-time War Room data for Sunday Morning command center."""
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    total_members = await db.people.count_documents({"tenant_id": tenant_id})
    active_members = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "active"})

    kids_today = await db.kids_checkins.find({"tenant_id": tenant_id, "checked_in_at": {"$gte": today_start}}, {"_id": 0}).to_list(500)
    kids_checked_in = sum(1 for k in kids_today if not k.get("checked_out_at"))
    kids_total = len(kids_today)

    today_checkins = await db.member_checkins.count_documents({"tenant_id": tenant_id, "service_date": now.strftime("%Y-%m-%d")})

    donations_today_list = await db.donations.find({"tenant_id": tenant_id, "created_at": {"$gte": today_start}}, {"_id": 0, "amount": 1}).to_list(5000)
    given_today = sum(d.get("amount", 0) for d in donations_today_list)

    donations_mtd = await db.donations.find({"tenant_id": tenant_id, "created_at": {"$gte": month_start}}, {"_id": 0, "amount": 1}).to_list(5000)
    mtd_giving = sum(d.get("amount", 0) for d in donations_mtd)

    cafe_orders_today = await db.cafe_orders.count_documents({"tenant_id": tenant_id, "created_at": {"$gte": today_start}})

    volunteer_count = await db.volunteer_assignments.count_documents({"tenant_id": tenant_id})

    first_time_count = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "visitor", "created_at": {"$gte": today_start}})

    merch_sales = await db.merch_orders.count_documents({"tenant_id": tenant_id, "created_at": {"$gte": today_start}})
    merch_rev_docs = await db.merch_orders.find({"tenant_id": tenant_id, "created_at": {"$gte": today_start}}, {"_id": 0, "total": 1}).to_list(500)
    merch_revenue = sum(d.get("total", 0) for d in merch_rev_docs)

    cafe_rev_docs = await db.cafe_orders.find({"tenant_id": tenant_id, "created_at": {"$gte": today_start}}, {"_id": 0, "total": 1}).to_list(500)
    cafe_revenue = sum(d.get("total", 0) for d in cafe_rev_docs)

    recent = await db.audit_log.find({"tenant_id": tenant_id}, {"_id": 0}).sort("timestamp", -1).to_list(25)
    activity_feed = []
    for r in recent:
        activity_feed.append({
            "action": r.get("action", ""),
            "entity_type": r.get("entity_type", ""),
            "performed_by_name": r.get("performed_by_name", "System"),
            "timestamp": r.get("timestamp", ""),
            "details": r.get("new_values", {})
        })

    # Use realistic seed data when no live data exists (demo mode)
    use_seed = kids_checked_in == 0 and given_today == 0 and today_checkins == 0
    if use_seed:
        kids_checked_in = 47
        kids_total = 52
        today_checkins = 312
        given_today = 28450
        mtd_giving = mtd_giving if mtd_giving > 0 else 69668
        cafe_orders_today = 34
        cafe_revenue = 289
        volunteer_count = max(volunteer_count, 23)
        first_time_count = 12
        merch_sales = 8
        merch_revenue = 680

        seed_time = now.replace(hour=9, minute=0, second=0)
        seed_events = [
            {"action": "kid_checkin", "performed_by_name": "Sarah Miller", "details": {"child": "Emma Davis", "classroom": "PreK"}, "offset": 42},
            {"action": "donation_processed", "performed_by_name": "Anonymous", "details": {"amount": 100, "fund": "General Fund"}, "offset": 38},
            {"action": "cafe_order", "performed_by_name": "James Wilson", "details": {"items": "Latte + Cold Brew"}, "offset": 35},
            {"action": "visitor_registered", "performed_by_name": "Marcus Thompson", "details": {"note": "First-time visitor"}, "offset": 31},
            {"action": "merch_sale", "performed_by_name": "Rachel Kim", "details": {"item": "SO BE IT Hoodie", "amount": 45}, "offset": 28},
            {"action": "kid_checkin", "performed_by_name": "David Chen", "details": {"child": "Lily Chen", "classroom": "Elementary"}, "offset": 25},
            {"action": "donation_processed", "performed_by_name": "The Johnson Family", "details": {"amount": 500, "fund": "Building Fund"}, "offset": 22},
            {"action": "service_checkin", "performed_by_name": "Maria Rodriguez", "details": {"service": "9:00 AM Service"}, "offset": 19},
            {"action": "cafe_order", "performed_by_name": "Tom Patterson", "details": {"items": "Cappuccino"}, "offset": 16},
            {"action": "kid_checkin", "performed_by_name": "Jennifer Park", "details": {"child": "Noah Park", "classroom": "Nursery"}, "offset": 13},
            {"action": "donation_processed", "performed_by_name": "Robert & Lisa Adams", "details": {"amount": 250, "fund": "Missions"}, "offset": 10},
            {"action": "volunteer_checkin", "performed_by_name": "Carlos Mendez", "details": {"role": "Worship Team Lead"}, "offset": 8},
            {"action": "visitor_registered", "performed_by_name": "Ashley Brooks", "details": {"note": "Invited by small group"}, "offset": 5},
            {"action": "cafe_order", "performed_by_name": "Daniel Wright", "details": {"items": "Drip Coffee + Muffin"}, "offset": 3},
            {"action": "donation_processed", "performed_by_name": "Grace Fellowship Group", "details": {"amount": 1000, "fund": "General Fund"}, "offset": 1},
        ]
        activity_feed = []
        for se in seed_events:
            ts = (seed_time + timedelta(minutes=se["offset"])).isoformat()
            activity_feed.append({"action": se["action"], "performed_by_name": se["performed_by_name"], "timestamp": ts, "details": se["details"], "entity_type": ""})

    giving_goal = 250000
    kids_capacity = 60
    classrooms_active = 5 if use_seed else max(1, len(set(k.get("classroom", "") for k in kids_today if not k.get("checked_out_at"))))

    # Giving trend (last 4 Sundays + today)
    giving_trend = []
    for i in range(4, -1, -1):
        d = now - timedelta(weeks=i)
        label = "Today" if i == 0 else f"Week {5 - i}"
        if use_seed:
            amounts = [18200, 22400, 19800, 25600, 28450]
            giving_trend.append({"label": label, "amount": amounts[4 - i]})
        else:
            w_start = d.replace(hour=0, minute=0, second=0, microsecond=0)
            w_end = w_start + timedelta(days=1)
            w_docs = await db.donations.find({"tenant_id": tenant_id, "created_at": {"$gte": w_start.isoformat(), "$lt": w_end.isoformat()}}, {"_id": 0, "amount": 1}).to_list(5000)
            giving_trend.append({"label": label, "amount": sum(dd.get("amount", 0) for dd in w_docs)})

    return {
        "timestamp": now.isoformat(),
        "church_name": user.get("tenant_name", "Abundant Church"),
        "is_seed_data": use_seed,
        "counters": {
            "members_present": today_checkins,
            "total_members": total_members,
            "active_members": active_members,
            "kids_checked_in": kids_checked_in,
            "kids_total_today": kids_total,
            "kids_capacity": kids_capacity,
            "classrooms_active": classrooms_active,
            "today_checkins": today_checkins,
            "volunteers_on_duty": volunteer_count,
            "first_time_visitors": first_time_count,
            "given_today": round(given_today, 2),
            "mtd_giving": round(mtd_giving, 2),
            "giving_goal": giving_goal,
            "cafe_orders_today": cafe_orders_today,
            "cafe_revenue": round(cafe_revenue, 2),
            "merch_sales": merch_sales,
            "merch_revenue": round(merch_revenue, 2),
        },
        "activity_feed": activity_feed[:20],
        "giving_trend": giving_trend,
        "capacity": {
            "kids": {"current": kids_checked_in, "max": kids_capacity, "pct": round(kids_checked_in / max(kids_capacity, 1) * 100)},
            "cafe": {"queue": cafe_orders_today, "label": f"{cafe_orders_today} orders today"},
            "giving": {"current": round(mtd_giving, 2), "goal": giving_goal, "pct": round(mtd_giving / max(giving_goal, 1) * 100)},
        }
    }


# ============== PAYMENT ORCHESTRATION LAYER ==============

PAYMENT_PROCESSORS = {
    "solomon_pay": {"name": "Solomon Pay", "description": "Proprietary card, ACH, and digital wallet processing — built-in, no third-party account needed", "supported_methods": ["card", "ach", "apple_pay", "google_pay"]},
    "manual": {"name": "Cash & Check", "description": "Record offline gifts, cash collections, and check deposits manually", "supported_methods": ["cash", "check", "other"]},
}


@router.get("/admin/audit-log")
async def get_audit_log(
    request: Request,
    start_date: str = None,
    end_date: str = None,
    entity_type: str = None,
    user_id: str = None,
    action: str = None,
    page: int = 1,
    limit: int = 50
):
    """Get audit log entries with filtering."""
    user = await require_permission(request, "admin.dashboard")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    query = {"tenant_id": tenant_id}

    if start_date:
        query["timestamp"] = {"$gte": start_date}
    if end_date:
        query.setdefault("timestamp", {})["$lte"] = end_date + "T23:59:59"
    if entity_type:
        query["entity_type"] = entity_type
    if user_id:
        query["performed_by"] = user_id
    if action:
        query["action"] = action

    total = await db.audit_log.count_documents(query)
    skip = (page - 1) * limit
    entries = await db.audit_log.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "entries": entries,
        "total": total,
        "page": page,
        "pages": max(1, (total + limit - 1) // limit)
    }


# ============== ADMIN REPORT ALIASES + PDF EXPORT ==============


@router.get("/admin/settings/branding")
async def get_branding(request: Request):
    user = await require_permission(request, "admin.settings")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    branding = await db.tenant_branding.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not branding:
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "name": 1, "primary_color": 1})
        branding = {"tenant_id": tenant_id, "app_name": (tenant or {}).get("name", "My Church"), "primary_color": (tenant or {}).get("primary_color", "#3b82f6"), "logo_url": "", "tagline": "", "app_store_description": ""}
    return branding


@router.put("/admin/settings/branding")
async def update_branding(request: Request, payload: dict):
    user = await require_permission(request, "admin.settings")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    updates = {k: v for k, v in payload.items() if k in ["app_name", "primary_color", "logo_url", "tagline", "app_store_description"]}
    updates["tenant_id"] = tenant_id
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.tenant_branding.update_one({"tenant_id": tenant_id}, {"$set": updates}, upsert=True)
    return {**updates, "success": True}


# --- SEARCH ROUTE ---
@router.get("/admin/api-keys")
async def list_api_keys(request: Request):
    """List all API keys for the tenant"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    keys = await db.agent_api_keys.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "key_hash": 0}  # Don't expose the hash
    ).sort("created_at", -1).to_list(100)
    
    return {
        "api_keys": [serialize_doc(k) for k in keys],
        "available_permissions": AGENT_PERMISSIONS
    }


@router.post("/admin/api-keys")
async def create_api_key(request: Request, payload: AgentAPIKeyCreate):
    """Generate a new API key for external agent access"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    # Validate permissions
    for perm in payload.permissions:
        if perm not in AGENT_PERMISSIONS and not perm.endswith(":*"):
            raise HTTPException(status_code=400, detail=f"Invalid permission: {perm}")
    
    # Generate the key
    full_key, key_hash, key_prefix = generate_api_key()
    
    # Calculate expiration
    expires_at = None
    if payload.expires_in_days:
        expires_at = (datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)).isoformat()
    
    key_doc = AgentAPIKey(
        tenant_id=tenant_id,
        name=payload.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        permissions=payload.permissions,
        rate_limit=payload.rate_limit,
        created_by=user.get("user_id", "unknown"),
        expires_at=expires_at
    )
    
    await db.agent_api_keys.insert_one(key_doc.model_dump())
    
    # Return the full key ONLY on creation (never stored or shown again)
    return {
        "api_key": full_key,  # Show only once!
        "key_id": key_doc.id,
        "name": key_doc.name,
        "key_prefix": key_prefix,
        "permissions": key_doc.permissions,
        "rate_limit": key_doc.rate_limit,
        "expires_at": expires_at,
        "warning": "Save this key now! It will not be shown again."
    }


@router.delete("/admin/api-keys/{key_id}")
async def revoke_api_key(request: Request, key_id: str):
    """Revoke an API key"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    result = await db.agent_api_keys.update_one(
        {"id": key_id, "tenant_id": tenant_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"message": "API key revoked", "key_id": key_id}


@router.patch("/admin/api-keys/{key_id}")
async def update_api_key(request: Request, key_id: str, payload: dict):
    """Update API key settings (permissions, rate limit, active status)"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    update_data = {}
    if "permissions" in payload:
        update_data["permissions"] = payload["permissions"]
    if "rate_limit" in payload:
        update_data["rate_limit"] = payload["rate_limit"]
    if "is_active" in payload:
        update_data["is_active"] = payload["is_active"]
    if "name" in payload:
        update_data["name"] = payload["name"]
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    result = await db.agent_api_keys.update_one(
        {"id": key_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key = await db.agent_api_keys.find_one({"id": key_id}, {"_id": 0, "key_hash": 0})
    return {"api_key": serialize_doc(key)}

# --- Agent API v1 Endpoints (External Access) ---



# ============== CUSTOM FIELD DEFINITIONS ==============

FIELD_TYPES = ["text", "number", "select", "multiselect", "date", "boolean", "textarea"]
FIELD_CATEGORIES = ["personal", "church", "medical", "other"]


@router.get("/admin/custom-field-definitions")
async def list_custom_field_definitions(request: Request):
    """List all custom field definitions for this tenant."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    fields = await db.custom_field_definitions.find(
        {"tenant_id": tenant_id}, {"_id": 0}
    ).sort("sort_order", 1).to_list(200)
    return {"fields": fields}


@router.post("/admin/custom-field-definitions")
async def create_custom_field_definition(request: Request):
    """Create a new custom field definition."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()

    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Field name is required")

    field_type = body.get("field_type", "text")
    if field_type not in FIELD_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid field type. Use: {', '.join(FIELD_TYPES)}")

    # Generate key from name
    field_key = name.lower().replace(" ", "_").replace("-", "_")
    field_key = "".join(c for c in field_key if c.isalnum() or c == "_")

    # Check for duplicate key
    existing = await db.custom_field_definitions.find_one(
        {"tenant_id": tenant_id, "field_key": field_key}, {"_id": 0}
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Field '{name}' already exists")

    # Get max sort order
    last = await db.custom_field_definitions.find(
        {"tenant_id": tenant_id}, {"_id": 0, "sort_order": 1}
    ).sort("sort_order", -1).limit(1).to_list(1)
    next_order = (last[0]["sort_order"] + 1) if last else 0

    now_iso = datetime.now(timezone.utc).isoformat()
    field_def = {
        "id": f"cf_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "name": name,
        "field_key": field_key,
        "field_type": field_type,
        "options": body.get("options", []),
        "required": body.get("required", False),
        "category": body.get("category", "other") if body.get("category") in FIELD_CATEGORIES else "other",
        "sort_order": next_order,
        "is_active": True,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    await db.custom_field_definitions.insert_one(field_def)
    return {k: v for k, v in field_def.items() if k != "_id"}


@router.put("/admin/custom-field-definitions/reorder")
async def reorder_custom_fields(request: Request):
    """Reorder custom field definitions. Expects {field_ids: [ordered list]}."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    field_ids = body.get("field_ids", [])

    for i, fid in enumerate(field_ids):
        await db.custom_field_definitions.update_one(
            {"id": fid, "tenant_id": tenant_id},
            {"$set": {"sort_order": i, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    return {"message": "Fields reordered", "count": len(field_ids)}


@router.put("/admin/custom-field-definitions/{field_id}")
async def update_custom_field_definition(request: Request, field_id: str):
    """Update a custom field definition."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()

    existing = await db.custom_field_definitions.find_one(
        {"id": field_id, "tenant_id": tenant_id}, {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Field definition not found")

    update = {}
    if "name" in body and body["name"].strip():
        update["name"] = body["name"].strip()
    if "field_type" in body and body["field_type"] in FIELD_TYPES:
        update["field_type"] = body["field_type"]
    if "options" in body:
        update["options"] = body["options"]
    if "required" in body:
        update["required"] = bool(body["required"])
    if "category" in body and body["category"] in FIELD_CATEGORIES:
        update["category"] = body["category"]
    if "is_active" in body:
        update["is_active"] = bool(body["is_active"])
    if "sort_order" in body:
        update["sort_order"] = int(body["sort_order"])

    update["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.custom_field_definitions.update_one(
        {"id": field_id, "tenant_id": tenant_id}, {"$set": update}
    )
    updated = await db.custom_field_definitions.find_one({"id": field_id}, {"_id": 0})
    return updated


@router.delete("/admin/custom-field-definitions/{field_id}")
async def delete_custom_field_definition(request: Request, field_id: str):
    """Delete a custom field definition."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    result = await db.custom_field_definitions.delete_one(
        {"id": field_id, "tenant_id": tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Field definition not found")
    return {"message": "Custom field deleted"}
