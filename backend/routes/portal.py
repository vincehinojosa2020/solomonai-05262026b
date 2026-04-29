"""Solomon AI — Portal (Member-Facing) Routes"""
from fastapi import APIRouter, HTTPException, Request, Response, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import random
import re
import logging
import os

from core import (
    db, DEFAULT_TENANT_ID,
    get_current_portal_user, get_current_member_user,
    get_session_token_from_request,
    require_tenant, audit_log, check_idempotency, store_idempotency,
    logger,
)
from core.helpers import (
    serialize_doc, DEFAULT_MERCH_EMBED_URL, DEFAULT_NEXT_STEPS_URL,
    evaluate_member_next_steps_membership, get_next_steps_required_course_ids,
    generate_next_steps_certificate_pdf, notify_meeting_event,
    generate_pickup_code, calculate_attendance_streak, extract_youtube_id,
)
from core.seed import (
    ensure_demo_merch_data, ensure_demo_cafe_data, ensure_demo_meetings_data,
    ensure_abundant_pathways_data, ensure_abundant_go_live_portal_content,
)
from models.schemas import (
    PortalProfileUpdate, WatchProgressUpdate,
    AttendanceCheckinRequest, KidsCheckinRequest, KidsCheckoutRequest,
    ChildCreate, Child, Checkin, Event, Fund, Group, GroupMember,
    LeadershipNote, LeadershipNoteCreate, MerchOrderCreate,
    CafeOrderCreate, PastorMeetingBooking, PastorMeeting,
    PathwaysProgressUpdate, PrayerRequestAliasCreate,
    PrayerRequest, PrayerRequestCreate, MemberCheckIn,
    GivingDonateRequest, CheckoutWithNudgeRequest, SavePaymentMethodRequest,
    AddMemberToGroupRequest, EventCreate, GroupCreate,
    VideoNote, VideoNoteCreate, VideoNoteUpdate, VideoNoteShare,
    VolunteerSignupRequest, Service, User,
    CreateRecurringGivingRequest, UpdateRecurringGivingRequest,
)

router = APIRouter()

@router.get("/portal/me")
async def get_member_profile(request: Request):
    """Get current member's profile for portal"""
    user = await get_current_member_user(request)
    
    # Find linked person record
    person = await db.people.find_one({"email": user["email"]}, {"_id": 0})
    
    # Get member's groups
    groups = []
    if person:
        group_memberships = await db.group_members.find(
            {"person_id": person["id"], "is_active": True},
            {"_id": 0}
        ).to_list(100)
        
        # Optimized: Fetch all groups in a single query instead of N+1
        if group_memberships:
            group_ids = [gm["group_id"] for gm in group_memberships]
            groups_docs = await db.groups.find(
                {"id": {"$in": group_ids}},
                {"_id": 0}
            ).to_list(len(group_ids))
            groups = [serialize_doc(g) for g in groups_docs]
    
    # Get giving summary
    ytd_giving = 0
    last_gift = None
    if person:
        today = datetime.now(timezone.utc)
        ytd_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
        
        ytd_pipeline = [
            {"$match": {"person_id": person["id"], "donation_date": {"$gte": ytd_start}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        ytd_result = await db.donations.aggregate(ytd_pipeline).to_list(1)
        ytd_giving = ytd_result[0]["total"] if ytd_result else 0
        
        last_gift_doc = await db.donations.find_one(
            {"person_id": person["id"]},
            {"_id": 0},
            sort=[("donation_date", -1)]
        )
        if last_gift_doc:
            last_gift = serialize_doc(last_gift_doc)
    
    # Get recurring giving
    recurring = None
    if person:
        recurring_doc = await db.recurring_giving.find_one(
            {"person_id": person["id"], "is_active": True},
            {"_id": 0}
        )
        if recurring_doc:
            recurring = serialize_doc(recurring_doc)
    
    return {
        "user": serialize_doc(user),
        "person": serialize_doc(person) if person else None,
        "groups": groups,
        "giving": {
            "ytd_total": ytd_giving,
            "last_gift": last_gift,
            "recurring": recurring
        },
        "member_since": user.get("member_since") or (person.get("membership_date") if person else None)
    }


@router.get("/portal/profile")
async def get_portal_profile(request: Request):
    """Mobile-friendly alias for member profile."""
    return await get_member_profile(request)


@router.put("/portal/profile")
async def update_portal_profile(request: Request, payload: PortalProfileUpdate):
    """Update current member profile for both web and mobile clients."""
    user = await get_current_member_user(request)

    update_fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_fields:
        return {"message": "No changes submitted", "user": serialize_doc(user)}

    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    if "name" not in update_fields:
        first_name = update_fields.get("first_name") or user.get("first_name")
        last_name = update_fields.get("last_name") or user.get("last_name")
        if first_name and last_name:
            update_fields["name"] = f"{first_name} {last_name}".strip()

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": update_fields}
    )

    refreshed_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})

    person_update = {}
    if update_fields.get("first_name"):
        person_update["first_name"] = update_fields["first_name"]
    if update_fields.get("last_name"):
        person_update["last_name"] = update_fields["last_name"]
    if update_fields.get("mobile_phone"):
        person_update["mobile_phone"] = update_fields["mobile_phone"]
    elif update_fields.get("phone"):
        person_update["mobile_phone"] = update_fields["phone"]
    for addr_field in ["address", "city", "state", "zip"]:
        if update_fields.get(addr_field):
            person_update[addr_field] = update_fields[addr_field]
    if person_update:
        person_update["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.people.update_one(
            {"email": refreshed_user.get("email"), "tenant_id": refreshed_user.get("tenant_id")},
            {"$set": person_update}
        )

    return {"message": "Profile updated", "user": serialize_doc(refreshed_user)}


@router.put("/portal/profile/privacy")
async def update_privacy_settings(request: Request):
    """Update directory privacy preferences."""
    user = await get_current_member_user(request)
    body = await request.json()
    PRIVACY_FIELDS = {"share_email", "share_phone", "share_address", "directory_visible"}
    safe = {k: v for k, v in body.items() if k in PRIVACY_FIELDS and isinstance(v, bool)}
    if not safe:
        return {"message": "No valid privacy fields"}
    safe["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": safe})
    await db.people.update_one(
        {"email": user.get("email"), "tenant_id": user.get("tenant_id")},
        {"$set": safe}
    )
    return {"message": "Privacy settings updated"}




@router.get("/portal/giving/history")
async def get_member_giving_history(request: Request, limit: int = 50):
    """Get member's giving history for portal"""
    user = await get_current_member_user(request)
    person = await db.people.find_one(
        {"email": user["email"], "tenant_id": user.get("tenant_id")},
        {"_id": 0}
    )
    
    if not person:
        return {"donations": [], "total": 0}
    
    donations = await db.donations.find(
        {"tenant_id": user.get("tenant_id"), "person_id": person["id"]},
        {"_id": 0}
    ).sort("donation_date", -1).limit(limit).to_list(limit)
    
    # Optimized: Fetch all fund names in a single query instead of N+1
    if donations:
        fund_ids = list(set(d.get("fund_id") for d in donations if d.get("fund_id")))
        if fund_ids:
            funds_list = await db.funds.find(
                {"id": {"$in": fund_ids}},
                {"_id": 0, "id": 1, "name": 1}
            ).to_list(len(fund_ids))
            funds_map = {f["id"]: f["name"] for f in funds_list}
        else:
            funds_map = {}
        
        for d in donations:
            d["fund_name"] = funds_map.get(d.get("fund_id"), "General Fund")
    
    return {
        "donations": [serialize_doc(d) for d in donations],
        "total": len(donations)
    }


@router.get("/portal/giving/ytd")
async def get_member_giving_ytd(request: Request):
    """Return YTD giving totals for the authenticated member."""
    user = await get_current_member_user(request)
    person = await db.people.find_one({"email": user["email"], "tenant_id": user.get("tenant_id")}, {"_id": 0})

    if not person:
        return {"ytd_total": 0, "currency": "USD", "donation_count": 0}

    ytd_start = datetime.now(timezone.utc).replace(month=1, day=1).strftime("%Y-%m-%d")
    donations = await db.donations.find(
        {
            "tenant_id": user.get("tenant_id"),
            "person_id": person["id"],
            "donation_date": {"$gte": ytd_start}
        },
        {"_id": 0, "amount": 1}
    ).to_list(1000)

    ytd_total = round(sum(float(d.get("amount", 0) or 0) for d in donations), 2)
    return {
        "ytd_total": ytd_total,
        "currency": "USD",
        "donation_count": len(donations)
    }



# ============== GIVING GOALS / PLEDGES ==============

@router.get("/portal/giving-goal")
async def get_giving_goal(request: Request, year: int = None):
    """Get the member's giving goal for the specified year and current progress."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    if not year:
        year = datetime.now(timezone.utc).year

    person = await db.people.find_one(
        {"email": user["email"], "tenant_id": tenant_id}, {"_id": 0}
    )
    person_id = person["id"] if person else user.get("user_id")

    goal = await db.giving_goals.find_one(
        {"tenant_id": tenant_id, "person_id": person_id, "year": year},
        {"_id": 0}
    )

    # Calculate YTD progress
    ytd_start = f"{year}-01-01"
    ytd_end = f"{year}-12-31"
    pipeline = [
        {"$match": {"tenant_id": tenant_id, "person_id": person_id, "donation_date": {"$gte": ytd_start, "$lte": ytd_end}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]
    agg = await db.donations.aggregate(pipeline).to_list(1)
    ytd_total = round(agg[0]["total"], 2) if agg else 0
    donation_count = agg[0]["count"] if agg else 0

    target = goal["target_amount"] if goal else 0
    progress_pct = round((ytd_total / target) * 100, 1) if target > 0 else 0

    return {
        "year": year,
        "target_amount": target,
        "ytd_given": ytd_total,
        "donation_count": donation_count,
        "progress_pct": min(progress_pct, 100),
        "remaining": round(max(target - ytd_total, 0), 2),
        "has_goal": goal is not None,
    }


@router.post("/portal/giving-goal")
async def set_giving_goal(request: Request):
    """Set or update the member's giving goal for the year."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()

    target_amount = body.get("target_amount")
    year = body.get("year", datetime.now(timezone.utc).year)

    if target_amount is None or target_amount <= 0:
        raise HTTPException(status_code=400, detail="Target amount must be positive")

    person = await db.people.find_one(
        {"email": user["email"], "tenant_id": tenant_id}, {"_id": 0}
    )
    person_id = person["id"] if person else user.get("user_id")

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.giving_goals.update_one(
        {"tenant_id": tenant_id, "person_id": person_id, "year": year},
        {"$set": {
            "target_amount": round(float(target_amount), 2),
            "updated_at": now_iso,
        }, "$setOnInsert": {
            "id": f"goal_{uuid.uuid4().hex[:12]}",
            "tenant_id": tenant_id,
            "person_id": person_id,
            "year": year,
            "created_at": now_iso,
        }},
        upsert=True
    )

    return {"message": f"Giving goal for {year} set to ${target_amount:.2f}", "target_amount": round(float(target_amount), 2), "year": year}


@router.delete("/portal/giving-goal")
async def delete_giving_goal(request: Request, year: int = None):
    """Remove the member's giving goal."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    if not year:
        year = datetime.now(timezone.utc).year

    person = await db.people.find_one(
        {"email": user["email"], "tenant_id": tenant_id}, {"_id": 0}
    )
    person_id = person["id"] if person else user.get("user_id")

    result = await db.giving_goals.delete_one(
        {"tenant_id": tenant_id, "person_id": person_id, "year": year}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No goal found for this year")
    return {"message": "Giving goal removed"}



# ============== TAX STATEMENT ==============

@router.get("/portal/giving/statement/{year}")
async def get_my_giving_statement(request: Request, year: int):
    """Get the member's giving statement data for a specific year."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    person = await db.people.find_one({"email": user["email"], "tenant_id": tenant_id}, {"_id": 0})
    if not person:
        raise HTTPException(status_code=404, detail="Member not found")
    person_id = person["id"]

    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    donations = await db.donations.find(
        {"tenant_id": tenant_id, "person_id": person_id, "donation_date": {"$gte": start_date, "$lte": end_date}},
        {"_id": 0}
    ).sort("donation_date", 1).to_list(1000)

    fund_totals = {}
    for d in donations:
        fn = d.get("fund_name", "General Fund")
        fund_totals[fn] = fund_totals.get(fn, 0) + d.get("amount", 0)
    total = sum(d.get("amount", 0) for d in donations)

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})

    return {
        "year": year,
        "generated_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "church": {
            "name": tenant.get("name", "Abundant Life Church") if tenant else "Abundant Life Church",
            "address": tenant.get("address", "1200 E Paisano Dr") if tenant else "1200 E Paisano Dr",
            "city_state_zip": f"{tenant.get('city', 'El Paso')}, {tenant.get('state', 'TX')} {tenant.get('zip', '79901')}" if tenant else "El Paso, TX 79901",
            "ein": tenant.get("ein", "74-1234567") if tenant else "74-1234567",
        },
        "donor": {
            "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
            "address": person.get("address", ""),
            "email": person.get("email", ""),
        },
        "donations": [{"date": d["donation_date"], "amount": d["amount"], "fund": d.get("fund_name", "General")} for d in donations],
        "fund_totals": [{"fund": k, "total": round(v, 2)} for k, v in fund_totals.items()],
        "total_amount": round(total, 2),
        "donation_count": len(donations),
        "disclaimer": "No goods or services were provided in exchange for these contributions except intangible religious benefits. This statement may be used for tax purposes.",
    }


@router.get("/portal/giving/statement/{year}/pdf")
async def download_giving_statement_pdf(request: Request, year: int):
    """Download the member's giving statement as a PDF."""
    from fastapi.responses import StreamingResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    import io

    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    person = await db.people.find_one({"email": user["email"], "tenant_id": tenant_id}, {"_id": 0})
    if not person:
        raise HTTPException(status_code=404, detail="Member not found")
    person_id = person["id"]

    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    donations = await db.donations.find(
        {"tenant_id": tenant_id, "person_id": person_id, "donation_date": {"$gte": start_date, "$lte": end_date}},
        {"_id": 0}
    ).sort("donation_date", 1).to_list(1000)

    fund_totals = {}
    for d in donations:
        fn = d.get("fund_name", "General Fund")
        fund_totals[fn] = fund_totals.get(fn, 0) + d.get("amount", 0)
    total = sum(d.get("amount", 0) for d in donations)

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    church_name = tenant.get("name", "Abundant Life Church") if tenant else "Abundant Life Church"
    church_ein = tenant.get("ein", "74-1234567") if tenant else "74-1234567"
    donor_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter
    y = h - 60

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, y, church_name)
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(72, y, f"EIN: {church_ein}")
    y -= 30

    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, y, f"Annual Giving Statement — {year}")
    y -= 25

    c.setFont("Helvetica", 11)
    c.drawString(72, y, f"Donor: {donor_name}")
    y -= 15
    c.drawString(72, y, f"Email: {person.get('email', '')}")
    y -= 15
    c.drawString(72, y, f"Generated: {datetime.now(timezone.utc).strftime('%B %d, %Y')}")
    y -= 30

    # Table header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(72, y, "Date")
    c.drawString(220, y, "Fund")
    c.drawRightString(w - 72, y, "Amount")
    y -= 3
    c.line(72, y, w - 72, y)
    y -= 15

    c.setFont("Helvetica", 10)
    for don in donations:
        if y < 100:
            c.showPage()
            y = h - 60
            c.setFont("Helvetica", 10)
        c.drawString(72, y, don.get("donation_date", ""))
        c.drawString(220, y, don.get("fund_name", "General Fund"))
        c.drawRightString(w - 72, y, f"${don.get('amount', 0):,.2f}")
        y -= 14

    y -= 10
    c.line(72, y, w - 72, y)
    y -= 18

    # Fund totals
    c.setFont("Helvetica-Bold", 10)
    for fn, ft in fund_totals.items():
        c.drawString(220, y, fn)
        c.drawRightString(w - 72, y, f"${ft:,.2f}")
        y -= 14

    y -= 6
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Total Contributions")
    c.drawRightString(w - 72, y, f"${total:,.2f}")
    y -= 30

    # Disclaimer
    c.setFont("Helvetica", 8)
    c.drawString(72, y, "No goods or services were provided in exchange for these contributions")
    y -= 11
    c.drawString(72, y, "except intangible religious benefits. This statement may be used for tax purposes.")

    c.save()
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=giving_statement_{year}.pdf"}
    )


@router.get("/portal/giving/statement-pdf/{pdf_id}")
async def download_solomon_generated_pdf(request: Request, pdf_id: str):
    """Download a PDF generated by Solomon AI."""
    from fastapi.responses import Response
    user = await get_current_member_user(request)
    pdf_doc = await db.generated_pdfs.find_one({"id": pdf_id, "user_id": user["user_id"]}, {"_id": 0})
    if not pdf_doc:
        raise HTTPException(status_code=404, detail="PDF not found")
    year = pdf_doc.get("year", "")
    content = pdf_doc.get("content", b"")
    if isinstance(content, bytes):
        pdf_bytes = content
    else:
        pdf_bytes = bytes(content)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=giving_statement_{year}.pdf"}
    )



# ============== RECURRING GIVING MANAGEMENT ==============

def _calculate_next_charge_date(frequency: str, from_date: str = None) -> str:
    """Calculate the next charge date based on frequency."""
    base = datetime.strptime(from_date, "%Y-%m-%d") if from_date else datetime.now(timezone.utc)
    if frequency == "weekly":
        next_date = base + timedelta(days=7)
    elif frequency == "biweekly":
        next_date = base + timedelta(days=14)
    elif frequency == "monthly":
        month = base.month + 1
        year = base.year
        if month > 12:
            month = 1
            year += 1
        day = min(base.day, 28)
        next_date = base.replace(year=year, month=month, day=day)
    elif frequency == "annually":
        next_date = base.replace(year=base.year + 1)
    else:
        next_date = base + timedelta(days=30)
    return next_date.strftime("%Y-%m-%d")


@router.post("/portal/recurring-giving")
async def create_recurring_giving(request: Request, payload: CreateRecurringGivingRequest):
    """Create a new recurring giving schedule for the current member."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if payload.frequency not in ("weekly", "biweekly", "monthly", "annually"):
        raise HTTPException(status_code=400, detail="Invalid frequency")

    person = await db.people.find_one(
        {"email": user["email"], "tenant_id": tenant_id}, {"_id": 0}
    )
    person_id = person["id"] if person else user.get("user_id")
    person_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip() if person else user.get("name", "")

    start_date = payload.start_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    next_charge = _calculate_next_charge_date(payload.frequency, start_date)

    schedule = {
        "id": f"rec_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "person_id": person_id,
        "person_name": person_name,
        "person_email": user.get("email", ""),
        "amount": round(payload.amount, 2),
        "fund_id": payload.fund_id,
        "fund_name": payload.fund_name,
        "frequency": payload.frequency,
        "start_date": start_date,
        "next_charge_date": next_charge,
        "payment_method_id": payload.payment_method_id,
        "card_last_four": payload.card_last_four,
        "card_brand": payload.card_brand,
        "status": "active",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "cancelled_at": None,
    }
    await db.recurring_giving.insert_one(schedule)

    return {
        "id": schedule["id"],
        "amount": schedule["amount"],
        "fund_name": schedule["fund_name"],
        "frequency": schedule["frequency"],
        "next_charge_date": schedule["next_charge_date"],
        "status": "active",
        "message": f"Recurring {payload.frequency} gift of ${payload.amount:.2f} to {payload.fund_name} created successfully.",
    }


@router.get("/portal/recurring-giving")
async def list_my_recurring_giving(request: Request):
    """List all recurring giving schedules for the current member."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    person = await db.people.find_one(
        {"email": user["email"], "tenant_id": tenant_id}, {"_id": 0}
    )
    person_id = person["id"] if person else user.get("user_id")

    schedules = await db.recurring_giving.find(
        {"tenant_id": tenant_id, "person_id": person_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)

    return {"schedules": schedules}


@router.put("/portal/recurring-giving/{schedule_id}")
async def update_recurring_giving(request: Request, schedule_id: str, payload: UpdateRecurringGivingRequest):
    """Update an existing recurring giving schedule (amount, fund, frequency)."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    person = await db.people.find_one(
        {"email": user["email"], "tenant_id": tenant_id}, {"_id": 0}
    )
    person_id = person["id"] if person else user.get("user_id")

    schedule = await db.recurring_giving.find_one(
        {"id": schedule_id, "tenant_id": tenant_id, "person_id": person_id},
        {"_id": 0}
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Recurring schedule not found")
    if schedule.get("status") == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot edit a cancelled schedule")

    update_fields = {}
    if payload.amount is not None:
        if payload.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        update_fields["amount"] = round(payload.amount, 2)
    if payload.fund_id is not None:
        update_fields["fund_id"] = payload.fund_id
    if payload.fund_name is not None:
        update_fields["fund_name"] = payload.fund_name
    if payload.frequency is not None:
        if payload.frequency not in ("weekly", "biweekly", "monthly", "annually"):
            raise HTTPException(status_code=400, detail="Invalid frequency")
        update_fields["frequency"] = payload.frequency
        update_fields["next_charge_date"] = _calculate_next_charge_date(payload.frequency)
    if payload.payment_method_id is not None:
        update_fields["payment_method_id"] = payload.payment_method_id
    if payload.card_last_four is not None:
        update_fields["card_last_four"] = payload.card_last_four
    if payload.card_brand is not None:
        update_fields["card_brand"] = payload.card_brand

    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.recurring_giving.update_one(
        {"id": schedule_id, "tenant_id": tenant_id},
        {"$set": update_fields}
    )

    updated = await db.recurring_giving.find_one({"id": schedule_id}, {"_id": 0})
    return {"message": "Recurring schedule updated", "schedule": updated}


@router.put("/portal/recurring-giving/{schedule_id}/pause")
async def pause_recurring_giving(request: Request, schedule_id: str):
    """Pause a recurring giving schedule."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    person = await db.people.find_one(
        {"email": user["email"], "tenant_id": tenant_id}, {"_id": 0}
    )
    person_id = person["id"] if person else user.get("user_id")

    schedule = await db.recurring_giving.find_one(
        {"id": schedule_id, "tenant_id": tenant_id, "person_id": person_id},
        {"_id": 0}
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Recurring schedule not found")
    if schedule.get("status") != "active":
        raise HTTPException(status_code=400, detail="Only active schedules can be paused")

    await db.recurring_giving.update_one(
        {"id": schedule_id},
        {"$set": {"status": "paused", "is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Recurring schedule paused", "status": "paused"}


@router.put("/portal/recurring-giving/{schedule_id}/resume")
async def resume_recurring_giving(request: Request, schedule_id: str):
    """Resume a paused recurring giving schedule."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    person = await db.people.find_one(
        {"email": user["email"], "tenant_id": tenant_id}, {"_id": 0}
    )
    person_id = person["id"] if person else user.get("user_id")

    schedule = await db.recurring_giving.find_one(
        {"id": schedule_id, "tenant_id": tenant_id, "person_id": person_id},
        {"_id": 0}
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Recurring schedule not found")
    if schedule.get("status") != "paused":
        raise HTTPException(status_code=400, detail="Only paused schedules can be resumed")

    next_charge = _calculate_next_charge_date(schedule.get("frequency", "monthly"))
    await db.recurring_giving.update_one(
        {"id": schedule_id},
        {"$set": {
            "status": "active",
            "is_active": True,
            "next_charge_date": next_charge,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    return {"message": "Recurring schedule resumed", "status": "active", "next_charge_date": next_charge}


@router.delete("/portal/recurring-giving/{schedule_id}")
async def cancel_recurring_giving(request: Request, schedule_id: str):
    """Cancel a recurring giving schedule (soft delete)."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    person = await db.people.find_one(
        {"email": user["email"], "tenant_id": tenant_id}, {"_id": 0}
    )
    person_id = person["id"] if person else user.get("user_id")

    schedule = await db.recurring_giving.find_one(
        {"id": schedule_id, "tenant_id": tenant_id, "person_id": person_id},
        {"_id": 0}
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Recurring schedule not found")
    if schedule.get("status") == "cancelled":
        raise HTTPException(status_code=400, detail="Schedule is already cancelled")

    await db.recurring_giving.update_one(
        {"id": schedule_id},
        {"$set": {
            "status": "cancelled",
            "is_active": False,
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    return {"message": "Recurring schedule cancelled", "status": "cancelled"}



@router.get("/portal/events")
async def get_member_events(request: Request):
    """Get upcoming events for member portal"""
    user = await get_current_member_user(request)
    
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Try both date formats for events
    events = await db.events.find(
        {
            "tenant_id": tenant_id,
            "$or": [
                {"start_datetime": {"$gte": today}},
                {"event_date": {"$gte": today}}
            ]
        },
        {"_id": 0}
    ).sort("event_date", 1).limit(50).to_list(50)
    
    # Enrich with waitlist count (batched)
    enriched = []
    event_ids_with_capacity = [e["id"] for e in events if e.get("capacity")]
    waitlist_map = {}
    if event_ids_with_capacity:
        pipeline = [
            {"$match": {"event_id": {"$in": event_ids_with_capacity}, "status": "waitlisted"}},
            {"$group": {"_id": "$event_id", "count": {"$sum": 1}}}
        ]
        wl_results = await db.event_registrations.aggregate(pipeline).to_list(len(event_ids_with_capacity))
        waitlist_map = {wc["_id"]: wc["count"] for wc in wl_results}
    for e in events:
        event_data = serialize_doc(e)
        if e.get("capacity"):
            event_data["waitlist_count"] = waitlist_map.get(e["id"], 0)
        enriched.append(event_data)
    
    return enriched


@router.get("/portal/groups")
async def get_available_groups(request: Request):
    """Get groups available to join for member portal"""
    user = await get_current_member_user(request)
    
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    
    groups = await db.groups.find(
        {"tenant_id": tenant_id, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    # Enrich with leader info (batched)
    leader_ids = [g.get("leader_id") for g in groups if g.get("leader_id")]
    leaders_map = {}
    if leader_ids:
        leaders_list = await db.people.find({"id": {"$in": leader_ids}}, {"_id": 0}).to_list(len(leader_ids))
        leaders_map = {leader["id"]: leader for leader in leaders_list}
    for g in groups:
        if g.get("leader_id"):
            g["leader"] = serialize_doc(leaders_map.get(g["leader_id"]))
    
    return [serialize_doc(g) for g in groups]

# ============== WATCH PROGRESS ROUTES ==============


@router.post("/portal/watch/progress")
async def update_watch_progress(request: Request, progress: WatchProgressUpdate):
    """Save or update video watch progress for a user"""
    # Get user from session
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_id = session.get("user_id")
    
    # Calculate progress percentage
    progress_percent = (progress.position_seconds / progress.duration_seconds * 100) if progress.duration_seconds > 0 else 0
    completed = progress_percent >= 90  # Mark as completed if watched 90%+
    
    # Upsert watch progress
    watch_data = {
        "user_id": user_id,
        "video_id": progress.video_id,
        "youtube_id": progress.youtube_id,
        "title": progress.title,
        "thumbnail": progress.thumbnail,
        "instructor": progress.instructor,
        "position_seconds": progress.position_seconds,
        "duration_seconds": progress.duration_seconds,
        "progress_percent": round(progress_percent, 1),
        "completed": completed,
        "last_watched": datetime.now(timezone.utc).isoformat()
    }
    
    # Check if entry exists
    existing = await db.watch_progress.find_one(
        {"user_id": user_id, "video_id": progress.video_id},
        {"_id": 0}
    )
    
    if existing:
        await db.watch_progress.update_one(
            {"user_id": user_id, "video_id": progress.video_id},
            {"$set": watch_data}
        )
    else:
        watch_data["id"] = str(uuid.uuid4())
        await db.watch_progress.insert_one(watch_data)
    
    return {"status": "saved", "progress_percent": watch_data["progress_percent"], "completed": completed}


@router.get("/portal/watch/progress")
async def get_watch_progress(request: Request):
    """Get all watch progress for current user (for Continue Watching)"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_id = session.get("user_id")
    
    # Get in-progress videos (not completed, sorted by last watched)
    in_progress = await db.watch_progress.find(
        {"user_id": user_id, "completed": False, "progress_percent": {"$gt": 0}},
        {"_id": 0}
    ).sort("last_watched", -1).to_list(20)
    
    # Get completed videos
    completed = await db.watch_progress.find(
        {"user_id": user_id, "completed": True},
        {"_id": 0}
    ).sort("last_watched", -1).to_list(50)
    
    return {
        "continue_watching": [serialize_doc(p) for p in in_progress],
        "completed": [serialize_doc(p) for p in completed],
        "total_watched": len(completed)
    }


@router.get("/portal/watch/progress/{video_id}")
async def get_video_progress(request: Request, video_id: str):
    """Get watch progress for a specific video"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        return {"position_seconds": 0, "progress_percent": 0, "completed": False}
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        return {"position_seconds": 0, "progress_percent": 0, "completed": False}
    
    user_id = session.get("user_id")
    
    progress = await db.watch_progress.find_one(
        {"user_id": user_id, "video_id": video_id},
        {"_id": 0}
    )
    
    if progress:
        return serialize_doc(progress)
    
    return {"position_seconds": 0, "progress_percent": 0, "completed": False}

# ============== THINKIFIC ROUTES ==============


@router.get("/portal/thinkific")
async def get_portal_thinkific(request: Request):
    """Get Thinkific URL for member portal"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "thinkific_url": 1})
    thinkific_url = tenant.get("thinkific_url") if tenant else None
    if tenant_id == "abundant-east-001" and (not thinkific_url or "abundant.thinkific.com" in thinkific_url):
        thinkific_url = "https://abundantchurch.thinkific.com/collections"
        await db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {"thinkific_url": thinkific_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    return {"thinkific_url": thinkific_url}


@router.get("/portal/next-steps/status")
async def get_portal_next_steps_status(request: Request):
    """Member-facing status for Abundant Next Steps journey."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    await ensure_abundant_pathways_data(tenant_id)
    journey = await evaluate_member_next_steps_membership(tenant_id, user.get("user_id"))

    tenant = await db.tenants.find_one(
        {"id": tenant_id},
        {"_id": 0, "name": 1, "thinkific_url": 1, "next_steps_url": 1}
    )
    thinkific_url = (tenant or {}).get("next_steps_url") or DEFAULT_NEXT_STEPS_URL

    course_docs = await db.pathways_courses.find(
        {"tenant_id": tenant_id, "id": {"$in": journey.get("required_course_ids", [])}},
        {"_id": 0, "id": 1, "title": 1}
    ).to_list(50)
    course_map = {course["id"]: course.get("title", "Course") for course in course_docs}

    return {
        "track_name": "Abundant Next Steps",
        "church_name": (tenant or {}).get("name", "Abundant Church"),
        "thinkific_url": thinkific_url,
        "required_courses": [
            {
                "course_id": course_id,
                "title": course_map.get(course_id, "Course"),
                "completed": course_id in journey.get("completed_course_ids", [])
            }
            for course_id in journey.get("required_course_ids", [])
        ],
        "completion_percent": journey.get("completion_percent", 0),
        "eligible": journey.get("eligible", False),
        "approval_status": journey.get("approval_status"),
        "certificate_available": journey.get("approval_status") == "approved",
        "certificate_url": "/api/portal/next-steps/certificate"
    }


@router.get("/portal/next-steps")
async def get_portal_next_steps(request: Request):
    """Legacy/mobile-friendly Next Steps endpoint."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_abundant_go_live_portal_content()

    journey = await db.next_steps_journeys.find_one(
        {"tenant_id": tenant_id, "user_id": user.get("user_id")},
        {"_id": 0}
    )
    if journey:
        return {
            "current_step": journey.get("current_step", "Salvation"),
            "steps": journey.get("steps", []),
            "percentage_complete": journey.get("percentage_complete", 0),
            "status": journey.get("status", "in_progress"),
            "thinkific_url": journey.get("thinkific_url", "https://abundant.thinkific.com/courses")
        }

    status_data = await get_portal_next_steps_status(request)
    required = status_data.get("required_courses", [])
    completed_count = len([course for course in required if course.get("completed")])
    total_count = len(required)
    pct = round((completed_count / total_count) * 100) if total_count else 0
    return {
        "current_step": required[completed_count]["title"] if completed_count < total_count else "Completed",
        "steps": [
            {"id": idx + 1, "title": course.get("title", f"Step {idx+1}"), "completed": course.get("completed", False)}
            for idx, course in enumerate(required)
        ],
        "percentage_complete": pct,
        "status": "completed" if status_data.get("approval_status") == "approved" else "in_progress",
        "thinkific_url": status_data.get("thinkific_url", "https://abundant.thinkific.com/courses")
    }


@router.get("/portal/legacy-courses")
async def get_portal_courses(request: Request):
    """Get member courses for mobile clients (legacy pathways)."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_abundant_go_live_portal_content()

    courses = await db.member_courses.find(
        {"tenant_id": tenant_id, "user_id": user.get("user_id")},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)

    if courses:
        return {"courses": [serialize_doc(course) for course in courses]}

    pathways = await get_member_pathways_courses(request)
    mapped = []
    for item in pathways.get("courses", [])[:5]:
        mapped.append({
            "id": item.get("course_id"),
            "title": item.get("title"),
            "description": item.get("description"),
            "progress": int(item.get("progress_percent", 0)),
            "completed": item.get("status") == "completed",
            "thinkific_url": "https://abundant.thinkific.com/courses",
            "thumbnail": item.get("cover_image_url")
        })
    return {"courses": mapped}


@router.get("/portal/next-steps/certificate")
async def download_next_steps_certificate(request: Request):
    """Generate and download completion certificate after admin approval."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    journey = await evaluate_member_next_steps_membership(tenant_id, user.get("user_id"))
    if journey.get("approval_status") != "approved":
        raise HTTPException(status_code=403, detail="Certificate available after admin approval")

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "name": 1})
    completed_on = datetime.now(timezone.utc).strftime("%B %d, %Y")
    pdf_bytes = generate_next_steps_certificate_pdf(
        user.get("name", "Member"),
        (tenant or {}).get("name", "Abundant Church"),
        completed_on
    )

    safe_name = (user.get("name", "member").replace(" ", "_")).lower()
    filename = f"abundant-next-steps-certificate-{safe_name}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/portal/pathways/courses")
async def get_member_pathways_courses(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    # Ensure demo data exists for Abundant Church
    await ensure_abundant_pathways_data(tenant_id)

    enrollments = await db.pathways_enrollments.find(
        {"user_id": user.get("user_id"), "tenant_id": tenant_id, "status": {"$ne": "dropped"}},
        {"_id": 0}
    ).to_list(200)

    next_steps = await evaluate_member_next_steps_membership(tenant_id, user.get("user_id"))

    course_ids = [e["course_id"] for e in enrollments]
    if not course_ids:
        return {
            "courses": [],
            "next_steps": {
                "completion_percent": next_steps.get("completion_percent", 0),
                "eligible": next_steps.get("eligible", False),
                "approval_status": next_steps.get("approval_status")
            }
        }

    courses = await db.pathways_courses.find(
        {"id": {"$in": course_ids}, "tenant_id": tenant_id},
        {"_id": 0}
    ).to_list(200)

    lesson_rows = await db.pathways_lessons.aggregate([
        {"$match": {"course_id": {"$in": course_ids}, "tenant_id": tenant_id, "is_published": True}},
        {"$group": {"_id": "$course_id", "count": {"$sum": 1}}}
    ]).to_list(200)
    lesson_counts = {row["_id"]: row["count"] for row in lesson_rows}

    progress_records = await db.pathways_progress.find(
        {"course_id": {"$in": course_ids}, "tenant_id": tenant_id, "user_id": user.get("user_id")},
        {"_id": 0}
    ).to_list(500)

    completed_map = {}
    last_activity = {}
    for record in progress_records:
        if record.get("completed"):
            completed_map[record["course_id"]] = completed_map.get(record["course_id"], 0) + 1
        if record.get("last_watched"):
            last_activity[record["course_id"]] = max(last_activity.get(record["course_id"], ""), record.get("last_watched"))

    course_map = {course["id"]: course for course in courses}
    response = []

    for enrollment in sorted(enrollments, key=lambda e: e.get("assigned_at", ""), reverse=True):
        course = course_map.get(enrollment["course_id"])
        if not course:
            continue
        total_lessons = lesson_counts.get(course["id"], 0)
        completed_lessons = completed_map.get(course["id"], 0)
        progress_percent = round((completed_lessons / total_lessons * 100) if total_lessons else 0, 1)
        response.append({
            **serialize_doc(course),
            "enrollment_status": enrollment.get("status"),
            "progress_percent": progress_percent,
            "completed_lessons": completed_lessons,
            "total_lessons": total_lessons,
            "last_activity": last_activity.get(course["id"])
        })

    return {
        "courses": response,
        "next_steps": {
            "completion_percent": next_steps.get("completion_percent", 0),
            "eligible": next_steps.get("eligible", False),
            "approval_status": next_steps.get("approval_status")
        }
    }


@router.get("/portal/pathways/courses/{course_id}/lessons")
async def get_member_pathways_lessons(request: Request, course_id: str):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    enrollment = await db.pathways_enrollments.find_one(
        {"course_id": course_id, "tenant_id": tenant_id, "user_id": user.get("user_id"), "status": {"$ne": "dropped"}},
        {"_id": 0}
    )
    if not enrollment:
        raise HTTPException(status_code=403, detail="Course not assigned")

    lessons = await db.pathways_lessons.find(
        {"course_id": course_id, "tenant_id": tenant_id, "is_published": True},
        {"_id": 0}
    ).sort("sort_order", 1).to_list(200)

    progress_records = await db.pathways_progress.find(
        {"course_id": course_id, "tenant_id": tenant_id, "user_id": user.get("user_id")},
        {"_id": 0}
    ).to_list(200)
    progress_map = {p["lesson_id"]: p for p in progress_records}

    response = []
    for lesson in lessons:
        progress = progress_map.get(lesson["id"], {})
        response.append({
            **serialize_doc(lesson),
            "progress_percent": progress.get("progress_percent", 0),
            "position_seconds": progress.get("position_seconds", 0),
            "completed": progress.get("completed", False)
        })

    return {"lessons": response}


@router.post("/portal/pathways/progress")
async def update_pathways_progress(request: Request, payload: PathwaysProgressUpdate):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    enrollment = await db.pathways_enrollments.find_one(
        {"course_id": payload.course_id, "tenant_id": tenant_id, "user_id": user.get("user_id"), "status": {"$ne": "dropped"}},
        {"_id": 0}
    )
    if not enrollment:
        raise HTTPException(status_code=403, detail="Course not assigned")

    progress_percent = (payload.position_seconds / payload.duration_seconds * 100) if payload.duration_seconds > 0 else 0
    completed = progress_percent >= 90

    progress_data = {
        "tenant_id": tenant_id,
        "course_id": payload.course_id,
        "lesson_id": payload.lesson_id,
        "user_id": user.get("user_id"),
        "position_seconds": payload.position_seconds,
        "duration_seconds": payload.duration_seconds,
        "progress_percent": round(progress_percent, 1),
        "completed": completed,
        "last_watched": datetime.now(timezone.utc).isoformat()
    }

    existing = await db.pathways_progress.find_one(
        {"lesson_id": payload.lesson_id, "tenant_id": tenant_id, "user_id": user.get("user_id")},
        {"_id": 0}
    )

    if existing:
        await db.pathways_progress.update_one(
            {"id": existing["id"]},
            {"$set": progress_data}
        )
    else:
        progress_data["id"] = str(uuid.uuid4())
        await db.pathways_progress.insert_one(progress_data)

    total_lessons = await db.pathways_lessons.count_documents({"course_id": payload.course_id, "tenant_id": tenant_id, "is_published": True})
    completed_lessons = await db.pathways_progress.count_documents(
        {"course_id": payload.course_id, "tenant_id": tenant_id, "user_id": user.get("user_id"), "completed": True}
    )

    status = "completed" if total_lessons > 0 and completed_lessons >= total_lessons else "in_progress"
    await db.pathways_enrollments.update_one(
        {"id": enrollment["id"]},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    next_steps = await evaluate_member_next_steps_membership(tenant_id, user.get("user_id"))

    return {
        "status": "saved",
        "progress_percent": progress_data["progress_percent"],
        "completed": completed,
        "course_status": status,
        "next_steps": {
            "completion_percent": next_steps.get("completion_percent", 0),
            "eligible": next_steps.get("eligible", False),
            "approval_status": next_steps.get("approval_status")
        }
    }

# ============== MERCH ROUTES ==============


@router.get("/portal/merch/settings")
async def get_portal_merch_settings(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    await ensure_demo_merch_data(tenant_id)
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "merch_embed_url": 1})
    return {"merch_embed_url": tenant.get("merch_embed_url", DEFAULT_MERCH_EMBED_URL) if tenant else DEFAULT_MERCH_EMBED_URL}


@router.get("/portal/merch/products")
async def get_portal_merch_products(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None
):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_demo_merch_data(tenant_id)

    query = {"tenant_id": tenant_id, "is_active": True}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]

    products = await db.merch_products.find(query, {"_id": 0}).sort("is_featured", -1).to_list(200)
    return {"products": [serialize_doc(p) for p in products]}


@router.post("/portal/merch/orders")
async def create_merch_order(request: Request, payload: MerchOrderCreate):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    if not payload.items:
        raise HTTPException(status_code=400, detail="No items in order")

    subtotal = 0
    items = []
    for item in payload.items:
        total_line = item.price * item.quantity
        subtotal += total_line
        items.append(item.model_dump())

    subtotal = round(subtotal, 2)
    order = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "user_id": user.get("user_id"),
        "items": items,
        "subtotal": subtotal,
        "total": subtotal,
        "status": "placed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.merch_orders.insert_one(order)
    return {
        "order": serialize_doc(order),
        "giving_nudge": {
            "show": True,
            "message": "Would you like to add a gift?",
            "subtitle": "Support Abundant Church",
            "suggested_amounts": [5, 10, 20, 100]
        }
    }

# ============== KIDS CHECK-IN ROUTES ==============

@router.get("/portal/kids")
async def get_my_kids(request: Request):
    """Get all children for the current user"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    children = await db.children.find(
        {"tenant_id": tenant_id, "parent_user_id": user_id},
        {"_id": 0}
    ).to_list(50)
    
    return {"children": [serialize_doc(c) for c in children]}


@router.get("/portal/kids/children")
async def get_mobile_children(request: Request):
    """Mobile alias for children list."""
    return await get_my_kids(request)


@router.post("/portal/kids")
async def add_child(request: Request, payload: ChildCreate):
    """Add a new child"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    child = Child(
        tenant_id=tenant_id,
        parent_user_id=user_id,
        name=payload.name,
        birthdate=payload.birthdate,
        allergies=payload.allergies,
        special_needs=payload.special_needs,
        emergency_contact=payload.emergency_contact,
        emergency_phone=payload.emergency_phone
    ).model_dump()
    child["created_at"] = datetime.now(timezone.utc).isoformat()
    child["grade"] = payload.grade
    child["classroom"] = payload.classroom or "Sunday School Adventures"
    child["first_name"] = payload.first_name
    child["last_name"] = payload.last_name
    
    await db.children.insert_one(child)
    return {"message": "Child added", "child": serialize_doc(child)}


@router.post("/portal/kids/children")
async def add_mobile_child(request: Request, payload: ChildCreate):
    """Mobile alias for adding child profile."""
    return await add_child(request, payload)


@router.delete("/portal/kids/{child_id}")
async def delete_child(request: Request, child_id: str):
    """Delete a child"""
    user = await get_current_member_user(request)
    user_id = user.get("user_id")
    
    child = await db.children.find_one({"id": child_id}, {"_id": 0})
    if not child or child.get("parent_user_id") != user_id:
        raise HTTPException(status_code=404, detail="Child not found")
    
    await db.children.delete_one({"id": child_id})
    return {"message": "Child deleted"}


@router.post("/portal/kids/{child_id}/checkin")
async def checkin_child(request: Request, child_id: str, payload: dict = None):
    """Check in a child for Sunday School. Supports idempotency key."""
    # Idempotency check
    idem_key = request.headers.get("x-idempotency-key")
    if idem_key:
        cached = await check_idempotency(f"checkin:{idem_key}")
        if cached:
            return cached
    
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    child = await db.children.find_one({"id": child_id, "parent_user_id": user_id}, {"_id": 0})
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    existing = await db.checkins.find_one({"child_id": child_id, "status": "checked_in"}, {"_id": 0})
    if existing:
        # Return existing check-in data instead of error (idempotent)
        result = {"message": "Child is already checked in", "pickup_code": existing.get("pickup_code"), "checkin_time": existing.get("checked_in_at"), "status": "checked_in", "checkin": serialize_doc(existing), "sms_sent": False}
        return result
    
    pickup_code = generate_pickup_code()
    parent = await db.users.find_one({"user_id": user_id}, {"_id": 0, "name": 1, "phone": 1})
    parent_name = parent.get("name", "Parent") if parent else "Parent"
    parent_phone = parent.get("phone", "") if parent else ""
    
    checkin = Checkin(
        tenant_id=tenant_id, child_id=child_id, child_name=child.get("name"),
        parent_user_id=user_id, parent_name=parent_name, parent_phone=parent_phone,
        pickup_code=pickup_code, classroom=payload.get("classroom") if payload else "Sunday School",
        status="checked_in"
    ).model_dump()
    checkin["checked_in_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.checkins.insert_one(checkin)
    await audit_log("kids_checkin", "checkin", checkin.get("id", ""), tenant_id, user_id, parent_name, request=request)
    
    sms_message = f"Thanks for bringing {child.get('name')} to Sunday School! Pickup code: {pickup_code}."
    
    result = {
        "message": "Child checked in successfully",
        "pickup_code": pickup_code,
        "checkin_time": checkin["checked_in_at"],
        "status": "checked_in",
        "checkin": serialize_doc(checkin),
        "sms_sent": True,
        "sms_message": sms_message,
        "nudge": {
            "show_giving": True,
            "show_cafe": True,
            "give_amounts": [10, 25, 50, 100],
            "message": "The kids are in — support your church today?"
        }
    }
    
    if idem_key:
        await store_idempotency(f"checkin:{idem_key}", result)
    
    return result


@router.post("/portal/kids/checkin")
async def checkin_child_mobile(request: Request, payload: KidsCheckinRequest):
    """Mobile-friendly check-in endpoint using child_id in request body."""
    checkin_payload = {"classroom": payload.classroom or "Sunday School"}
    return await checkin_child(request, payload.child_id, checkin_payload)


@router.get("/portal/kids/checkins/active")
async def get_active_checkins(request: Request):
    """Get all active check-ins for the current user's children"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    checkins = await db.checkins.find({
        "tenant_id": tenant_id,
        "parent_user_id": user_id,
        "status": "checked_in"
    }, {"_id": 0}).to_list(50)
    
    return {"checkins": [serialize_doc(c) for c in checkins]}


@router.get("/portal/kids/checkin/history")
async def get_portal_kids_checkin_history(request: Request, limit: int = 100):
    """Get historical check-ins for the current parent's children."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")

    checkins = await db.checkins.find(
        {
            "tenant_id": tenant_id,
            "parent_user_id": user_id
        },
        {"_id": 0}
    ).sort("checked_in_at", -1).limit(limit).to_list(limit)

    return {
        "checkins": [serialize_doc(c) for c in checkins],
        "total": len(checkins)
    }

# Admin routes for Kids Check-in
@router.get("/portal/cafe/settings")
async def get_portal_cafe_settings(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    await ensure_demo_cafe_data(tenant_id)
    settings = await db.cafe_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
    return {"settings": serialize_doc(settings) if settings else None}


@router.get("/portal/cafe/items")
async def get_portal_cafe_items(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None
):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_demo_cafe_data(tenant_id)

    query = {"tenant_id": tenant_id, "is_active": True}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]

    items = await db.cafe_items.find(query, {"_id": 0}).sort("is_featured", -1).to_list(200)
    return {"items": [serialize_doc(item) for item in items]}


@router.get("/portal/cafe/menu")
async def get_portal_cafe_menu(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None
):
    """Mobile alias for cafe items list."""
    return await get_portal_cafe_items(request, search=search, category=category)


@router.post("/portal/cafe/orders")
async def create_portal_cafe_order(request: Request, payload: CafeOrderCreate):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    if not payload.items:
        raise HTTPException(status_code=400, detail="No items in order")
    if not payload.pickup_time:
        raise HTTPException(status_code=400, detail="Pickup time is required")

    items = []
    total = 0
    for item in payload.items:
        total += item.price * item.quantity
        items.append(item.model_dump())

    total = round(total, 2)
    order = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "user_id": user.get("user_id"),
        "items": items,
        "pickup_time": payload.pickup_time,
        "notes": payload.notes or "",
        "total": total,
        "status": "placed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.cafe_orders.insert_one(order)
    return {
        "order": serialize_doc(order),
        "giving_nudge": {
            "show": True,
            "message": "Would you like to add a gift?",
            "subtitle": "Support Abundant Church",
            "suggested_amounts": [5, 10, 20, 100]
        }
    }


@router.post("/portal/cafe/order")
async def create_mobile_cafe_order(request: Request, payload: CafeOrderCreate):
    """Mobile alias for placing cafe order."""
    return await create_portal_cafe_order(request, payload)

# ============== PASTOR MEETINGS ROUTES ==============


@router.get("/portal/meetings/slots")
async def get_portal_meeting_slots(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    await ensure_demo_meetings_data(tenant_id)
    slots = await db.pastor_meeting_slots.find({"tenant_id": tenant_id, "status": "open"}, {"_id": 0}).sort("start_time", 1).to_list(200)
    return {"slots": [serialize_doc(slot) for slot in slots]}


@router.post("/portal/meetings/book")
async def book_portal_meeting(request: Request, payload: PastorMeetingBooking):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    slot = await db.pastor_meeting_slots.find_one({"id": payload.slot_id, "tenant_id": tenant_id}, {"_id": 0})
    if not slot or slot.get("status") != "open":
        raise HTTPException(status_code=400, detail="Slot is no longer available")

    await db.pastor_meeting_slots.update_one({"id": slot["id"]}, {"$set": {"status": "booked", "updated_at": datetime.now(timezone.utc).isoformat()}})

    meeting = PastorMeeting(
        tenant_id=tenant_id,
        slot_id=slot["id"],
        user_id=user.get("user_id"),
        member_name=user.get("name"),
        member_email=user.get("email"),
        topic=payload.topic,
        notes=payload.notes,
        status="scheduled"
    ).model_dump()
    meeting["created_at"] = datetime.now(timezone.utc).isoformat()
    meeting["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.pastor_meetings.insert_one(meeting)
    notifications = await notify_meeting_event("meeting_scheduled", meeting)

    return {"meeting": serialize_doc(meeting), "notifications": notifications}


@router.get("/portal/meetings")
async def get_portal_meetings(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    meetings = await db.pastor_meetings.find({"tenant_id": tenant_id, "user_id": user.get("user_id")}, {"_id": 0}).sort("created_at", -1).to_list(100)
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


@router.post("/portal/notes")
async def create_leadership_note(request: Request, payload: LeadershipNoteCreate):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    if not payload.subject or not payload.subject.strip():
        raise HTTPException(status_code=400, detail="Subject is required")
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    note = LeadershipNote(
        tenant_id=tenant_id,
        user_id=user.get("user_id"),
        subject=payload.subject.strip(),
        message=payload.message.strip(),
        category=payload.category,
        status="new",
        member_name=user.get("name"),
        member_email=user.get("email")
    ).model_dump()
    note["created_at"] = datetime.now(timezone.utc).isoformat()

    await db.leadership_notes.insert_one(note)
    return {"message": "Note submitted", "note": serialize_doc(note)}


@router.post("/portal/video-notes")
async def create_video_note(request: Request, payload: VideoNoteCreate):
    """Create a note for a video"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    if not payload.content or not payload.content.strip():
        raise HTTPException(status_code=400, detail="Note content is required")
    
    # Get video title for reference
    video = await db.media_videos.find_one({"id": payload.video_id}, {"_id": 0, "title": 1})
    video_title = video.get("title") if video else None
    
    note = VideoNote(
        tenant_id=tenant_id,
        user_id=user_id,
        video_id=payload.video_id,
        content=payload.content.strip(),
        timestamp=payload.timestamp,
        is_public=payload.is_public,
        author_name=user.get("name"),
        video_title=video_title
    ).model_dump()
    note["created_at"] = datetime.now(timezone.utc).isoformat()
    note["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.video_notes.insert_one(note)
    return {"message": "Note created", "note": serialize_doc(note)}


@router.get("/portal/video-notes")
async def get_my_video_notes(
    request: Request,
    video_id: Optional[str] = None,
    limit: int = 100
):
    """Get current user's notes, optionally filtered by video"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    query = {"tenant_id": tenant_id, "user_id": user_id}
    if video_id:
        query["video_id"] = video_id
    
    notes = await db.video_notes.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"notes": [serialize_doc(n) for n in notes]}


@router.get("/portal/video-notes/video/{video_id}")
async def get_video_notes_for_video(request: Request, video_id: str):
    """Get all notes for a specific video (own notes + shared notes)"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    # Get own notes + notes shared with me + public notes from same tenant
    query = {
        "tenant_id": tenant_id,
        "video_id": video_id,
        "$or": [
            {"user_id": user_id},  # Own notes
            {"shared_with": user_id},  # Shared with me
            {"is_public": True}  # Public notes from same church
        ]
    }
    
    notes = await db.video_notes.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    
    # Mark which notes are own vs shared
    result = []
    for note in notes:
        note_data = serialize_doc(note)
        note_data["is_own"] = note.get("user_id") == user_id
        note_data["is_shared_with_me"] = user_id in (note.get("shared_with") or [])
        result.append(note_data)
    
    return {"notes": result}


@router.get("/portal/video-notes/shared")
async def get_notes_shared_with_me(request: Request, limit: int = 100):
    """Get all notes shared with the current user"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    query = {
        "tenant_id": tenant_id,
        "user_id": {"$ne": user_id},  # Not my own notes
        "$or": [
            {"shared_with": user_id},
            {"is_public": True}
        ]
    }
    
    notes = await db.video_notes.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"notes": [serialize_doc(n) for n in notes]}


@router.put("/portal/video-notes/{note_id}")
async def update_video_note(request: Request, note_id: str, payload: VideoNoteUpdate):
    """Update a note (only own notes)"""
    user = await get_current_member_user(request)
    user_id = user.get("user_id")
    
    # Find note and verify ownership
    note = await db.video_notes.find_one({"id": note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Cannot edit someone else's note")
    
    update_data = {}
    if payload.content is not None:
        update_data["content"] = payload.content.strip()
    if payload.timestamp is not None:
        update_data["timestamp"] = payload.timestamp
    if payload.is_public is not None:
        update_data["is_public"] = payload.is_public
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.video_notes.update_one({"id": note_id}, {"$set": update_data})
    
    updated_note = await db.video_notes.find_one({"id": note_id}, {"_id": 0})
    return {"message": "Note updated", "note": serialize_doc(updated_note)}


@router.delete("/portal/video-notes/{note_id}")
async def delete_video_note(request: Request, note_id: str):
    """Delete a note (only own notes)"""
    user = await get_current_member_user(request)
    user_id = user.get("user_id")
    
    note = await db.video_notes.find_one({"id": note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Cannot delete someone else's note")
    
    await db.video_notes.delete_one({"id": note_id})
    return {"message": "Note deleted"}


@router.post("/portal/video-notes/{note_id}/share")
async def share_video_note(request: Request, note_id: str, payload: VideoNoteShare):
    """Share a note with specific users or the entire church"""
    user = await get_current_member_user(request)
    user_id = user.get("user_id")
    tenant_id = user.get("tenant_id")
    
    note = await db.video_notes.find_one({"id": note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Cannot share someone else's note")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    # Add users to share list
    if payload.user_ids:
        # Verify users exist and are in same tenant
        valid_users = await db.users.find(
            {"user_id": {"$in": payload.user_ids}, "tenant_id": tenant_id},
            {"_id": 0, "user_id": 1}
        ).to_list(100)
        valid_user_ids = [u["user_id"] for u in valid_users]
        
        # Merge with existing shared_with list
        existing_shared = set(note.get("shared_with") or [])
        existing_shared.update(valid_user_ids)
        update_data["shared_with"] = list(existing_shared)
    
    # Update public status if provided
    if payload.is_public is not None:
        update_data["is_public"] = payload.is_public
    
    await db.video_notes.update_one({"id": note_id}, {"$set": update_data})
    
    updated_note = await db.video_notes.find_one({"id": note_id}, {"_id": 0})
    return {"message": "Note shared", "note": serialize_doc(updated_note)}


@router.get("/portal/church-members")
async def get_church_members_for_sharing(request: Request, search: Optional[str] = None):
    """Get list of church members for sharing notes (excluding self)"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    query = {"tenant_id": tenant_id, "user_id": {"$ne": user_id}}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    members = await db.users.find(
        query,
        {"_id": 0, "user_id": 1, "name": 1, "email": 1}
    ).limit(50).to_list(50)
    
    return {"members": members}

# ============== SOLOMONPAY PAYMENT METHOD ROUTES ==============


@router.get("/portal/media/videos")
async def get_portal_videos(request: Request, category: Optional[str] = None, limit: int = 50):
    """Get published videos for member portal"""
    user = await get_current_member_user(request)
    
    tenant_id = user.get("tenant_id")
    
    query = {"is_published": True, "tenant_id": tenant_id}
    if category and category != "all":
        query["category_id"] = category
    
    videos = await db.media_videos.find(
        query, {"_id": 0}
    ).sort([("is_featured", -1), ("created_at", -1)]).limit(limit).to_list(limit)
    
    # Get categories for this tenant
    cat_query = {"tenant_id": tenant_id} if tenant_id else {}
    categories = await db.media_categories.find(cat_query, {"_id": 0}).sort("sort_order", 1).to_list(20)
    
    return {
        "videos": videos,
        "categories": categories,
        "total": len(videos)
    }


@router.get("/portal/media/sermons")
async def get_portal_sermons(request: Request, limit: int = 50):
    """Sermon-focused feed for mobile/web clients."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    sermons = await db.media_videos.find(
        {
            "tenant_id": tenant_id,
            "$or": [
                {"is_published": True},
                {"published": True}
            ]
        },
        {"_id": 0}
    ).sort("published_at", -1).limit(limit).to_list(limit)

    return {
        "videos": [serialize_doc(v) for v in sermons],
        "total": len(sermons)
    }


@router.get("/portal/bootstrap")
async def get_portal_bootstrap(request: Request):
    """Tiny mobile bootstrap endpoint to reduce initial round-trips."""
    user = await get_current_member_user(request)

    merch = await get_portal_merch_products(request)
    cafe = await get_portal_cafe_menu(request)
    children = await get_mobile_children(request)
    sermons = await get_portal_sermons(request, limit=10)

    return {
        "user": {
            "user_id": user.get("user_id"),
            "name": user.get("name"),
            "role": user.get("role"),
            "tenant_id": user.get("tenant_id") or DEFAULT_TENANT_ID
        },
        "merch_products": merch.get("products", []),
        "cafe_menu": cafe.get("items", []),
        "kids_children": children.get("children", []),
        "sermons": sermons.get("videos", []),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/portal/media/featured")
async def get_featured_video(request: Request):
    """Get the featured/hero video for the portal"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    tenant_id = user.get("tenant_id") if user else None
    
    query = {"is_published": True, "is_featured": True, "tenant_id": tenant_id}
    
    featured = await db.media_videos.find_one(query, {"_id": 0})
    
    if not featured:
        # Fall back to most recent video
        query = {"is_published": True, "tenant_id": tenant_id}
        featured = await db.media_videos.find_one(
            query, {"_id": 0}, sort=[("created_at", -1)]
        )
    
    return {"video": featured}

# ============== ADMIN GROUP MANAGEMENT API ==============


@router.post("/portal/groups/{group_id}/join")
async def request_to_join_group(request: Request, group_id: str):
    """Member requests to join a group"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    tenant_id = user.get("tenant_id")
    
    # Check group exists and is open
    group = await db.groups.find_one({"id": group_id, "tenant_id": tenant_id, "is_active": True}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if not group.get("is_open", True):
        raise HTTPException(status_code=400, detail="This group is not accepting new members")
    
    enrollment_type = group.get("enrollment_type", "open")
    
    # Check capacity
    if group.get("capacity"):
        current_count = await db.group_members.count_documents({"group_id": group_id, "is_active": True})
        if current_count >= group["capacity"]:
            raise HTTPException(status_code=400, detail="This group is full")
    
    # Get person ID from user
    person = await db.people.find_one({"email": user["email"], "tenant_id": tenant_id}, {"_id": 0})
    if not person:
        raise HTTPException(status_code=404, detail="Member profile not found")
    
    # Check if already a member
    existing = await db.group_members.find_one({
        "group_id": group_id,
        "person_id": person["id"],
        "is_active": True
    })
    if existing:
        raise HTTPException(status_code=400, detail="You are already a member of this group")
    
    # Check for pending join request
    pending_request = await db.group_join_requests.find_one({
        "group_id": group_id,
        "person_id": person["id"],
        "status": "pending"
    })
    if pending_request:
        raise HTTPException(status_code=400, detail="You already have a pending join request")
    
    # Handle request_to_join enrollment
    if enrollment_type == "request_to_join":
        join_request = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "group_id": group_id,
            "person_id": person["id"],
            "person_name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
            "person_email": person.get("email", ""),
            "status": "pending",
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.group_join_requests.insert_one(join_request)
        return {"message": f"Your request to join {group['name']} has been submitted for approval", "status": "pending"}
    
    # Add to group directly for open enrollment
    new_membership = GroupMember(
        tenant_id=tenant_id,
        group_id=group_id,
        person_id=person["id"],
        role="member"
    )
    
    await db.group_members.insert_one(new_membership.model_dump())
    
    # Update group member count
    await db.groups.update_one({"id": group_id}, {"$inc": {"member_count": 1}})
    
    logger.info("group_member_joined", extra={"tenant_id": user.get("tenant_id"), "user_id": user.get("user_id"), "group_id": group["id"]})
    
    return {"message": f"You have joined {group['name']}!"}



# ============== GROUP NOTIFICATIONS & Q&A ==============

@router.post("/portal/groups/{group_id}/notify")
async def subscribe_group_notification(request: Request, group_id: str):
    """Member subscribes to be notified when a spot opens in a full/closed group."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    person = await db.people.find_one({"email": user["email"], "tenant_id": tenant_id}, {"_id": 0})
    if not person:
        raise HTTPException(status_code=404, detail="Member not found")

    group = await db.groups.find_one({"id": group_id, "tenant_id": tenant_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    existing = await db.group_notifications.find_one({
        "group_id": group_id, "person_id": person["id"], "status": "waiting"
    })
    if existing:
        return {"message": "You're already on the notification list"}

    await db.group_notifications.insert_one({
        "id": f"gn_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "group_id": group_id,
        "group_name": group.get("name"),
        "person_id": person["id"],
        "person_name": f"{person.get('first_name','')} {person.get('last_name','')}".strip(),
        "person_email": person.get("email"),
        "status": "waiting",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"message": f"You'll be notified when a spot opens in {group.get('name')}"}


@router.get("/portal/groups/{group_id}/detail")
async def get_group_detail(request: Request, group_id: str):
    """Get detailed group info for member view (no member names for privacy)."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    group = await db.groups.find_one({"id": group_id, "tenant_id": tenant_id, "is_active": True}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    member_count = await db.group_members.count_documents({"group_id": group_id, "is_active": True})
    spots_available = max(0, (group.get("capacity", 0) - member_count)) if group.get("capacity") else None

    return {
        "id": group["id"],
        "name": group.get("name"),
        "description": group.get("description"),
        "group_type": group.get("group_type", "Small Group"),
        "leader_name": f"{group.get('leader', {}).get('first_name', '')} {group.get('leader', {}).get('last_name', '')}".strip() if group.get("leader") else None,
        "location": group.get("location"),
        "address": group.get("address", group.get("location")),
        "meeting_day": group.get("meeting_day"),
        "meeting_time": group.get("meeting_time"),
        "start_date": group.get("start_date"),
        "end_date": group.get("end_date"),
        "capacity": group.get("capacity"),
        "member_count": member_count,
        "spots_available": spots_available,
        "is_open": group.get("is_open", True),
        "is_full": spots_available == 0 if spots_available is not None else False,
    }


@router.post("/portal/groups/{group_id}/questions")
async def submit_group_question(request: Request, group_id: str):
    """Member submits a question to the group leader."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    question_text = body.get("question", "").strip()
    if not question_text:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    person = await db.people.find_one({"email": user["email"], "tenant_id": tenant_id}, {"_id": 0})
    if not person:
        raise HTTPException(status_code=404, detail="Member not found")

    group = await db.groups.find_one({"id": group_id, "tenant_id": tenant_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    question = {
        "id": f"gq_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "group_id": group_id,
        "group_name": group.get("name"),
        "person_id": person["id"],
        "person_name": f"{person.get('first_name','')} {person.get('last_name','')}".strip(),
        "person_email": person.get("email"),
        "question": question_text,
        "answer": None,
        "answered_by": None,
        "answered_at": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.group_questions.insert_one(question)
    return {"message": "Question submitted. The group leader will respond soon.", "question_id": question["id"]}


@router.get("/portal/groups/{group_id}/questions")
async def get_group_questions(request: Request, group_id: str):
    """Get Q&A for a group (member sees their own questions + answered ones)."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    person = await db.people.find_one({"email": user["email"], "tenant_id": tenant_id}, {"_id": 0})
    person_id = person["id"] if person else None

    questions = await db.group_questions.find(
        {"group_id": group_id, "tenant_id": tenant_id,
         "$or": [{"person_id": person_id}, {"status": "answered"}]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"questions": questions}


# ============== ADMIN GROUP MEMBER MANAGEMENT ==============


@router.get("/portal/groups/{group_id}/messages")
async def get_portal_group_messages(request: Request, group_id: str, limit: int = 50):
    """Portal: Get group messages for member"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    tenant_id = user.get("tenant_id")
    messages = await db.group_messages.find(
        {"group_id": group_id, "tenant_id": tenant_id}, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    messages.reverse()
    return {"messages": messages}


@router.post("/portal/groups/{group_id}/messages")
async def send_portal_group_message(request: Request, group_id: str, payload: dict):
    """Portal: Send message in group chat"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    tenant_id = user.get("tenant_id")
    person = await db.people.find_one({"email": user["email"], "tenant_id": tenant_id}, {"_id": 0})
    # Verify membership
    membership = await db.group_members.find_one({"group_id": group_id, "person_id": person["id"], "is_active": True})
    if not membership:
        raise HTTPException(status_code=403, detail="You must be a member of this group to send messages")
    message = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "group_id": group_id,
        "sender_id": user.get("user_id"),
        "sender_name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
        "content": payload.get("content", ""),
        "message_type": "text",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.group_messages.insert_one(message)
    return {"message": {k: v for k, v in message.items() if k != "_id"}}

# Group messaging routes extracted to routes/messaging.py

# ============== PHASE 5: REGISTRATIONS MODULE ==============


@router.get("/portal/my-groups")
async def get_my_groups(request: Request):
    """Get groups the current member belongs to"""
    user = await get_current_member_user(request)
    
    tenant_id = user.get("tenant_id")
    
    # Find person record
    person = await db.people.find_one({"email": user["email"], "tenant_id": tenant_id}, {"_id": 0})
    if not person:
        return {"groups": []}
    
    # Get group memberships
    memberships = await db.group_members.find(
        {"person_id": person["id"], "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    # Get group details
    groups = []
    for m in memberships:
        group = await db.groups.find_one({"id": m["group_id"]}, {"_id": 0})
        if group:
            groups.append({
                **serialize_doc(group),
                "joined_at": m.get("joined_at"),
                "role": m.get("role", "member")
            })
    
    return {"groups": groups}


@router.get("/portal/groups/mine")
async def get_mobile_my_groups(request: Request):
    """Mobile alias for member groups."""
    return await get_my_groups(request)


@router.get("/portal/my-events")
async def get_my_registered_events(request: Request):
    """Get events the current member is registered for"""
    user = await get_current_member_user(request)
    
    # Get registrations
    registrations = await db.event_registrations.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).to_list(100)
    
    # Get event details
    events = []
    for r in registrations:
        event = await db.events.find_one({"id": r["event_id"]}, {"_id": 0})
        if event:
            events.append({
                **serialize_doc(event),
                "registration_id": r["id"],
                "registered_at": r.get("registered_at")
            })
    
    return {"events": events}


@router.get("/portal/events/registered")
async def get_mobile_registered_events(request: Request):
    """Mobile alias for registered events."""
    return await get_my_registered_events(request)


@router.delete("/portal/groups/{group_id}/leave")
async def leave_group(request: Request, group_id: str):
    """Member leaves a group"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    tenant_id = user.get("tenant_id")
    
    # Find person record
    person = await db.people.find_one({"email": user["email"], "tenant_id": tenant_id}, {"_id": 0})
    if not person:
        raise HTTPException(status_code=404, detail="Member profile not found")
    
    # Remove from group
    result = await db.group_members.delete_one({
        "group_id": group_id,
        "person_id": person["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="You are not a member of this group")
    
    # Update count
    await db.groups.update_one({"id": group_id}, {"$inc": {"member_count": -1}})
    
    return {"message": "You have left the group"}

# ============== ADMIN EVENT MANAGEMENT API ==============


@router.post("/portal/events/{event_id}/register")
async def register_for_event(request: Request, event_id: str):
    """
    Member registers for an event — handles both free and paid events.
    For paid events: processes payment via Solomon Pay before confirming.
    Mobile-optimised: returns full receipt data for confirmation screen.
    """
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    tenant_id = user.get("tenant_id")

    try:
        body = await request.json()
    except Exception:
        body = {}
    tier_id = body.get("tier_id", "general")
    payment_method_id = body.get("payment_method_id")
    cover_fee = body.get("cover_fee", False)

    # Get event
    event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Already registered?
    existing = await db.event_registrations.find_one({"event_id": event_id, "user_id": user["user_id"]})
    if existing:
        raise HTTPException(status_code=400, detail="You are already registered for this event")

    # Capacity check
    if event.get("capacity"):
        current_count = await db.event_registrations.count_documents({"event_id": event_id, "status": {"$ne": "waitlisted"}})
        if current_count >= event["capacity"]:
            entry = {"id": str(uuid.uuid4()), "tenant_id": tenant_id, "event_id": event_id,
                     "user_id": user["user_id"], "user_name": user.get("name",""), "user_email": user.get("email",""),
                     "status": "waitlisted", "registered_at": datetime.now(timezone.utc).isoformat()}
            await db.event_registrations.insert_one(entry)
            return {"message": f"Event is full — you're on the waitlist for {event['name']}!", "status": "waitlisted"}

    # Resolve selected tier
    tier_price = 0.0
    tier_name = "General Admission"
    tiers = event.get("ticket_tiers", [])
    selected_tier = next((t for t in tiers if t.get("id") == tier_id), tiers[0] if tiers else None)
    if selected_tier:
        tier_price = float(selected_tier.get("price", 0))
        tier_name = selected_tier.get("name", "General Admission")

    event_price = float(event.get("price", 0))
    amount = tier_price if tier_price > 0 else event_price

    # ── PAYMENT (if event has a fee) ─────────────────────────────────────────
    transaction_id = None
    payment_receipt = None
    if amount > 0:
        # Find payment method
        pm = None
        if payment_method_id:
            pm = await db.payment_methods.find_one({"id": payment_method_id, "user_id": user["user_id"]}, {"_id": 0})
        if not pm:
            pm = await db.payment_methods.find_one({"user_id": user["user_id"], "is_active": True, "is_default": True}, {"_id": 0})
        if not pm:
            pm = await db.payment_methods.find_one({"user_id": user["user_id"], "is_active": True}, {"_id": 0})
        if not pm:
            raise HTTPException(status_code=400, detail="No payment method on file. Please add a card first.")

        token = pm.get("token") or pm.get("solomonpay_token") or f"tok_event_{uuid.uuid4().hex[:8]}"
        fee_amount = round(amount * 0.019 + 0.30, 2)
        total_charged = amount + (fee_amount if cover_fee else 0)

        # Process via Solomon Pay adapter
        try:
            from services.processor_adapter import ACTIVE_ADAPTER, ChargeStatus
            result = await ACTIVE_ADAPTER.charge_card(
                token=token, amount_cents=int(total_charged * 100),
                description=f"Event registration: {event['name']} — {tier_name}",
                metadata={"tenant_id": tenant_id, "event_id": event_id, "user_id": user["user_id"]}
            )
            if result.status != ChargeStatus.SUCCESS:
                raise HTTPException(status_code=402, detail=f"Payment failed: {result.message}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error("event_payment_failed", extra={"tenant_id": tenant_id, "event_id": event_id, "user_id": user["user_id"], "exc_type": type(e).__name__})
            raise HTTPException(status_code=402, detail="Payment could not be processed. Please check your card.")

        # Record transaction
        transaction_id = f"sp_evt_{uuid.uuid4().hex[:12]}"
        await db.solomonpay_transactions.insert_one({
            "id": transaction_id, "tenant_id": tenant_id,
            "type": "event_registration", "amount": amount,
            "fee_amount": fee_amount, "net_amount": round(amount - fee_amount, 2),
            "status": "completed", "payment_method_type": "card",
            "payment_method_last_four": pm.get("card_last_four",""),
            "card_brand": pm.get("card_brand",""),
            "donor_person_id": user["user_id"],
            "event_id": event_id, "event_name": event["name"],
            "created_at": datetime.now(timezone.utc), "completed_at": datetime.now(timezone.utc),
        })
        payment_receipt = {
            "amount_charged": round(total_charged, 2),
            "ticket_price": amount,
            "processing_fee": fee_amount if cover_fee else 0,
            "card_brand": pm.get("card_brand","Visa"),
            "card_last_four": pm.get("card_last_four",""),
            "transaction_id": transaction_id,
        }

    # ── CREATE REGISTRATION ──────────────────────────────────────────────────
    registration = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "event_id": event_id,
        "event_name": event["name"],
        "user_id": user["user_id"],
        "user_name": user.get("name", ""),
        "user_email": user.get("email", ""),
        "tier_id": tier_id,
        "tier_name": tier_name,
        "amount_paid": amount,
        "transaction_id": transaction_id,
        "status": "confirmed",
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.event_registrations.insert_one(registration)
    await db.events.update_one({"id": event_id}, {"$inc": {"registration_count": 1}})

    logger.info("event_registered", extra={"tenant_id": tenant_id, "event_id": event_id, "user_id": user["user_id"], "amount": amount})

    # Push notification
    try:
        msg = f"You're in! See you at {event['name']}."
        if amount > 0:
            msg = f"Payment confirmed ${amount:.0f}. See you at {event['name']}!"
        await send_push_notification(user["user_id"], tenant_id, "You're Registered!", msg, "/portal/events")
    except Exception:
        pass

    return {
        "status": "confirmed",
        "message": f"You're in! See you at {event['name']}.",
        "registration_id": registration["id"],
        "event": {"id": event_id, "name": event["name"], "date": event.get("event_date"), "time": event.get("start_time"), "location": event.get("location","")},
        "tier": {"name": tier_name, "price": amount},
        "payment": payment_receipt,
        "is_paid": amount > 0,
    }


@router.delete("/portal/events/{event_id}/register")
async def cancel_event_registration(request: Request, event_id: str):
    """Member cancels their event registration"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    result = await db.event_registrations.delete_one({
        "event_id": event_id,
        "user_id": user["user_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    # Update event registration count
    await db.events.update_one({"id": event_id}, {"$inc": {"registration_count": -1}})
    
    return {"message": "Registration cancelled"}


@router.get("/portal/volunteer/schedule")
async def get_my_volunteer_schedule(request: Request):
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    entries = await db.volunteer_schedule.find({"user_id": user["user_id"], "date": {"$gte": datetime.now(timezone.utc).strftime("%Y-%m-%d")}}, {"_id": 0}).sort("date", 1).to_list(50)
    return {"schedule": entries}


# ============== PHASE 3: SONG LIBRARY ==============


@router.post("/portal/volunteer/blockout-dates")
async def create_my_blockout_date(request: Request, payload: dict):
    """Members can set their own blockout dates"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    blockout = {
        "id": str(uuid.uuid4()),
        "tenant_id": user.get("tenant_id"),
        "user_id": user["user_id"],
        "user_name": user.get("name", ""),
        "start_date": payload.get("start_date"),
        "end_date": payload.get("end_date", payload.get("start_date")),
        "reason": payload.get("reason", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.blockout_dates.insert_one(blockout)
    return {"blockout": {k: v for k, v in blockout.items() if k != "_id"}}

# ============== PHASE 3: MUSIC STAND ==============


@router.get("/portal/directory")
async def get_member_directory(request: Request, search: str = None, group: str = None):
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)

    query = {"tenant_id": tenant_id}
    members = await db.people.find(query, {"_id": 0, "name": 1, "first_name": 1, "last_name": 1, "email": 1, "phone": 1, "membership_status": 1, "groups": 1, "directory_visible": 1, "share_email": 1, "share_phone": 1, "user_id": 1}).to_list(2000)

    directory = []
    for m in members:
        visible = m.get("directory_visible", True)
        if not visible:
            continue
        display_name = m.get("name", "") or f"{m.get('first_name', '')} {m.get('last_name', '')}".strip()
        if not display_name:
            continue
        entry = {
            "name": display_name,
            "avatar_initials": "".join(w[0].upper() for w in display_name.split()[:2]),
            "groups": m.get("groups", []),
            "membership_status": m.get("membership_status", "visitor"),
        }
        if m.get("share_email", True):
            entry["email"] = m.get("email", "")
        if m.get("share_phone", False):
            entry["phone"] = m.get("phone", "")
        directory.append(entry)

    if search:
        search_lower = search.lower()
        directory = [d for d in directory if search_lower in d.get("name", "").lower()]
    if group:
        directory = [d for d in directory if group in [g.get("name", "") if isinstance(g, dict) else g for g in d.get("groups", [])]]

    return {"members": directory, "total": len(directory)}


# ============== CHURCH BRANDING SETTINGS ==============


@router.get("/portal/service-mode")
async def get_service_mode_status(request: Request):
    """Get current service mode status for the homepage"""
    user = await get_current_portal_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    now = datetime.now(timezone.utc)
    today = now.date()
    current_day = today.strftime("%A")  # Sunday, Monday, etc.
    current_time = now.time()
    
    # Check if today is a service day (typically Sunday or Wednesday)
    service_days = ["Sunday", "Wednesday"]
    is_service_day = current_day in service_days
    
    # Define service times
    services = [
        {"name": "Sunday 9AM", "day": "Sunday", "start": "09:00", "end": "10:30"},
        {"name": "Sunday 11AM", "day": "Sunday", "start": "11:00", "end": "12:30"},
        {"name": "Wednesday Night", "day": "Wednesday", "start": "19:00", "end": "20:30"},
    ]
    
    current_service = None
    next_service = None
    is_service_time = False
    
    for svc in services:
        if svc["day"] == current_day:
            start_time = datetime.strptime(svc["start"], "%H:%M").time()
            end_time = datetime.strptime(svc["end"], "%H:%M").time()
            
            # Allow check-in 30 minutes before service
            early_start = (datetime.combine(today, start_time) - timedelta(minutes=30)).time()
            
            if early_start <= current_time <= end_time:
                is_service_time = True
                current_service = svc
                break
            elif current_time < start_time:
                if not next_service:
                    next_service = svc
    
    # Get user's check-in status for today
    check_in_status = None
    today_checkin = await db.member_checkins.find_one({
        "tenant_id": tenant_id,
        "user_id": user_id,
        "service_date": today.isoformat()
    }, {"_id": 0})
    
    if today_checkin:
        check_in_status = today_checkin.get("check_in_type")
    
    # Get attendance streak
    streak_data = await calculate_attendance_streak(tenant_id, user_id)
    
    return {
        "is_service_day": is_service_day,
        "is_service_time": is_service_time,
        "current_service": current_service,
        "next_service": next_service,
        "attendance_streak": streak_data["current_streak"],
        "check_in_status": check_in_status,
        "today": today.isoformat(),
        "current_day": current_day
    }


@router.post("/portal/service-checkin")
async def check_in_to_service(
    request: Request,
    check_in_type: str = "in_person"
):
    """Check in to current service (in-person or online)"""
    user = await get_current_portal_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Check if already checked in today
    existing = await db.member_checkins.find_one({
        "tenant_id": tenant_id,
        "user_id": user_id,
        "service_date": today
    })
    
    if existing:
        return {"message": "Already checked in today", "check_in_type": existing.get("check_in_type")}
    
    # Create check-in
    checkin = MemberCheckIn(
        tenant_id=tenant_id,
        user_id=user_id,
        check_in_type=check_in_type,
        service_date=today
    )
    
    await db.member_checkins.insert_one(checkin.model_dump())
    
    # Calculate new streak
    streak_data = await calculate_attendance_streak(tenant_id, user_id)

    # Build nudge response (Geofence arrival flow)
    nudge = {"show": False, "cafe_open": False, "show_giving": False}
    try:
        geo_config = await db.geofence_config.find_one({"tenant_id": tenant_id}, {"_id": 0})
        cafe_settings = await db.cafe_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
        tenant_doc = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
        church_name = tenant_doc.get("name", "your church") if tenant_doc else "your church"
        
        if geo_config:
            nudge["show"] = True
            if geo_config.get("nudge_cafe") and cafe_settings and cafe_settings.get("is_open"):
                nudge["cafe_open"] = True
                nudge["cafe_message"] = f"Order your coffee for {cafe_settings.get('pickup_location', 'Sunday')} pickup"
            if geo_config.get("nudge_giving"):
                nudge["show_giving"] = True
                nudge["give_message"] = f"Support {church_name} today"
                nudge["give_amounts"] = geo_config.get("nudge_giving_amounts", [25, 50, 100, 250])
    except Exception:
        pass

    return {
        "success": True,
        "message": "Checked in successfully!",
        "check_in_type": check_in_type,
        "streak": {
            "current": streak_data["current_streak"],
            "best": streak_data["longest_streak"],
            "total": streak_data["total_attended"]
        },
        "new_streak": streak_data["current_streak"],
        "current_streak": streak_data["current_streak"],
        "badges_earned": streak_data.get("streak_badges", []),
        "nudge": nudge
    }

@router.get("/portal/attendance-streak")
async def get_attendance_streak(request: Request):
    """Get user's attendance streak and badges"""
    user = await get_current_portal_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    streak_data = await calculate_attendance_streak(tenant_id, user_id)
    return streak_data


@router.get("/portal/attendance/streak")
async def get_mobile_attendance_streak(request: Request):
    """Mobile alias for attendance streak endpoint."""
    return await get_attendance_streak(request)


@router.post("/portal/attendance/checkin")
async def checkin_mobile_attendance(request: Request, payload: AttendanceCheckinRequest):
    """Mobile alias for service attendance check-in."""
    return await check_in_to_service(request, check_in_type=payload.check_in_type)


@router.get("/portal/attendance/history")
async def get_mobile_attendance_history(request: Request, limit: int = 90):
    """Return member attendance check-in history for mobile timeline views."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")

    checkins = await db.member_checkins.find(
        {"tenant_id": tenant_id, "user_id": user_id},
        {"_id": 0}
    ).sort("service_date", -1).limit(limit).to_list(limit)

    return {
        "history": [serialize_doc(c) for c in checkins],
        "total": len(checkins)
    }

# ============== SUNDAY MORNING PUSH NOTIFICATION PAYLOADS ==============

SUNDAY_MORNING_NOTIFICATIONS = {
    "service_starting": {
        "title": "Service Starting Soon!",
        "body": "Join us in {minutes} minutes. Tap to check in!",
        "url": "/portal"
    },
    "welcome_arrived": {
        "title": "Welcome to {church_name}!",
        "body": "You're checked in. Order your coffee or give today!",
        "url": "/portal"
    },
    "kids_reminder": {
        "title": "Don't Forget Kids Check-In",
        "body": "Check your kids into Sunday School before service starts.",
        "url": "/portal/kids"
    },
    "giving_reminder": {
        "title": "Give Today",
        "body": "Your generosity makes a difference at {church_name}.",
        "url": "/portal/give"
    },
    "cafe_ready": {
        "title": "Your Coffee is Ready!",
        "body": "Pick up your order at the cafe counter.",
        "url": "/portal/cafe"
    },
    "post_service": {
        "title": "Thank You for Worshipping With Us!",
        "body": "Have a blessed week. See you next Sunday!",
        "url": "/portal"
    }
}


@router.get("/portal/prayer-requests")
async def get_portal_prayer_requests_alias(request: Request):
    """Mobile alias for a member's prayer requests."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    user_id = user.get("user_id")

    await ensure_abundant_go_live_portal_content()

    requests = await db.prayer_requests.find(
        {"tenant_id": tenant_id, "user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    return {
        "requests": [
            {
                "id": row.get("id"),
                "title": row.get("title"),
                "description": row.get("content"),
                "created_at": row.get("created_at"),
                "status": row.get("status", "active"),
                "is_public": bool(row.get("is_public", False))
            }
            for row in requests
        ]
    }


@router.post("/portal/prayer-requests")
async def create_portal_prayer_request_alias(payload: PrayerRequestAliasCreate, request: Request):
    """Mobile alias to create prayer request with description field."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    prayer_request = PrayerRequest(
        tenant_id=tenant_id,
        user_id=user.get("user_id"),
        user_name=user.get("name", "Anonymous"),
        category="general",
        title=payload.title,
        content=payload.description,
        is_public=payload.is_public,
        is_anonymous=False
    ).model_dump()

    prayer_request["created_at"] = datetime.now(timezone.utc)
    await db.prayer_requests.insert_one(prayer_request)

    return {
        "message": "Prayer request submitted",
        "request": {
            "id": prayer_request.get("id"),
            "title": prayer_request.get("title"),
            "description": prayer_request.get("content"),
            "created_at": prayer_request.get("created_at"),
            "status": prayer_request.get("status", "active"),
            "is_public": prayer_request.get("is_public", False)
        }
    }


@router.get("/portal/prayer-requests/community")
async def get_portal_prayer_requests_community(request: Request):
    """Mobile alias for public prayer wall."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    requests = await db.prayer_requests.find(
        {"tenant_id": tenant_id, "is_public": True, "status": "active"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    return {
        "requests": [
            {
                "id": row.get("id"),
                "title": row.get("title"),
                "description": row.get("content"),
                "created_at": row.get("created_at"),
                "status": row.get("status", "active"),
                "is_public": True
            }
            for row in requests
        ]
    }

PRAYER_CATEGORIES = [
    {"id": "general", "name": "General", "icon": "🙏"},
    {"id": "healing", "name": "Healing", "icon": "💚"},
    {"id": "family", "name": "Family", "icon": "👨‍👩‍👧‍👦"},
    {"id": "financial", "name": "Financial", "icon": "💰"},
    {"id": "guidance", "name": "Guidance", "icon": "🧭"},
    {"id": "thanksgiving", "name": "Thanksgiving", "icon": "🙌"},
    {"id": "salvation", "name": "Salvation", "icon": "✝️"},
    {"id": "relationships", "name": "Relationships", "icon": "❤️"},
]


@router.get("/portal/prayer/categories")
async def get_prayer_categories():
    """Get available prayer request categories"""
    return {"categories": PRAYER_CATEGORIES}


@router.post("/portal/prayer/requests")
async def create_prayer_request(
    data: PrayerRequestCreate,
    request: Request
):
    """Submit a new prayer request"""
    user = await get_current_portal_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    user_name = user.get("name", "Anonymous")
    
    prayer_request = PrayerRequest(
        tenant_id=tenant_id,
        user_id=user_id,
        user_name="Anonymous" if data.is_anonymous else user_name,
        category=data.category,
        title=data.title,
        content=data.content,
        is_public=data.is_public,
        is_anonymous=data.is_anonymous
    )
    
    await db.prayer_requests.insert_one(prayer_request.model_dump())
    
    return {"message": "Prayer request submitted", "id": prayer_request.id}


@router.get("/portal/prayer/requests")
async def get_my_prayer_requests(
    request: Request
):
    """Get user's own prayer requests"""
    user = await get_current_portal_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    requests = await db.prayer_requests.find(
        {"tenant_id": tenant_id, "user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(length=50)
    
    return {"requests": requests}


@router.get("/portal/prayer/wall")
async def get_prayer_wall(
    request: Request,
    category: Optional[str] = None
):
    """Get public prayer wall - requests shared with community"""
    user = await get_current_portal_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    
    query = {
        "tenant_id": tenant_id,
        "is_public": True,
        "status": "active"
    }
    
    if category and category != "all":
        query["category"] = category
    
    requests = await db.prayer_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(length=50)
    
    return {"requests": requests, "categories": PRAYER_CATEGORIES}


@router.post("/portal/prayer/requests/{request_id}/pray")
async def pray_for_request(
    request_id: str,
    request: Request
):
    """Increment prayer count for a request"""
    user = await get_current_portal_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    # Check if user already prayed (optional - could track in separate collection)
    prayer_log = await db.prayer_logs.find_one({
        "request_id": request_id,
        "user_id": user_id
    })
    
    if prayer_log:
        return {"message": "Already prayed for this request", "prayed": True}
    
    # Increment prayer count
    await db.prayer_requests.update_one(
        {"id": request_id, "tenant_id": tenant_id},
        {"$inc": {"prayer_count": 1}}
    )
    
    # Log the prayer
    await db.prayer_logs.insert_one({
        "id": str(uuid.uuid4()),
        "request_id": request_id,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Prayer recorded", "prayed": True}

# ============== ADMIN PRAYER DASHBOARD ==============


@router.get("/portal/volunteer/opportunities")
async def get_portal_volunteer_opportunities(request: Request):
    """List available volunteer opportunities for the authenticated user."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_abundant_go_live_portal_content()

    opportunities = await db.volunteer_opportunities.find(
        {"tenant_id": tenant_id, "is_active": True},
        {"_id": 0}
    ).sort("title", 1).to_list(200)

    return {"opportunities": [serialize_doc(item) for item in opportunities]}


@router.post("/portal/volunteer/signup")
async def signup_portal_volunteer(request: Request, payload: VolunteerSignupRequest):
    """Create a volunteer signup for an opportunity."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    opportunity = await db.volunteer_opportunities.find_one(
        {"tenant_id": tenant_id, "id": payload.opportunity_id, "is_active": True},
        {"_id": 0}
    )
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    existing = await db.volunteer_signups.find_one(
        {
            "tenant_id": tenant_id,
            "opportunity_id": payload.opportunity_id,
            "user_id": user.get("user_id")
        },
        {"_id": 0}
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
        {"tenant_id": tenant_id, "id": payload.opportunity_id},
        {"$inc": {"spots_available": -1}}
    )

    return {"message": "Signed up successfully", "signup": serialize_doc(signup)}


@router.get("/portal/announcements")
async def get_portal_announcements(request: Request):
    """Get active church announcements for the member portal."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_abundant_go_live_portal_content()

    now_iso = datetime.now(timezone.utc).isoformat()
    announcements = await db.announcements.find(
        {
            "tenant_id": tenant_id,
            "$or": [
                {"expires_at": {"$gte": now_iso}},
                {"expires_at": {"$exists": False}},
                {"expires_at": None}
            ]
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    return {"announcements": [serialize_doc(item) for item in announcements]}


# ============== MOBILE-COMPATIBLE PAYMENT METHOD ALIASES ==============


@router.get("/portal/payment-methods")
async def get_portal_payment_methods(request: Request):
    """Get saved payment methods (Bearer-compatible alias)."""
    user = await get_current_member_user(request)
    methods = await db.payment_methods.find(
        {"user_id": user["user_id"], "is_active": True}, {"_id": 0}
    ).to_list(10)
    return {"payment_methods": [serialize_doc(m) for m in methods]}


@router.post("/portal/payment-methods")
async def save_portal_payment_method(request: Request, method_data: SavePaymentMethodRequest):
    """Save a new payment method (Bearer-compatible alias)."""
    user = await get_current_member_user(request)

    if method_data.is_default:
        await db.payment_methods.update_many(
            {"user_id": user["user_id"]}, {"$set": {"is_default": False}}
        )

    pm = {
        "id": str(uuid.uuid4()),
        "user_id": user["user_id"],
        "tenant_id": user.get("tenant_id"),
        "card_last_four": method_data.card_last_four,
        "card_brand": method_data.card_brand,
        "card_exp_month": method_data.card_exp_month,
        "card_exp_year": method_data.card_exp_year,
        "solomonpay_token": method_data.solomonpay_token,
        "is_default": method_data.is_default,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_methods.insert_one(pm)
    return {"message": "Payment method saved", "payment_method": {k: v for k, v in pm.items() if k != "_id"}}


@router.delete("/portal/payment-methods/{method_id}")
async def delete_portal_payment_method(request: Request, method_id: str):
    """Delete a payment method (Bearer-compatible alias)."""
    user = await get_current_member_user(request)
    result = await db.payment_methods.update_one(
        {"id": method_id, "user_id": user["user_id"]},
        {"$set": {"is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return {"message": "Payment method removed"}


@router.put("/portal/payment-methods/{method_id}/default")
async def set_portal_default_payment_method(request: Request, method_id: str):
    """Set default payment method (Bearer-compatible alias)."""
    user = await get_current_member_user(request)
    await db.payment_methods.update_many(
        {"user_id": user["user_id"]}, {"$set": {"is_default": False}}
    )
    result = await db.payment_methods.update_one(
        {"id": method_id, "user_id": user["user_id"], "is_active": True},
        {"$set": {"is_default": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return {"message": "Default payment method updated"}


# ============== GO-LIVE: MISSING ENDPOINTS ==============

# --- Kids: Portal Checkout ---


@router.post("/portal/kids/checkout")
async def portal_kids_checkout(request: Request, payload: KidsCheckoutRequest):
    """Member checks out their child using pickup code."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    checkin = await db.checkins.find_one(
        {"tenant_id": tenant_id, "child_id": payload.child_id, "status": "checked_in"},
        {"_id": 0}
    )
    if not checkin:
        raise HTTPException(status_code=404, detail="No active check-in found for this child")
    if checkin.get("pickup_code") != payload.pickup_code:
        raise HTTPException(status_code=400, detail="Invalid pickup code")
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.checkins.update_one(
        {"id": checkin["id"]},
        {"$set": {"status": "checked_out", "checked_out_at": now_iso, "checked_out_by": user.get("name", "Parent")}}
    )
    return {"status": "checked_out", "checkout_time": now_iso, "child_name": checkin.get("child_name")}

# --- Kids: Admin /today and checkout ---
@router.post("/portal/giving/donate")
async def portal_giving_donate(request: Request, payload: GivingDonateRequest):
    """Process a donation from the member portal via SolomonPay."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    cover_fees = getattr(payload, 'cover_fees', False)
    base_amount = round(payload.amount, 2)
    processing_fee = round(base_amount * 0.025 + 0.30, 2) if cover_fees else 0
    total_amount = round(base_amount + processing_fee, 2)
    txn_id = f"sp_txn_{uuid.uuid4().hex[:12]}"
    donation = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "person_id": user.get("user_id"),
        "person_name": user.get("name", ""),
        "person_email": user.get("email", ""),
        "amount": total_amount,
        "base_amount": base_amount,
        "processing_fee": processing_fee,
        "fees_covered_by_donor": cover_fees,
        "fund": payload.fund,
        "fund_name": payload.fund,
        "fund_id": payload.fund_id if hasattr(payload, 'fund_id') else "general",
        "frequency": payload.frequency,
        "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "payment_method": "solomonpay",
        "payment_method_id": payload.payment_method_id,
        "transaction_id": txn_id,
        "source": "solomonpay",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.donations.insert_one(donation)
    return {
        "donation_id": donation["id"],
        "transaction_id": txn_id,
        "amount": donation["amount"],
        "fund": donation["fund"],
        "status": "pending",
        "message": f"Thank you for your ${donation['amount']:.2f} gift! Transaction will be processed when SolomonPay goes live."
    }


# Include router
# ============== NOTIFICATIONS ==============


@router.get("/portal/notifications")
async def get_notifications(request: Request, limit: int = 20):
    """Get user's notifications with unread count."""
    user = await get_current_member_user(request)
    notifications = await db.notifications.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    unread = sum(1 for n in notifications if not n.get("is_read"))
    return {"notifications": [serialize_doc(n) for n in notifications], "unread_count": unread}


@router.put("/portal/notifications/{notif_id}/read")
async def mark_notification_read(request: Request, notif_id: str):
    """Mark a notification as read."""
    user = await get_current_member_user(request)
    await db.notifications.update_one(
        {"id": notif_id, "user_id": user["user_id"]},
        {"$set": {"is_read": True}}
    )
    return {"message": "Marked as read"}


@router.put("/portal/notifications/read-all")
async def mark_all_notifications_read(request: Request):
    """Mark all notifications as read."""
    user = await get_current_member_user(request)
    await db.notifications.update_many(
        {"user_id": user["user_id"], "is_read": False},
        {"$set": {"is_read": True}}
    )
    return {"message": "All marked as read"}


@router.post("/portal/checkout/with-giving")
async def checkout_with_giving_nudge(req: CheckoutWithNudgeRequest, request: Request):
    """4-step checkout: Review -> Giving Moment -> Payment -> Confirmation"""
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
    subtotal = sum(item.get("price", 0) * item.get("quantity", 1) for item in req.items)
    total = round(subtotal + req.giving_amount, 2)

    order_id = str(uuid.uuid4())
    order_doc = {
        "id": order_id,
        "tenant_id": tenant_id,
        "user_id": user["user_id"],
        "user_name": user.get("name", ""),
        "order_type": req.order_type,
        "items": req.items,
        "subtotal": subtotal,
        "giving_amount": req.giving_amount,
        "giving_fund": req.giving_fund if req.giving_amount > 0 else None,
        "total": total,
        "payment_method_id": req.payment_method_id,
        "pickup_time": req.pickup_time,
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    collection = "cafe_orders" if req.order_type == "cafe" else "merch_orders"
    await db[collection].insert_one(order_doc)

    # If giving was added, also create a donation record
    if req.giving_amount > 0:
        donation_doc = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": user["user_id"],
            "person_name": user.get("name", ""),
            "amount": req.giving_amount,
            "fund_name": req.giving_fund,
            "fund": req.giving_fund,
            "payment_method": "card",
            "frequency": "one_time",
            "status": "completed",
            "source": f"{req.order_type}_nudge",
            "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.donations.insert_one(donation_doc)

    return {
        "order_id": order_id,
        "status": "confirmed",
        "subtotal": subtotal,
        "giving_amount": req.giving_amount,
        "giving_fund": req.giving_fund if req.giving_amount > 0 else None,
        "total": total,
        "pickup_time": req.pickup_time,
        "message": "Order confirmed! Thank you for your generosity." if req.giving_amount > 0 else "Order confirmed!"
    }

# ============== PLATFORM HEALTH MONITORING ==============




# ════════════════════════════════════════════════════════════
# MULTI-CAMPUS MANAGEMENT
# ════════════════════════════════════════════════════════════

@router.get("/portal/campuses")
async def get_available_campuses(request: Request):
    """Get all campuses for the user's organization (for campus selector)."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)

    # Get current tenant
    current_tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "name": 1, "parent_organization": 1})
    parent_name = current_tenant.get("parent_organization") if current_tenant else None

    # If no parent org set, derive from common name prefix
    if not parent_name and current_tenant:
        name = current_tenant.get("name", "")
        # e.g. "Abundant East" → parent == "Abundant"
        for suffix in [" East", " West", " Downtown", " North", " South", " Central", " Online"]:
            if name.endswith(suffix):
                parent_name = name[: -len(suffix)].strip()
                break

    campuses = []
    if parent_name:
        # Find all ACTIVE campuses sharing this parent — exclude parent_org entities
        all_tenants = await db.tenants.find(
            {
                "name": {"$regex": f"^{parent_name}", "$options": "i"},
                "subscription_status": "active",   # filter out parent_org / inactive
                "is_parent": {"$ne": True},         # filter out parent entity
            },
            {"_id": 0, "id": 1, "name": 1, "address": 1, "city": 1}
        ).to_list(10)
        for t in all_tenants:
            label = t["name"].replace(parent_name, "").strip() or "Main"
            campuses.append({
                "id": t["id"],
                "name": t["name"],
                "label": label if label else t["name"],
                "parent_name": parent_name,
                "address": t.get("address", ""),
                "city": t.get("city", ""),
            })
    else:
        campuses = [{"id": tenant_id, "name": current_tenant.get("name", "Main Campus"), "label": "Main Campus"}]

    user_campus = user.get("home_campus_id") or tenant_id

    return {
        "campuses": campuses,
        "parent_name": parent_name,
        "home_campus_id": user_campus,
        "is_multi_campus": len(campuses) > 1,
    }


@router.post("/portal/campus/select")
async def select_home_campus(request: Request):
    """Set the member's home campus."""
    user = await get_current_member_user(request)
    body = await request.json()
    campus_id = body.get("campus_id")
    if not campus_id:
        raise HTTPException(status_code=400, detail="campus_id required")

    # Verify campus exists
    campus = await db.tenants.find_one({"id": campus_id}, {"_id": 0, "name": 1})
    if not campus:
        raise HTTPException(status_code=404, detail="Campus not found")

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"home_campus_id": campus_id, "home_campus_name": campus["name"],
                  "campus_selected": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Home campus set", "campus_id": campus_id, "campus_name": campus["name"]}
