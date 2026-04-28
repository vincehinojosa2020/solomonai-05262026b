"""
Seed realistic campus data for Abundant East, West, Downtown.
Each campus: 10,000+ members, groups, kids checkins, giving stats.
Also fixes tenant name and Shannon's multi-campus access.
"""
import asyncio
import os
import uuid
import random
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

CAMPUSES = [
    {"id": "abundant-east-001", "name": "Abundant East"},
    {"id": "abundant-west-001", "name": "Abundant West"},
    {"id": "abundant-downtown-001", "name": "Abundant Downtown"},
]

GROUP_TYPES = ["Life Group", "Bible Study", "Prayer Group", "Worship Team", "Outreach", "Youth", "Men's Ministry", "Women's Ministry", "Marriage", "Recovery"]
GROUP_NAMES = [
    "Faith Builders", "Kingdom Seekers", "Grace Community", "Lighthouse",
    "Restored Hope", "Iron Sharpens Iron", "Daughters of the King", "Young Adults Unite",
    "Revive", "Encounter", "Anchored", "The Table", "Roots", "Elevate",
    "Crossroads", "Arise", "Overflow", "Connected", "Thrive", "Legacy",
    "Brave Hearts", "New Creation", "Cornerstone", "Living Water", "Harvest",
]

CHILD_FIRST_NAMES = ["Emma", "Liam", "Olivia", "Noah", "Ava", "Sophia", "Mason", "Isabella", "Lucas", "Mia",
                     "Ethan", "Amelia", "Aiden", "Harper", "Jackson", "Ella", "Sebastian", "Chloe", "Mateo", "Luna"]

async def seed():
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "solomonai")]
    now = datetime.now(timezone.utc)

    # ── 1. Fix tenant name ──────────────────────────────────────────────────
    await db.tenants.update_one(
        {"id": "abundant-downtown-001"},
        {"$set": {"name": "Abundant Downtown"}}
    )
    print("Fixed: Abundant Northeast → Abundant Downtown")

    # ── 2. Fix Shannon's multi-campus access ──────────────────────────────
    await db.users.update_one(
        {"email": "shannonnieman1030@gmail.com"},
        {"$set": {
            "accessible_tenant_ids": ["abundant-east-001", "abundant-west-001", "abundant-downtown-001"],
            "organization_id": "abundant-org",
            "organization_name": "Abundant Church",
        }}
    )
    print("Updated Shannon with all 3 campus access")

    # Also update Jacob
    await db.users.update_one(
        {"email": "jacobpacheco@abundanteast.com"},
        {"$set": {
            "accessible_tenant_ids": ["abundant-east-001", "abundant-west-001", "abundant-downtown-001"],
            "organization_id": "abundant-org",
            "organization_name": "Abundant Church",
        }}
    )
    print("Updated Jacob with all 3 campus access")

    # ── 3. Seed groups for West & Downtown ────────────────────────────────
    for campus in CAMPUSES:
        cid = campus["id"]
        existing = await db.groups.count_documents({"tenant_id": cid})
        if existing >= 40:
            print(f"Groups for {campus['name']}: {existing} already exist, skipping")
            continue

        # Delete sparse groups first
        if existing < 40 and existing > 0:
            await db.groups.delete_many({"tenant_id": cid})

        groups = []
        for i in range(random.randint(45, 65)):
            gtype = random.choice(GROUP_TYPES)
            gname = f"{random.choice(GROUP_NAMES)} {gtype}" if i > len(GROUP_NAMES) else random.choice(GROUP_NAMES)
            groups.append({
                "id": str(uuid.uuid4()),
                "tenant_id": cid,
                "name": gname,
                "type": gtype,
                "description": f"A vibrant {gtype.lower()} at {campus['name']}",
                "leader_name": f"Leader {i+1}",
                "meeting_day": random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
                "meeting_time": random.choice(["6:00 PM", "6:30 PM", "7:00 PM", "9:00 AM", "10:00 AM"]),
                "location": random.choice(["Campus Room A", "Campus Room B", "Off-site Home", "Fellowship Hall", "Youth Center"]),
                "member_count": random.randint(8, 45),
                "max_capacity": random.randint(20, 50),
                "is_active": True,
                "is_open": random.random() > 0.3,
                "created_at": (now - timedelta(days=random.randint(30, 365))).isoformat(),
            })
        await db.groups.insert_many(groups)
        print(f"Seeded {len(groups)} groups for {campus['name']}")

    # ── 4. Seed kids check-in records ─────────────────────────────────────
    existing_checkins = await db.checkins.count_documents({
        "tenant_id": {"$in": [c["id"] for c in CAMPUSES]}
    })
    if existing_checkins < 50:
        checkins = []
        for campus in CAMPUSES:
            cid = campus["id"]
            num_kids = random.randint(85, 140)
            for k in range(num_kids):
                checked_in_at = now - timedelta(minutes=random.randint(10, 180))
                checkins.append({
                    "id": str(uuid.uuid4()),
                    "tenant_id": cid,
                    "child_name": f"{random.choice(CHILD_FIRST_NAMES)} {chr(65+k%26)}.",
                    "child_id": str(uuid.uuid4()),
                    "parent_id": str(uuid.uuid4()),
                    "room": random.choice(["Nursery", "Toddlers", "Pre-K", "K-2nd", "3rd-5th", "Middle School"]),
                    "status": "checked_in" if random.random() > 0.15 else "checked_out",
                    "checked_in_at": checked_in_at.isoformat(),
                    "checked_out_at": None if random.random() > 0.15 else (checked_in_at + timedelta(minutes=random.randint(60, 120))).isoformat(),
                    "service_name": random.choice(["9:00 AM Service", "11:00 AM Service", "6:00 PM Service"]),
                    "created_at": checked_in_at.isoformat(),
                })
        await db.checkins.insert_many(checkins)
        print(f"Seeded {len(checkins)} kids check-in records across all campuses")
    else:
        print(f"Kids check-ins: {existing_checkins} already exist")

    # ── 5. Seed dashboard_stats_cache for each campus ─────────────────────
    for campus in CAMPUSES:
        cid = campus["id"]
        # Count actual groups
        active_groups = await db.groups.count_documents({"tenant_id": cid, "is_active": True})
        all_groups = await db.groups.count_documents({"tenant_id": cid})

        # Count actual kids checked in now
        kids_now = await db.checkins.count_documents({"tenant_id": cid, "status": "checked_in"})

        # Get MTD donations
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        mtd_pipe = [
            {"$match": {"tenant_id": cid, "donation_date": {"$gte": month_start.isoformat()}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
        ]
        mtd_result = await db.donations.aggregate(mtd_pipe).to_list(1)
        mtd_giving = mtd_result[0]["total"] if mtd_result else 0

        ytd_pipe = [
            {"$match": {"tenant_id": cid, "donation_date": {"$gte": year_start.isoformat()}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        ytd_result = await db.donations.aggregate(ytd_pipe).to_list(1)
        ytd_giving = ytd_result[0]["total"] if ytd_result else 0

        # Different member counts per campus for realism
        member_counts = {
            "abundant-east-001": {"total": 12847, "active": 10215, "visitors": 1542, "new_week": 38},
            "abundant-west-001": {"total": 11563, "active": 9187, "visitors": 1389, "new_week": 32},
            "abundant-downtown-001": {"total": 10921, "active": 8654, "visitors": 1205, "new_week": 27},
        }
        mc = member_counts.get(cid, {"total": 10000, "active": 8000, "visitors": 1200, "new_week": 25})

        stats = {
            "tenant_id": cid,
            "total_members": mc["total"],
            "active_members": mc["active"],
            "visitors": mc["visitors"],
            "new_this_week": mc["new_week"],
            "active_groups": active_groups,
            "open_groups": max(1, active_groups - random.randint(5, 15)),
            "mtd_giving": round(mtd_giving, 2),
            "ytd_giving": round(ytd_giving, 2),
            "mtd_goal": round(mtd_giving * 1.15, -3),
            "last_attendance": random.randint(2800, 3800),
            "last_attendance_change": random.randint(45, 180),
            "recurring_givers": random.randint(2200, 3500),
            "kids_checked_in_today": kids_now,
            "cafe_orders_week": random.randint(120, 280),
            "cafe_giving_added": round(random.uniform(800, 2500), 2),
            "merch_orders_week": random.randint(35, 85),
            "merch_giving_added": round(random.uniform(300, 1200), 2),
            "event_registrations_month": random.randint(150, 400),
            "at_risk_members": random.randint(80, 200),
            "updated_at": now.isoformat(),
        }

        await db.dashboard_stats_cache.replace_one(
            {"tenant_id": cid},
            stats,
            upsert=True
        )
        print(f"Updated dashboard_stats_cache for {campus['name']}: {mc['total']} members, {active_groups} groups, ${mtd_giving:,.0f} MTD giving, {kids_now} kids checked in")

    # ── 6. Summary ────────────────────────────────────────────────────────
    total_members = sum(mc["total"] for mc in member_counts.values())
    print(f"\nDone! Total members across all 3 campuses: {total_members:,}")
    print("Shannon & Jacob now have access to all 3 campuses.")
    print("Aggregate view will show combined stats when 'All Campuses' is selected.")

    client.close()

if __name__ == "__main__":
    from scripts._prod_guard import refuse_in_production
    refuse_in_production(__file__)
    asyncio.run(seed())
