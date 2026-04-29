"""
Complete test-mode Connect onboarding by prefilling representative
person + external bank account. Flips status from pending_verification
→ active so the rest of the platform can be exercised end-to-end.

REFUSES on live keys.
REFUSES in production.

Usage:
    python -m scripts.activate_test_connect_accounts
    python -m scripts.activate_test_connect_accounts eden-church-001
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

import stripe  # noqa: E402

from core import db  # noqa: E402
from core.connect import derive_status_from_account, CONNECT_STATUS_ACTIVE  # noqa: E402
from scripts._prod_guard import refuse_in_production  # noqa: E402


async def activate_one(tenant: dict) -> dict:
    acct_id = tenant.get("stripe_connect_account_id")
    if not acct_id:
        return {"tenant_id": tenant["id"], "skipped": "no_account"}

    # Look up admin user for the representative email
    admin = await db.users.find_one(
        {"tenant_id": tenant["id"], "role": "church_admin"},
        {"_id": 0, "email": 1, "first_name": 1, "last_name": 1},
    )
    rep_email = (admin or {}).get("email", f"admin@{tenant.get('subdomain','solomon')}.church")
    rep_first = (admin or {}).get("first_name") or "Test"
    rep_last = (admin or {}).get("last_name") or "Representative"

    # ── 1. Prefill representative person ──
    # Test-mode magic values: id_number=000000000, address_full_match,
    # phone=0000000000. Idempotent: if a representative person already
    # exists from a prior run, update it; otherwise create a new one.
    person_kwargs = dict(
        first_name=rep_first[:50],
        last_name=rep_last[:50],
        email=rep_email,
        phone="0000000000",
        dob={"day": 1, "month": 1, "year": 1985},
        ssn_last_4="0000",
        id_number="000000000",
        address={
            "line1": "address_full_match",
            "city": "Austin",
            "state": "TX",
            "postal_code": "78701",
            "country": "US",
        },
        relationship={
            "representative": True,
            "executive": True,
            "title": "Pastor",
        },
    )
    try:
        existing = stripe.Account.list_persons(acct_id, limit=10)
        rep = next((p for p in existing.data
                    if p.get("relationship", {}).get("representative")), None)
        if rep:
            person = stripe.Account.modify_person(acct_id, rep.id, **person_kwargs)
        else:
            person = stripe.Account.create_person(acct_id, **person_kwargs)
    except stripe.error.StripeError as e:
        return {"tenant_id": tenant["id"], "error": f"Person op: {e}"}

    # ── 2. Attach an external bank account (test-mode magic numbers).
    #       Idempotent: skip if any external account already attached. ──
    try:
        existing_ext = stripe.Account.list_external_accounts(acct_id, limit=1)
        if not existing_ext.data:
            bank_token = stripe.Token.create(
                bank_account={
                    "country": "US",
                    "currency": "usd",
                    "account_holder_name": tenant["name"][:60],
                    "account_holder_type": "company",
                    "routing_number": "110000000",
                    "account_number": "000123456789",
                },
            )
            stripe.Account.create_external_account(acct_id, external_account=bank_token.id)
    except stripe.error.StripeError as e:
        return {"tenant_id": tenant["id"], "error": f"external_account: {e}"}

    # ── 3. Re-accept TOS + signal we're done ──
    try:
        stripe.Account.modify(
            acct_id,
            tos_acceptance={
                "date": int(datetime.now(timezone.utc).timestamp()),
                "ip": "127.0.0.1",
                "service_agreement": "full",
            },
        )
    except stripe.error.StripeError as e:
        return {"tenant_id": tenant["id"], "error": f"modify: {e}"}

    # ── 4. Pull updated state ──
    # Brief wait for Stripe's async test-mode verification queue to clear.
    import time
    time.sleep(2)
    acct = stripe.Account.retrieve(acct_id)
    status = derive_status_from_account(acct)
    update = {"stripe_connect_status": status}
    if status == CONNECT_STATUS_ACTIVE and not tenant.get("stripe_connect_onboarded_at"):
        update["stripe_connect_onboarded_at"] = datetime.now(timezone.utc).isoformat()
    await db.tenants.update_one({"id": tenant["id"]}, {"$set": update})

    return {
        "tenant_id": tenant["id"],
        "account_id": acct_id,
        "status": status,
        "charges_enabled": acct.charges_enabled,
        "payouts_enabled": acct.payouts_enabled,
        "person_id": person.id,
    }


async def main(only: str | None = None):
    refuse_in_production(__file__)
    if not stripe.api_key:
        stripe.api_key = os.environ.get("STRIPE_API_KEY", "")
    if stripe.api_key.startswith("sk_live_"):
        raise SystemExit("Refusing to run on a LIVE key")

    q = {"id": only} if only else {"stripe_connect_account_id": {"$ne": None}}
    tenants = await db.tenants.find(q, {"_id": 0}).to_list(50)
    if not tenants:
        raise SystemExit("No tenants with Connect accounts found")

    print(f"{'tenant_id':<25} {'account_id':<28} {'status':<22} charges payouts")
    print("-" * 90)
    for t in tenants:
        r = await activate_one(t)
        if "error" in r:
            print(f"{t['id']:<25} {t.get('stripe_connect_account_id','?'):<28} ERROR: {r['error'][:50]}")
        elif "skipped" in r:
            print(f"{t['id']:<25} (skipped: {r['skipped']})")
        else:
            print(f"{r['tenant_id']:<25} {r['account_id']:<28} {r['status']:<22} "
                  f"{str(r['charges_enabled']):<7} {r['payouts_enabled']}")


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(only))
