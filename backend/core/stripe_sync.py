"""Stripe → MongoDB donation sync.

Guarantees every succeeded Stripe PaymentIntent lands in `db.donations`
within seconds of the charge — even when the frontend's `confirm-donation`
call is never made (tab closed, network drop, webhook not yet configured).

Design:
  * `backfill_from_intents(intents)` — upsert a batch of already-fetched
    Stripe PaymentIntent objects into donations (cheap, reused by any
    endpoint that already has the list).
  * `sync_recent(hours=24)` — pull recent PIs from Stripe and backfill.
    Used for the 60-second startup warm + periodic background sweep.

Idempotent: donation `id = f"don_{intent.id}"` is the stable key.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Iterable

import stripe
from dotenv import dotenv_values

from core import db

logger = logging.getLogger("solomon.stripe_sync")

# Load Stripe key the same way stripe_elements.py does so platform-default
# env vars don't override the real user key.
_env = dotenv_values("/app/backend/.env")
_key = _env.get("STRIPE_API_KEY") or _env.get("STRIPE_SECRET_KEY") or os.environ.get("STRIPE_API_KEY", "")
if _key and _key != "sk_test_emergent":
    stripe.api_key = _key


# ─────────────────────────────────────────────────────────────────────────
def _donation_from_intent(intent, tenant_id: str | None) -> dict:
    """Build the donation doc matching the shape `confirm-donation` emits."""
    md = intent.metadata or {}
    base_cents = int(md.get("base_amount_cents") or intent.amount)
    fee_cents = int(md.get("fee_cents") or 0)
    donor_name = (
        f"{md.get('donor_first_name', '')} {md.get('donor_last_name', '')}"
    ).strip() or "Guest Donor"

    # Best-effort card lookup — never let one bad retrieve kill the whole sync
    pm_brand = pm_last4 = None
    ch_id = None
    try:
        if intent.latest_charge:
            ch = stripe.Charge.retrieve(intent.latest_charge)
            ch_id = ch.id
            if ch.payment_method_details and ch.payment_method_details.card:
                pm_brand = ch.payment_method_details.card.brand
                pm_last4 = ch.payment_method_details.card.last4
    except Exception:
        pass

    created_dt = datetime.fromtimestamp(intent.created, tz=timezone.utc)
    return {
        "id": f"don_{intent.id}",
        "tenant_id": tenant_id or md.get("tenant_id", ""),
        "donor_name": donor_name,
        "donor_email": md.get("donor_email", ""),
        "amount": round(base_cents / 100.0, 2),
        "fee_amount": round(fee_cents / 100.0, 2),
        "total_charged": round(intent.amount / 100.0, 2),
        "currency": intent.currency,
        "fund_name": md.get("fund") or "Tithes",
        "frequency": md.get("frequency") or "one-time",
        "payment_method": "card",
        "payment_source": "stripe",
        "test_mode": md.get("test_mode") == "true",
        "cover_fees": md.get("cover_fees") == "true",
        "donation_date": created_dt.strftime("%Y-%m-%d"),
        "created_at": created_dt.isoformat(),
        "stripe_payment_intent_id": intent.id,
        "stripe_charge_id": ch_id,
        "card_brand": pm_brand,
        "card_last_four": pm_last4,
        "message": md.get("message", ""),
        "status": "succeeded",
        "synced_by": "stripe_sync",
    }


async def backfill_from_intents(intents: Iterable, tenant_hint: dict | None = None) -> int:
    """Upsert a list of already-fetched PaymentIntents into db.donations.
    Only acts on succeeded intents. Returns count inserted (not updates).
    `tenant_hint` is an optional dict {intent_id: tenant_id} to avoid a
    second lookup when the caller already computed it.
    """
    if not stripe.api_key:
        return 0

    tenant_hint = tenant_hint or {}
    inserted = 0

    # Pre-fetch ids already in Mongo so we do a single round-trip
    intents_list = [i for i in intents if getattr(i, "status", None) == "succeeded"]
    if not intents_list:
        return 0
    ids = [i.id for i in intents_list]
    existing = set()
    async for r in db.donations.find(
        {"stripe_payment_intent_id": {"$in": ids}},
        {"_id": 0, "stripe_payment_intent_id": 1},
    ):
        existing.add(r["stripe_payment_intent_id"])

    # Resolve tenant_id for any intent that didn't come with a hint
    for intent in intents_list:
        if intent.id in existing:
            continue
        md = intent.metadata or {}
        tid = tenant_hint.get(intent.id) or md.get("tenant_id")
        if not tid:
            # Can't place this into any church's books — skip, but log.
            logger.warning(f"[stripe_sync] skipping {intent.id}: no tenant_id in metadata")
            continue
        try:
            doc = _donation_from_intent(intent, tid)
            await db.donations.insert_one(doc)
            # Keep funds rollup honest for the receiving church
            await db.funds.update_one(
                {"tenant_id": tid, "name": doc["fund_name"]},
                {"$inc": {"current_amount": doc["amount"]}},
            )
            inserted += 1
        except Exception as e:
            logger.warning(f"[stripe_sync] insert failed for {intent.id}: {e}")

    if inserted:
        logger.info(f"[stripe_sync] backfilled {inserted} donations from Stripe")
        # Invalidate the stats cache so dashboards reflect the new rows
        try:
            from routes.stripe_elements import _STATS_CACHE, _PLATFORM_TXN_CACHE
            _STATS_CACHE["ts"] = 0.0
            _STATS_CACHE["data"] = None
            _PLATFORM_TXN_CACHE.clear()
        except Exception:
            pass

    return inserted


async def sync_recent(hours: int = 24, limit: int = 100) -> int:
    """Pull recent Stripe PaymentIntents from the last `hours` and backfill
    anything missing. Called on boot + every 60s by the background task."""
    if not stripe.api_key:
        return 0
    cutoff = int((datetime.now(timezone.utc).timestamp() - hours * 3600))
    try:
        intents = stripe.PaymentIntent.list(limit=max(1, min(limit, 100)), created={"gte": cutoff})
    except Exception as e:
        logger.warning(f"[stripe_sync] list failed: {e}")
        return 0
    return await backfill_from_intents(intents.data)
