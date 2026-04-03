"""
Solomon AI — Extended Seed Script (Section F)
Adds 3 new church tenants: Potter's House (Dallas), EdenX (Folsom CA), City Reach (Cedar Park TX)
Each with 3 years of realistic data, Pareto giving, attendance, groups, cafe, merch
"""
import asyncio
import os
import random
import uuid
import hashlib
from datetime import datetime, timezone, timedelta, date
from typing import List, Dict, Any, Tuple, Generator
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('seed_ext')

MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ.get('DB_NAME', 'solomonai')

START_DATE = date(2023, 4, 1)
END_DATE = date(2026, 3, 31)

NEW_TENANTS = [
    {
        "id": "potters-house-001",
        "name": "The Potter's House",
        "city": "Dallas", "state": "TX",
        "address": "6777 W. Kiest Blvd", "zip": "75236",
        "subdomain": "pottershouse",
        "members_target": 14500,
        "annual_giving": 5_200_000,
        "demographics": "60% Black, 20% Hispanic, 15% White, 5% Other",
        "active_pct": 0.85,
        "color": "#7c3aed",
        "admin_email": "admin@pottershouse.org",
        "admin_name": "Pastor Michael Freeman",
    },
    {
        "id": "edenx-001",
        "name": "EdenX Ministries",
        "city": "Folsom", "state": "CA",
        "address": "2250 Prairie City Rd", "zip": "95630",
        "subdomain": "edenx",
        "members_target": 10300,
        "annual_giving": 3_100_000,
        "demographics": "45% White, 25% Hispanic, 15% Asian",
        "active_pct": 0.81,
        "color": "#059669",
        "admin_email": "admin@edenx.church",
        "admin_name": "Pastor Nathan Kim",
    },
    {
        "id": "cityreach-001",
        "name": "City Reach Church",
        "city": "Cedar Park", "state": "TX",
        "address": "2700 W Whitestone Blvd", "zip": "78613",
        "subdomain": "cityreach",
        "members_target": 10400,
        "annual_giving": 3_400_000,
        "demographics": "50% White, 30% Hispanic",
        "active_pct": 0.84,
        "color": "#dc2626",
        "admin_email": "admin@cityreach.church",
        "admin_name": "Pastor Brandon Wells",
    },
]

FIRST_NAMES_M = ["James", "John", "Michael", "William", "David", "Marcus", "DeShawn", "Jordan", "Tyler", "Brandon", "Kevin", "Andre", "Marcus", "Darius", "Nathan", "Chris", "Jason", "Ryan", "Matthew", "Daniel", "Justin", "Eric", "Anthony", "Christopher", "Jonathan"]
FIRST_NAMES_F = ["Jennifer", "Ashley", "Tiffany", "Keisha", "Shanice", "Amanda", "Sarah", "Emily", "Jessica", "Jasmine", "Brianna", "Destiny", "Diamond", "Aaliyah", "Nicole", "Lauren", "Stephanie", "Megan", "Rachel", "Samantha", "Christina", "Michelle", "Kimberly", "Angela", "Taylor"]
LAST_NAMES = ["Johnson", "Williams", "Brown", "Davis", "Jones", "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Robinson", "Clark", "Lewis", "Walker", "Hall", "Allen", "Young", "Hernandez", "King", "Wright", "Scott", "Green", "Baker", "Adams", "Nelson", "Carter", "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans", "Edwards", "Collins", "Stewart", "Sanchez", "Morris", "Rogers", "Reed", "Cook", "Morgan", "Bell"]

FUNDS = [
    ("General Fund", 0.72), ("Building Fund", 0.10), ("Missions", 0.08),
    ("Youth Ministry", 0.05), ("Benevolence", 0.03), ("Special Projects", 0.02),
]

CARD_FEE_RATE = 0.019
CARD_FEE_FLAT = 0.30
ACH_FEE_RATE = 0.008
ACH_FEE_FLAT = 0.30

def calc_fee(amount: float, method: str = "card") -> float:
    if method == "ach":
        return round(min(amount * ACH_FEE_RATE + ACH_FEE_FLAT, 5.0), 2)
    return round(amount * CARD_FEE_RATE + CARD_FEE_FLAT, 2)

def rand_name() -> Tuple[str, str, str]:
    gender = random.choice(["M", "F"])
    first = random.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
    last = random.choice(LAST_NAMES)
    return first, last, gender

def date_range(start: date, end: date) -> Generator[date, None, None]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)

def all_sundays(start: date, end: date) -> List[date]:
    d = start
    while d.weekday() != 6:
        d += timedelta(days=1)
    sundays = []
    while d <= end:
        sundays.append(d)
        d += timedelta(days=7)
    return sundays

def monthly_giving_factor(month: int) -> float:
    """Seasonal giving multiplier."""
    factors = {1: 1.1, 2: 0.9, 3: 1.0, 4: 1.15, 5: 1.0, 6: 0.85,
               7: 0.80, 8: 0.90, 9: 1.0, 10: 1.05, 11: 1.10, 12: 1.55}
    return factors.get(month, 1.0)

def yoy_factor(year: int) -> float:
    """Year-over-year growth."""
    base = 0.85  # 2023 = 85% of target
    if year == 2023: return base
    if year == 2024: return base * 1.04
    return base * 1.04 * 1.04

async def seed_tenant(db: Any, tenant: Dict[str, Any]) -> None:
    tid = tenant["id"]
    log.info(f"Seeding {tenant['name']} ({tid})...")

    # 1. Upsert tenant doc
    demo_pw = hashlib.sha256("Demo2026!".encode()).hexdigest()
    await db.tenants.update_one(
        {"id": tid},
        {"$set": {
            "id": tid, "name": tenant["name"], "subscription_status": "active",
            "plan": "enterprise", "city": tenant["city"], "state": tenant["state"],
            "address": tenant["address"], "zip": tenant["zip"],
            "subdomain": tenant["subdomain"], "primary_color": tenant["color"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True
    )

    # 2. Admin user
    admin_uid = f"admin_{tid[:8]}"
    await db.users.update_one(
        {"email": tenant["admin_email"]},
        {"$set": {
            "user_id": admin_uid, "email": tenant["admin_email"],
            "name": tenant["admin_name"], "role": "church_admin",
            "tenant_id": tid, "password_hash": demo_pw,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True
    )

    # 3. Check if already seeded
    existing_people = await db.people.count_documents({"tenant_id": tid})
    if existing_people > 100:
        log.info(f"  {tenant['name']} already seeded ({existing_people} people). Skipping.")
        return

    # 4. Generate people
    n_members = tenant["members_target"]
    n_active = int(n_members * tenant["active_pct"])
    people = []
    for i in range(n_members):
        first, last, gender = rand_name()
        pid = f"p_{tid[:6]}_{i:05d}"
        is_active = i < n_active
        join_date = START_DATE - timedelta(days=random.randint(0, 1200))
        status = "member" if is_active and random.random() < 0.7 else ("regular" if is_active else "visitor")
        people.append({
            "id": pid, "tenant_id": tid,
            "first_name": first, "last_name": last,
            "name": f"{first} {last}", "gender": gender,
            "email": f"{first.lower()}.{last.lower()}.{i}@{tenant['subdomain']}.church",
            "mobile_phone": f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}",
            "membership_status": status,
            "is_active": is_active,
            "membership_date": join_date.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    # Batch insert people
    log.info(f"  Inserting {len(people)} people...")
    for i in range(0, len(people), 500):
        await db.people.insert_many(people[i:i+500])

    # 5. Generate funds
    fund_docs = []
    for fname, fpct in FUNDS:
        fid = f"fund_{tid[:6]}_{uuid.uuid4().hex[:8]}"
        fund_docs.append({
            "id": fid, "tenant_id": tid, "name": fname,
            "is_active": True, "current_amount": 0,
            "goal_amount": int(tenant["annual_giving"] * fpct),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    await db.funds.insert_many(fund_docs)
    log.info(f"  Funds created: {len(fund_docs)}")

    # 6. Generate giving (Pareto distribution)
    annual = tenant["annual_giving"]
    active_people = [p for p in people if p["is_active"]]
    givers = random.sample(active_people, min(int(len(active_people) * 0.60), len(active_people)))

    # Tier assignments (Pareto)
    champions = givers[:int(len(givers) * 0.02)]   # top 2%: $5K-$15K/year
    committed = givers[len(champions):int(len(givers) * 0.10)]   # $1K-$5K/year
    engaged = givers[len(committed):int(len(givers) * 0.25)]   # $300-$1K/year
    occasional = givers[len(engaged):]   # $50-$300/year

    def annual_amount_for_tier(tier):
        if tier == "champion": return random.uniform(5000, 15000)
        if tier == "committed": return random.uniform(1000, 5000)
        if tier == "engaged": return random.uniform(300, 1000)
        return random.uniform(50, 300)

    # Assign annual amounts
    giver_amounts = {}
    for p in champions: giver_amounts[p["id"]] = annual_amount_for_tier("champion")
    for p in committed: giver_amounts[p["id"]] = annual_amount_for_tier("committed")
    for p in engaged: giver_amounts[p["id"]] = annual_amount_for_tier("engaged")
    for p in occasional: giver_amounts[p["id"]] = annual_amount_for_tier("occasional")

    # Scale to target
    actual_total = sum(giver_amounts.values())
    scale = annual / max(actual_total, 1)
    for pid in giver_amounts:
        giver_amounts[pid] = round(giver_amounts[pid] * scale, 2)

    # Generate 3 years of donations
    log.info(f"  Generating donations for {len(givers)} givers...")
    donations = []
    pay_methods = ["card"] * 55 + ["check"] * 25 + ["cash"] * 10 + ["ach"] * 10
    sundays = all_sundays(START_DATE, END_DATE)

    for p in givers:
        annual_amt = giver_amounts[p["id"]]
        # Distribute across ~47 giving events per year
        events_per_year = random.randint(6, 52)
        per_event = annual_amt / events_per_year

        for year_offset in range(3):
            year = 2023 + year_offset
            yr_factor = yoy_factor(year)
            yr_events = max(2, int(events_per_year * yr_factor))
            yr_sundays = [s for s in sundays if s.year == year]
            if not yr_sundays: continue
            chosen = random.sample(yr_sundays, min(yr_events, len(yr_sundays)))
            for d in chosen:
                amt = per_event * monthly_giving_factor(d.month) * yr_factor
                amt = round(random.uniform(amt * 0.8, amt * 1.2), 2)
                if amt < 5: continue
                fund = random.choices(fund_docs, weights=[f[1] for f in FUNDS], k=1)[0]
                method = random.choice(pay_methods)
                fee = calc_fee(amt, method) if method in ("card", "ach") else 0
                donations.append({
                    "id": str(uuid.uuid4()),
                    "tenant_id": tid,
                    "person_id": p["id"],
                    "donor_name": p["name"],
                    "fund_id": fund["id"],
                    "fund_name": fund["name"],
                    "amount": round(amt, 2),
                    "fee_amount": fee,
                    "net_amount": round(amt - fee, 2),
                    "donation_date": d.isoformat(),
                    "payment_method": method,
                    "status": "completed",
                    "source": "solomonpay",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

    log.info(f"  Inserting {len(donations)} donations...")
    for i in range(0, len(donations), 1000):
        await db.donations.insert_many(donations[i:i+1000])

    # 7. Attendance (weekly, 50-60% of active per Sunday)
    log.info("  Generating attendance records...")
    attendance_docs = []
    for sunday in sundays:
        pct = random.uniform(0.50, 0.62)
        attendees = random.sample(active_people, int(len(active_people) * pct))
        for p in attendees:
            attendance_docs.append({
                "id": str(uuid.uuid4()),
                "tenant_id": tid,
                "person_id": p["id"],
                "service_date": sunday.isoformat(),
                "service_type": "sunday_service",
                "check_in_time": f"{sunday.isoformat()}T{'09' if random.random() < 0.5 else '11'}:00:00Z",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
    log.info(f"  Inserting {len(attendance_docs)} attendance records...")
    for i in range(0, len(attendance_docs), 2000):
        await db.attendance.insert_many(attendance_docs[i:i+2000])

    # 8. Groups (simplified)
    group_names = ["Monday Bible Study", "Tuesday Life Group", "Wednesday Women", "Thursday Men",
                   "Young Adults", "Recovery Group", "Leadership Team", "Serve Team Alpha",
                   "Serve Team Beta", "Youth Group", "Prayer Circle", "Business Leaders"]
    group_docs = []
    for gname in group_names:
        gid = f"grp_{tid[:6]}_{uuid.uuid4().hex[:8]}"
        max_cap = random.randint(12, 40)
        group_docs.append({
            "id": gid, "tenant_id": tid, "name": gname,
            "description": f"{gname} at {tenant['name']}",
            "is_active": True, "is_open": True,
            "capacity": max_cap, "member_count": 0,
            "meeting_day": random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
            "meeting_time": random.choice(["6:30 PM", "7:00 PM", "7:30 PM", "12:00 PM"]),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    await db.groups.insert_many(group_docs)

    # 9. Update dashboard stats cache
    total_donations = sum(d["amount"] for d in donations)
    year_start = datetime.now(timezone.utc).replace(month=1, day=1).strftime("%Y-%m-%d")
    month_start = datetime.now(timezone.utc).replace(day=1).strftime("%Y-%m-%d")
    ytd = sum(d["amount"] for d in donations if d["donation_date"] >= year_start)
    mtd = sum(d["amount"] for d in donations if d["donation_date"] >= month_start)

    await db.dashboard_stats_cache.update_one(
        {"tenant_id": tid},
        {"$set": {
            "tenant_id": tid,
            "total_members": n_members,
            "active_members": n_active,
            "ytd_giving": round(ytd, 2),
            "mtd_giving": round(mtd, 2),
            "mtd_goal": round(annual / 12, 2),
            "active_groups": len(group_docs),
            "last_attendance": int(len(active_people) * 0.55),
            "recurring_givers": int(len(givers) * 0.12),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True
    )

    # 10. Add a portal member account
    member_uid = f"member_{tid[:8]}"
    await db.users.update_one(
        {"email": f"member@{tenant['subdomain']}.church"},
        {"$set": {
            "user_id": member_uid,
            "email": f"member@{tenant['subdomain']}.church",
            "name": f"{random.choice(FIRST_NAMES_F)} {random.choice(LAST_NAMES)}",
            "role": "member", "tenant_id": tid, "password_hash": demo_pw,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True
    )

    log.info(f"  {tenant['name']} seeded: {n_members} people, {len(donations)} donations, ${total_donations:,.0f} total.")


async def main() -> None:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    log.info(f"Connected to {DB_NAME}. Seeding {len(NEW_TENANTS)} new tenants...")
    for tenant in NEW_TENANTS:
        await seed_tenant(db, tenant)
    log.info("All new tenants seeded successfully!")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
