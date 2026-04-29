"""
DEV-ONLY stub: pretend each tenant has an active Stripe Connect account
========================================================================
Why this exists
---------------
Until the Stripe platform Connect signup is fully active on the account
that owns our `sk_test_*` key, `stripe.Account.create()` rejects every
call with "you can only create new accounts if you've signed up for
Connect." The platform code that runs AFTER Connect provisioning (PI
creation with `stripe_account=`, application_fee math, recurring setup,
frontend gate, scheduler) cannot be exercised end-to-end while every
tenant sits at `stripe_connect_status='not_started'`.

This script seeds **fake** `acct_test_*` IDs onto every tenant so the
status flips to `active` and the PI-creation path gets exercised. Stripe
will reject the fake account at the API call itself with a clear error,
but every line of OUR code runs.

Refuses production. Refuses live keys. Always reversible:
    python -m scripts.stub_connect_accounts --reset
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            override=True)

from core import db  # noqa: E402
from scripts._prod_guard import refuse_in_production  # noqa: E402


def _fake_acct_id(tenant_id: str) -> str:
    # Use a syntactically Stripe-shaped id with our own prefix — never
    # collides with real `acct_*` once Connect is wired up.
    suffix = "".join(c for c in tenant_id if c.isalnum())[:16].ljust(16, "0").upper()
    return f"acct_stub_{suffix}"


async def stub_all() -> None:
    refuse_in_production(__file__)
    if os.environ.get("STRIPE_API_KEY", "").startswith("sk_live_"):
        raise SystemExit("Refusing to stub against a live key")
    cursor = db.tenants.find({}, {"_id": 0})
    n = 0
    print(f"{'tenant_id':<28} {'fake stripe_connect_account_id':<40} status")
    print("-" * 80)
    async for t in cursor:
        fake = _fake_acct_id(t["id"])
        await db.tenants.update_one(
            {"id": t["id"]},
            {"$set": {
                "stripe_connect_account_id": fake,
                "stripe_connect_status": "active",
                "stripe_connect_onboarded_at": datetime.now(timezone.utc).isoformat(),
                "stripe_connect_stub": True,  # marker for revert
            }},
        )
        print(f"{t['id']:<28} {fake:<40} active (stub)")
        n += 1
    print(f"\n✓ stubbed {n} tenant(s). Run with --reset to revert.")


async def reset_all() -> None:
    refuse_in_production(__file__)
    res = await db.tenants.update_many(
        {"stripe_connect_stub": True},
        {"$set": {
            "stripe_connect_account_id": None,
            "stripe_connect_status": "not_started",
            "stripe_connect_onboarded_at": None,
        },
         "$unset": {"stripe_connect_stub": ""}},
    )
    print(f"✓ reverted {res.modified_count} stubbed tenant(s) to not_started.")


if __name__ == "__main__":
    if "--reset" in sys.argv:
        asyncio.run(reset_all())
    else:
        asyncio.run(stub_all())
