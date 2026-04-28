"""
Migration: 2026-04-28-connect-fields
=====================================
Adds Stripe Connect fields to every existing tenant doc:
    stripe_connect_account_id        : str | null
    stripe_connect_status            : enum (default "not_started")
    stripe_connect_onboarded_at      : ISO datetime | null
    fee_schedule                     : { platform_percent, platform_fixed_cents, override }

Idempotent — uses $setOnInsert-style behavior via $cond / $exists checks.
Safe to re-run.

Usage:
    cd /app/backend && python -m scripts.migrate_2026_04_28_connect_fields
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

# Allow running as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import db  # noqa: E402
from core.connect import (  # noqa: E402
    CONNECT_STATUS_NOT_STARTED,
    default_fee_schedule,
)

logger = logging.getLogger("solomon.migrate.connect_fields")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


async def migrate() -> dict:
    cursor = db.tenants.find({}, {"_id": 0})
    touched = 0
    skipped = 0
    async for t in cursor:
        update = {}
        if "stripe_connect_account_id" not in t:
            update["stripe_connect_account_id"] = None
        if "stripe_connect_status" not in t:
            update["stripe_connect_status"] = CONNECT_STATUS_NOT_STARTED
        if "stripe_connect_onboarded_at" not in t:
            update["stripe_connect_onboarded_at"] = None
        if not t.get("fee_schedule"):
            update["fee_schedule"] = default_fee_schedule()
        if update:
            await db.tenants.update_one({"id": t["id"]}, {"$set": update})
            touched += 1
            logger.info(f"  ✓ migrated {t['id']} (added {sorted(update.keys())})")
        else:
            skipped += 1
    summary = {"touched": touched, "skipped": skipped}
    logger.info(f"done: {summary}")
    return summary


if __name__ == "__main__":
    asyncio.run(migrate())
