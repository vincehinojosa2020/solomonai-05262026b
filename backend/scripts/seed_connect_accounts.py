"""
Solomon AI — Seed Stripe test-mode Connect accounts for demo tenants
=====================================================================
For local/staging testing of the Connect direct-charge flow without
manually completing Express onboarding for each of the 7+ demo tenants,
this script provisions a `custom` Connect account per tenant with all
required KYB fields prefilled. Stripe test mode flips the resulting
account to charges_enabled=true / payouts_enabled=true within seconds.

Refuses to run with a live key.
Refuses to run if ENVIRONMENT=production.

Usage:
    cd /app/backend && python -m scripts.seed_connect_accounts            # all
    cd /app/backend && python -m scripts.seed_connect_accounts eden-church-001
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

# Allow running as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stripe  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

# Force override of shell env vars (Emergent preview pod ships
# STRIPE_API_KEY=sk_test_emergent which masks the real key in .env).
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            override=True)

from core import db  # noqa: E402
from core.connect import (  # noqa: E402
    create_test_custom_account,
    derive_status_from_account,
    CONNECT_STATUS_ACTIVE,
)
from scripts._prod_guard import refuse_in_production  # noqa: E402

logger = logging.getLogger("solomon.seed_connect")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


async def seed_one(tenant: dict, force: bool = False) -> dict:
    tenant_id = tenant["id"]
    if tenant.get("stripe_connect_account_id") and not force:
        logger.info(f"  ↪ {tenant_id}: already has Connect account "
                    f"{tenant['stripe_connect_account_id']} (status="
                    f"{tenant.get('stripe_connect_status')}), skipping")
        return {"tenant_id": tenant_id, "skipped": True}

    # Find an admin email
    admin_user = await db.users.find_one(
        {"tenant_id": tenant_id, "role": "church_admin"},
        {"_id": 0, "email": 1},
    )
    admin_email = (admin_user or {}).get("email") or f"admin@{tenant.get('subdomain','solomon')}.church"

    try:
        acct = await create_test_custom_account(
            tenant_id=tenant_id,
            tenant_name=tenant["name"],
            admin_email=admin_email,
        )
    except stripe.error.StripeError as e:
        logger.error(f"  ✗ {tenant_id}: Stripe error: {e}")
        return {"tenant_id": tenant_id, "error": str(e)}

    status = derive_status_from_account(acct)
    update = {
        "stripe_connect_account_id": acct.id,
        "stripe_connect_status": status,
    }
    if status == CONNECT_STATUS_ACTIVE:
        update["stripe_connect_onboarded_at"] = datetime.now(timezone.utc).isoformat()
    await db.tenants.update_one({"id": tenant_id}, {"$set": update})
    logger.info(f"  ✓ {tenant_id}: {acct.id} → {status}")
    return {"tenant_id": tenant_id, "account_id": acct.id, "status": status}


async def seed_all(only_tenant_id: str | None = None, force: bool = False) -> list:
    refuse_in_production(__file__)

    if not stripe.api_key:
        stripe.api_key = os.environ.get("STRIPE_API_KEY", "")
    if not stripe.api_key:
        raise SystemExit("STRIPE_API_KEY not set in env")
    if stripe.api_key.startswith("sk_live_"):
        raise SystemExit("Refusing to run seed_connect_accounts on a LIVE Stripe key")

    q = {"id": only_tenant_id} if only_tenant_id else {}
    tenants = await db.tenants.find(q, {"_id": 0}).to_list(50)
    if not tenants:
        raise SystemExit(f"No tenants matched: {q}")

    results = []
    for t in tenants:
        results.append(await seed_one(t, force=force))
    logger.info(f"done. {len(results)} tenant(s) processed.")
    return results


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    force = "--force" in sys.argv
    asyncio.run(seed_all(only, force=force))
