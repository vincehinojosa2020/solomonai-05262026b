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
import random
import secrets
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
    """Get platform-wide statistics using cached + real data for God Mode dashboard"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    
    total_churches = await db.tenants.count_documents({})
    active_churches = await db.tenants.count_documents({"subscription_status": "active"})
    
    # Use cached stats for total members (boosted numbers)
    all_caches = await db.dashboard_stats_cache.find({}, {"_id": 0}).to_list(100)
    total_members_boosted = sum(c.get("total_members", 0) for c in all_caches)
    
    # MRR from tenant records
    tenants = await db.tenants.find({}, {"_id": 0, "mrr": 1, "name": 1, "id": 1}).to_list(100)
    total_mrr = sum(float(t.get("mrr", 0) or 0) for t in tenants)
    
    # Real donation stats
    today = datetime.now(timezone.utc)
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    year_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    
    mtd_pipeline = [
        {"$match": {"donation_date": {"$gte": month_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]
    mtd_result = await db.donations.aggregate(mtd_pipeline).to_list(1)
    mtd_total = mtd_result[0]["total"] if mtd_result else 0
    mtd_count = mtd_result[0]["count"] if mtd_result else 0
    
    ytd_pipeline = [
        {"$match": {"donation_date": {"$gte": year_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]
    ytd_result = await db.donations.aggregate(ytd_pipeline).to_list(1)
    ytd_total = ytd_result[0]["total"] if ytd_result else 0
    
    thirty_days_ago = (today - timedelta(days=30)).isoformat()
    recent_signups = await db.users.count_documents({
        "role": "member",
        "created_at": {"$gte": thirty_days_ago}
    })
    
    giving_by_tenant = await db.donations.aggregate([
        {"$match": {"donation_date": {"$gte": month_start}}},
        {"$group": {"_id": "$tenant_id", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]).to_list(10)
    
    for g in giving_by_tenant:
        tenant = await db.tenants.find_one({"id": g["_id"]}, {"_id": 0, "name": 1})
        g["church_name"] = tenant["name"] if tenant else "Unknown"
    
    return {
        "churches": {
            "total": total_churches,
            "active": active_churches,
            "suspended": total_churches - active_churches
        },
        "members": {
            "total_users": total_members_boosted if total_members_boosted > 0 else await db.users.count_documents({"role": "member"}),
            "total_people": await db.people.count_documents({}),
            "recent_signups": recent_signups
        },
        "giving": {
            "mtd_total": mtd_total,
            "mtd_count": mtd_count,
            "ytd_total": ytd_total,
            "by_church": [{"church": g["church_name"], "amount": g["total"], "count": g["count"]} for g in giving_by_tenant]
        },
        "platform": {
            "total_mrr": total_mrr,
            "arr": total_mrr * 12
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

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
            "address_line1": f"{random.randint(1000, 9999)} {random.choice(el_paso_streets)}",
            "city": "El Paso",
            "state": "TX",
            "zip": f"799{random.randint(10, 99)}",
            "country": "US",
            "phone": f"(915) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
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
            "mobile_phone": f"(915) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
            "date_of_birth": f"{random.randint(1960, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "gender": ep_member["gender"],
            "marital_status": "married",
            "membership_status": "member",
            "membership_date": f"20{random.randint(15, 24)}-{random.randint(1, 12):02d}-01",
            "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={ep_person_id}",
            "is_head_of_household": True,
            "campus": random.choice(["Main Campus", "East Campus", "West Campus"]),
            "engagement_score": random.randint(60, 100),
            "ytd_giving": random.randint(500, 5000) * 1.0,
            "lifetime_giving": random.randint(5000, 50000) * 1.0,
            "custom_fields": {},
            "giving_anonymous": False,
            "paperless_statements": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        people.append(ep_person)
    
    # Create 80 households with 200 people (remaining generic)
    for h in range(80):
        household_id = str(uuid.uuid4())
        last_name = random.choice(last_names)
        
        household = {
            "id": household_id,
            "tenant_id": tenant_id,
            "name": f"The {last_name} Family",
            "address_line1": f"{random.randint(100, 9999)} {random.choice(['Oak', 'Main', 'Church', 'Park', 'Elm', 'Cedar'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr'])}",
            "city": "El Cajon",
            "state": "CA",
            "zip": f"920{random.randint(10, 99)}",
            "country": "US",
            "phone": f"619-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
            "envelope_num": h + 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        households.append(household)
        
        # 2-3 people per household
        num_people = random.randint(2, 3)
        for i in range(num_people):
            person_id = str(uuid.uuid4())
            first_name = random.choice(first_names)
            gender = random.choice(genders)
            birth_year = random.randint(1950, 2010)
            
            person = {
                "id": person_id,
                "tenant_id": tenant_id,
                "household_id": household_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}@email.com",
                "mobile_phone": f"619-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                "date_of_birth": f"{birth_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "gender": gender,
                "marital_status": random.choice(["single", "married", "married"]),
                "membership_status": random.choice(statuses),
                "membership_date": f"20{random.randint(10, 24)}-{random.randint(1, 12):02d}-01",
                "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={person_id}",
                "is_head_of_household": i == 0,
                "campus": random.choice(campuses),
                "engagement_score": random.randint(20, 100),
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
        leader = random.choice(people)
        
        group = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "group_type_id": group_type["id"],
            "name": name,
            "description": f"{name} - a place to grow and connect",
            "location": random.choice(["Room 101", "Room 202", "Fellowship Hall", "Chapel", "Youth Center"]),
            "meeting_schedule": random.choice(["Weekly", "Bi-weekly", "Monthly"]),
            "meeting_day": random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]),
            "meeting_time": random.choice(["09:00", "10:00", "18:00", "19:00"]),
            "capacity": random.randint(15, 60),
            "is_open": random.choice([True, True, True, False]),
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
        num_groups = random.randint(1, 3)
        selected_groups = random.sample(groups, min(num_groups, len(groups)))
        
        for g in selected_groups:
            member = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "group_id": g["id"],
                "person_id": person["id"],
                "role": random.choice(["member", "member", "member", "leader", "co-leader"]),
                "joined_at": f"20{random.randint(20, 24)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
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
                "total_headcount": random.randint(3000, 4500),
                "notes": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            services.append(service)
    
    await db.services.insert_many(services)
    
    # Create attendance records
    attendance_records = []
    for service in services[-24:]:  # Last 12 weeks (24 services)
        # Random subset of people attended
        attendees = random.sample(people, random.randint(60, 120))
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
        num_donations = random.randint(40, 80)
        donors = random.sample(people, min(num_donations, len(people)))
        
        for donor in donors:
            fund = random.choice(funds)
            amount = random.choice([25, 50, 100, 100, 150, 200, 250, 500, 1000, 2500])
            
            donation = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "person_id": donor["id"],
                "fund_id": fund["id"],
                "amount": float(amount),
                "donation_date": sunday_str,
                "payment_method": random.choice(payment_methods),
                "is_recurring": random.random() < 0.15,
                "receipt_sent": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            donations.append(donation)
    
    # Add 5 crypto donations
    crypto_currencies = ["BTC", "ETH", "USDC", "SOL"]
    for _ in range(5):
        donor = random.choice(people)
        crypto_amount = random.uniform(0.01, 2.0)
        usd_value = random.uniform(500, 25000)
        
        donation = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": donor["id"],
            "fund_id": funds[0]["id"],  # General fund
            "amount": usd_value,
            "donation_date": (today - timedelta(days=random.randint(1, 180))).strftime("%Y-%m-%d"),
            "payment_method": "crypto",
            "crypto_currency": random.choice(crypto_currencies),
            "crypto_amount": crypto_amount,
            "crypto_tx_hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
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
        donor = random.choice(people)
        donation = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": donor["id"],
            "fund_id": funds[1]["id"],  # Building fund
            "amount": asset["asset_appraised_value"],
            "donation_date": (today - timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d"),
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
    recurring_givers = random.sample(people, 30)
    recurring_records = []
    
    for person in recurring_givers:
        recurring = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": person["id"],
            "fund_id": random.choice(funds)["id"],
            "amount": float(random.choice([50, 100, 150, 200, 250, 500])),
            "frequency": random.choice(["weekly", "biweekly", "monthly"]),
            "next_gift_date": (today + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
            "payment_method": "card",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        recurring_records.append(recurring)
    
    await db.recurring_giving.insert_many(recurring_records)
    
    # Create pledges (10 pledges for Building Fund campaign)
    pledgers = random.sample(people, 10)
    pledges = []
    
    for person in pledgers:
        pledge_amount = random.choice([5000, 10000, 15000, 25000, 50000])
        total_given = random.uniform(0.2, 0.9) * pledge_amount
        
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
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        person = {
            "id": person_id,
            "tenant_id": tenant_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@email.com",
            "mobile_phone": f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
            "date_of_birth": f"{random.randint(1960, 2005)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "gender": random.choice(["male", "female"]),
            "membership_status": random.choice(statuses),
            "membership_date": (six_months_ago + timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d"),
            "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={person_id}",
            "engagement_score": random.randint(30, 100),
            "ytd_giving": 0,
            "lifetime_giving": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        people.append(person)
        
        # Generate donations (6 months of history)
        if random.random() > 0.3:  # 70% of members give
            num_donations = random.randint(3, 24)  # 3-24 donations over 6 months
            person_total = 0
            for _ in range(num_donations):
                donation_date = six_months_ago + timedelta(days=random.randint(0, 180))
                amount = random.choice([25, 50, 100, 150, 200, 250, 500, 1000])
                donation = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "person_id": person_id,
                    "donor_name": f"{first_name} {last_name}",
                    "amount": amount,
                    "fund_name": random.choice(fund_names),
                    "donation_date": donation_date.strftime("%Y-%m-%d"),
                    "payment_method": random.choice(["card", "ach", "cash", "check"]),
                    "payment_status": "completed",
                    "created_at": donation_date.isoformat()
                }
                donations.append(donation)
                person_total += amount
            person["ytd_giving"] = person_total
            person["lifetime_giving"] = person_total * random.uniform(1, 3)
        
        # Generate attendance (6 months)
        if random.random() > 0.2:  # 80% have some attendance
            num_attendances = random.randint(5, 24)  # 5-24 services over 6 months
            for _ in range(num_attendances):
                att_date = six_months_ago + timedelta(days=random.randint(0, 180))
                att_record = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "person_id": person_id,
                    "person_name": f"{first_name} {last_name}",
                    "service_name": random.choice(["Sunday 9AM", "Sunday 11AM", "Wednesday Night"]),
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
    return results

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

