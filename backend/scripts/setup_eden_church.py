"""
Eden Church — Clean Tenant Setup
=================================
Wipes all existing Eden/EdenX tenant data and creates a fresh Eden Church tenant
with one admin user (Christopher) and four default funds. Used for the Stripe
POC where every donation Christopher sees in his dashboard must be a REAL
Stripe test transaction, not seeded demo data.

Run directly:
    cd /app/backend && python3 scripts/setup_eden_church.py

Or programmatically via the admin reset endpoint: POST /api/admin/eden-church/reset
"""
import asyncio
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure backend/ is on the path so `core` imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bcrypt  # noqa: E402
from core import db, logger  # noqa: E402


EDEN_TENANT_ID = "eden-church-001"
EDEN_SLUG = "eden-church"
CHRISTOPHER_EMAIL = "christopher@eden-x.io"
CHRISTOPHER_PASSWORD = "EdenChurch2026!"

# All tenant-scoped collections that may hold Eden data
TENANT_SCOPED_COLLECTIONS = [
    "donations", "people", "households", "recurring_giving", "payouts",
    "funds", "groups", "events", "checkins", "attendance", "communications",
    "workflows", "forms", "cafe_orders", "merch_orders",
    "solomon_conversations", "audit_log", "kids_checkins", "kids_children",
    "attendance_sessions", "pathways", "course_enrollments",
    "giving_goals", "recurring_schedules", "statements", "registrations",
    "announcements", "notifications", "prayer_requests",
    "payment_transactions",
]


async def wipe_all_eden_tenants() -> int:
    """Find every tenant with 'eden' anywhere in id/slug/name and delete all
    their data. Returns count of tenants wiped."""
    cursor = db.tenants.find({
        "$or": [
            {"id": {"$regex": "eden", "$options": "i"}},
            {"slug": {"$regex": "eden", "$options": "i"}},
            {"name": {"$regex": "eden", "$options": "i"}},
        ]
    })
    tenants = await cursor.to_list(None)
    if not tenants:
        return 0

    wiped = 0
    for t in tenants:
        tid = t.get("id")
        if not tid:
            continue
        logger.info(f"Wiping tenant: id={tid} name={t.get('name')} slug={t.get('slug')}")
        # Delete tenant-scoped data
        for coll in TENANT_SCOPED_COLLECTIONS:
            try:
                await db[coll].delete_many({"tenant_id": tid})
            except Exception as e:
                logger.warning(f"  skip {coll}: {e}")
        # Delete users belonging to this tenant
        await db.users.delete_many({"tenant_id": tid})
        # Delete the tenant doc itself
        await db.tenants.delete_one({"id": tid})
        wiped += 1
    return wiped


async def create_fresh_eden() -> dict:
    """Create Eden Church tenant, Christopher admin user, and 4 default funds.
    Assumes wipe has already run."""
    now = datetime.now(timezone.utc).isoformat()

    tenant_doc = {
        "id": EDEN_TENANT_ID,
        "name": "Eden Church",
        "slug": EDEN_SLUG,
        "city": "Austin",
        "state": "TX",
        "website": "https://eden-x.io",
        "subscription_status": "active",
        "plan": "starter",
        "primary_color": "#000000",
        "accent_color": "#2dd4bf",
        "subdomain": "eden",
        "parent_organization": None,
        "pastor_name": "Christopher Hinojosa",
        "stripe_test_mode": True,
        "member_count": 0,
        "total_donations": 0,
        "total_giving": 0,
        "created_at": now,
    }
    await db.tenants.insert_one(tenant_doc)

    user_doc = {
        "user_id": str(uuid.uuid4()),
        "email": CHRISTOPHER_EMAIL,
        "name": "Christopher Hinojosa",
        "role": "church_admin",
        "tenant_id": EDEN_TENANT_ID,
        "home_campus_id": EDEN_TENANT_ID,
        "campus_selected": True,
        "password_hash": bcrypt.hashpw(
            CHRISTOPHER_PASSWORD.encode(), bcrypt.gensalt()
        ).decode(),
        "created_at": now,
    }
    await db.users.insert_one(user_doc)

    funds = [
        {"id": str(uuid.uuid4()), "tenant_id": EDEN_TENANT_ID,
         "name": "Tithes", "is_active": True, "is_default": True,
         "goal_amount": None, "current_amount": 0, "created_at": now},
        {"id": str(uuid.uuid4()), "tenant_id": EDEN_TENANT_ID,
         "name": "Offerings", "is_active": True, "is_default": False,
         "goal_amount": None, "current_amount": 0, "created_at": now},
        {"id": str(uuid.uuid4()), "tenant_id": EDEN_TENANT_ID,
         "name": "Building Fund", "is_active": True, "is_default": False,
         "goal_amount": 50000, "current_amount": 0, "created_at": now},
        {"id": str(uuid.uuid4()), "tenant_id": EDEN_TENANT_ID,
         "name": "Missions", "is_active": True, "is_default": False,
         "goal_amount": 10000, "current_amount": 0, "created_at": now},
    ]
    await db.funds.insert_many(funds)

    return {
        "tenant_id": EDEN_TENANT_ID,
        "slug": EDEN_SLUG,
        "admin_email": CHRISTOPHER_EMAIL,
        "funds": [f["name"] for f in funds],
    }


async def reset_eden_data_only() -> dict:
    """Used by /api/admin/eden-church/reset — wipes donations / payouts /
    people while keeping the tenant, admin user, and funds intact. Resets
    fund current_amount to 0."""
    await db.donations.delete_many({"tenant_id": EDEN_TENANT_ID})
    await db.payouts.delete_many({"tenant_id": EDEN_TENANT_ID})
    await db.people.delete_many({"tenant_id": EDEN_TENANT_ID})
    await db.households.delete_many({"tenant_id": EDEN_TENANT_ID})
    await db.recurring_giving.delete_many({"tenant_id": EDEN_TENANT_ID})
    await db.payment_transactions.delete_many({"tenant_id": EDEN_TENANT_ID})
    await db.funds.update_many(
        {"tenant_id": EDEN_TENANT_ID},
        {"$set": {"current_amount": 0}},
    )
    return {
        "status": "reset",
        "message": "Eden Church data wiped. Ready for fresh testing.",
    }


async def verify_clean_state() -> dict:
    """Return counts so a caller can confirm the tenant is clean."""
    return {
        "tenants": await db.tenants.count_documents({"id": EDEN_TENANT_ID}),
        "users": await db.users.count_documents({"tenant_id": EDEN_TENANT_ID}),
        "funds": await db.funds.count_documents({"tenant_id": EDEN_TENANT_ID}),
        "donations": await db.donations.count_documents({"tenant_id": EDEN_TENANT_ID}),
        "people": await db.people.count_documents({"tenant_id": EDEN_TENANT_ID}),
        "payouts": await db.payouts.count_documents({"tenant_id": EDEN_TENANT_ID}),
    }


async def auto_seed_on_boot() -> dict:
    """Run exactly once per fresh deploy. Checks a platform_flags doc; if not
    present, wipes any legacy Eden/EdenX data and seeds the clean Eden Church
    tenant. Safe to call on every backend start — the flag check makes it a
    no-op after the first successful run."""
    flag = await db.platform_flags.find_one({"key": "eden-church-seeded"})
    if flag and flag.get("completed"):
        return {"seeded": False, "reason": "already_seeded", "at": flag.get("at")}

    try:
        wiped = await wipe_all_eden_tenants()
        info = await create_fresh_eden()
        state = await verify_clean_state()
        now = datetime.now(timezone.utc).isoformat()
        await db.platform_flags.update_one(
            {"key": "eden-church-seeded"},
            {"$set": {
                "key": "eden-church-seeded",
                "completed": True,
                "at": now,
                "wiped_legacy_tenants": wiped,
                "state": state,
            }},
            upsert=True,
        )
        logger.info(f"Eden auto-seed complete: wiped={wiped} state={state}")
        return {"seeded": True, "wiped_legacy_tenants": wiped, "state": state, "info": info}
    except Exception as e:
        logger.error(f"Eden auto-seed failed: {e}")
        return {"seeded": False, "reason": "error", "error": str(e)}


async def main():
    print("Wiping all existing Eden/EdenX tenants…")
    n = await wipe_all_eden_tenants()
    print(f"  wiped {n} tenant(s)")

    print("Creating fresh Eden Church…")
    info = await create_fresh_eden()
    print(f"  {info}")

    print("Verifying clean state…")
    state = await verify_clean_state()
    print(f"  {state}")

    expected = {"tenants": 1, "users": 1, "funds": 4,
                "donations": 0, "people": 0, "payouts": 0}
    assert state == expected, f"Unexpected state: {state}"
    print("\nOK — Eden Church ready.")
    print(f"  Login: {CHRISTOPHER_EMAIL} / {CHRISTOPHER_PASSWORD}")
    print(f"  Public give URL: /give/{EDEN_SLUG}")


if __name__ == "__main__":
    asyncio.run(main())
