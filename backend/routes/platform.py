"""Solomon AI — Platform Admin, Seed Routes"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import uuid
import re
import hashlib
import logging
from random import SystemRandom
_rng = SystemRandom()
import os
import bcrypt

from core import (
    db, DEFAULT_TENANT_ID, ROLE_TEMPLATES,
    get_permissions_for_user, get_session_token_from_request, audit_log,
    logger,
)
from core.helpers import serialize_doc, DEFAULT_MERCH_EMBED_URL, compute_health_score
from models.schemas import (
    Attendance, Donation, Fund, Group, Service, User, AttendanceStreakData, CheckoutWithNudgeRequest, ChurchOnboardingRequest, MemberCheckIn, PrayerRequest, PrayerRequestCreate, ServiceModeStatus,
)

router = APIRouter()

@router.get("/platform/stats")
async def get_platform_stats(request: Request):
    """Get platform-wide statistics for God Mode executive dashboard"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    today = datetime.now(timezone.utc)
    today_str = today.strftime("%Y-%m-%d")
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    year_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")

    # Get all active tenants — exclude TEST_ tenants and empty/stub campuses
    all_tenants = await db.tenants.find(
        {"subscription_status": "active"}, {"_id": 0, "id": 1, "name": 1, "city": 1, "state": 1}
    ).to_list(100)
    # Filter: real churches only (exclude test and zero-data stubs)
    real_tenants = [t for t in all_tenants if not t["name"].startswith("TEST_")]
    # Further filter to tenants with actual donation data
    campuses_all = [t["id"] for t in real_tenants]
    # Build a set of tenant_ids that have > 10 donations (real data)
    real_campus_ids = []
    for tid in campuses_all:
        cnt = await db.donations.count_documents({"tenant_id": tid})
        if cnt > 10:
            real_campus_ids.append(tid)
    campuses = real_campus_ids if real_campus_ids else campuses_all if campuses_all else [DEFAULT_TENANT_ID]
    real_tenants_map = {t["id"]: t for t in real_tenants}

    # All-time totals
    all_time = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": None, "vol": {"$sum": "$amount"}, "fees": {"$sum": {"$ifNull": ["$fee_amount", {"$ifNull": ["$solomon_fee", 0]}]}}, "cnt": {"$sum": 1}}},
    ]).to_list(1)
    all_time_vol = all_time[0]["vol"] if all_time else 0
    all_time_fees = all_time[0]["fees"] if all_time else 0
    all_time_cnt = all_time[0]["cnt"] if all_time else 0

    # YTD
    ytd = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}, "donation_date": {"$gte": year_start}}},
        {"$group": {"_id": None, "vol": {"$sum": "$amount"}, "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}}, "cnt": {"$sum": 1}}},
    ]).to_list(1)
    ytd_vol = ytd[0]["vol"] if ytd else 0
    ytd_fees = ytd[0]["fees"] if ytd else 0

    # MTD
    mtd = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}, "donation_date": {"$gte": month_start}}},
        {"$group": {"_id": None, "vol": {"$sum": "$amount"}, "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}}, "cnt": {"$sum": 1}}},
    ]).to_list(1)
    mtd_vol = mtd[0]["vol"] if mtd else 0
    mtd_fees = mtd[0]["fees"] if mtd else 0

    # This week
    wtd = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}, "donation_date": {"$gte": week_start}}},
        {"$group": {"_id": None, "vol": {"$sum": "$amount"}, "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}}}},
    ]).to_list(1)
    wtd_vol = wtd[0]["vol"] if wtd else 0
    wtd_fees = wtd[0]["fees"] if wtd else 0

    # Today
    today_data = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}, "donation_date": today_str}},
        {"$group": {"_id": None, "vol": {"$sum": "$amount"}, "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}}}},
    ]).to_list(1)
    today_vol = today_data[0]["vol"] if today_data else 0
    today_fees = today_data[0]["fees"] if today_data else 0

    # Donor count
    total_donors = await db.platform_donors.count_documents({"tenant_id": {"$in": campuses}})

    # Average transaction
    avg_txn = round(all_time_vol / max(all_time_cnt, 1), 2)

    # Active churches (real data only)
    active_churches = len(campuses)
    total_churches = len(campuses)

    # Giving trend (last 12 months by campus)
    twelve_months_ago = (today - timedelta(days=365)).strftime("%Y-%m")
    trend_pipeline = [
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$addFields": {"month": {"$substr": ["$donation_date", 0, 7]}}},
        {"$match": {"month": {"$gte": twelve_months_ago}}},
        {"$group": {"_id": {"month": "$month", "tenant": "$tenant_id"}, "vol": {"$sum": "$amount"}, "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}}, "cnt": {"$sum": 1}}},
        {"$sort": {"_id.month": 1}},
    ]
    trend_raw = await db.donations.aggregate(trend_pipeline).to_list(200)
    trend_by_month = {}
    for r in trend_raw:
        m = r["_id"]["month"]
        if m not in trend_by_month:
            trend_by_month[m] = {"month": m, "total_giving": 0, "total_fees": 0, "txn_count": 0, "by_campus": {}}
        trend_by_month[m]["total_giving"] += r["vol"]
        trend_by_month[m]["total_fees"] += r["fees"]
        trend_by_month[m]["txn_count"] += r["cnt"]
        t = await db.tenants.find_one({"id": r["_id"]["tenant"]}, {"_id": 0, "name": 1})
        name = t.get("name", r["_id"]["tenant"]) if t else r["_id"]["tenant"]
        trend_by_month[m]["by_campus"][name] = round(r["vol"], 2)
    giving_trend = [trend_by_month[m] for m in sorted(trend_by_month)]

    # Campus breakdown with full portfolio metrics
    campus_pipe = [
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": "$tenant_id", "vol": {"$sum": "$amount"}, "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}}, "cnt": {"$sum": 1}}},
        {"$sort": {"vol": -1}},
    ]
    campus_raw = await db.donations.aggregate(campus_pipe).to_list(20)
    campus_breakdown = []
    ninety_days_ago = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    for r in campus_raw:
        tid = r["_id"]
        t = real_tenants_map.get(tid) or await db.tenants.find_one({"id": tid}, {"_id": 0, "name": 1, "city": 1, "state": 1})
        # Active donors (gave in last 90 days)
        active_donors = await db.donations.distinct("person_id", {"tenant_id": tid, "donation_date": {"$gte": ninety_days_ago}})
        # MTD giving
        mtd_church = await db.donations.aggregate([
            {"$match": {"tenant_id": tid, "donation_date": {"$gte": month_start}}},
            {"$group": {"_id": None, "vol": {"$sum": "$amount"}}},
        ]).to_list(1)
        campus_breakdown.append({
            "tenant_id": tid,
            "name": t.get("name", tid) if t else tid,
            "city": t.get("city", "") if t else "",
            "state": t.get("state", "") if t else "",
            "giving": round(r["vol"], 2),
            "fees": round(r["fees"], 2),
            "txn_count": r["cnt"],
            "active_donors": len(active_donors),
            "mtd_giving": round(mtd_church[0]["vol"], 2) if mtd_church else 0,
        })

    # YoY growth calculation
    prev_year_start = today.replace(year=today.year - 1, month=1, day=1).strftime("%Y-%m-%d")
    prev_year_same_date = today.replace(year=today.year - 1).strftime("%Y-%m-%d")
    prev_ytd = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}, "donation_date": {"$gte": prev_year_start, "$lte": prev_year_same_date}}},
        {"$group": {"_id": None, "vol": {"$sum": "$amount"}}},
    ]).to_list(1)
    prev_ytd_vol = prev_ytd[0]["vol"] if prev_ytd else 0
    yoy_change = round((ytd_vol - prev_ytd_vol) / max(prev_ytd_vol, 1) * 100, 1) if prev_ytd_vol else 0

    # MRR / ARR calculation from active recurring schedules
    recurring_pipeline = [
        {"$match": {"tenant_id": {"$in": campuses}, "is_active": True}},
        {"$group": {"_id": "$frequency", "total_amount": {"$sum": "$amount"}, "count": {"$sum": 1}}},
    ]
    recurring_data = await db.recurring_giving.aggregate(recurring_pipeline).to_list(10)
    mrr = 0
    for rd in recurring_data:
        freq = rd["_id"]
        monthly_equiv = rd["total_amount"] * (
            4.33 if freq == "weekly" else 2.17 if freq == "biweekly" else
            1.0 if freq == "monthly" else 1/12 if freq == "annually" else 1.0
        )
        mrr += monthly_equiv * SOLOMON_FEE_RATE

    total_member_count = await db.people.count_documents({"tenant_id": {"$in": campuses}})

    return {
        "churches": {"total": total_churches, "active": active_churches},
        "members": {"total": total_member_count},
        "giving": {
            "all_time": round(all_time_vol, 2),
            "ytd": round(ytd_vol, 2),
            "mtd": round(mtd_vol, 2),
            "wtd": round(wtd_vol, 2),
            "today": round(today_vol, 2),
            "yoy_change": yoy_change,
        },
        "fees": {
            "all_time": round(all_time_fees, 2),
            "ytd": round(ytd_fees, 2),
            "mtd": round(mtd_fees, 2),
            "wtd": round(wtd_fees, 2),
            "today": round(today_fees, 2),
        },
        "platform": {
            "total_mrr": round(mrr, 2),
            "arr": round(mrr * 12, 2),
            "total_churches": total_churches,
            "total_members": total_member_count,
        },
        "transactions": {"total": all_time_cnt, "avg_amount": avg_txn},
        "donors": {"total": total_donors},
        "giving_trend": giving_trend,
        "campus_breakdown": campus_breakdown,
        "fee_config": {
            "card_rate": f"{SOLOMON_FEE_RATE * 100}%",
            "card_flat": f"${SOLOMON_FEE_FLAT}",
            "ach_rate": "0.8%",
            "ach_flat": "$0.30",
            "industry_rate": "2.5% + $0.30",
            "savings": "24% lower",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }



# ─── Platform Activity Feed ───────────────────────────────────────────────────

@router.get("/platform/activity-feed")
async def get_platform_activity(request: Request, limit: int = 20):
    """Recent platform events across all churches for the activity feed."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401)
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401)
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403)

    # Get real church tenants
    all_tenants = await db.tenants.find({"subscription_status": "active"}, {"_id": 0, "id": 1, "name": 1}).to_list(50)
    real_tenants = {t["id"]: t["name"] for t in all_tenants if not t["name"].startswith("TEST_")}
    campuses = list(real_tenants.keys())

    # Recent large donations (>= $500)
    recent_donations = await db.donations.find(
        {"tenant_id": {"$in": campuses}, "amount": {"$gte": 500}, "status": "completed"},
        {"_id": 0, "tenant_id": 1, "amount": 1, "donation_date": 1, "donor_name": 1, "fund_name": 1, "created_at": 1}
    ).sort("created_at", -1).limit(30).to_list(30)

    # Recent recurring signups
    recent_recurring = await db.recurring_giving.find(
        {"tenant_id": {"$in": campuses}, "is_active": True},
        {"_id": 0, "tenant_id": 1, "amount": 1, "frequency": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10).to_list(10)

    events = []
    for d in recent_donations:
        church = real_tenants.get(d["tenant_id"], "A church")
        name_parts = (d.get("donor_name") or "Anonymous").split()
        masked = f"{name_parts[0]} {name_parts[-1][0]}." if len(name_parts) > 1 else name_parts[0] if name_parts else "Anonymous"
        events.append({
            "type": "donation",
            "icon": "gift",
            "church": church,
            "message": f"{church}: ${d['amount']:,.0f} gift from {masked}",
            "amount": d["amount"],
            "timestamp": d.get("created_at") or d.get("donation_date"),
            "color": "emerald",
        })

    for r in recent_recurring:
        church = real_tenants.get(r["tenant_id"], "A church")
        events.append({
            "type": "recurring",
            "icon": "repeat",
            "church": church,
            "message": f"{church}: New recurring donor (${r['amount']:,.0f}/{r.get('frequency','month')})",
            "amount": r["amount"],
            "timestamp": r.get("created_at", ""),
            "color": "blue",
        })

    # Sort by timestamp descending and return top N
    events.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return {"events": events[:limit]}



# ============== MEMBER DIRECTORY (ADMIN) ==============


@router.post("/seed")
async def seed_database():
    """Seed the database with demo data for Abundant Church"""
    import hashlib
    tenant_id = DEFAULT_TENANT_ID
    
    # Check if already seeded
    existing = await db.tenants.find_one({"id": tenant_id})
    if existing:
        # Still seed demo accounts if they don't exist
        await seed_demo_accounts(tenant_id)
        return {"message": "Database already seeded", "seeded": False}
    
    # ============== SEED DEMO ACCOUNTS ==============
    await seed_demo_accounts(tenant_id)
    
    # Create tenant

async def seed_demo_accounts(tenant_id: str):
    """Seed or update demo accounts"""
    import hashlib
    demo_password_hash = hashlib.sha256("Demo2026!".encode()).hexdigest()
    
    # Admin account
    await db.users.update_one(
        {"email": "admin@abundant.org"},
        {"$set": {
            "user_id": "user_admin_demo",
            "email": "admin@abundant.org",
            "name": "Pastor David Rivera",
            "picture": None,
            "role": "admin",
            "password_hash": demo_password_hash,
            "church_id": tenant_id,
            "created_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )
    
    # Member account - Maria Gonzalez
    await db.users.update_one(
        {"email": "member@abundant.org"},
        {"$set": {
            "user_id": "user_member_demo",
            "email": "member@abundant.org", 
            "name": "Maria Gonzalez",
            "picture": None,
            "role": "member",
            "password_hash": demo_password_hash,
            "church_id": tenant_id,
            "member_since": "2019-03-15",
            "created_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )

# --- SEED DATA ROUTE ---
    tenant = {
        "id": tenant_id,
        "name": "Abundant Church",
        "subdomain": "abundant",
        "plan": "enterprise",
        "member_limit": 100000,
        "logo_url": None,
        "primary_color": "#4f6ef7",
        "accent_color": "#00c896",
        "timezone": "America/Denver",
        "address": "1556 George Dieter Dr, El Paso, TX 79936",
        "website": "https://www.abundant.org",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.tenants.insert_one(tenant)
    
    # Create funds - Mega church scale
    funds_data = [
        {"name": "General Fund", "description": "General operating fund", "goal_amount": 8000000},
        {"name": "Building Fund", "description": "New sanctuary construction", "goal_amount": 5000000},
        {"name": "Missions", "description": "Global missions support", "goal_amount": 500000},
        {"name": "Benevolence", "description": "Community assistance", "goal_amount": 150000},
        {"name": "Youth Ministry", "description": "Youth programs and events", "goal_amount": 200000},
    ]
    
    funds = []
    for f in funds_data:
        fund = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "is_active": True,
            "current_amount": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **f
        }
        funds.append(fund)
    await db.funds.insert_many(funds)
    
    # Create group types
    group_types_data = [
        {"name": "Small Group", "color": "#4f6ef7", "icon": "users"},
        {"name": "Ministry Team", "color": "#00c896", "icon": "heart"},
        {"name": "Volunteer Team", "color": "#f5a623", "icon": "hand"},
        {"name": "Class", "color": "#8b5cf6", "icon": "book"},
    ]
    
    group_types = []
    for gt in group_types_data:
        gtype = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            **gt
        }
        group_types.append(gtype)
    await db.group_types.insert_many(group_types)
    
    # Create service types
    service_types_data = [
        {"name": "Sunday 9:00 AM", "default_time": "09:00", "default_day": "Sunday"},
        {"name": "Sunday 11:00 AM", "default_time": "11:00", "default_day": "Sunday"},
        {"name": "Wednesday Night", "default_time": "19:00", "default_day": "Wednesday"},
    ]
    
    service_types = []
    for st in service_types_data:
        stype = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "is_active": True,
            **st
        }
        service_types.append(stype)
    await db.service_types.insert_many(service_types)
    
    # Generate sample people (200 members)
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
                   "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
                   "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
                   "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
                   "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                  "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
                  "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
                  "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
    
    statuses = ["member", "member", "member", "member", "visitor", "regular", "inactive"]
    genders = ["male", "female"]
    campuses = ["Main Campus", "North Campus", "South Campus"]
    
    people = []
    households = []
    
    # ============== SPECIAL SEED: Maria Gonzalez (Demo Member Account) ==============
    maria_household_id = str(uuid.uuid4())
    maria_person_id = "person_maria_gonzalez"
    
    maria_household = {
        "id": maria_household_id,
        "tenant_id": tenant_id,
        "name": "The Gonzalez Family",
        "address_line1": "4521 Dyer St",
        "city": "El Paso",
        "state": "TX",
        "zip": "79930",
        "country": "US",
        "phone": "(915) 555-0142",
        "envelope_num": 1001,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    households.append(maria_household)
    
    maria_person = {
        "id": maria_person_id,
        "tenant_id": tenant_id,
        "household_id": maria_household_id,
        "first_name": "Maria",
        "last_name": "Gonzalez",
        "email": "member@abundant.org",
        "mobile_phone": "(915) 555-0142",
        "date_of_birth": "1985-06-14",
        "gender": "female",
        "marital_status": "married",
        "membership_status": "member",
        "membership_date": "2019-03-15",
        "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={maria_person_id}",
        "is_head_of_household": False,
        "campus": "East Campus",
        "engagement_score": 88,
        "ytd_giving": 1200.0,
        "lifetime_giving": 18500.0,
        "custom_fields": {},
        "giving_anonymous": False,
        "paperless_statements": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    people.append(maria_person)
    
    # ============== SEED: 10 El Paso-specific named members ==============
    el_paso_members = [
        {"first": "Carlos", "last": "Rivera", "gender": "male"},
        {"first": "Sofia", "last": "Martinez", "gender": "female"},
        {"first": "Juan", "last": "Hernandez", "gender": "male"},
        {"first": "Isabella", "last": "Lopez", "gender": "female"},
        {"first": "Miguel", "last": "Torres", "gender": "male"},
        {"first": "Valentina", "last": "Ramirez", "gender": "female"},
        {"first": "Diego", "last": "Castillo", "gender": "male"},
        {"first": "Ana", "last": "Reyes", "gender": "female"},
        {"first": "Roberto", "last": "Vega", "gender": "male"},
        {"first": "Pastor David", "last": "Rivera", "gender": "male"},
    ]
    
    el_paso_streets = ["Montana Ave", "Alameda Ave", "Mesa St", "Dyer St", "Lee Trevino Dr", 
                       "Gateway Blvd", "Viscount Blvd", "Zaragoza Rd", "Transmountain Dr", "Paisano Dr"]
    
    for i, ep_member in enumerate(el_paso_members):
        ep_household_id = str(uuid.uuid4())
        ep_person_id = str(uuid.uuid4())
        
        ep_household = {
            "id": ep_household_id,
            "tenant_id": tenant_id,
            "name": f"The {ep_member['last']} Family",
            "address_line1": f"{_rng.randint(1000, 9999)} {_rng.choice(el_paso_streets)}",
            "city": "El Paso",
            "state": "TX",
            "zip": f"799{_rng.randint(10, 99)}",
            "country": "US",
            "phone": f"(915) {_rng.randint(200, 999)}-{_rng.randint(1000, 9999)}",
            "envelope_num": 1002 + i,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        households.append(ep_household)
        
        ep_person = {
            "id": ep_person_id,
            "tenant_id": tenant_id,
            "household_id": ep_household_id,
            "first_name": ep_member["first"],
            "last_name": ep_member["last"],
            "email": f"{ep_member['first'].lower()}.{ep_member['last'].lower()}@email.com",
            "mobile_phone": f"(915) {_rng.randint(200, 999)}-{_rng.randint(1000, 9999)}",
            "date_of_birth": f"{_rng.randint(1960, 2000)}-{_rng.randint(1, 12):02d}-{_rng.randint(1, 28):02d}",
            "gender": ep_member["gender"],
            "marital_status": "married",
            "membership_status": "member",
            "membership_date": f"20{_rng.randint(15, 24)}-{_rng.randint(1, 12):02d}-01",
            "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={ep_person_id}",
            "is_head_of_household": True,
            "campus": _rng.choice(["Main Campus", "East Campus", "West Campus"]),
            "engagement_score": _rng.randint(60, 100),
            "ytd_giving": _rng.randint(500, 5000) * 1.0,
            "lifetime_giving": _rng.randint(5000, 50000) * 1.0,
            "custom_fields": {},
            "giving_anonymous": False,
            "paperless_statements": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        people.append(ep_person)
    
    # Create 80 households with 200 people (remaining generic)
    for h in range(80):
        household_id = str(uuid.uuid4())
        last_name = _rng.choice(last_names)
        
        household = {
            "id": household_id,
            "tenant_id": tenant_id,
            "name": f"The {last_name} Family",
            "address_line1": f"{_rng.randint(100, 9999)} {_rng.choice(['Oak', 'Main', 'Church', 'Park', 'Elm', 'Cedar'])} {_rng.choice(['St', 'Ave', 'Blvd', 'Dr'])}",
            "city": "El Cajon",
            "state": "CA",
            "zip": f"920{_rng.randint(10, 99)}",
            "country": "US",
            "phone": f"619-{_rng.randint(200, 999)}-{_rng.randint(1000, 9999)}",
            "envelope_num": h + 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        households.append(household)
        
        # 2-3 people per household
        num_people = _rng.randint(2, 3)
        for i in range(num_people):
            person_id = str(uuid.uuid4())
            first_name = _rng.choice(first_names)
            gender = _rng.choice(genders)
            birth_year = _rng.randint(1950, 2010)
            
            person = {
                "id": person_id,
                "tenant_id": tenant_id,
                "household_id": household_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name.lower()}.{last_name.lower()}{_rng.randint(1, 99)}@email.com",
                "mobile_phone": f"619-{_rng.randint(200, 999)}-{_rng.randint(1000, 9999)}",
                "date_of_birth": f"{birth_year}-{_rng.randint(1, 12):02d}-{_rng.randint(1, 28):02d}",
                "gender": gender,
                "marital_status": _rng.choice(["single", "married", "married"]),
                "membership_status": _rng.choice(statuses),
                "membership_date": f"20{_rng.randint(10, 24)}-{_rng.randint(1, 12):02d}-01",
                "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={person_id}",
                "is_head_of_household": i == 0,
                "campus": _rng.choice(campuses),
                "engagement_score": _rng.randint(20, 100),
                "ytd_giving": 0,
                "lifetime_giving": 0,
                "custom_fields": {},
                "giving_anonymous": False,
                "paperless_statements": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            people.append(person)
    
    await db.households.insert_many(households)
    await db.people.insert_many(people)
    
    # Create groups (20 groups)
    group_names = [
        "Young Adults", "Marriage Builders", "New Believers", "Prayer Warriors",
        "Women's Bible Study", "Men's Brotherhood", "College & Career", "Empty Nesters",
        "Parents of Teens", "Grief Support", "Financial Peace", "Spanish Fellowship",
        "Worship Team", "Tech Team", "Greeting Team", "Parking Team",
        "Children's Ministry", "Youth Group", "Senior Saints", "Community Outreach"
    ]
    
    groups = []
    for i, name in enumerate(group_names):
        group_type = group_types[i % len(group_types)]
        leader = _rng.choice(people)
        
        group = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "group_type_id": group_type["id"],
            "name": name,
            "description": f"{name} - a place to grow and connect",
            "location": _rng.choice(["Room 101", "Room 202", "Fellowship Hall", "Chapel", "Youth Center"]),
            "meeting_schedule": _rng.choice(["Weekly", "Bi-weekly", "Monthly"]),
            "meeting_day": _rng.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]),
            "meeting_time": _rng.choice(["09:00", "10:00", "18:00", "19:00"]),
            "capacity": _rng.randint(15, 60),
            "is_open": _rng.choice([True, True, True, False]),
            "is_active": True,
            "leader_id": leader["id"],
            "tags": [],
            "member_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        groups.append(group)
    await db.groups.insert_many(groups)
    
    # Assign people to groups (each person in 1-3 groups)
    group_members = []
    for person in people:
        num_groups = _rng.randint(1, 3)
        selected_groups = _rng.sample(groups, min(num_groups, len(groups)))
        
        for g in selected_groups:
            member = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "group_id": g["id"],
                "person_id": person["id"],
                "role": _rng.choice(["member", "member", "member", "leader", "co-leader"]),
                "joined_at": f"20{_rng.randint(20, 24)}-{_rng.randint(1, 12):02d}-{_rng.randint(1, 28):02d}",
                "is_active": True
            }
            group_members.append(member)
    await db.group_members.insert_many(group_members)
    
    # Update group member counts
    for g in groups:
        count = sum(1 for gm in group_members if gm["group_id"] == g["id"])
        await db.groups.update_one({"id": g["id"]}, {"$set": {"member_count": count}})
    
    # Create services for last 18 months (every Sunday)
    services = []
    today = datetime.now(timezone.utc)
    
    for weeks_ago in range(78):  # ~18 months
        service_date = today - timedelta(weeks=weeks_ago)
        # Find the Sunday
        days_until_sunday = (6 - service_date.weekday()) % 7
        sunday = service_date - timedelta(days=service_date.weekday() + 1)
        sunday_str = sunday.strftime("%Y-%m-%d")
        
        for st in service_types[:2]:  # Two Sunday services
            service = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "service_type_id": st["id"],
                "date": sunday_str,
                "time": st["default_time"],
                "total_headcount": _rng.randint(3000, 4500),
                "notes": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            services.append(service)
    
    await db.services.insert_many(services)
    
    # Create attendance records
    attendance_records = []
    for service in services[-24:]:  # Last 12 weeks (24 services)
        # Random subset of people attended
        attendees = _rng.sample(people, _rng.randint(60, 120))
        for person in attendees:
            record = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "service_id": service["id"],
                "person_id": person["id"],
                "check_in_time": datetime.now(timezone.utc).isoformat()
            }
            attendance_records.append(record)
    
    if attendance_records:
        await db.attendance.insert_many(attendance_records)
    
    # Create donations (18 months of giving)
    donations = []
    payment_methods = ["card", "card", "card", "check", "check", "cash", "ach", "ach"]
    
    for weeks_ago in range(78):
        week_date = today - timedelta(weeks=weeks_ago)
        sunday = week_date - timedelta(days=week_date.weekday() + 1)
        sunday_str = sunday.strftime("%Y-%m-%d")
        
        # 40-80 donations per week
        num_donations = _rng.randint(40, 80)
        donors = _rng.sample(people, min(num_donations, len(people)))
        
        for donor in donors:
            fund = _rng.choice(funds)
            amount = _rng.choice([25, 50, 100, 100, 150, 200, 250, 500, 1000, 2500])
            
            donation = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "person_id": donor["id"],
                "fund_id": fund["id"],
                "amount": float(amount),
                "donation_date": sunday_str,
                "payment_method": _rng.choice(payment_methods),
                "is_recurring": _rng.random() < 0.15,
                "receipt_sent": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            donations.append(donation)
    
    # Add 5 crypto donations
    crypto_currencies = ["BTC", "ETH", "USDC", "SOL"]
    for _ in range(5):
        donor = _rng.choice(people)
        crypto_amount = _rng.uniform(0.01, 2.0)
        usd_value = _rng.uniform(500, 25000)
        
        donation = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": donor["id"],
            "fund_id": funds[0]["id"],  # General fund
            "amount": usd_value,
            "donation_date": (today - timedelta(days=_rng.randint(1, 180))).strftime("%Y-%m-%d"),
            "payment_method": "crypto",
            "crypto_currency": _rng.choice(crypto_currencies),
            "crypto_amount": crypto_amount,
            "crypto_tx_hash": f"0x{''.join(_rng.choices('0123456789abcdef', k=64))}",
            "crypto_usd_value": usd_value,
            "is_recurring": False,
            "receipt_sent": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        donations.append(donation)
    
    # Add 2 asset donations
    asset_donations = [
        {"asset_type": "vehicle", "asset_description": "2020 Toyota Camry", "asset_appraised_value": 22000},
        {"asset_type": "stock", "asset_description": "500 shares AAPL", "asset_appraised_value": 95000},
    ]
    
    for asset in asset_donations:
        donor = _rng.choice(people)
        donation = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": donor["id"],
            "fund_id": funds[1]["id"],  # Building fund
            "amount": asset["asset_appraised_value"],
            "donation_date": (today - timedelta(days=_rng.randint(30, 180))).strftime("%Y-%m-%d"),
            "payment_method": "stock" if asset["asset_type"] == "stock" else "vehicle",
            "asset_type": asset["asset_type"],
            "asset_description": asset["asset_description"],
            "asset_appraised_value": asset["asset_appraised_value"],
            "is_recurring": False,
            "receipt_sent": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        donations.append(donation)
    
    await db.donations.insert_many(donations)
    
    # Update fund totals
    for fund in funds:
        total = sum(d["amount"] for d in donations if d["fund_id"] == fund["id"])
        await db.funds.update_one({"id": fund["id"]}, {"$set": {"current_amount": total}})
    
    # Update person giving totals
    ytd_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    for person in people:
        person_donations = [d for d in donations if d["person_id"] == person["id"]]
        lifetime = sum(d["amount"] for d in person_donations)
        ytd = sum(d["amount"] for d in person_donations if d["donation_date"] >= ytd_start)
        await db.people.update_one(
            {"id": person["id"]},
            {"$set": {"lifetime_giving": lifetime, "ytd_giving": ytd}}
        )
    
    # Create recurring giving (30 givers)
    recurring_givers = _rng.sample(people, 30)
    recurring_records = []
    
    for person in recurring_givers:
        recurring = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": person["id"],
            "fund_id": _rng.choice(funds)["id"],
            "amount": float(_rng.choice([50, 100, 150, 200, 250, 500])),
            "frequency": _rng.choice(["weekly", "biweekly", "monthly"]),
            "next_gift_date": (today + timedelta(days=_rng.randint(1, 30))).strftime("%Y-%m-%d"),
            "payment_method": "card",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        recurring_records.append(recurring)
    
    await db.recurring_giving.insert_many(recurring_records)
    
    # Create pledges (10 pledges for Building Fund campaign)
    pledgers = _rng.sample(people, 10)
    pledges = []
    
    for person in pledgers:
        pledge_amount = _rng.choice([5000, 10000, 15000, 25000, 50000])
        total_given = _rng.uniform(0.2, 0.9) * pledge_amount
        
        pledge = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": person["id"],
            "fund_id": funds[1]["id"],  # Building Fund
            "pledge_amount": float(pledge_amount),
            "start_date": "2024-01-01",
            "end_date": "2026-12-31",
            "frequency": "monthly",
            "total_given": total_given,
            "notes": "Building Fund Campaign 2024-2026",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        pledges.append(pledge)
    
    await db.pledges.insert_many(pledges)
    
    # Create donation batches
    batches = [
        {"name": "Sunday Offering 01/12/2025", "date": "2025-01-12", "status": "open", "total_amount": 45230.00, "donation_count": 87},
        {"name": "Sunday Offering 01/05/2025", "date": "2025-01-05", "status": "closed", "total_amount": 52100.00, "donation_count": 102},
        {"name": "Sunday Offering 12/29/2024", "date": "2024-12-29", "status": "deposited", "total_amount": 89500.00, "donation_count": 156},
    ]
    
    batch_records = []
    for b in batches:
        batch = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **b
        }
        batch_records.append(batch)
    await db.donation_batches.insert_many(batch_records)
    
    # Create upcoming events
    events = [
        {
            "name": "Sunday Service",
            "description": "Join us for worship, prayer, and the Word",
            "location": "Main Sanctuary",
            "start_datetime": (today + timedelta(days=(6 - today.weekday()))).strftime("%Y-%m-%dT09:00:00"),
            "is_public": True,
            "capacity": 5000,
            "registration_required": False,
            "registration_count": 0
        },
        {
            "name": "Youth Night",
            "description": "Middle and High School students gather for games, worship, and teaching",
            "location": "Youth Center",
            "start_datetime": (today + timedelta(days=3)).strftime("%Y-%m-%dT18:30:00"),
            "is_public": True,
            "capacity": 200,
            "registration_required": False,
            "registration_count": 45
        },
        {
            "name": "Women's Conference",
            "description": "Annual women's conference - 'Renewed'",
            "location": "Fellowship Hall",
            "start_datetime": (today + timedelta(days=14)).strftime("%Y-%m-%dT09:00:00"),
            "is_public": True,
            "capacity": 500,
            "registration_required": True,
            "registration_count": 287
        },
        {
            "name": "Baptism Sunday",
            "description": "Celebrate new believers taking the step of baptism",
            "location": "Main Sanctuary",
            "start_datetime": (today + timedelta(days=21)).strftime("%Y-%m-%dT11:00:00"),
            "is_public": True,
            "capacity": 5000,
            "registration_required": False,
            "registration_count": 23
        },
        {
            "name": "Marriage Retreat",
            "description": "Strengthen your marriage at our couples retreat",
            "location": "Pine Valley Resort",
            "start_datetime": (today + timedelta(days=45)).strftime("%Y-%m-%dT17:00:00"),
            "is_public": True,
            "capacity": 50,
            "registration_required": True,
            "registration_count": 34
        },
        {
            "name": "Volunteer Appreciation Dinner",
            "description": "Thank you dinner for all church volunteers",
            "location": "Fellowship Hall",
            "start_datetime": (today + timedelta(days=30)).strftime("%Y-%m-%dT18:00:00"),
            "is_public": False,
            "capacity": 300,
            "registration_required": True,
            "registration_count": 156
        }
    ]
    
    event_records = []
    for e in events:
        event = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **e
        }
        event_records.append(event)
    await db.events.insert_many(event_records)
    
    # Create activity log entries
    activities = [
        {"action": "member_added", "description": "New member added: Sarah Johnson", "entity_type": "person"},
        {"action": "donation_recorded", "description": "Donation of $1,500.00 recorded", "entity_type": "donation"},
        {"action": "group_created", "description": "New group created: Young Professionals", "entity_type": "group"},
        {"action": "event_created", "description": "New event created: Easter Service", "entity_type": "event"},
        {"action": "member_updated", "description": "Member status updated: John Smith → Active Member", "entity_type": "person"},
        {"action": "batch_closed", "description": "Batch closed: Sunday Offering 01/05/2025", "entity_type": "batch"},
        {"action": "email_sent", "description": "Email sent to 4,287 recipients: January Newsletter", "entity_type": "communication"},
        {"action": "attendance_recorded", "description": "Attendance recorded for Sunday 9AM: 3,421 attendees", "entity_type": "attendance"},
    ]
    
    activity_records = []
    for i, a in enumerate(activities):
        activity = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "entity_id": str(uuid.uuid4()),
            "created_at": (today - timedelta(hours=i*2)).isoformat(),
            **a
        }
        activity_records.append(activity)
    await db.activity_log.insert_many(activity_records)
    
    # Create communication templates
    communications = [
        {
            "subject": "Welcome to Abundant Church!",
            "body_html": "<h1>Welcome!</h1><p>We're so glad you visited us...</p>",
            "comm_type": "email",
            "status": "template",
            "recipient_count": 0
        },
        {
            "subject": "Prayer Request Follow-up",
            "body_html": "<p>Dear {first_name},</p><p>We've been praying for you...</p>",
            "comm_type": "email",
            "status": "template",
            "recipient_count": 0
        },
        {
            "subject": "You're Invited: {event_name}",
            "body_html": "<h2>{event_name}</h2><p>Join us for this special event...</p>",
            "comm_type": "email",
            "status": "template",
            "recipient_count": 0
        },
        {
            "subject": "Your Giving Statement",
            "body_html": "<h1>Annual Giving Statement</h1><p>Thank you for your generosity...</p>",
            "comm_type": "email",
            "status": "template",
            "recipient_count": 0
        }
    ]
    
    comm_records = []
    for c in communications:
        comm = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **c
        }
        comm_records.append(comm)
    await db.communications.insert_many(comm_records)
    
    return {
        "message": "Database seeded successfully",
        "seeded": True,
        "counts": {
            "tenant": 1,
            "households": len(households),
            "people": len(people),
            "groups": len(groups),
            "group_members": len(group_members),
            "funds": len(funds),
            "services": len(services),
            "attendance": len(attendance_records),
            "donations": len(donations),
            "recurring_giving": len(recurring_records),
            "pledges": len(pledges),
            "batches": len(batch_records),
            "events": len(event_records),
            "communications": len(comm_records)
        }
    }

# ============== MULTI-TENANT SEED ==============


@router.post("/seed-platform")
async def seed_platform():
    """Seed the entire Solomon AI platform with multiple churches and demo data"""
    import hashlib
    
    demo_password_hash = hashlib.sha256("Demo2026!".encode()).hexdigest()
    
    # Define the three demo churches
    churches = [
        {
            "id": "abundant-east-001",
            "name": "Abundant Church",
            "subdomain": "abundant",
            "plan": "enterprise",
            "member_limit": 100000,
            "subscription_status": "active",
            "address": "1556 George Dieter Dr",
            "city": "El Paso",
            "state": "TX",
            "timezone": "America/Denver",
            "website": "https://www.abundant.org",
            "phone": "(915) 755-3000",
            "primary_color": "#4f6ef7",
            "accent_color": "#00c896",
            "thinkific_url": "https://abundantchurch.thinkific.com/collections",
            "merch_embed_url": DEFAULT_MERCH_EMBED_URL
        },
        {
            "id": "cristoviene-church-001",
            "name": "Cristo Viene",
            "subdomain": "cristoviene",
            "plan": "enterprise",
            "member_limit": 50000,
            "subscription_status": "active",
            "address": "7500 N Loop Dr",
            "city": "El Paso",
            "state": "TX",
            "timezone": "America/Denver",
            "website": "https://cristoviene.org",
            "phone": "(915) 598-4000",
            "primary_color": "#dc2626",
            "accent_color": "#fbbf24",
            "thinkific_url": "https://cristoviene.thinkific.com",
            "merch_embed_url": DEFAULT_MERCH_EMBED_URL
        },
        {
            "id": "pottershouse-church-001",
            "name": "The Potter's House",
            "subdomain": "pottershouse",
            "plan": "enterprise",
            "member_limit": 100000,
            "subscription_status": "active",
            "address": "6777 W Kiest Blvd",
            "city": "Dallas",
            "state": "TX",
            "timezone": "America/Chicago",
            "website": "https://thepottershouse.org",
            "phone": "(214) 331-0954",
            "primary_color": "#7c3aed",
            "accent_color": "#ec4899",
            "thinkific_url": "https://pottershouse.thinkific.com",
            "merch_embed_url": DEFAULT_MERCH_EMBED_URL
        }
    ]
    
    results = {"churches": [], "platform_accounts": []}
    
    # Create/update Solomon platform admin accounts
    platform_accounts = [
        {
            "user_id": "platform_admin_001",
            "email": "admin@solomon.ai",
            "name": "Solomon Platform Admin",
            "role": "platform_admin",
            "tenant_id": None  # Platform admin has no tenant restriction
        },
        {
            "user_id": "platform_member_001",
            "email": "member@solomon.ai",
            "name": "Demo Member",
            "role": "member",
            "tenant_id": "abundant-east-001"  # Default to Abundant for demo
        },
        {
            "user_id": "platform_newmember_001",
            "email": "newmember@solomon.ai",
            "name": "New Member Demo",
            "role": "member",
            "tenant_id": "abundant-east-001"
        }
    ]
    
    for account in platform_accounts:
        await db.users.update_one(
            {"user_id": account["user_id"]},
            {"$set": {
                **account,
                "password_hash": demo_password_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }},
            upsert=True
        )
        results["platform_accounts"].append(account["email"])
    
    # Seed each church
    for church in churches:
        # Create/update tenant
        await db.tenants.update_one(
            {"id": church["id"]},
            {"$set": {
                **church,
                "created_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        # Create church admin account
        admin_email = f"admin@{church['subdomain']}.church"
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {
                "user_id": f"admin_{church['subdomain']}",
                "email": admin_email,
                "name": f"{church['name']} Admin",
                "role": "church_admin",
                "tenant_id": church["id"],
                "password_hash": demo_password_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }},
            upsert=True
        )
        
        # Create demo member account
        member_email = f"member@{church['subdomain']}.church"
        await db.users.update_one(
            {"email": member_email},
            {"$set": {
                "user_id": f"member_{church['subdomain']}",
                "email": member_email,
                "name": f"{church['name']} Member",
                "role": "member",
                "tenant_id": church["id"],
                "password_hash": demo_password_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }},
            upsert=True
        )
        
        # Generate 500 members for this church with 6 months of data
        existing_members = await db.people.count_documents({"tenant_id": church["id"]})
        if existing_members < 100:  # Only seed if not already seeded
            await seed_church_members(church["id"], church["name"], 500)
        
        results["churches"].append({
            "name": church["name"],
            "subdomain": church["subdomain"],
            "admin_email": admin_email,
            "member_email": member_email
        })
    
    # Seed media videos for Abundant Church (as demo content - matching member portal)
    abundant_videos = [
        {
            "id": "video_001",
            "tenant_id": "abundant-east-001",
            "title": "Community With a Purpose",
            "description": "Discover how the church is God's purposeful community - not a club but a family with divine purpose.",
            "youtube_id": "FoPI3hMbXvw",
            "youtube_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration": "40:45",
            "instructor": "Pastor Charles Nieman",
            "category_id": "community",
            "is_featured": True,
            "is_published": True,
            "badge": "New",
            "view_count": 1250,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_002",
            "tenant_id": "abundant-east-001",
            "title": "Blessing & Healing Through Humility",
            "description": "Learn how humility unlocks God's blessings and healing in your life.",
            "youtube_id": "pzpbbibEWPE",
            "youtube_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration": "38:30",
            "instructor": "Pastor Charles Nieman",
            "category_id": "faith",
            "is_featured": True,
            "is_published": True,
            "badge": "New",
            "view_count": 890,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_003",
            "tenant_id": "abundant-east-001",
            "title": "Building Your Life",
            "description": "Build your life on God's Word - biblical principles for personal spiritual development.",
            "youtube_id": "Lnj6vMvOLME",
            "youtube_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration": "45:00",
            "instructor": "Pastor Charles Nieman",
            "category_id": "growth",
            "is_featured": False,
            "is_published": True,
            "view_count": 1520,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_004",
            "tenant_id": "abundant-east-001",
            "title": "The Missing Peace",
            "description": "Find God's inner peace through grace and righteousness.",
            "youtube_id": "OjhMsB6czxc",
            "youtube_url": "https://youtube.com/watch?v=OjhMsB6czxc",
            "thumbnail_url": "https://i.ytimg.com/vi/OjhMsB6czxc/maxresdefault.jpg",
            "duration": "38:30",
            "instructor": "Pastor Charles Nieman",
            "category_id": "faith",
            "is_featured": True,
            "is_published": True,
            "view_count": 780,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_005",
            "tenant_id": "abundant-east-001",
            "title": "The Laws of Life",
            "description": "Your thoughts and beliefs shape your outcomes - learn the laws that govern life.",
            "youtube_id": "WQy48ANpj5c",
            "youtube_url": "https://youtube.com/watch?v=WQy48ANpj5c",
            "thumbnail_url": "https://i.ytimg.com/vi/WQy48ANpj5c/maxresdefault.jpg",
            "duration": "37:57",
            "instructor": "Pastor Charles Nieman",
            "category_id": "growth",
            "is_featured": False,
            "is_published": True,
            "view_count": 650,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_006",
            "tenant_id": "abundant-east-001",
            "title": "The Story Behind the Story",
            "description": "Discover the deeper meaning of Christmas and God's plan through Jesus' birth.",
            "youtube_id": "wCjwUQMhCIY",
            "youtube_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration": "37:30",
            "instructor": "Pastor Charles Nieman",
            "category_id": "faith",
            "is_featured": False,
            "is_published": True,
            "view_count": 430,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_007",
            "tenant_id": "abundant-east-001",
            "title": "Managing Your Emotions",
            "description": "Biblical wisdom on understanding and handling your emotions effectively.",
            "youtube_id": "0grr2E0kuFg",
            "youtube_url": "https://youtube.com/watch?v=0grr2E0kuFg",
            "thumbnail_url": "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
            "duration": "42:00",
            "instructor": "Pastor Charles Nieman",
            "category_id": "growth",
            "is_featured": False,
            "is_published": True,
            "badge": "Popular",
            "view_count": 2100,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_008",
            "tenant_id": "abundant-east-001",
            "title": "Worship In Spirit & In Truth",
            "description": "Experience authentic worship that transforms your relationship with God.",
            "youtube_id": "uwkmP6sDihI",
            "youtube_url": "https://youtube.com/watch?v=uwkmP6sDihI",
            "thumbnail_url": "https://i.ytimg.com/vi/uwkmP6sDihI/maxresdefault.jpg",
            "duration": "35:00",
            "instructor": "Pastor Jared Nieman",
            "category_id": "worship",
            "is_featured": False,
            "is_published": True,
            "view_count": 560,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_009",
            "tenant_id": "abundant-east-001",
            "title": "Vision Sunday 2025",
            "description": "The church's vision and community outreach efforts for the year ahead.",
            "youtube_id": "O0WfS3Ma2XM",
            "youtube_url": "https://youtube.com/watch?v=O0WfS3Ma2XM",
            "thumbnail_url": "https://i.ytimg.com/vi/O0WfS3Ma2XM/maxresdefault.jpg",
            "duration": "48:00",
            "instructor": "Pastor Jared Nieman",
            "category_id": "leadership",
            "is_featured": False,
            "is_published": True,
            "view_count": 1800,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_010",
            "tenant_id": "abundant-east-001",
            "title": "Abundant Conference 2025",
            "description": "Night 2 of the Abundant Conference featuring worship and powerful teaching.",
            "youtube_id": "kGXOOO6hHUk",
            "youtube_url": "https://youtube.com/watch?v=kGXOOO6hHUk",
            "thumbnail_url": "https://i.ytimg.com/vi/kGXOOO6hHUk/maxresdefault.jpg",
            "duration": "1:20:00",
            "instructor": "Pastor Marcos Witt",
            "category_id": "worship",
            "is_featured": True,
            "is_published": True,
            "badge": "Featured",
            "view_count": 3200,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_011",
            "tenant_id": "abundant-east-001",
            "title": "We Are Abundant",
            "description": "Understanding our calling to be a blessing to others in our community.",
            "youtube_id": "rMmIcJCDsaU",
            "youtube_url": "https://youtube.com/watch?v=rMmIcJCDsaU",
            "thumbnail_url": "https://i.ytimg.com/vi/rMmIcJCDsaU/maxresdefault.jpg",
            "duration": "40:00",
            "instructor": "Pastor Charles Nieman",
            "category_id": "community",
            "is_featured": False,
            "is_published": True,
            "view_count": 920,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_012",
            "tenant_id": "abundant-east-001",
            "title": "Faith That Moves Mountains",
            "description": "Discover the kind of faith that can move any mountain in your life.",
            "youtube_id": "3BHJSkx3J4E",
            "youtube_url": "https://youtube.com/watch?v=3BHJSkx3J4E",
            "thumbnail_url": "https://i.ytimg.com/vi/3BHJSkx3J4E/maxresdefault.jpg",
            "duration": "36:00",
            "instructor": "Pastor Charles Nieman",
            "category_id": "faith",
            "is_featured": False,
            "is_published": True,
            "view_count": 750,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Seed media categories
    categories = [
        {"id": "faith", "tenant_id": "abundant-east-001", "name": "Faith", "slug": "faith", "icon": "heart", "sort_order": 1},
        {"id": "family", "tenant_id": "abundant-east-001", "name": "Family", "slug": "family", "icon": "users", "sort_order": 2},
        {"id": "leadership", "tenant_id": "abundant-east-001", "name": "Leadership", "slug": "leadership", "icon": "briefcase", "sort_order": 3},
        {"id": "worship", "tenant_id": "abundant-east-001", "name": "Worship", "slug": "worship", "icon": "music", "sort_order": 4},
        {"id": "growth", "tenant_id": "abundant-east-001", "name": "Growth", "slug": "growth", "icon": "trending-up", "sort_order": 5},
        {"id": "community", "tenant_id": "abundant-east-001", "name": "Community", "slug": "community", "icon": "home", "sort_order": 6},
    ]
    
    # Insert categories
    for cat in categories:
        await db.media_categories.update_one(
            {"id": cat["id"], "tenant_id": cat["tenant_id"]},
            {"$set": cat},
            upsert=True
        )
    
    # Insert videos
    for video in abundant_videos:
        await db.media_videos.update_one(
            {"id": video["id"]},
            {"$set": video},
            upsert=True
        )

    # Seed Abundant Pathways courses
    pathways_courses = [
        {
            "id": "pathway_course_001",
            "tenant_id": "abundant-east-001",
            "title": "Abundant Next Steps",
            "description": "Your on-ramp to belonging, serving, and growing at Abundant.",
            "cover_image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
            "category": "New Members Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_002",
            "tenant_id": "abundant-east-001",
            "title": "Preparing for Baptism",
            "description": "Understand baptism and get ready to share your story.",
            "cover_image_url": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=80",
            "category": "Baptism Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_003",
            "tenant_id": "abundant-east-001",
            "title": "Foundations of Discipleship",
            "description": "Build daily rhythms of scripture, prayer, and obedience.",
            "cover_image_url": "https://images.unsplash.com/photo-1529070538774-1843cb3265df?auto=format&fit=crop&w=1200&q=80",
            "category": "Discipleship Track",
            "level": "Intermediate",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_004",
            "tenant_id": "abundant-east-001",
            "title": "Financial Peace University",
            "description": "Walk through budgeting, generosity, and debt-free living.",
            "cover_image_url": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80",
            "category": "Stewardship Track",
            "level": "Intermediate",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_005",
            "tenant_id": "abundant-east-001",
            "title": "Serving with Purpose",
            "description": "Discover your gifts and find the right team to serve.",
            "cover_image_url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80",
            "category": "Leadership Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_006",
            "tenant_id": "abundant-east-001",
            "title": "Prayer & Presence",
            "description": "Deepen your prayer life and sensitivity to God's presence.",
            "cover_image_url": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1200&q=80",
            "category": "Spiritual Practices",
            "level": "Intermediate",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_007",
            "tenant_id": "abundant-east-001",
            "title": "Marriage & Family Care",
            "description": "Strengthen your relationships and build a healthy home.",
            "cover_image_url": "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=1200&q=80",
            "category": "Family Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_008",
            "tenant_id": "abundant-east-001",
            "title": "Mission & Outreach",
            "description": "Live on mission through local and global outreach.",
            "cover_image_url": "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?auto=format&fit=crop&w=1200&q=80",
            "category": "Outreach Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    pathways_lessons = [
        {
            "id": "pathway_lesson_001",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_001",
            "title": "Welcome to Abundant",
            "description": "Meet the heart, mission, and values of Abundant Church.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "15:40",
            "duration_seconds": 940,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_002",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_001",
            "title": "Belonging & Community",
            "description": "Find your people and take your next step into community.",
            "youtube_id": "pzpbbibEWPE",
            "video_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration_label": "18:20",
            "duration_seconds": 1100,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_003",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_002",
            "title": "Why Baptism Matters",
            "description": "Understand the significance of baptism and next steps.",
            "youtube_id": "Lnj6vMvOLME",
            "video_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration_label": "16:05",
            "duration_seconds": 965,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_004",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_002",
            "title": "Preparing Your Story",
            "description": "Craft your testimony and prepare for the baptism service.",
            "youtube_id": "wCjwUQMhCIY",
            "video_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration_label": "14:35",
            "duration_seconds": 875,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_005",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_003",
            "title": "Daily Discipleship",
            "description": "Develop a daily walk with Jesus through scripture and prayer.",
            "youtube_id": "0grr2E0kuFg",
            "video_url": "https://youtube.com/watch?v=0grr2E0kuFg",
            "thumbnail_url": "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
            "duration_label": "20:10",
            "duration_seconds": 1210,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_006",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_003",
            "title": "Scripture & Spirit",
            "description": "Learn to listen to God's voice and apply the word.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "19:05",
            "duration_seconds": 1145,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_007",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_004",
            "title": "Budgeting with Purpose",
            "description": "Build a budget aligned with your values and goals.",
            "youtube_id": "pzpbbibEWPE",
            "video_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration_label": "21:20",
            "duration_seconds": 1280,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_008",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_004",
            "title": "Debt-Free Journey",
            "description": "Steps to reduce debt and build margin for generosity.",
            "youtube_id": "Lnj6vMvOLME",
            "video_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration_label": "17:30",
            "duration_seconds": 1050,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_009",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_005",
            "title": "Discover Your Gifts",
            "description": "Identify your gifts and how they serve the church.",
            "youtube_id": "wCjwUQMhCIY",
            "video_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration_label": "14:55",
            "duration_seconds": 895,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_010",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_005",
            "title": "Serving Teams",
            "description": "Explore serving opportunities and next steps.",
            "youtube_id": "0grr2E0kuFg",
            "video_url": "https://youtube.com/watch?v=0grr2E0kuFg",
            "thumbnail_url": "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
            "duration_label": "13:50",
            "duration_seconds": 830,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_011",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_006",
            "title": "Prayer Rhythm",
            "description": "Create a daily prayer rhythm that anchors your week.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "18:00",
            "duration_seconds": 1080,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_012",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_006",
            "title": "Hearing God's Voice",
            "description": "Learn to discern and respond to God's leading.",
            "youtube_id": "wCjwUQMhCIY",
            "video_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration_label": "17:15",
            "duration_seconds": 1035,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_013",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_007",
            "title": "Healthy Relationships",
            "description": "Build healthy rhythms in your marriage and family.",
            "youtube_id": "pzpbbibEWPE",
            "video_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration_label": "16:45",
            "duration_seconds": 1005,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_014",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_007",
            "title": "Family Devotions",
            "description": "Practical ideas for discipleship at home.",
            "youtube_id": "Lnj6vMvOLME",
            "video_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration_label": "15:30",
            "duration_seconds": 930,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_015",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_008",
            "title": "Living on Mission",
            "description": "Share your faith through local outreach.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "17:05",
            "duration_seconds": 1025,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_016",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_008",
            "title": "Community Outreach",
            "description": "Plan practical ways to serve El Paso together.",
            "youtube_id": "0grr2E0kuFg",
            "video_url": "https://youtube.com/watch?v=0grr2E0kuFg",
            "thumbnail_url": "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
            "duration_label": "18:35",
            "duration_seconds": 1115,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    for course in pathways_courses:
        await db.pathways_courses.update_one(
            {"id": course["id"]},
            {"$set": course},
            upsert=True
        )

    for lesson in pathways_lessons:
        await db.pathways_lessons.update_one(
            {"id": lesson["id"]},
            {"$set": lesson},
            upsert=True
        )

    # Assign demo member to pathways courses
    enrollments = []
    for idx, course in enumerate(pathways_courses, start=1):
        enrollments.append({
            "id": f"pathway_enroll_{idx:03d}",
            "tenant_id": "abundant-east-001",
            "course_id": course["id"],
            "user_id": "member_abundant",
            "assigned_by": "admin_abundant",
            "status": "assigned",
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

    for enrollment in enrollments:
        await db.pathways_enrollments.update_one(
            {"id": enrollment["id"]},
            {"$set": enrollment},
            upsert=True
        )

    return {
        "message": "Platform seeded successfully",
        "results": results,
        "demo_credentials": {
            "password": "Demo2026!",
            "platform_admin": "admin@solomon.ai",
            "abundant_admin": "admin@abundant.church",
            "cristoviene_admin": "admin@cristoviene.church",
            "pottershouse_admin": "admin@pottershouse.church"
        }
    }

async def seed_church_members(tenant_id: str, church_name: str, count: int = 500):
    """Generate realistic church members with 6 months of giving/attendance data"""
    
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
                   "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
                   "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
                   "Matthew", "Betty", "Anthony", "Margaret", "Carlos", "Maria", "Juan", "Sofia",
                   "Miguel", "Isabella", "Diego", "Valentina", "Roberto", "Ana", "Luis", "Carmen"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                  "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
                  "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
                  "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
    
    statuses = ["member", "member", "member", "member", "visitor", "regular"]
    
    people = []
    donations = []
    attendance_records = []
    
    today = datetime.now(timezone.utc)
    six_months_ago = today - timedelta(days=180)
    
    fund_names = ["General Fund", "Building Fund", "Missions", "Benevolence", "Youth Ministry"]
    
    for i in range(count):
        person_id = str(uuid.uuid4())
        first_name = _rng.choice(first_names)
        last_name = _rng.choice(last_names)
        
        person = {
            "id": person_id,
            "tenant_id": tenant_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@email.com",
            "mobile_phone": f"({_rng.randint(200, 999)}) {_rng.randint(200, 999)}-{_rng.randint(1000, 9999)}",
            "date_of_birth": f"{_rng.randint(1960, 2005)}-{_rng.randint(1, 12):02d}-{_rng.randint(1, 28):02d}",
            "gender": _rng.choice(["male", "female"]),
            "membership_status": _rng.choice(statuses),
            "membership_date": (six_months_ago + timedelta(days=_rng.randint(0, 180))).strftime("%Y-%m-%d"),
            "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={person_id}",
            "engagement_score": _rng.randint(30, 100),
            "ytd_giving": 0,
            "lifetime_giving": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        people.append(person)
        
        # Generate donations (6 months of history)
        if _rng.random() > 0.3:  # 70% of members give
            num_donations = _rng.randint(3, 24)  # 3-24 donations over 6 months
            person_total = 0
            for _ in range(num_donations):
                donation_date = six_months_ago + timedelta(days=_rng.randint(0, 180))
                amount = _rng.choice([25, 50, 100, 150, 200, 250, 500, 1000])
                donation = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "person_id": person_id,
                    "donor_name": f"{first_name} {last_name}",
                    "amount": amount,
                    "fund_name": _rng.choice(fund_names),
                    "donation_date": donation_date.strftime("%Y-%m-%d"),
                    "payment_method": _rng.choice(["card", "ach", "cash", "check"]),
                    "payment_status": "completed",
                    "created_at": donation_date.isoformat()
                }
                donations.append(donation)
                person_total += amount
            person["ytd_giving"] = person_total
            person["lifetime_giving"] = person_total * _rng.uniform(1, 3)
        
        # Generate attendance (6 months)
        if _rng.random() > 0.2:  # 80% have some attendance
            num_attendances = _rng.randint(5, 24)  # 5-24 services over 6 months
            for _ in range(num_attendances):
                att_date = six_months_ago + timedelta(days=_rng.randint(0, 180))
                att_record = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "person_id": person_id,
                    "person_name": f"{first_name} {last_name}",
                    "service_name": _rng.choice(["Sunday 9AM", "Sunday 11AM", "Wednesday Night"]),
                    "check_in_time": att_date.isoformat(),
                    "created_at": att_date.isoformat()
                }
                attendance_records.append(att_record)
    
    # Bulk insert
    if people:
        await db.people.insert_many(people)
    if donations:
        await db.donations.insert_many(donations)
    if attendance_records:
        await db.attendance.insert_many(attendance_records)
    
    logger.info(f"Seeded {len(people)} members for {church_name}")
    return len(people)

# ============== SUMMIT ENHANCEMENTS - SERVICE MODE & ATTENDANCE STREAKS ==============

class ServiceModeStatus(BaseModel):
    is_service_day: bool
    is_service_time: bool
    current_service: Optional[Dict[str, Any]] = None
    next_service: Optional[Dict[str, Any]] = None
    attendance_streak: int = 0
    check_in_status: Optional[str] = None  # 'in_person', 'online', None

class AttendanceStreakData(BaseModel):
    current_streak: int = 0
    longest_streak: int = 0
    total_attended: int = 0
    last_attendance: Optional[str] = None
    streak_badges: List[Dict[str, Any]] = []

class PrayerRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    user_name: str
    category: str = "general"  # general, healing, family, financial, guidance, thanksgiving
    title: str
    content: str
    is_public: bool = False  # For prayer wall
    is_anonymous: bool = False
    prayer_count: int = 0  # How many people prayed
    status: str = "active"  # active, answered, closed
    admin_notes: Optional[str] = None
    follow_up_date: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class PrayerRequestCreate(BaseModel):
    category: str = "general"
    title: str
    content: str
    is_public: bool = False
    is_anonymous: bool = False

class MemberCheckIn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    service_id: Optional[str] = None
    check_in_type: str = "in_person"  # 'in_person' or 'online'
    service_date: str
    check_in_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== SERVICE MODE ENDPOINTS ==============


@router.get("/platform/health-scores")
async def get_all_health_scores(request: Request):
    """Get Church Health Scores for all tenants."""
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
    results = []
    for t in tenants:
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": t["id"]}, {"_id": 0})
        health = compute_health_score(cached, t)
        results.append({
            "tenant_id": t["id"],
            "name": t["name"],
            "location": t.get("location", ""),
            "plan": t.get("plan", ""),
            "members": cached.get("total_members", 0) if cached else 0,
            "health": health,
        })

    results.sort(key=lambda x: x["health"]["score"], reverse=True)
    return {"churches": results}


@router.get("/platform/churches")
async def get_all_platform_churches(request: Request):
    """List all church tenants with metrics and health scores."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    tenants = await db.tenants.find({"subscription_status": "active"}, {"_id": 0}).to_list(100)
    churches = []
    now = datetime.now(timezone.utc)
    year_start = now.replace(month=1, day=1).strftime("%Y-%m-%d")
    month_start = now.replace(day=1).strftime("%Y-%m-%d")

    for t in tenants:
        tid = t["id"]
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": tid}, {"_id": 0})
        health = compute_health_score(cached, t)
        # Giving metrics
        alltime = await db.donations.aggregate([
            {"$match": {"tenant_id": tid, "status": "completed"}},
            {"$group": {"_id": None, "vol": {"$sum": "$amount"}, "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}}, "cnt": {"$sum": 1}}}
        ]).to_list(1)
        ytd_r = await db.donations.aggregate([
            {"$match": {"tenant_id": tid, "donation_date": {"$gte": year_start}}},
            {"$group": {"_id": None, "vol": {"$sum": "$amount"}}}
        ]).to_list(1)
        mtd_r = await db.donations.aggregate([
            {"$match": {"tenant_id": tid, "donation_date": {"$gte": month_start}}},
            {"$group": {"_id": None, "vol": {"$sum": "$amount"}}}
        ]).to_list(1)
        churches.append({
            "id": tid,
            "name": t.get("name", ""),
            "city": t.get("city", ""),
            "state": t.get("state", ""),
            "plan": t.get("plan", "starter"),
            "subdomain": t.get("subdomain", ""),
            "total_members": cached.get("total_members", 0) if cached else 0,
            "giving": round(alltime[0]["vol"] if alltime else 0, 2),
            "fees": round(alltime[0]["fees"] if alltime else 0, 2),
            "txn_count": alltime[0]["cnt"] if alltime else 0,
            "ytd_giving": round(ytd_r[0]["vol"] if ytd_r else 0, 2),
            "mtd_giving": round(mtd_r[0]["vol"] if mtd_r else 0, 2),
            "health": health,
        })

    churches.sort(key=lambda x: x["giving"], reverse=True)
    return {"churches": churches, "total": len(churches)}

# ============== PLATFORM CHURCH ONBOARDING (Task 2) ==============

class ChurchOnboardingRequest(BaseModel):
    name: str
    city: str = ""
    state: str = ""
    denomination: str = ""
    website: str = ""
    service_times: list = []
    primary_color: str = "#2563eb"
    subdomain: str = ""
    admin_name: str = ""
    admin_email: str = ""
    admin_password: str = ""
    admin_phone: str = ""
    estimated_members: int = 0
    plan: str = "starter"


@router.post("/platform/churches/create")
async def create_church_onboarding(request: Request, payload: ChurchOnboardingRequest):
    """5-step church onboarding wizard — creates a new tenant with admin account."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    if not payload.name:
        raise HTTPException(status_code=400, detail="Church name is required")
    if not payload.admin_email:
        raise HTTPException(status_code=400, detail="Admin email is required")

    subdomain = payload.subdomain or payload.name.lower().replace(" ", "-").replace("'", "")[:30]
    existing = await db.tenants.find_one({"subdomain": subdomain})
    if existing:
        raise HTTPException(status_code=409, detail=f"Subdomain '{subdomain}' is already taken")

    existing_email = await db.users.find_one({"email": payload.admin_email.lower()})
    if existing_email:
        raise HTTPException(status_code=409, detail=f"Email '{payload.admin_email}' is already registered")

    tenant_id = f"{subdomain}-001"
    now_iso = datetime.now(timezone.utc).isoformat()

    tenant = {
        "id": tenant_id,
        "name": payload.name,
        "subdomain": subdomain,
        "city": payload.city,
        "state": payload.state,
        "denomination": payload.denomination,
        "website": payload.website,
        "primary_color": payload.primary_color,
        "plan": payload.plan,
        "subscription_status": "active",
        "estimated_members": payload.estimated_members,
        "service_times": payload.service_times,
        "created_at": now_iso,
        "onboarded_by": user.get("user_id")
    }
    await db.tenants.insert_one({**tenant})

    import bcrypt as _bc; admin_password_hash = _bc.hashpw((payload.admin_password or "Welcome2026!").encode("utf-8"), _bc.gensalt()).decode("utf-8")
    admin_user = {
        "user_id": str(uuid.uuid4()),
        "email": payload.admin_email.lower(),
        "password_hash": admin_password_hash,
        "name": payload.admin_name or payload.name + " Admin",
        "role": "church_admin",
        "role_title": "Church Administrator",
        "permissions": ROLE_TEMPLATES["church_admin"]["permissions"],
        "tenant_id": tenant_id,
        "phone": payload.admin_phone,
        "created_at": now_iso,
        "is_verified": True
    }
    await db.users.insert_one({**admin_user})

    await audit_log("church_created", "tenant", tenant_id, tenant_id, user.get("user_id"), user.get("name", ""), {}, {"tenant": payload.name, "admin_email": payload.admin_email}, request)

    return {
        "success": True,
        "tenant_id": tenant_id,
        "subdomain": subdomain,
        "church_name": payload.name,
        "admin_email": payload.admin_email,
        "admin_user_id": admin_user["user_id"],
        "message": f"Church '{payload.name}' created successfully with admin account."
    }


# ============== PLATFORM USER MANAGEMENT ==============


@router.post("/platform/users/create")
async def platform_create_user(request: Request, payload: dict):
    """Platform admin creates a user tied to a specific church."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    admin = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not admin or admin.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    email = (payload.get("email") or "").strip().lower()
    name = (payload.get("name") or "").strip()
    tenant_id = payload.get("tenant_id")
    role_template = payload.get("role_template", "member")
    password = payload.get("password", "Welcome2026!")

    if not email or not name or not tenant_id:
        raise HTTPException(status_code=400, detail="email, name, and tenant_id are required")

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Church '{tenant_id}' not found")

    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail=f"Email '{email}' is already registered")

    if role_template not in ROLE_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid role_template. Options: {', '.join(sorted(ROLE_TEMPLATES.keys()))}")

    tmpl = ROLE_TEMPLATES[role_template]
    role_field = role_template if role_template in ("church_admin", "platform_admin", "member") else ("church_admin" if any(p.startswith("admin.") for p in tmpl["permissions"]) else "member")

    new_user = {
        "user_id": str(uuid.uuid4()),
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        "name": name,
        "first_name": name.split()[0] if name.split() else name,
        "last_name": name.split()[-1] if len(name.split()) > 1 else "",
        "role": role_field,
        "role_title": tmpl["role_title"],
        "permissions": tmpl["permissions"],
        "tenant_id": tenant_id,
        "church_id": tenant_id,
        "is_active": True,
        "membership_status": "Active",
        "email_verified": True,
        "registration_source": "platform_created",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "directory_visible": True,
        "share_email": True,
        "share_phone": True,
    }
    await db.users.insert_one({**new_user})

    await db.people.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": new_user["user_id"],
        "name": name,
        "first_name": new_user["first_name"],
        "last_name": new_user["last_name"],
        "email": email,
        "role": role_field,
        "membership_status": "Active",
        "tenant_id": tenant_id,
        "created_at": new_user["created_at"],
        "directory_visible": True,
        "share_email": True,
        "share_phone": True,
        "groups": [],
        "tags": [],
    })

    await audit_log("user_created", "user", new_user["user_id"], tenant_id, admin.get("user_id"), admin.get("name", ""), {}, {"email": email, "name": name, "role": role_field, "church": tenant.get("name")}, request)

    return {
        "success": True,
        "user_id": new_user["user_id"],
        "email": email,
        "name": name,
        "role": role_field,
        "role_title": tmpl["role_title"],
        "church": tenant.get("name"),
        "message": f"User '{name}' created for {tenant.get('name')}"
    }


@router.put("/platform/users/{user_id}/promote")
async def platform_promote_user(request: Request, user_id: str, payload: dict):
    """Platform admin promotes a member to admin (or changes their role template)."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    admin = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not admin or admin.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    role_template = payload.get("role_template", "church_admin")
    if role_template not in ROLE_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Options: {', '.join(sorted(ROLE_TEMPLATES.keys()))}")

    tmpl = ROLE_TEMPLATES[role_template]
    role_field = role_template if role_template in ("church_admin", "platform_admin", "member") else ("church_admin" if any(p.startswith("admin.") for p in tmpl["permissions"]) else "member")

    before = {"role": target.get("role"), "role_title": target.get("role_title"), "permissions": get_permissions_for_user(target)}

    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "role": role_field,
            "role_title": tmpl["role_title"],
            "permissions": tmpl["permissions"],
        }}
    )

    after = {"role": role_field, "role_title": tmpl["role_title"], "permissions": tmpl["permissions"]}
    await audit_log("role_promotion", "user", user_id, target.get("tenant_id", ""), admin.get("user_id"), admin.get("name", ""), before, after, request)

    return {
        "success": True,
        "user_id": user_id,
        "name": target.get("name"),
        "email": target.get("email"),
        "new_role": role_field,
        "role_title": tmpl["role_title"],
        "permissions_count": len(tmpl["permissions"]),
        "message": f"{target.get('name')} promoted to {tmpl['role_title']}"
    }


# ============== ORGANIZATIONS & CAMPUS COMPARISON (Universal Multi-Campus) ==============


@router.get("/platform/organizations")
async def list_organizations(request: Request):
    """List all multi-campus organizations with their campuses."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    tenants = await db.tenants.find({"organization_id": {"$exists": True, "$ne": None}}, {"_id": 0}).to_list(200)

    orgs = {}
    for t in tenants:
        org_id = t["organization_id"]
        if org_id not in orgs:
            orgs[org_id] = {
                "organization_id": org_id,
                "organization_name": t.get("organization_name", org_id),
                "campuses": [],
                "total_members": 0,
                "total_mrr": 0,
                "total_mtd_giving": 0,
            }
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": t["id"]}, {"_id": 0})
        campus_info = {
            "tenant_id": t["id"],
            "name": t["name"],
            "location": t.get("location", ""),
            "plan": t.get("plan", ""),
            "mrr": float(t.get("mrr", 0) or 0),
            "subscription_status": t.get("subscription_status", "active"),
            "members": cached.get("total_members", 0) if cached else 0,
            "active_members": cached.get("active_members", 0) if cached else 0,
            "mtd_giving": cached.get("mtd_giving", 0) if cached else 0,
            "ytd_giving": cached.get("ytd_giving", 0) if cached else 0,
            "weekly_attendance": cached.get("last_attendance", 0) if cached else 0,
            "groups": cached.get("active_groups", 0) if cached else 0,
            "cafe_orders_week": cached.get("cafe_orders_week", 0) if cached else 0,
            "merch_orders_week": cached.get("merch_orders_week", 0) if cached else 0,
            "recurring_givers": cached.get("recurring_givers", 0) if cached else 0,
        }
        orgs[org_id]["campuses"].append(campus_info)
        orgs[org_id]["total_members"] += campus_info["members"]
        orgs[org_id]["total_mrr"] += campus_info["mrr"]
        orgs[org_id]["total_mtd_giving"] += campus_info["mtd_giving"]

    return list(orgs.values())


@router.get("/platform/organizations/{org_id}/comparison")
async def get_campus_comparison(org_id: str, request: Request):
    """Get detailed campus comparison metrics for a multi-campus organization."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    tenants = await db.tenants.find({"organization_id": org_id}, {"_id": 0}).to_list(50)
    if not tenants:
        raise HTTPException(status_code=404, detail="Organization not found")

    org_name = tenants[0].get("organization_name", org_id)
    campuses = []
    totals = {"members": 0, "active": 0, "attendance": 0, "mtd_giving": 0, "ytd_giving": 0, "groups": 0, "mrr": 0,
              "cafe_orders": 0, "cafe_giving": 0, "merch_orders": 0, "merch_giving": 0, "recurring_givers": 0}

    for t in tenants:
        tid = t["id"]
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": tid}, {"_id": 0})
        c = cached or {}

        members = c.get("total_members", 0)
        active = c.get("active_members", 0)
        attendance = c.get("last_attendance", 0)
        mtd = c.get("mtd_giving", 0)
        ytd = c.get("ytd_giving", 0)
        groups = c.get("active_groups", 0)
        cafe_orders = c.get("cafe_orders_week", 0)
        cafe_giving = c.get("cafe_giving_added", 0)
        merch_orders = c.get("merch_orders_week", 0)
        merch_giving = c.get("merch_giving_added", 0)
        recurring = c.get("recurring_givers", 0)

        campus = {
            "tenant_id": tid,
            "name": t["name"],
            "location": t.get("location", ""),
            "plan": t.get("plan", ""),
            "mrr": float(t.get("mrr", 0) or 0),
            "metrics": {
                "total_members": members,
                "active_members": active,
                "engagement_rate": round((active / members * 100), 1) if members > 0 else 0,
                "weekly_attendance": attendance,
                "attendance_rate": round((attendance / members * 100), 1) if members > 0 else 0,
                "mtd_giving": mtd,
                "ytd_giving": ytd,
                "giving_per_capita": round(mtd / members, 2) if members > 0 else 0,
                "recurring_givers": recurring,
                "recurring_rate": round((recurring / members * 100), 1) if members > 0 else 0,
                "active_groups": groups,
                "members_per_group": round(members / groups, 0) if groups > 0 else 0,
                "cafe_orders_week": cafe_orders,
                "cafe_giving_added": cafe_giving,
                "merch_orders_week": merch_orders,
                "merch_giving_added": merch_giving,
            }
        }
        campuses.append(campus)

        for k in totals:
            if k == "members": totals[k] += members
            elif k == "active": totals[k] += active
            elif k == "attendance": totals[k] += attendance
            elif k == "mtd_giving": totals[k] += mtd
            elif k == "ytd_giving": totals[k] += ytd
            elif k == "groups": totals[k] += groups
            elif k == "mrr": totals[k] += float(t.get("mrr", 0) or 0)
            elif k == "cafe_orders": totals[k] += cafe_orders
            elif k == "cafe_giving": totals[k] += cafe_giving
            elif k == "merch_orders": totals[k] += merch_orders
            elif k == "merch_giving": totals[k] += merch_giving
            elif k == "recurring_givers": totals[k] += recurring

    # Giving trends by campus (last 4 weeks)
    giving_trends = []
    for week_offset in range(4):
        week_end = NOW - timedelta(weeks=week_offset)
        week_start = week_end - timedelta(days=7)
        week_label = week_start.strftime("%b %d")
        week_data = {"week": week_label}
        for t in tenants:
            pipeline = [
                {"$match": {
                    "tenant_id": t["id"],
                    "donation_date": {"$gte": week_start.strftime("%Y-%m-%d"), "$lt": week_end.strftime("%Y-%m-%d")}
                }},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            result = await db.donations.aggregate(pipeline).to_list(1)
            week_data[t["name"]] = result[0]["total"] if result else 0
        giving_trends.append(week_data)

    giving_trends.reverse()

    return {
        "organization_id": org_id,
        "organization_name": org_name,
        "campus_count": len(campuses),
        "campuses": campuses,
        "totals": {
            "total_members": totals["members"],
            "total_active": totals["active"],
            "total_attendance": totals["attendance"],
            "total_mtd_giving": totals["mtd_giving"],
            "total_ytd_giving": totals["ytd_giving"],
            "total_groups": totals["groups"],
            "total_mrr": totals["mrr"],
            "total_cafe_orders": totals["cafe_orders"],
            "total_merch_orders": totals["merch_orders"],
            "engagement_rate": round((totals["active"] / totals["members"] * 100), 1) if totals["members"] > 0 else 0,
            "giving_per_capita": round(totals["mtd_giving"] / totals["members"], 2) if totals["members"] > 0 else 0,
        },
        "giving_trends": giving_trends,
    }


# ============== GIVING NUDGE CHECKOUT FLOW ==============

class CheckoutWithNudgeRequest(BaseModel):
    items: List[Dict[str, Any]]
    giving_amount: float = 0
    giving_fund: str = "General Fund"
    payment_method_id: Optional[str] = None
    order_type: str = "cafe"  # "cafe" or "merch"
    pickup_time: Optional[str] = None


@router.get("/platform/health")
async def platform_health(request: Request):
    """System health check for platform admin dashboard."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    # DB health check
    db_healthy = True
    try:
        await db.command("ping")
    except Exception:
        db_healthy = False

    # Active sessions
    active_sessions = await db.user_sessions.count_documents({
        "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
    })

    # Failed logins (check for any rate limiting triggers)
    twenty_four_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    recent_activity = await db.activity_log.count_documents({
        "created_at": {"$gte": twenty_four_hours_ago}
    })

    total_collections = await db.list_collection_names()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": {
            "status": "connected" if db_healthy else "disconnected",
            "collections": len(total_collections),
        },
        "sessions": {
            "active_now": active_sessions,
        },
        "activity": {
            "events_24h": recent_activity,
        },
        "uptime": "99.9%",
        "checked_at": datetime.now(timezone.utc).isoformat()
    }

# NOW is used in comparison endpoint
NOW = datetime.now(timezone.utc)

# ============== PUBLIC ENDPOINTS (NO AUTH) ==============



# ============== GODMODE REVENUE DASHBOARD ==============

SOLOMON_FEE_RATE = 0.019  # 1.9%
SOLOMON_FEE_FLAT = 0.30   # $0.30 per transaction


@router.get("/platform/revenue")
async def get_platform_revenue(request: Request):
    """Godmode Revenue Dashboard — Processing fees earned by Solomon AI"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    # Revenue by church
    church_pipeline = [
        {"$match": {"source": "solomonpay", "status": "completed"}},
        {"$group": {
            "_id": "$tenant_id",
            "total_volume": {"$sum": "$amount"},
            "total_fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}},
            "txn_count": {"$sum": 1},
        }},
        {"$sort": {"total_volume": -1}},
    ]
    church_results = await db.donations.aggregate(church_pipeline).to_list(50)

    churches = []
    for r in church_results:
        if not r["_id"]:
            continue
        tenant = await db.tenants.find_one({"id": r["_id"]}, {"_id": 0, "name": 1, "church_name": 1})
        name = (tenant.get("name") or tenant.get("church_name") or r["_id"]) if tenant else r["_id"]
        # Recalculate fees if solomon_fee not stored
        fees = r["total_fees"] if r["total_fees"] > 0 else round(r["total_volume"] * SOLOMON_FEE_RATE + r["txn_count"] * SOLOMON_FEE_FLAT, 2)
        churches.append({
            "tenant_id": r["_id"],
            "name": name,
            "total_volume": round(r["total_volume"], 2),
            "total_fees": round(fees, 2),
            "txn_count": r["txn_count"],
        })

    # Revenue by year
    year_pipeline = [
        {"$match": {"source": "solomonpay", "status": "completed"}},
        {"$addFields": {"year": {"$substr": ["$donation_date", 0, 4]}}},
        {"$group": {
            "_id": "$year",
            "total_volume": {"$sum": "$amount"},
            "total_fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}},
            "txn_count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    year_results = await db.donations.aggregate(year_pipeline).to_list(10)
    by_year = []
    for r in year_results:
        fees = r["total_fees"] if r["total_fees"] > 0 else round(r["total_volume"] * SOLOMON_FEE_RATE + r["txn_count"] * SOLOMON_FEE_FLAT, 2)
        by_year.append({
            "year": r["_id"],
            "total_volume": round(r["total_volume"], 2),
            "total_fees": round(fees, 2),
            "txn_count": r["txn_count"],
        })

    # Revenue by year by church (for detailed breakdown)
    detail_pipeline = [
        {"$match": {"source": "solomonpay", "status": "completed"}},
        {"$addFields": {"year": {"$substr": ["$donation_date", 0, 4]}}},
        {"$group": {
            "_id": {"tenant_id": "$tenant_id", "year": "$year"},
            "volume": {"$sum": "$amount"},
            "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}},
            "txn_count": {"$sum": 1},
        }},
        {"$sort": {"_id.year": 1}},
    ]
    detail_results = await db.donations.aggregate(detail_pipeline).to_list(200)
    by_church_year = {}
    for r in detail_results:
        tid = r["_id"]["tenant_id"]
        yr = r["_id"]["year"]
        if not tid:
            continue
        if tid not in by_church_year:
            by_church_year[tid] = {}
        fees = r["fees"] if r["fees"] > 0 else round(r["volume"] * SOLOMON_FEE_RATE + r["txn_count"] * SOLOMON_FEE_FLAT, 2)
        by_church_year[tid][yr] = {
            "volume": round(r["volume"], 2),
            "fees": round(fees, 2),
            "txn_count": r["txn_count"],
        }

    # Monthly trend (last 12 months)
    monthly_pipeline = [
        {"$match": {"source": "solomonpay", "status": "completed"}},
        {"$addFields": {"month": {"$substr": ["$donation_date", 0, 7]}}},
        {"$group": {
            "_id": "$month",
            "volume": {"$sum": "$amount"},
            "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}},
            "txn_count": {"$sum": 1},
        }},
        {"$sort": {"_id": -1}},
        {"$limit": 36},
    ]
    monthly_results = await db.donations.aggregate(monthly_pipeline).to_list(36)
    monthly_trend = []
    for r in sorted(monthly_results, key=lambda x: x["_id"]):
        fees = r["fees"] if r["fees"] > 0 else round(r["volume"] * SOLOMON_FEE_RATE + r["txn_count"] * SOLOMON_FEE_FLAT, 2)
        monthly_trend.append({
            "month": r["_id"],
            "volume": round(r["volume"], 2),
            "fees": round(fees, 2),
            "txn_count": r["txn_count"],
        })

    # Grand totals
    total_volume = sum(c["total_volume"] for c in churches)
    total_fees = sum(c["total_fees"] for c in churches)
    total_txns = sum(c["txn_count"] for c in churches)

    return {
        "summary": {
            "total_processing_volume": round(total_volume, 2),
            "total_fees_earned": round(total_fees, 2),
            "total_transactions": total_txns,
            "active_churches": len(churches),
            "fee_rate": f"{SOLOMON_FEE_RATE * 100:.1f}% + ${SOLOMON_FEE_FLAT:.2f}",
            "industry_rate": "2.5% + $0.30",
            "savings_vs_industry": "24% cheaper",
        },
        "by_church": churches,
        "by_year": by_year,
        "by_church_year": {
            tid: {
                "name": next((c["name"] for c in churches if c["tenant_id"] == tid), tid),
                "years": data,
            }
            for tid, data in by_church_year.items()
        },
        "monthly_trend": monthly_trend,
    }


# ═══════════════════ PLATFORM TRANSACTIONS ═══════════════════

@router.get("/platform/transactions")
async def get_platform_transactions(request: Request, page: int = 1, limit: int = 50, church: str = "", status: str = "", method: str = "", fund: str = "", search: str = "", start_date: str = "", end_date: str = ""):
    """All transactions across platform with filters, pagination, search."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    query = {}
    if church:
        query["tenant_id"] = church
    if status:
        query["status"] = status
    if method:
        query["payment_method"] = method
    if fund:
        query["fund_name"] = fund
    if search:
        query["$or"] = [
            {"donor_name": {"$regex": search, "$options": "i"}},
            {"person_name": {"$regex": search, "$options": "i"}},
            {"person_email": {"$regex": search, "$options": "i"}},
        ]
    if start_date:
        query.setdefault("donation_date", {})["$gte"] = start_date
    if end_date:
        query.setdefault("donation_date", {})["$lte"] = end_date

    total = await db.donations.count_documents(query)
    skip = (page - 1) * limit
    txns = await db.donations.find(query, {"_id": 0}).sort("donation_date", -1).skip(skip).limit(limit).to_list(limit)

    # Enrich with church names
    tenant_cache = {}
    for txn in txns:
        tid = txn.get("tenant_id")
        if tid and tid not in tenant_cache:
            t = await db.tenants.find_one({"id": tid}, {"_id": 0, "name": 1})
            tenant_cache[tid] = t.get("name", tid) if t else tid
        txn["church_name"] = tenant_cache.get(tid, tid)

    return {
        "transactions": txns,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/platform/transactions/export")
async def export_platform_transactions(request: Request, church: str = "", status: str = "", method: str = "", fund: str = "", start_date: str = "", end_date: str = ""):
    """Export all matching transactions as CSV."""
    from fastapi.responses import StreamingResponse
    import csv
    import io

    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    query = {}
    if church:
        query["tenant_id"] = church
    if status:
        query["status"] = status
    if method:
        query["payment_method"] = method
    if fund:
        query["fund_name"] = fund
    if start_date:
        query.setdefault("donation_date", {})["$gte"] = start_date
    if end_date:
        query.setdefault("donation_date", {})["$lte"] = end_date

    txns = await db.donations.find(query, {"_id": 0}).sort("donation_date", -1).limit(100000).to_list(100000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Church", "Donor", "Email", "Amount", "Fee", "Net", "Fund", "Method", "Status", "Transaction ID"])
    for t in txns:
        writer.writerow([
            t.get("donation_date", ""),
            t.get("tenant_id", ""),
            t.get("person_name", ""),
            t.get("person_email", ""),
            t.get("amount", 0),
            t.get("solomon_fee", 0),
            t.get("net_amount", 0),
            t.get("fund_name", ""),
            t.get("payment_method", ""),
            t.get("status", ""),
            t.get("transaction_id", ""),
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=solomon_transactions.csv"},
    )


# ═══════════════════ PLATFORM PAYOUTS ═══════════════════

@router.get("/platform/payouts")
async def get_platform_payouts(request: Request, page: int = 1, limit: int = 50, church: str = "", start_date: str = "", end_date: str = ""):
    """Weekly payout history across platform."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    query = {}
    if church:
        query["tenant_id"] = church
    if start_date:
        query.setdefault("payout_date", {})["$gte"] = start_date
    if end_date:
        query.setdefault("payout_date", {})["$lte"] = end_date

    total = await db.payouts.count_documents(query)
    skip = (page - 1) * limit
    raw_payouts = await db.payouts.find(query, {"_id": 0}).sort("payout_date", -1).skip(skip).limit(limit).to_list(limit)

    # Normalize field names and enrich with church name
    tenant_cache = {}
    payouts = []
    for p in raw_payouts:
        tid = p.get("tenant_id", "")
        if tid and tid not in tenant_cache:
            t = await db.tenants.find_one({"id": tid}, {"_id": 0, "name": 1})
            tenant_cache[tid] = t.get("name", tid) if t else tid
        normalized = {
            "id": p.get("id", ""),
            "payout_date": p.get("payout_date") or p.get("period_end") or p.get("created_at", "")[:10] if p.get("created_at") else "",
            "church_name": p.get("church_name") or tenant_cache.get(tid, tid),
            "gross_amount": round(float(p.get("gross_amount") or p.get("amount") or 0), 2),
            "total_fees": round(float(p.get("total_fees") or p.get("fee_amount") or 0), 2),
            "net_payout": round(float(p.get("net_payout") or p.get("net_amount") or 0), 2),
            "transaction_count": p.get("transaction_count") or p.get("txn_count") or 0,
            "status": p.get("status", "completed"),
            "bank_account": f"****{p.get('bank_last_four', '????')}",
            "tenant_id": tid,
        }
        payouts.append(normalized)

    # Pending balances: sum of donations since last payout for each church
    pending = []
    pending_tenants = await db.tenants.find(
        {"subscription_status": "active"}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(100)
    for tenant_doc in pending_tenants:
        tid = tenant_doc["id"]
        last_payout = await db.payouts.find_one({"tenant_id": tid}, {"_id": 0, "payout_date": 1}, sort=[("payout_date", -1)])
        since = last_payout["payout_date"] if last_payout else "2023-01-01"
        pipe = [
            {"$match": {"tenant_id": tid, "donation_date": {"$gt": since}, "status": "completed"}},
            {"$group": {"_id": None, "gross": {"$sum": "$amount"}, "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}}}},
        ]
        result = await db.donations.aggregate(pipe).to_list(1)
        if result:
            pending.append({
                "tenant_id": tid,
                "church_name": tenant_doc.get("name", tid),
                "available_balance": round(result[0]["gross"] - result[0]["fees"], 2),
                "bank_account": f"****{tid[-4:]}",
                "payout_method": "ACH - Standard",
            })

    return {
        "payouts": payouts,
        "pending_payouts": pending,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


# ═══════════════════ PLATFORM DONOR ANALYTICS ═══════════════════

@router.get("/platform/donors/stats")
async def get_platform_donor_stats(request: Request):
    """Platform-wide donor analytics."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    from datetime import datetime as dt
    today = dt.now(timezone.utc)
    d90 = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    d30 = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    # Dynamic tenant lookup
    all_tenants_d = await db.tenants.find(
        {"subscription_status": "active"}, {"_id": 0, "id": 1}
    ).to_list(100)
    campuses = [t["id"] for t in all_tenants_d]
    if not campuses:
        campuses = [DEFAULT_TENANT_ID]

    total_donors = await db.platform_donors.count_documents({"tenant_id": {"$in": campuses}})

    # Active donors (gift in last 90 days)
    active_pipe = [
        {"$match": {"tenant_id": {"$in": campuses}, "donation_date": {"$gte": d90}}},
        {"$group": {"_id": "$person_id"}},
        {"$count": "count"},
    ]
    active_res = await db.donations.aggregate(active_pipe).to_list(1)
    active_donors = active_res[0]["count"] if active_res else 0

    # Recurring donors
    recurring_pipe = [
        {"$match": {"tenant_id": {"$in": campuses}, "is_recurring": True}},
        {"$group": {"_id": "$person_id"}},
        {"$count": "count"},
    ]
    recurring_res = await db.donations.aggregate(recurring_pipe).to_list(1)
    recurring_donors = recurring_res[0]["count"] if recurring_res else 0

    # First-time donors (last 30 days)
    first_time_pipe = [
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": "$person_id", "first": {"$min": "$donation_date"}}},
        {"$match": {"first": {"$gte": d30}}},
        {"$count": "count"},
    ]
    first_time_res = await db.donations.aggregate(first_time_pipe).to_list(1)
    first_time = first_time_res[0]["count"] if first_time_res else 0

    lapsed = max(0, total_donors - active_donors)

    # Average lifetime value
    ltv_pipe = [
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": "$person_id", "total": {"$sum": "$amount"}}},
        {"$group": {"_id": None, "avg": {"$avg": "$total"}}},
    ]
    ltv_res = await db.donations.aggregate(ltv_pipe).to_list(1)
    avg_ltv = round(ltv_res[0]["avg"], 2) if ltv_res else 0

    # Average gift
    avg_pipe = [
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": None, "avg": {"$avg": "$amount"}}},
    ]
    avg_res = await db.donations.aggregate(avg_pipe).to_list(1)
    avg_gift = round(avg_res[0]["avg"], 2) if avg_res else 0

    # DonorIQ stages (simplified)
    one_time_only = max(0, total_donors - recurring_donors)
    stages = {
        "first_time": first_time,
        "occasional": round(one_time_only * 0.35),
        "regular": round(one_time_only * 0.30),
        "recurring": recurring_donors,
        "at_risk": round(lapsed * 0.05),
        "lapsed": round(lapsed * 0.03),
    }

    # Retention rate (donors active in both current and previous year)
    this_year_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    last_year_start = today.replace(year=today.year - 1, month=1, day=1).strftime("%Y-%m-%d")
    last_year_end = today.replace(year=today.year - 1, month=12, day=31).strftime("%Y-%m-%d")

    retention_pipe = [
        {"$match": {"tenant_id": {"$in": campuses}, "donation_date": {"$gte": last_year_start, "$lte": last_year_end}}},
        {"$group": {"_id": "$person_id"}},
    ]
    last_year_donors = set()
    async for d in db.donations.aggregate(retention_pipe):
        last_year_donors.add(d["_id"])

    this_year_pipe = [
        {"$match": {"tenant_id": {"$in": campuses}, "donation_date": {"$gte": this_year_start}}},
        {"$group": {"_id": "$person_id"}},
    ]
    this_year_donors = set()
    async for d in db.donations.aggregate(this_year_pipe):
        this_year_donors.add(d["_id"])

    retained = len(last_year_donors & this_year_donors)
    retention_rate = round(retained / max(len(last_year_donors), 1) * 100, 1)

    # Donors by campus
    campus_pipe = [
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": "$tenant_id", "count": {"$sum": 1}}},
    ]
    campus_donors = {}
    async for d in db.platform_donors.aggregate(campus_pipe):
        campus_donors[d["_id"]] = d["count"]

    return {
        "total_donors": total_donors,
        "active_donors": active_donors,
        "recurring_donors": recurring_donors,
        "first_time_donors_30d": first_time,
        "lapsed_donors": lapsed,
        "avg_lifetime_value": avg_ltv,
        "avg_gift": avg_gift,
        "retention_rate_yoy": retention_rate,
        "donor_stages": stages,
        "by_campus": campus_donors,
    }


# ═══════════════════ PLATFORM IMPERSONATE ═══════════════════

@router.post("/platform/impersonate")
async def impersonate_church(request: Request):
    """Impersonate a church admin — returns a session for that church."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    body = await request.json()
    target_tenant = body.get("tenant_id")
    if not target_tenant:
        raise HTTPException(status_code=400, detail="tenant_id required")

    # Find a church_admin for that tenant
    admin = await db.users.find_one({"tenant_id": target_tenant, "role": "church_admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=404, detail="No admin found for this church")

    import secrets as _sec
    imp_token = _sec.token_hex(32)
    await db.user_sessions.insert_one({
        "session_token": imp_token,
        "user_id": admin["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_impersonation": True,
        "impersonated_by": user["user_id"],
    })

    return {
        "token": imp_token,
        "user": {
            "name": admin.get("name"),
            "email": admin.get("email"),
            "role": admin.get("role"),
            "tenant_id": admin.get("tenant_id"),
        },
        "impersonating": True,
    }
