"""Solomon AI — Emergency tenant-recovery seed.

Purpose
-------
If the `tenants` collection is ever found EMPTY at backend startup (catastrophic
state — usually after an aggressive cleanup script wipes everything), this
module re-creates the 8 demo tenants Vince expects to see in God Mode plus the
two foundational user accounts (platform admin + Christopher / Eden).

This is **idempotent** by construction: we early-out the moment any tenant
exists. It will *never* overwrite live data, *never* run if the database
already has any tenant whatsoever — it only fires on a true empty state.

Eden Church is intentionally kept **clean** (zero donations, zero members) so
real Stripe test transactions are the only history the demo team sees on
/give/eden-church.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from core import db

logger = logging.getLogger("solomon.emergency_seed")

# ── Account material ─────────────────────────────────────────────────────
ADMIN_EMAIL = "admin@solomonai.us"
ADMIN_PASSWORD = "Demo2026!"
CHRISTOPHER_EMAIL = "christopher@eden-x.io"
CHRISTOPHER_PASSWORD = "EdenChurch2026!"

# ── Tenant catalog (per Vince's spec) ────────────────────────────────────
EDEN_TENANT_ID = "eden-church-001"  # canonical id elsewhere in the codebase
EDEN_SLUG = "eden-church"

DEMO_TENANTS = [
    {"id": "abundant-east-001",     "name": "Abundant East",            "city": "El Paso",   "state": "TX", "plan": "growth",     "member_count":  9004, "total_giving":  8_900_000},
    {"id": "abundant-west-001",     "name": "Abundant West",            "city": "El Paso",   "state": "TX", "plan": "growth",     "member_count": 10735, "total_giving": 10_600_000},
    {"id": "abundant-downtown-001", "name": "Abundant Northeast",       "city": "El Paso",   "state": "TX", "plan": "growth",     "member_count": 11752, "total_giving": 11_600_000},
    {"id": "cristoviene-001",       "name": "Cristo Viene Church",      "city": "El Paso",   "state": "TX", "plan": "growth",     "member_count": 25492, "total_giving": 25_100_000},
    {"id": "hillcountry-001",       "name": "Hill Country Bible Church","city": "Cedar Park","state": "TX", "plan": "growth",     "member_count": 21776, "total_giving": 21_500_000},
    {"id": "potters-house-001",     "name": "The Potter's House",       "city": "Dallas",    "state": "TX", "plan": "growth",     "member_count": 15011, "total_giving": 14_800_000},
    {"id": "cityreach-001",         "name": "City Reach Church",        "city": "Cedar Park","state": "TX", "plan": "growth",     "member_count":  8659, "total_giving":  8_500_000},
]

EDEN_FUNDS = ["Tithes", "Offerings", "Building Fund", "Missions"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


async def emergency_seed_if_empty() -> dict:
    """Run on backend startup.

    Returns a dict describing what happened. Possible shapes:
      {"action": "skipped", "reason": "tenants_exist", "count": N}
      {"action": "seeded", "tenants": 8, "users": 2, "funds": 4}
      {"action": "error",  "error": "..."}

    The function is fully idempotent — it only touches the DB when
    `tenants` is empty.
    """
    try:
        existing = await db.tenants.count_documents({})
        if existing > 0:
            return {"action": "skipped", "reason": "tenants_exist", "count": existing}

        logger.warning(
            "[emergency_seed] tenants collection EMPTY — running recovery seed "
            "(this should normally never trigger)."
        )

        now = _now()

        # ── Eden Church (clean, zero data, real Stripe target) ───────────
        eden_tenant = {
            "id": EDEN_TENANT_ID,
            "name": "Eden Church",
            "slug": EDEN_SLUG,
            "subdomain": EDEN_SLUG,
            "city": "Austin",
            "state": "TX",
            "country": "USA",
            "website": "https://eden-x.io",
            "subscription_status": "active",
            "plan": "starter",
            "primary_color": "#000000",
            "accent_color": "#2dd4bf",
            "pastor_name": "Christopher Hinojosa",
            "senior_pastor": "Christopher Hinojosa",
            "stripe_test_mode": True,
            "member_count": 0,
            "total_donations": 0,
            "total_giving": 0,
            "monthly_rate": 99,
            "created_at": now,
            "seeded_by": "emergency_recovery",
        }
        await db.tenants.insert_one(eden_tenant)

        # ── Demo tenants 2-8 ─────────────────────────────────────────────
        demo_docs = []
        for t in DEMO_TENANTS:
            demo_docs.append({
                **t,
                "slug": t["id"].rsplit("-", 1)[0],   # e.g. "abundant-east"
                "subdomain": t["id"].rsplit("-", 1)[0],
                "country": "USA",
                "subscription_status": "active",
                "monthly_rate": 999,
                "created_at": now,
                "seeded_by": "emergency_recovery",
            })
        if demo_docs:
            await db.tenants.insert_many(demo_docs)

        # ── Eden funds (4 default funds) ─────────────────────────────────
        fund_docs = []
        for i, name in enumerate(EDEN_FUNDS):
            fund_docs.append({
                "id": f"{EDEN_TENANT_ID}-fund-{name.lower().replace(' ', '-')}",
                "tenant_id": EDEN_TENANT_ID,
                "name": name,
                "description": f"{name} fund",
                "is_default": i == 0,         # Tithes default
                "is_active": True,
                "current_amount": 0,
                "goal_amount": 0,
                "created_at": now,
            })
        await db.funds.insert_many(fund_docs)

        # ── Foundational users (platform admin + Eden church admin) ─────
        admin_pw = _sha256(ADMIN_PASSWORD)
        christopher_pw = _sha256(CHRISTOPHER_PASSWORD)
        user_docs = [
            {
                "user_id": "platform_admin_001",
                "email": ADMIN_EMAIL,
                "password_hash": admin_pw,
                "name": "Solomon Platform Admin",
                "first_name": "Solomon",
                "last_name": "Admin",
                "role": "platform_admin",
                "tenant_id": None,
                "is_active": True,
                "created_at": now,
            },
            {
                "user_id": "christopher_eden_001",
                "email": CHRISTOPHER_EMAIL,
                "password_hash": christopher_pw,
                "name": "Christopher Hinojosa",
                "first_name": "Christopher",
                "last_name": "Hinojosa",
                "role": "church_admin",
                "tenant_id": EDEN_TENANT_ID,
                "is_active": True,
                "created_at": now,
            },
        ]
        await db.users.insert_many(user_docs)

        # ── dashboard_stats_cache so each tenant passes the >10 member
        #    gate in _get_real_campuses_fast(); demos use real counts, Eden
        #    stays at 1 (not zero, so it still appears in God Mode lists).
        dsc_docs = [{
            "tenant_id": EDEN_TENANT_ID,
            "total_members": 1,
            "seeded_by": "emergency_recovery",
            "updated_at": now,
        }]
        for t in DEMO_TENANTS:
            dsc_docs.append({
                "tenant_id": t["id"],
                "total_members": t["member_count"],
                "seeded_by": "emergency_recovery",
                "updated_at": now,
            })
        await db.dashboard_stats_cache.insert_many(dsc_docs)

        result = {
            "action": "seeded",
            "tenants": 1 + len(DEMO_TENANTS),
            "users": len(user_docs),
            "funds": len(fund_docs),
            "dashboard_stats_cache": len(dsc_docs),
        }
        logger.warning(f"[emergency_seed] recovery complete: {result}")
        return result

    except Exception as e:
        logger.exception("[emergency_seed] failed")
        return {"action": "error", "error": str(e)}
