"""
Solomon AI — Stripe Connect helpers
====================================
Centralizes everything related to per-tenant Stripe Connect accounts so
the rest of the codebase never has to think about Connect plumbing.

Design rules
------------
* `STRIPE_API_KEY` is the platform's secret key. Test or live, doesn't
  matter — the same code paths work on both. Item C requirement:
  "swapping sk_test → sk_live requires ZERO code changes."
* We use **Direct Charges** (`stripe_account=connected_id`): the charge
  appears on the connected account's statement (church's name on the
  donor's bank statement, not Solomon's). `application_fee_amount`
  captures Solomon's cut.
* All Stripe calls go through `_run_stripe()` so we can swap the SDK to
  threadpool / async / mocked at one chokepoint.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

import stripe

logger = logging.getLogger("solomon.connect")

# Default Solomon platform fee — overridable per tenant via tenant.fee_schedule
DEFAULT_PLATFORM_PERCENT = 0.019      # 1.9 %
DEFAULT_PLATFORM_FIXED_CENTS = 30     # $0.30


# ─────────────────────────── Status enum ────────────────────────────────
CONNECT_STATUS_NOT_STARTED = "not_started"
CONNECT_STATUS_ONBOARDING = "onboarding"
CONNECT_STATUS_PENDING_VERIFICATION = "pending_verification"
CONNECT_STATUS_ACTIVE = "active"
CONNECT_STATUS_RESTRICTED = "restricted"

ALL_STATUSES = {
    CONNECT_STATUS_NOT_STARTED,
    CONNECT_STATUS_ONBOARDING,
    CONNECT_STATUS_PENDING_VERIFICATION,
    CONNECT_STATUS_ACTIVE,
    CONNECT_STATUS_RESTRICTED,
}


def default_fee_schedule() -> dict:
    """Default fee schedule applied to a tenant on creation."""
    return {
        "platform_percent": DEFAULT_PLATFORM_PERCENT,
        "platform_fixed_cents": DEFAULT_PLATFORM_FIXED_CENTS,
        "override": False,
    }


def calculate_application_fee(amount_cents: int, fee_schedule: Optional[dict] = None) -> int:
    """Compute Solomon's application_fee_amount (in cents) for a charge.

    Stripe will deduct this from the connected account's balance and
    transfer it to the platform. The donor still pays `amount_cents`;
    the church receives `amount_cents - application_fee_amount - stripe_fee`.

    Defensive: never returns >= amount_cents (Stripe rejects fees that
    would leave the merchant with $0 or less).
    """
    fs = fee_schedule or default_fee_schedule()
    pct = float(fs.get("platform_percent", DEFAULT_PLATFORM_PERCENT))
    fixed = int(fs.get("platform_fixed_cents", DEFAULT_PLATFORM_FIXED_CENTS))
    fee = int(round(amount_cents * pct)) + fixed
    return max(0, min(fee, amount_cents - 1))


# ───────────────────── Stripe SDK chokepoint ───────────────────────────
async def _run_stripe(fn, *args, **kwargs):
    """Run a synchronous stripe SDK call on a worker thread so async
    handlers don't block the event loop. Single chokepoint so we can
    swap in `stripe.AsyncClient` later in one place."""
    return await asyncio.to_thread(fn, *args, **kwargs)


# ───────────────────────── Account ops ──────────────────────────────────
async def create_express_account(tenant_id: str, tenant_name: str,
                                 admin_email: str, country: str = "US") -> stripe.Account:
    """Create a Stripe Express Connect account for a tenant. Idempotent
    via tenant_id metadata: callers should check tenant.stripe_connect_account_id
    before calling."""
    return await _run_stripe(
        stripe.Account.create,
        type="express",
        country=country,
        email=admin_email,
        business_type="non_profit",
        capabilities={
            "card_payments": {"requested": True},
            "transfers": {"requested": True},
        },
        business_profile={
            "name": tenant_name[:100],
            "mcc": "8661",  # MCC 8661 = Religious Organizations
            "product_description": f"Tithes and offerings for {tenant_name}",
        },
        metadata={
            "tenant_id": tenant_id,
            "platform": "solomon_ai",
        },
    )


async def create_test_custom_account(tenant_id: str, tenant_name: str,
                                     admin_email: str) -> stripe.Account:
    """TEST MODE ONLY — create a `custom` account that we can prefill so
    `details_submitted=true` and `charges_enabled=true` in seconds, no
    manual KYB UI dance. Used by `scripts/seed_connect_accounts.py` to
    bootstrap the 7 demo tenants. Refuses to run with a live key."""
    if os.environ.get("STRIPE_API_KEY", "").startswith("sk_live_"):
        raise RuntimeError("create_test_custom_account refuses to run on a live key")
    acct = await _run_stripe(
        stripe.Account.create,
        type="custom",
        country="US",
        email=admin_email,
        business_type="non_profit",
        capabilities={
            "card_payments": {"requested": True},
            "transfers": {"requested": True},
        },
        business_profile={
            "name": tenant_name[:100],
            "mcc": "8661",
            "url": "https://solomonai.us",
            "product_description": f"Tithes and offerings for {tenant_name}",
        },
        company={
            "name": tenant_name[:100],
            "tax_id": "000000000",
            "address": {"line1": "address_full_match", "city": "Austin",
                        "state": "TX", "postal_code": "78701", "country": "US"},
            "phone": "0000000000",
            "directors_provided": True,
            "executives_provided": True,
            "owners_provided": True,
        },
        tos_acceptance={
            "date": int(datetime.now(timezone.utc).timestamp()),
            "ip": "127.0.0.1",
            "service_agreement": "full",
        },
        metadata={"tenant_id": tenant_id, "platform": "solomon_ai", "seed": "test_mode"},
    )
    # In test mode Stripe will mark charges_enabled / payouts_enabled true
    # almost immediately for accounts with the prefilled fixture above.
    return acct


async def create_account_link(account_id: str, base_url: str) -> stripe.AccountLink:
    """Generate a one-time onboarding URL the church admin opens to
    complete KYB. Stripe-hosted UI."""
    return await _run_stripe(
        stripe.AccountLink.create,
        account=account_id,
        refresh_url=f"{base_url}/admin/settings/payments?connect=refresh",
        return_url=f"{base_url}/admin/settings/payments?connect=complete",
        type="account_onboarding",
    )


async def retrieve_account(account_id: str) -> stripe.Account:
    return await _run_stripe(stripe.Account.retrieve, account_id)


def derive_status_from_account(account: Any) -> str:
    """Map a Stripe Account object to our internal status enum."""
    if not account:
        return CONNECT_STATUS_NOT_STARTED
    # `account` may be a stripe object or a plain dict (from a webhook payload)
    def _g(k):
        if isinstance(account, dict):
            return account.get(k)
        return getattr(account, k, None)
    charges_enabled = bool(_g("charges_enabled"))
    payouts_enabled = bool(_g("payouts_enabled"))
    requirements = _g("requirements") or {}
    if isinstance(requirements, dict):
        disabled_reason = requirements.get("disabled_reason")
        currently_due = requirements.get("currently_due") or []
        past_due = requirements.get("past_due") or []
    else:
        disabled_reason = getattr(requirements, "disabled_reason", None)
        currently_due = getattr(requirements, "currently_due", None) or []
        past_due = getattr(requirements, "past_due", None) or []

    if disabled_reason and "rejected" in str(disabled_reason):
        return CONNECT_STATUS_RESTRICTED
    if charges_enabled and payouts_enabled:
        return CONNECT_STATUS_ACTIVE
    if past_due or currently_due:
        return CONNECT_STATUS_PENDING_VERIFICATION
    if _g("details_submitted"):
        return CONNECT_STATUS_PENDING_VERIFICATION
    return CONNECT_STATUS_ONBOARDING


async def sync_tenant_status_from_stripe(db, tenant_id: str) -> dict:
    """Pull the latest account state from Stripe and persist."""
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        return {"updated": False, "reason": "tenant_not_found"}
    acct_id = tenant.get("stripe_connect_account_id")
    if not acct_id:
        return {"updated": False, "reason": "no_connect_account"}
    try:
        account = await retrieve_account(acct_id)
    except stripe.error.StripeError as e:
        logger.warning(f"[connect] retrieve failed for {acct_id}: {e}")
        return {"updated": False, "reason": "stripe_error"}
    status = derive_status_from_account(account)
    update = {"stripe_connect_status": status}
    if status == CONNECT_STATUS_ACTIVE and not tenant.get("stripe_connect_onboarded_at"):
        update["stripe_connect_onboarded_at"] = datetime.now(timezone.utc).isoformat()
    await db.tenants.update_one({"id": tenant_id}, {"$set": update})
    return {"updated": True, "status": status}


# ─────────────────────────── Tenant guard ───────────────────────────────
class PaymentConfigError(Exception):
    """Raised when a tenant cannot accept payments (no/restricted Connect
    account). Caller maps to a 400/402 with a clear donor-facing message."""


async def require_active_connect_account(db, tenant_id: str) -> dict:
    """Lookup + validate. Returns the tenant doc on success.
    Raises PaymentConfigError otherwise. Use this at every PI-creation
    callsite so a misconfigured tenant fails closed with a clear error."""
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise PaymentConfigError(f"Tenant {tenant_id} not found")
    acct_id = tenant.get("stripe_connect_account_id")
    status = tenant.get("stripe_connect_status", CONNECT_STATUS_NOT_STARTED)
    if not acct_id or status in (CONNECT_STATUS_NOT_STARTED, CONNECT_STATUS_RESTRICTED):
        raise PaymentConfigError(
            "Payment processing not configured for this church. "
            "Please contact your church admin."
        )
    return tenant


def get_fee_schedule(tenant: dict) -> dict:
    """Read fee schedule off a tenant doc, falling back to platform default."""
    fs = tenant.get("fee_schedule") or {}
    if not fs:
        return default_fee_schedule()
    # Backfill any missing keys from defaults
    out = default_fee_schedule()
    out.update({k: v for k, v in fs.items() if k in out or k == "override"})
    return out
