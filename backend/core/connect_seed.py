"""
Stripe Connect account ID seeding (idempotent).

Why this exists:
The preview Atlas instance was seeded with `stripe_connect_account_id` for
each tenant via a one-shot script. Production Atlas is a separate cluster
and never received that seed, so every public giving page hit the
`accepts_payments=false` gate and rendered "Online giving coming soon".

This module exposes a single helper, `seed_connect_accounts()`, that:
  * is fully idempotent (safe to call on every boot)
  * only writes when a tenant doc is missing the canonical ID OR has stale
    state (status != "active" / accepts_payments != True)
  * is exception-isolated so a write failure can never crash startup
"""
from __future__ import annotations

from datetime import datetime, timezone
from core import db, logger


# ── Canonical 9-tenant Stripe Connect map (production source of truth) ──
# These IDs were created by Vince in the Stripe Dashboard during the
# multi-church onboarding. Hardcoded here so production Atlas converges
# automatically on every boot — no manual mongosh steps required.
CANONICAL_CONNECT_ACCOUNTS: dict[str, str] = {
    "eden-church-001":        "acct_1TRVWmJyE7zM7lxV",
    "abundant-church-001":    "acct_1TRVWFFLhzsPtPxj",
    "abundant-east-001":      "acct_1TRVWKFX1LQycf9p",
    "abundant-downtown-001":  "acct_1TRVWO2UEqb1nY3L",
    "abundant-west-001":      "acct_1TRVWSFQBi4A6opd",
    "potters-house-001":      "acct_1TRVWW2UWbVU32sa",
    "cityreach-001":          "acct_1TRVWaFVPswnbTrm",
    "hillcountry-001":        "acct_1TRVWdFYVzOINe2c",
    "cristoviene-001":        "acct_1TRVWhFMrsVdQxaV",
}


# ── Canonical public-URL slugs ──────────────────────────────────────────
# Some tenants were seeded with abbreviated slugs (e.g. abundant-church-001
# was stored as `slug='abundant'`) which broke the friendlier public URL
# Vince hands out (`solomonai.us/give/abundant-church`). The Stripe lookup
# `_tenant_by_slug` already searches slug ∪ subdomain ∪ id with $or, so we
# can safely *promote* the slug while leaving subdomain intact — every
# legacy URL keeps working.
CANONICAL_SLUGS: dict[str, str] = {
    "eden-church-001":        "eden-church",
    "abundant-church-001":    "abundant-church",
    "abundant-east-001":      "abundant-east",
    "abundant-downtown-001":  "abundant-downtown",
    "abundant-west-001":      "abundant-west",
    "potters-house-001":      "potters-house",
    "cityreach-001":          "cityreach",
    "hillcountry-001":        "hillcountry",
    "cristoviene-001":        "cristoviene",
}


async def seed_connect_accounts() -> dict:
    """
    Ensure every canonical tenant has its Stripe Connect ID + active status
    + accepts_payments=True. Returns a per-tenant summary so the caller (an
    admin endpoint or the startup hook) can log/diagnose without re-querying.

    Idempotent: tenants already in the correct state are skipped without
    a write.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    summary: list[dict] = []

    for tenant_id, account_id in CANONICAL_CONNECT_ACCOUNTS.items():
        existing = await db.tenants.find_one(
            {"id": tenant_id},
            {"_id": 0, "id": 1, "name": 1, "slug": 1,
             "stripe_connect_account_id": 1, "stripe_connect_status": 1,
             "accepts_payments": 1},
        )
        if not existing:
            summary.append({
                "tenant_id": tenant_id, "action": "skipped",
                "reason": "tenant doc not found",
            })
            continue

        canonical_slug = CANONICAL_SLUGS.get(tenant_id)
        before = {
            "stripe_connect_account_id": existing.get("stripe_connect_account_id"),
            "stripe_connect_status": existing.get("stripe_connect_status"),
            "accepts_payments": existing.get("accepts_payments"),
            "slug": existing.get("slug"),
        }
        slug_correct = (
            canonical_slug is None or before["slug"] == canonical_slug
        )
        if (
            before["stripe_connect_account_id"] == account_id
            and before["stripe_connect_status"] == "active"
            and before["accepts_payments"] is True
            and slug_correct
        ):
            summary.append({
                "tenant_id": tenant_id, "name": existing.get("name"),
                "action": "skipped", "reason": "already correct",
                "before": before,
            })
            continue

        update_doc = {
            "stripe_connect_account_id": account_id,
            "stripe_connect_status": "active",
            "stripe_connect_onboarded_at": now_iso,
            "accepts_payments": True,
        }
        if canonical_slug and before["slug"] != canonical_slug:
            update_doc["slug"] = canonical_slug

        result = await db.tenants.update_one(
            {"id": tenant_id},
            {"$set": update_doc},
        )
        summary.append({
            "tenant_id": tenant_id, "name": existing.get("name"),
            "action": "updated" if result.modified_count else "no-op",
            "before": before,
            "after": {
                **{k: v for k, v in update_doc.items()
                   if k != "stripe_connect_onboarded_at"},
            },
        })

    updated = sum(1 for s in summary if s["action"] == "updated")
    skipped = sum(1 for s in summary if s["action"] == "skipped")
    not_found = sum(1 for s in summary if s.get("reason") == "tenant doc not found")
    return {
        "ok": True,
        "tenants_total": len(CANONICAL_CONNECT_ACCOUNTS),
        "updated": updated,
        "skipped": skipped,
        "not_found": not_found,
        "ts": now_iso,
        "summary": summary,
    }


async def auto_seed_connect_on_boot() -> None:
    """
    Fire-and-forget wrapper for use inside `_deferred_startup()`.
    Logs a single structured line; never raises.
    """
    try:
        result = await seed_connect_accounts()
        logger.info(
            "[startup] connect_seed complete",
            extra={
                "updated": result["updated"],
                "skipped": result["skipped"],
                "not_found": result["not_found"],
                "tenants_total": result["tenants_total"],
            },
        )
    except Exception as exc:
        logger.warning(
            "startup_connect_seed_skipped",
            extra={"exc_type": type(exc).__name__, "error": str(exc)[:200]},
        )
