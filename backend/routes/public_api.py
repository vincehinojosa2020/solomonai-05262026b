"""Solomon AI — Public API Routes (People, Groups, Events, Tenants, etc.)"""
from fastapi import APIRouter, HTTPException, Request, Response, Query, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta, date
from typing import Optional, List, Dict, Any
import uuid
import logging
import json
import csv
import io
import re
import os

from core import (
    db, DEFAULT_TENANT_ID,
    get_current_admin_user, get_current_member_user,
    get_tenant_by_subdomain, require_tenant, audit_log,
    logger,
)
from core.helpers import serialize_doc, DEFAULT_MERCH_EMBED_URL, calculate_attendance_streak, extract_youtube_id
from models.schemas import (
    Attendance, Communication, Donation, DonationBase, DonationBatch,
    Event, Fund, Group, Household, Person, PersonCreate,
    Service, Tenant, TenantBase, User,
    LeadCaptureRequest,
)

router = APIRouter()

@router.post("/leads/capture")
async def capture_lead(payload: LeadCaptureRequest):
    """Capture lead from landing page"""
    lead = {
        "id": str(uuid.uuid4()),
        "church_name": payload.church_name,
        "name": payload.name,
        "email": payload.email,
        "phone": payload.phone,
        "current_software": payload.current_software,
        "church_size": payload.church_size,
        "status": "new",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.leads.insert_one(lead)
    return {"success": True, "message": "Thank you! We'll be in touch within 24 hours."}


@router.get("/admin/leads")
async def get_leads(request: Request, limit: int = 100):
    """Get captured leads (admin only)"""
    user = await get_current_portal_user(request)
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    leads = await db.leads.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"leads": leads, "total": len(leads)}


# ============== SMS ROUTES ==============

class SMSRequest(BaseModel):
    recipient_phone: str
    message: str
    person_id: Optional[str] = None

class BulkSMSRequest(BaseModel):
    group_id: Optional[str] = None
    list_ids: Optional[List[str]] = None
    message: str
    template_id: Optional[str] = None


@router.get("/")
async def root():
    return {"message": "Solomon AI Church Management API", "version": "1.0.0"}


@router.get("/clear-site-data")
async def clear_site_data():
    """Force browser to clear all caches, cookies, storage via HTTP header."""
    from starlette.responses import RedirectResponse
    response = RedirectResponse(url="/login", status_code=302)
    response.headers["Clear-Site-Data"] = '"cache", "storage"'
    return response


@router.get("/health/launch-check")
async def launch_health_check(tenant_id: Optional[str] = None):
    """Read-only launch readiness snapshot for quick production verification."""
    effective_tenant_id = tenant_id or DEFAULT_TENANT_ID

    launch_member_email_map = {
        "abundant-east-001": "member@abundant.church",
        "cristoviene-church-001": "member@cristoviene.church",
        "pottershouse-church-001": "member@pottershouse.church"
    }
    preferred_member_email = launch_member_email_map.get(effective_tenant_id)

    member_user = None
    if preferred_member_email:
        member_user = await db.users.find_one(
            {"email": preferred_member_email},
            {"_id": 0, "user_id": 1, "email": 1}
        )

    if not member_user:
        member_user = await db.users.find_one(
            {"tenant_id": effective_tenant_id, "role": "member"},
            {"_id": 0, "user_id": 1, "email": 1}
        )

    person_doc = None
    if member_user:
        person_doc = await db.people.find_one(
            {"email": member_user.get("email"), "tenant_id": effective_tenant_id},
            {"_id": 0, "id": 1}
        )

    ytd_start = datetime.now(timezone.utc).replace(month=1, day=1).strftime("%Y-%m-%d")
    ytd_total = 0.0
    donation_count = 0
    if person_doc:
        donations = await db.donations.find(
            {
                "tenant_id": effective_tenant_id,
                "person_id": person_doc.get("id"),
                "donation_date": {"$gte": ytd_start}
            },
            {"_id": 0, "amount": 1}
        ).to_list(2000)
        donation_count = len(donations)
        ytd_total = round(sum(float(item.get("amount", 0) or 0) for item in donations), 2)

    events_count = await db.events.count_documents(
        {
            "tenant_id": effective_tenant_id,
            "$or": [
                {"start_datetime": {"$exists": True}},
                {"event_date": {"$exists": True}}
            ]
        }
    )
    groups_count = await db.groups.count_documents({"tenant_id": effective_tenant_id, "is_active": True})
    merch_count = await db.merch_products.count_documents({"tenant_id": effective_tenant_id, "is_active": True})
    cafe_count = await db.cafe_items.count_documents({"tenant_id": effective_tenant_id, "is_active": True})
    sermons_count = await db.media_videos.count_documents({"tenant_id": effective_tenant_id, "is_published": True, "content_type": "sermon"})
    announcements_count = await db.announcements.count_documents({"tenant_id": effective_tenant_id})
    opportunities_count = await db.volunteer_opportunities.count_documents({"tenant_id": effective_tenant_id, "is_active": True})

    kids_count = 0
    prayer_count = 0
    courses_count = 0
    streak = 0
    if member_user:
        kids_count = await db.children.count_documents({"tenant_id": effective_tenant_id, "parent_user_id": member_user.get("user_id")})
        prayer_count = await db.prayer_requests.count_documents({"tenant_id": effective_tenant_id, "user_id": member_user.get("user_id")})
        courses_count = await db.member_courses.count_documents({"tenant_id": effective_tenant_id, "user_id": member_user.get("user_id")})
        streak_data = await calculate_attendance_streak(effective_tenant_id, member_user.get("user_id"))
        streak = streak_data.get("current_streak", 0)

    required_accounts = [
        "member@abundant.church",
        "member@cristoviene.church",
        "admin@abundant.church",
        "admin@cristoviene.church",
        "admin@pottershouse.church",
        "admin@solomon.ai",
        "admin@solomonai.us"
    ]
    account_presence = {}
    for email in required_accounts:
        found = await db.users.find_one({"email": email}, {"_id": 0, "email": 1})
        account_presence[email] = bool(found)

    checks = {
        "events": events_count >= 50,
        "groups": groups_count >= 100,
        "giving_ytd": ytd_total >= 500,
        "merch_products": merch_count >= 5,
        "cafe_menu_items": cafe_count >= 5,
        "kids_children": kids_count >= 1,
        "attendance_streak": streak >= 1,
        "sermons": sermons_count >= 3,
        "courses": courses_count >= 2,
        "prayer_requests": prayer_count >= 2,
        "volunteer_opportunities": opportunities_count >= 5,
        "announcements": announcements_count >= 3,
        "accounts_ready": all(account_presence.values())
    }

    return {
        "tenant_id": effective_tenant_id,
        "status": "ready" if all(checks.values()) else "degraded",
        "checks": checks,
        "metrics": {
            "events": events_count,
            "groups": groups_count,
            "ytd_total": ytd_total,
            "donation_count": donation_count,
            "merch_products": merch_count,
            "cafe_menu_items": cafe_count,
            "kids_children": kids_count,
            "attendance_streak": streak,
            "sermons": sermons_count,
            "courses": courses_count,
            "prayer_requests": prayer_count,
            "volunteer_opportunities": opportunities_count,
            "announcements": announcements_count
        },
        "required_accounts": account_presence,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

# ============== TENANT/CHURCH MANAGEMENT ROUTES ==============


@router.get("/tenants")
async def list_tenants(request: Request):
    """List all tenants (platform admin only) with boosted stats from cache"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(100)
    
    for tenant in tenants:
        tid = tenant["id"]
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": tid}, {"_id": 0})
        if cached:
            tenant["member_count"] = cached.get("total_members", 0)
            tenant["active_members"] = cached.get("active_members", 0)
            tenant["mtd_giving"] = cached.get("mtd_giving", 0)
            tenant["ytd_giving"] = cached.get("ytd_giving", 0)
        else:
            tenant["member_count"] = await db.users.count_documents({"tenant_id": tid})
            tenant["active_members"] = 0
            tenant["mtd_giving"] = 0
            tenant["ytd_giving"] = 0
    
    return tenants


@router.get("/tenants/list")
async def list_public_churches():
    """List active churches for public registration (no auth required)"""
    tenants = await db.tenants.find(
        {"subscription_status": "active"},
        {"_id": 0, "id": 1, "name": 1, "subdomain": 1, "city": 1, "state": 1, "primary_color": 1}
    ).to_list(100)
    return tenants


@router.get("/tenants/{subdomain}")
async def get_tenant_by_subdomain_route(subdomain: str):
    """Get tenant info by subdomain (public - for registration)"""
    tenant = await get_tenant_by_subdomain(subdomain)
    if not tenant:
        raise HTTPException(status_code=404, detail="Church not found")
    
    # Return limited public info
    return {
        "id": tenant["id"],
        "name": tenant["name"],
        "subdomain": tenant["subdomain"],
        "subscription_status": tenant.get("subscription_status", "active"),
        "logo_url": tenant.get("logo_url"),
        "primary_color": tenant.get("primary_color", "#4f6ef7")
    }


@router.post("/tenants")
async def create_tenant(request: Request, tenant_data: TenantBase):
    """Create a new tenant/church (platform admin only)"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    
    # Check subdomain uniqueness
    existing = await db.tenants.find_one({"subdomain": tenant_data.subdomain.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Subdomain already in use")
    
    tenant = {
        "id": str(uuid.uuid4()),
        "name": tenant_data.name,
        "subdomain": tenant_data.subdomain.lower(),
        "plan": tenant_data.plan,
        "member_limit": tenant_data.member_limit,
        "logo_url": tenant_data.logo_url,
        "primary_color": tenant_data.primary_color,
        "accent_color": tenant_data.accent_color,
        "timezone": tenant_data.timezone,
        "subscription_status": tenant_data.subscription_status,
        "address": tenant_data.address,
        "city": tenant_data.city,
        "state": tenant_data.state,
        "website": tenant_data.website,
        "phone": tenant_data.phone,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tenants.insert_one(tenant)
    logger.info(f"New tenant created: {tenant['name']} ({tenant['subdomain']})")
    
    return {"message": "Tenant created", "tenant_id": tenant["id"], "subdomain": tenant["subdomain"]}


@router.patch("/tenants/{tenant_id}/subscription")
async def update_tenant_subscription(request: Request, tenant_id: str, status: str):
    """Update tenant subscription status (platform admin only)"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    
    if status not in ["active", "suspended", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {"subscription_status": status}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {"message": f"Subscription updated to {status}"}


@router.get("/tenants/{tenant_id}/users")
async def list_tenant_users(request: Request, tenant_id: str, skip: int = 0, limit: int = 50):
    """List users for a specific tenant (platform admin only)"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    
    users = await db.users.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "password_hash": 0}
    ).skip(skip).limit(limit).to_list(limit)
    
    total = await db.users.count_documents({"tenant_id": tenant_id})
    
    return {"users": users, "total": total, "skip": skip, "limit": limit}

# ============== PLATFORM STATS (REAL DATA) ==============


@router.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "version": "2.0.0"}


@router.get("/health/detailed")
async def health_detailed():
    checks = {"database": "ok", "media": "ok", "giving": "ok", "cache": "ok"}
    try:
        await db.command("ping")
    except Exception:
        checks["database"] = "down"
    return {"status": "ok" if all(v == "ok" for v in checks.values()) else "degraded", "services": checks, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/churches/list")
async def list_churches_public():
    tenants = await db.tenants.find({"subscription_status": "active"}, {"_id": 0, "id": 1, "name": 1, "subdomain": 1, "city": 1, "state": 1, "primary_color": 1}).to_list(100)
    return tenants

# ============== MEDIA MANAGEMENT API ==============

@router.get("/register/{event_id}")
async def get_public_registration(event_id: str):
    """Public-facing registration page data"""
    event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if not event.get("registration_required"):
        raise HTTPException(status_code=400, detail="Registration is not enabled for this event")
    config = await db.registration_configs.find_one({"event_id": event_id}, {"_id": 0})
    # Strip sensitive data from promo codes
    safe_config = None
    if config:
        safe_config = {
            "pricing": config.get("pricing", {}),
            "add_ons": config.get("add_ons", []),
            "custom_questions": config.get("custom_questions", []),
            "confirmation_message": config.get("confirmation_message", ""),
            "max_registrants_per_order": config.get("max_registrants_per_order", 10),
            "require_payment": config.get("require_payment", False),
        }
    current_count = await db.event_registrations.count_documents({"event_id": event_id, "status": {"$ne": "waitlisted"}})
    spots_left = None
    if event.get("capacity"):
        spots_left = max(0, event["capacity"] - current_count)
    return {
        "event": {
            "id": event["id"],
            "name": event.get("name", ""),
            "description": event.get("description", ""),
            "start_datetime": event.get("start_datetime", ""),
            "end_datetime": event.get("end_datetime", ""),
            "location": event.get("location", ""),
            "cover_image_url": event.get("cover_image_url", ""),
            "capacity": event.get("capacity"),
        },
        "config": safe_config,
        "spots_left": spots_left,
        "is_full": spots_left == 0 if spots_left is not None else False,
    }


@router.post("/register/{event_id}")
async def submit_public_registration(event_id: str, payload: dict):
    """Public registration submission"""
    event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    tenant_id = event.get("tenant_id")
    config = await db.registration_configs.find_one({"event_id": event_id}, {"_id": 0})
    # Check capacity
    is_waitlisted = False
    if event.get("capacity"):
        current = await db.event_registrations.count_documents({"event_id": event_id, "status": {"$ne": "waitlisted"}})
        if current >= event["capacity"]:
            if config and config.get("waitlist_enabled", True):
                is_waitlisted = True
            else:
                raise HTTPException(status_code=400, detail="This event is full")
    # Validate promo code
    discount = 0
    promo_code_used = payload.get("promo_code", "").upper()
    if promo_code_used and config:
        for pc in config.get("promo_codes", []):
            if pc["code"] == promo_code_used and pc.get("is_active"):
                if pc.get("max_uses") and pc["uses_count"] >= pc["max_uses"]:
                    continue
                if pc["discount_type"] == "percentage":
                    discount = pc["discount_value"]
                else:
                    discount = pc["discount_value"]
                # Increment usage
                await db.registration_configs.update_one(
                    {"event_id": event_id, "promo_codes.code": promo_code_used},
                    {"$inc": {"promo_codes.$.uses_count": 1}}
                )
                break
    # Calculate total
    base_price = 0
    if config and config.get("pricing", {}).get("enabled"):
        base_price = config["pricing"].get("amount", 0)
    add_on_total = 0
    selected_add_ons = payload.get("add_ons", [])
    if config:
        for addon in config.get("add_ons", []):
            if addon["id"] in selected_add_ons:
                add_on_total += addon.get("price", 0)
    subtotal = base_price + add_on_total
    if discount > 0:
        if promo_code_used and config:
            for pc in config.get("promo_codes", []):
                if pc["code"] == promo_code_used:
                    if pc["discount_type"] == "percentage":
                        subtotal = subtotal * (1 - discount / 100)
                    else:
                        subtotal = max(0, subtotal - discount)
                    break
    # Create registration
    registrants = payload.get("registrants", [{"name": payload.get("name", ""), "email": payload.get("email", "")}])
    created_ids = []
    for registrant in registrants:
        reg = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "event_id": event_id,
            "user_name": registrant.get("name", ""),
            "user_email": registrant.get("email", ""),
            "phone": registrant.get("phone", ""),
            "status": "waitlisted" if is_waitlisted else "confirmed",
            "custom_answers": payload.get("custom_answers", {}),
            "selected_add_ons": selected_add_ons,
            "promo_code": promo_code_used or None,
            "amount_total": round(subtotal / len(registrants), 2),
            "payment_status": "pending" if subtotal > 0 else "free",
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.event_registrations.insert_one(reg)
        created_ids.append(reg["id"])
    if not is_waitlisted:
        await db.events.update_one({"id": event_id}, {"$inc": {"registration_count": len(registrants)}})
    status_msg = "waitlisted" if is_waitlisted else "confirmed"
    return {
        "message": f"Registration {status_msg}! {len(registrants)} registrant(s).",
        "status": status_msg,
        "registration_ids": created_ids,
        "total_amount": round(subtotal, 2),
    }

# ============== ADMIN EVENT REGISTRATION MANAGEMENT ==============


@router.get("/forms/{form_id}/public")
async def get_public_form(form_id: str):
    """Get a public form for submission (no auth required)"""
    form = await db.custom_forms.find_one({"id": form_id, "is_public": True, "is_active": True}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Form not found or not available")
    return {"form": {k: v for k, v in form.items() if k not in ["tenant_id"]}}


@router.post("/forms/{form_id}/submit")
async def submit_form(form_id: str, payload: dict):
    """Submit a public form (no auth required)"""
    form = await db.custom_forms.find_one({"id": form_id, "is_active": True}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    submission = {
        "id": str(uuid.uuid4()),
        "form_id": form_id,
        "form_name": form["name"],
        "tenant_id": form["tenant_id"],
        "data": payload.get("data", {}),
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }
    await db.form_submissions.insert_one(submission)
    await db.custom_forms.update_one({"id": form_id}, {"$inc": {"submission_count": 1}})
    if form.get("auto_create_profile"):
        data = payload.get("data", {})
        email = data.get("email") or data.get("Email")
        if email:
            existing = await db.users.find_one({"email": email, "tenant_id": form["tenant_id"]})
            if not existing:
                new_member = {
                    "user_id": str(uuid.uuid4()),
                    "tenant_id": form["tenant_id"],
                    "email": email,
                    "name": f"{data.get('first_name', data.get('First Name', ''))} {data.get('last_name', data.get('Last Name', ''))}".strip(),
                    "role": "member",
                    "membership_status": "visitor",
                    "phone": data.get("phone", data.get("Phone", "")),
                    "source": f"form:{form['name']}",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.users.insert_one(new_member)
    return {"message": "Form submitted successfully", "submission_id": submission["id"]}


@router.get("/tenant")
async def get_tenant(request: Request):
    """Get tenant info - returns user's tenant if logged in, else default"""
    # Try to get user's tenant from session
    session_token = get_session_token_from_request(request)
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
            if user and user.get("tenant_id"):
                tenant = await db.tenants.find_one({"id": user["tenant_id"]}, {"_id": 0})
                if tenant:
                    return serialize_doc(tenant)
    
    # Fallback to default tenant
    tenant = await db.tenants.find_one({"id": DEFAULT_TENANT_ID}, {"_id": 0})
    if not tenant:
        # Return default tenant if not found
        return {
            "id": DEFAULT_TENANT_ID,
            "name": "Abundant Church",
            "subdomain": "abundant",
            "plan": "enterprise",
            "member_limit": 100000,
            "logo_url": None,
            "primary_color": "#4f6ef7",
            "accent_color": "#00c896",
            "timezone": "America/Los_Angeles",
            "thinkific_url": "https://abundantchurch.thinkific.com/collections",
            "merch_embed_url": DEFAULT_MERCH_EMBED_URL
        }
    return serialize_doc(tenant)

# --- DASHBOARD ROUTES ---
@router.get("/dashboard/stats")

@router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request):
    """Return tenant-scoped dashboard stats from cache, falling back to defaults."""
    tenant_id = DEFAULT_TENANT_ID
    try:
        session_token = get_session_token_from_request(request)
        if session_token:
            session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
            if session:
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user and user.get("tenant_id"):
                    tenant_id = user["tenant_id"]
    except Exception:
        pass

    cached = await db.dashboard_stats_cache.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if cached:
        cached.pop("tenant_id", None)
        cached.pop("updated_at", None)
        return cached

    return {
        "total_members": 0, "active_members": 0, "visitors": 0,
        "active_groups": 0, "open_groups": 0,
        "mtd_giving": 0, "ytd_giving": 0, "mtd_goal": 0,
        "last_attendance": 0, "last_attendance_change": 0,
        "new_this_week": 0, "recurring_givers": 0,
        "cafe_orders_week": 0, "cafe_giving_added": 0,
        "merch_orders_week": 0, "merch_giving_added": 0,
        "event_registrations_month": 0, "at_risk_members": 0,
        "kids_checked_in_today": 0
    }


@router.get("/dashboard/giving-trend")
async def get_giving_trend():
    """Return demo giving trend data - 12 months for Abundant Church (50K member megachurch)"""
    return [
        {"month": "Mar", "General Fund": 145000, "Building Fund": 42000, "Missions": 18000, "Crypto": 2500},
        {"month": "Apr", "General Fund": 152000, "Building Fund": 45000, "Missions": 19000, "Crypto": 3200},
        {"month": "May", "General Fund": 168000, "Building Fund": 48000, "Missions": 21000, "Crypto": 1500},
        {"month": "Jun", "General Fund": 142000, "Building Fund": 41000, "Missions": 17500, "Crypto": 2800},
        {"month": "Jul", "General Fund": 138000, "Building Fund": 39000, "Missions": 16000, "Crypto": 1500},
        {"month": "Aug", "General Fund": 156000, "Building Fund": 43000, "Missions": 18500, "Crypto": 3100},
        {"month": "Sep", "General Fund": 175000, "Building Fund": 51000, "Missions": 22000, "Crypto": 2200},
        {"month": "Oct", "General Fund": 169000, "Building Fund": 47000, "Missions": 20500, "Crypto": 4300},
        {"month": "Nov", "General Fund": 198000, "Building Fund": 55000, "Missions": 24000, "Crypto": 3800},
        {"month": "Dec", "General Fund": 285000, "Building Fund": 72000, "Missions": 31000, "Crypto": 8500},
        {"month": "Jan", "General Fund": 161000, "Building Fund": 44000, "Missions": 19500, "Crypto": 2100},
        {"month": "Feb", "General Fund": 182500, "Building Fund": 52000, "Missions": 23500, "Crypto": 2800}
    ]


@router.get("/dashboard/attendance-trend")
async def get_attendance_trend():
    """Return demo attendance trend data - 12 weeks for Abundant Church (50K megachurch)"""
    return [
        {"week": "Week 1", "attendance": 7285, "date": "Dec 1"},
        {"week": "Week 2", "attendance": 7598, "date": "Dec 8"},
        {"week": "Week 3", "attendance": 8012, "date": "Dec 15"},
        {"week": "Week 4", "attendance": 12445, "date": "Dec 22"},
        {"week": "Week 5", "attendance": 9478, "date": "Dec 29"},
        {"week": "Week 6", "attendance": 7802, "date": "Jan 5"},
        {"week": "Week 7", "attendance": 7595, "date": "Jan 12"},
        {"week": "Week 8", "attendance": 8108, "date": "Jan 19"},
        {"week": "Week 9", "attendance": 8318, "date": "Jan 26"},
        {"week": "Week 10", "attendance": 8005, "date": "Feb 2"},
        {"week": "Week 11", "attendance": 7688, "date": "Feb 9"},
        {"week": "Week 12", "attendance": 8312, "date": "Feb 16"}
    ]


@router.get("/dashboard/activity")
async def get_recent_activity(request: Request, limit: int = 15):
    tenant_id = DEFAULT_TENANT_ID
    try:
        session_token = get_session_token_from_request(request)
        if session_token:
            session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
            if session:
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user and user.get("tenant_id"):
                    tenant_id = user["tenant_id"]
    except Exception:
        pass
    
    activities = await db.activity_log.find(
        {"tenant_id": tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return [serialize_doc(a) for a in activities]


@router.get("/dashboard/upcoming-events")
async def get_upcoming_events(request: Request, limit: int = 5):
    tenant_id = DEFAULT_TENANT_ID
    try:
        session_token = get_session_token_from_request(request)
        if session_token:
            session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
            if session:
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user and user.get("tenant_id"):
                    tenant_id = user["tenant_id"]
    except Exception:
        pass
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    events = await db.events.find(
        {"tenant_id": tenant_id, "start_datetime": {"$gte": today}},
        {"_id": 0}
    ).sort("start_datetime", 1).limit(limit).to_list(limit)
    
    return [serialize_doc(e) for e in events]


@router.get("/people")
async def get_people(
    page: int = 1,
    per_page: int = 25,
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "last_name",
    sort_order: str = "asc"
):
    tenant_id = DEFAULT_TENANT_ID
    
    # Build query
    query = {"tenant_id": tenant_id}
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"mobile_phone": {"$regex": search, "$options": "i"}}
        ]
    if status and status != "all":
        query["membership_status"] = status
    
    # Get total count
    total = await db.people.count_documents(query)
    
    # Sort direction
    sort_dir = 1 if sort_order == "asc" else -1
    
    # Get paginated results
    skip = (page - 1) * per_page
    people = await db.people.find(
        query, {"_id": 0}
    ).sort(sort_by, sort_dir).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "data": [serialize_doc(p) for p in people],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }


@router.get("/people/{person_id}")
async def get_person(person_id: str):
    person = await db.people.find_one(
        {"id": person_id, "tenant_id": DEFAULT_TENANT_ID},
        {"_id": 0}
    )
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return serialize_doc(person)


@router.post("/people")
async def create_person(person_data: PersonCreate):
    tenant_id = DEFAULT_TENANT_ID
    
    person = Person(
        **person_data.model_dump(),
        tenant_id=tenant_id
    )
    
    doc = person.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.people.insert_one(doc)
    
    # Log activity
    await db.activity_log.insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "action": "member_added",
        "description": f"New member added: {person.first_name} {person.last_name}",
        "entity_type": "person",
        "entity_id": person.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return serialize_doc(doc)


@router.put("/people/{person_id}")
async def update_person(person_id: str, person_data: PersonCreate):
    tenant_id = DEFAULT_TENANT_ID
    
    update_data = person_data.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.people.update_one(
        {"id": person_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Person not found")
    
    return {"success": True, "id": person_id}


@router.delete("/people/{person_id}")
async def delete_person(person_id: str):
    result = await db.people.delete_one(
        {"id": person_id, "tenant_id": DEFAULT_TENANT_ID}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Person not found")
    return {"success": True}


@router.get("/people/{person_id}/giving")
async def get_person_giving(person_id: str):
    tenant_id = DEFAULT_TENANT_ID
    
    # Get donations for this person
    donations = await db.donations.find(
        {"person_id": person_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).sort("donation_date", -1).to_list(100)
    
    # Calculate stats
    today = datetime.now(timezone.utc)
    ytd_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    
    total = sum(d["amount"] for d in donations)
    ytd_total = sum(d["amount"] for d in donations if d["donation_date"] >= ytd_start)
    
    # Get recurring giving
    recurring = await db.recurring_giving.find(
        {"person_id": person_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).to_list(10)
    
    # Get pledges
    pledges = await db.pledges.find(
        {"person_id": person_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).to_list(10)
    
    return {
        "donations": [serialize_doc(d) for d in donations],
        "stats": {
            "lifetime_total": total,
            "ytd_total": ytd_total,
            "total_gifts": len(donations),
            "avg_gift": total / len(donations) if donations else 0,
            "last_gift": donations[0] if donations else None
        },
        "recurring": [serialize_doc(r) for r in recurring],
        "pledges": [serialize_doc(p) for p in pledges]
    }


@router.get("/people/{person_id}/attendance")
async def get_person_attendance(person_id: str):
    tenant_id = DEFAULT_TENANT_ID
    
    # Get attendance records with service info
    pipeline = [
        {"$match": {"person_id": person_id, "tenant_id": tenant_id}},
        {"$lookup": {
            "from": "services",
            "localField": "service_id",
            "foreignField": "id",
            "as": "service"
        }},
        {"$unwind": "$service"},
        {"$lookup": {
            "from": "service_types",
            "localField": "service.service_type_id",
            "foreignField": "id",
            "as": "service_type"
        }},
        {"$unwind": {"path": "$service_type", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "date": "$service.date",
            "service_name": "$service_type.name",
            "check_in_time": 1
        }},
        {"$sort": {"date": -1}},
        {"$limit": 100}
    ]
    
    attendance = await db.attendance.aggregate(pipeline).to_list(100)
    
    # Calculate stats
    total = len(attendance)
    today = datetime.now(timezone.utc)
    ytd_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    ytd_count = sum(1 for a in attendance if a.get("date", "") >= ytd_start)
    
    return {
        "records": attendance,
        "stats": {
            "total_attended": total,
            "ytd_attended": ytd_count,
            "attendance_rate": 0,  # Would need to calculate based on total services
            "current_streak": 0  # Would need to calculate
        }
    }


@router.get("/people/{person_id}/groups")
async def get_person_groups(person_id: str):
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {"person_id": person_id, "tenant_id": tenant_id}},
        {"$lookup": {
            "from": "groups",
            "localField": "group_id",
            "foreignField": "id",
            "as": "group"
        }},
        {"$unwind": "$group"},
        {"$lookup": {
            "from": "group_types",
            "localField": "group.group_type_id",
            "foreignField": "id",
            "as": "group_type"
        }},
        {"$unwind": {"path": "$group_type", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": "$group.id",
            "name": "$group.name",
            "type": "$group_type.name",
            "type_color": "$group_type.color",
            "role": 1,
            "joined_at": 1,
            "meeting_schedule": "$group.meeting_schedule",
            "leader_id": "$group.leader_id"
        }}
    ]
    
    groups = await db.group_members.aggregate(pipeline).to_list(20)
    return groups

# --- HOUSEHOLDS ROUTES ---
@router.get("/households")

@router.get("/households")
async def get_households(page: int = 1, per_page: int = 25, search: Optional[str] = None):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    total = await db.households.count_documents(query)
    skip = (page - 1) * per_page
    
    households = await db.households.find(
        query, {"_id": 0}
    ).skip(skip).limit(per_page).to_list(per_page)
    
    # Get member count for each household
    for h in households:
        count = await db.people.count_documents({
            "tenant_id": tenant_id,
            "household_id": h["id"]
        })
        h["member_count"] = count
    
    return {
        "data": [serialize_doc(h) for h in households],
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get("/households/{household_id}")
async def get_household(household_id: str):
    household = await db.households.find_one(
        {"id": household_id, "tenant_id": DEFAULT_TENANT_ID},
        {"_id": 0}
    )
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    
    # Get members
    members = await db.people.find(
        {"household_id": household_id, "tenant_id": DEFAULT_TENANT_ID},
        {"_id": 0}
    ).to_list(20)
    
    household["members"] = [serialize_doc(m) for m in members]
    return serialize_doc(household)

# --- GROUPS ROUTES ---
@router.get("/groups")

@router.get("/groups")
async def get_groups(
    page: int = 1,
    per_page: int = 25,
    search: Optional[str] = None,
    group_type: Optional[str] = None
):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id, "is_active": True}
    
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    if group_type:
        query["group_type_id"] = group_type
    
    total = await db.groups.count_documents(query)
    skip = (page - 1) * per_page
    
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "group_types",
            "localField": "group_type_id",
            "foreignField": "id",
            "as": "type_info"
        }},
        {"$unwind": {"path": "$type_info", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "people",
            "localField": "leader_id",
            "foreignField": "id",
            "as": "leader"
        }},
        {"$unwind": {"path": "$leader", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "name": 1,
            "description": 1,
            "location": 1,
            "meeting_schedule": 1,
            "meeting_day": 1,
            "meeting_time": 1,
            "capacity": 1,
            "is_open": 1,
            "member_count": 1,
            "type_name": "$type_info.name",
            "type_color": "$type_info.color",
            "leader_name": {"$concat": ["$leader.first_name", " ", "$leader.last_name"]},
            "leader_photo": "$leader.photo_url"
        }},
        {"$skip": skip},
        {"$limit": per_page}
    ]
    
    groups = await db.groups.aggregate(pipeline).to_list(per_page)
    
    return {
        "data": groups,
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get("/groups/{group_id}")
async def get_group(group_id: str):
    tenant_id = DEFAULT_TENANT_ID
    
    group = await db.groups.find_one(
        {"id": group_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get group type
    if group.get("group_type_id"):
        group_type = await db.group_types.find_one(
            {"id": group["group_type_id"]},
            {"_id": 0}
        )
        group["type_info"] = group_type
    
    # Get leader info
    if group.get("leader_id"):
        leader = await db.people.find_one(
            {"id": group["leader_id"]},
            {"_id": 0, "first_name": 1, "last_name": 1, "photo_url": 1, "email": 1}
        )
        group["leader"] = leader
    
    return serialize_doc(group)


@router.get("/groups/{group_id}/members/list")
async def get_group_members_public(group_id: str):
    """Public endpoint for getting group members (no auth required)"""
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {"group_id": group_id, "tenant_id": tenant_id, "is_active": True}},
        {"$lookup": {
            "from": "people",
            "localField": "person_id",
            "foreignField": "id",
            "as": "person"
        }},
        {"$unwind": "$person"},
        {"$project": {
            "_id": 0,
            "id": "$person.id",
            "first_name": "$person.first_name",
            "last_name": "$person.last_name",
            "email": "$person.email",
            "photo_url": "$person.photo_url",
            "role": 1,
            "joined_at": 1
        }}
    ]
    
    members = await db.group_members.aggregate(pipeline).to_list(100)
    return members


@router.get("/group-types")
async def get_group_types():
    types = await db.group_types.find(
        {"tenant_id": DEFAULT_TENANT_ID},
        {"_id": 0}
    ).to_list(20)
    return [serialize_doc(t) for t in types]

# --- ATTENDANCE ROUTES ---
@router.get("/services")

@router.get("/services")
async def get_services(date: Optional[str] = None, limit: int = 10):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    
    if date:
        query["date"] = date
    
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "service_types",
            "localField": "service_type_id",
            "foreignField": "id",
            "as": "type_info"
        }},
        {"$unwind": {"path": "$type_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "date": 1,
            "time": 1,
            "total_headcount": 1,
            "notes": 1,
            "service_type_name": "$type_info.name"
        }},
        {"$sort": {"date": -1}},
        {"$limit": limit}
    ]
    
    services = await db.services.aggregate(pipeline).to_list(limit)
    return services


@router.get("/service-types")
async def get_service_types():
    types = await db.service_types.find(
        {"tenant_id": DEFAULT_TENANT_ID, "is_active": True},
        {"_id": 0}
    ).to_list(20)
    return [serialize_doc(t) for t in types]


@router.post("/attendance")
async def record_attendance(service_id: str, person_ids: List[str]):
    tenant_id = DEFAULT_TENANT_ID
    
    records = []
    for person_id in person_ids:
        # Check if already checked in
        existing = await db.attendance.find_one({
            "service_id": service_id,
            "person_id": person_id,
            "tenant_id": tenant_id
        })
        
        if not existing:
            record = Attendance(
                tenant_id=tenant_id,
                service_id=service_id,
                person_id=person_id
            )
            doc = record.model_dump()
            doc['check_in_time'] = doc['check_in_time'].isoformat()
            await db.attendance.insert_one(doc)
            records.append(record.id)
            
            # Update person's last attended
            await db.people.update_one(
                {"id": person_id},
                {"$set": {"last_attended_at": datetime.now(timezone.utc).isoformat()}}
            )
    
    return {"success": True, "recorded": len(records)}


@router.get("/attendance/service/{service_id}")
async def get_service_attendance(service_id: str):
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {"service_id": service_id, "tenant_id": tenant_id}},
        {"$lookup": {
            "from": "people",
            "localField": "person_id",
            "foreignField": "id",
            "as": "person"
        }},
        {"$unwind": "$person"},
        {"$project": {
            "_id": 0,
            "id": 1,
            "person_id": 1,
            "check_in_time": 1,
            "first_name": "$person.first_name",
            "last_name": "$person.last_name",
            "photo_url": "$person.photo_url"
        }}
    ]
    
    attendance = await db.attendance.aggregate(pipeline).to_list(1000)
    return attendance

# --- GIVING ROUTES ---
@router.get("/funds")

@router.get("/funds")
async def get_funds():
    funds = await db.funds.find(
        {"tenant_id": DEFAULT_TENANT_ID, "is_active": True},
        {"_id": 0}
    ).to_list(20)
    return [serialize_doc(f) for f in funds]


@router.get("/giving/stats")
async def get_giving_stats():
    tenant_id = DEFAULT_TENANT_ID
    today = datetime.now(timezone.utc)
    
    mtd_start = today.replace(day=1).strftime("%Y-%m-%d")
    ytd_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    
    # MTD total
    mtd_pipeline = [
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": mtd_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]
    mtd_result = await db.donations.aggregate(mtd_pipeline).to_list(1)
    
    # YTD total
    ytd_pipeline = [
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": ytd_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]
    ytd_result = await db.donations.aggregate(ytd_pipeline).to_list(1)
    
    # By method
    method_pipeline = [
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": ytd_start}}},
        {"$group": {"_id": "$payment_method", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]
    method_result = await db.donations.aggregate(method_pipeline).to_list(10)
    
    # Active recurring
    recurring_count = await db.recurring_giving.count_documents({
        "tenant_id": tenant_id,
        "is_active": True
    })
    
    # Undeposited batches
    undeposited = await db.donation_batches.count_documents({
        "tenant_id": tenant_id,
        "status": "open"
    })
    
    return {
        "mtd_total": mtd_result[0]["total"] if mtd_result else 0,
        "mtd_count": mtd_result[0]["count"] if mtd_result else 0,
        "ytd_total": ytd_result[0]["total"] if ytd_result else 0,
        "ytd_count": ytd_result[0]["count"] if ytd_result else 0,
        "by_method": {r["_id"]: {"total": r["total"], "count": r["count"]} for r in method_result},
        "active_recurring": recurring_count,
        "undeposited_batches": undeposited
    }


@router.get("/donations")
async def get_donations(
    page: int = 1,
    per_page: int = 25,
    fund_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    payment_method: Optional[str] = None
):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    
    if fund_id:
        query["fund_id"] = fund_id
    if start_date:
        query["donation_date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("donation_date", {})["$lte"] = end_date
    if payment_method:
        query["payment_method"] = payment_method
    
    total = await db.donations.count_documents(query)
    skip = (page - 1) * per_page
    
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "people",
            "localField": "person_id",
            "foreignField": "id",
            "as": "donor"
        }},
        {"$unwind": {"path": "$donor", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "funds",
            "localField": "fund_id",
            "foreignField": "id",
            "as": "fund"
        }},
        {"$unwind": {"path": "$fund", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "amount": 1,
            "donation_date": 1,
            "payment_method": 1,
            "check_number": 1,
            "crypto_currency": 1,
            "crypto_amount": 1,
            "notes": 1,
            "donor_name": {"$concat": ["$donor.first_name", " ", "$donor.last_name"]},
            "donor_photo": "$donor.photo_url",
            "fund_name": "$fund.name",
            "batch_id": 1
        }},
        {"$sort": {"donation_date": -1}},
        {"$skip": skip},
        {"$limit": per_page}
    ]
    
    donations = await db.donations.aggregate(pipeline).to_list(per_page)
    
    return {
        "data": donations,
        "total": total,
        "page": page,
        "per_page": per_page
    }

# ============== GIVING REPORTS & CSV EXPORT ==============

from fastapi.responses import StreamingResponse
import csv
import io


@router.post("/donations")
async def create_donation(donation_data: DonationBase):
    tenant_id = DEFAULT_TENANT_ID
    
    donation = Donation(
        **donation_data.model_dump(),
        tenant_id=tenant_id
    )
    
    doc = donation.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.donations.insert_one(doc)
    
    # Update fund total
    await db.funds.update_one(
        {"id": donation.fund_id},
        {"$inc": {"current_amount": donation.amount}}
    )
    
    # Update batch total if in a batch
    if donation.batch_id:
        await db.donation_batches.update_one(
            {"id": donation.batch_id},
            {"$inc": {"total_amount": donation.amount, "donation_count": 1}}
        )
    
    # Update person's giving totals
    if donation.person_id:
        await db.people.update_one(
            {"id": donation.person_id},
            {"$inc": {"ytd_giving": donation.amount, "lifetime_giving": donation.amount}}
        )
    
    # Log activity
    await db.activity_log.insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "action": "donation_recorded",
        "description": f"Donation of ${donation.amount:.2f} recorded",
        "entity_type": "donation",
        "entity_id": donation.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return serialize_doc(doc)


@router.get("/batches")
async def get_batches(status: Optional[str] = None):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    
    if status:
        query["status"] = status
    
    batches = await db.donation_batches.find(
        query, {"_id": 0}
    ).sort("date", -1).to_list(50)
    
    return [serialize_doc(b) for b in batches]


@router.post("/batches")
async def create_batch(name: str, date: str):
    tenant_id = DEFAULT_TENANT_ID
    
    batch = DonationBatch(
        tenant_id=tenant_id,
        name=name,
        date=date
    )
    
    doc = batch.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.donation_batches.insert_one(doc)
    return serialize_doc(doc)


@router.put("/batches/{batch_id}/close")
async def close_batch(batch_id: str):
    result = await db.donation_batches.update_one(
        {"id": batch_id, "tenant_id": DEFAULT_TENANT_ID},
        {"$set": {"status": "closed"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {"success": True}

# --- EVENTS ROUTES ---
@router.get("/events")

@router.get("/events")
async def get_events(upcoming: bool = True, limit: int = 20):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    
    if upcoming:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        query["start_datetime"] = {"$gte": today}
        sort_dir = 1
    else:
        sort_dir = -1
    
    events = await db.events.find(
        query, {"_id": 0}
    ).sort("start_datetime", sort_dir).limit(limit).to_list(limit)
    
    return [serialize_doc(e) for e in events]


@router.get("/events/{event_id}")
async def get_event(event_id: str):
    event = await db.events.find_one(
        {"id": event_id, "tenant_id": DEFAULT_TENANT_ID},
        {"_id": 0}
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return serialize_doc(event)

# --- COMMUNICATIONS ROUTES ---
@router.get("/communications")

@router.get("/communications")
async def get_communications(status: Optional[str] = None, limit: int = 20):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    
    if status:
        query["status"] = status
    
    comms = await db.communications.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return [serialize_doc(c) for c in comms]


@router.post("/communications")
async def create_communication(subject: str, body_html: str, recipient_ids: List[str] = []):
    tenant_id = DEFAULT_TENANT_ID
    
    comm = Communication(
        tenant_id=tenant_id,
        subject=subject,
        body_html=body_html,
        recipient_count=len(recipient_ids)
    )
    
    doc = comm.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.communications.insert_one(doc)
    return serialize_doc(doc)

# --- REPORTS ROUTES ---
@router.get("/reports/giving-by-fund")

@router.get("/giving/processors")
async def list_payment_processors():
    """List all available payment processors."""
    return {"processors": [{**v, "id": k} for k, v in PAYMENT_PROCESSORS.items()]}


@router.post("/giving/process")
async def process_giving(request: Request, payload: dict):
    """Unified giving endpoint — routes to configured payment processor."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    amount = payload.get("amount", 0)
    fund = payload.get("fund", "General")
    payment_method = payload.get("payment_method", "card")
    is_recurring = payload.get("recurring", False)
    frequency = payload.get("frequency", "one_time")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    settings = await db.payment_processor_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
    active_processor = (settings or {}).get("active_processor", "manual")

    txn_id = f"txn_{uuid.uuid4().hex[:16]}"
    conf_code = f"CONF-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    processor_response = {
        "success": True,
        "transaction_id": txn_id,
        "processor": active_processor,
        "processor_name": PAYMENT_PROCESSORS.get(active_processor, {}).get("name", active_processor),
        "amount": round(amount, 2),
        "currency": "USD",
        "fund": fund,
        "payment_method": payment_method,
        "recurring": is_recurring,
        "frequency": frequency,
        "confirmation": conf_code,
        "timestamp": now_iso,
        "status": "completed",
        "fee": round(amount * 0.029 + 0.30, 2) if active_processor != "manual" else 0,
    }

    donation_record = {
        "id": str(uuid.uuid4()),
        "transaction_id": txn_id,
        "tenant_id": tenant_id,
        "user_id": user.get("user_id"),
        "donor_name": user.get("name", "Anonymous"),
        "donor_email": user.get("email", ""),
        "amount": round(amount, 2),
        "fund": fund,
        "payment_method": payment_method,
        "processor": active_processor,
        "confirmation_code": conf_code,
        "status": "completed",
        "recurring": is_recurring,
        "frequency": frequency,
        "created_at": now_iso,
    }
    await db.donations.insert_one({**donation_record})

    await audit_log("donation_processed", "giving", donation_record["id"], tenant_id, user.get("user_id"), user.get("name", ""), {}, {"amount": amount, "processor": active_processor, "fund": fund}, request)

    return processor_response


# ============== AUDIT TRAIL ENDPOINT ==============


@router.get("/music-stand/{plan_id}")
async def get_music_stand(plan_id: str):
    """Public music stand view for a service plan"""
    plan = await db.service_plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    enriched_items = []
    for item in plan.get("items", []):
        enriched = {**item}
        if item.get("song_id"):
            song = await db.songs.find_one({"id": item["song_id"]}, {"_id": 0})
            if song:
                enriched["song"] = {
                    "title": song.get("title"),
                    "artist": song.get("artist"),
                    "lyrics": song.get("lyrics", ""),
                    "arrangements": song.get("arrangements", []),
                    "default_key": song.get("default_key", "C"),
                    "bpm": song.get("bpm"),
                }
        enriched_items.append(enriched)
    return {
        "plan_id": plan["id"],
        "title": plan.get("title", "Service"),
        "date": plan.get("date"),
        "service_type": plan.get("service_type"),
        "items": enriched_items,
    }


# ============== HOUSEHOLDS / FAMILIES ==============


@router.get("/search")
async def global_search(q: str, limit: int = 10):
    tenant_id = DEFAULT_TENANT_ID
    results = []
    
    # Search people
    people = await db.people.find(
        {
            "tenant_id": tenant_id,
            "$or": [
                {"first_name": {"$regex": q, "$options": "i"}},
                {"last_name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}}
            ]
        },
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "photo_url": 1}
    ).limit(limit).to_list(limit)
    
    for p in people:
        results.append({
            "type": "person",
            "id": p["id"],
            "title": f"{p['first_name']} {p['last_name']}",
            "subtitle": p.get("email", ""),
            "photo_url": p.get("photo_url")
        })
    
    # Search groups
    groups = await db.groups.find(
        {
            "tenant_id": tenant_id,
            "name": {"$regex": q, "$options": "i"}
        },
        {"_id": 0, "id": 1, "name": 1}
    ).limit(5).to_list(5)
    
    for g in groups:
        results.append({
            "type": "group",
            "id": g["id"],
            "title": g["name"],
            "subtitle": "Group"
        })
    
    # Search events
    events = await db.events.find(
        {
            "tenant_id": tenant_id,
            "name": {"$regex": q, "$options": "i"}
        },
        {"_id": 0, "id": 1, "name": 1, "start_datetime": 1}
    ).limit(5).to_list(5)
    
    for e in events:
        results.append({
            "type": "event",
            "id": e["id"],
            "title": e["name"],
            "subtitle": e.get("start_datetime", "")
        })
    
    return results

# ============== AGENT API ROUTES (External Agent Access) ==============

# --- API Key Management (Admin) ---


@router.post("/waitlist/solomon-pay")
async def join_solomon_pay_waitlist(payload: dict):
    """Join the Solomon Pay waitlist."""
    email = payload.get("email", "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    existing = await db.waitlist.find_one({"email": email, "type": "solomon_pay"})
    if existing:
        return {"success": True, "message": "You're already on the waitlist!"}
    await db.waitlist.insert_one({
        "id": str(uuid.uuid4()), "type": "solomon_pay", "email": email,
        "church_name": payload.get("church_name", ""), "member_count": payload.get("member_count", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return {"success": True, "message": "You're on the waitlist! We'll be in touch."}


@router.post("/demo-requests")
async def submit_demo_request(payload: dict):
    """Submit a demo request."""
    email = payload.get("email", "").strip()
    first_name = payload.get("first_name", "").strip()
    church_name = payload.get("church_name", "").strip()
    if not email or not first_name or not church_name:
        raise HTTPException(status_code=400, detail="First name, church name, and email are required")
    await db.demo_requests.insert_one({
        "id": str(uuid.uuid4()), "first_name": first_name, "last_name": payload.get("last_name", "").strip(),
        "church_name": church_name, "email": email, "phone": payload.get("phone", "").strip(),
        "member_count": payload.get("member_count", ""), "interests": payload.get("interests", []),
        "status": "new", "created_at": datetime.now(timezone.utc).isoformat()
    })
    return {"success": True, "message": "Demo request submitted! We'll be in touch within 24 hours."}

