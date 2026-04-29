"""
Stripe Elements — Embedded card-on-page payments for Solomon Pay.

Unlike stripe_connect.py (which uses the HOSTED Stripe Checkout redirect flow),
this router powers the EMBEDDED Stripe Elements flow used by:

  - /give/:church_slug                 — public, no-auth, guest giving page
  - /portal/give (future)              — authenticated member portal giving

It uses the raw stripe Python SDK (installed as stripe==14.3.0) so we can
process PaymentIntents, confirm on-page, and read balance/payouts without
redirecting to checkout.stripe.com.

Security posture:
  * Amounts are re-computed server-side from the request (package allow-list
    for quick amounts, or a raw amount capped at $100,000) — frontend cannot
    manipulate totals to produce negative fees.
  * tenant_id and fund name resolved server-side from the church_slug.
  * PaymentIntent metadata carries tenant_id + fund + donor fields so the
    confirm-donation step can reconstruct the donation record safely.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time as _time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import stripe
from dotenv import dotenv_values
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from core import db

logger = logging.getLogger("solomon.stripe_elements")
router = APIRouter()

# ═══ Configuration ══════════════════════════════════════════════════════════
# NOTE: The Emergent pod environment exports STRIPE_API_KEY=sk_test_emergent
# as a platform default. That value takes precedence over python-dotenv's
# non-override load_dotenv(), which would silently leave us with the wrong
# key. We therefore prefer the values straight out of backend/.env and only
# fall back to os.environ when the file is empty.
_DOTENV_VALUES = dotenv_values(Path(__file__).resolve().parents[1] / ".env")


def _stripe_env(name: str) -> str:
    val = (_DOTENV_VALUES.get(name) or "").strip().strip("\"'")
    if not val:
        val = (os.environ.get(name) or "").strip().strip("\"'")
    return val


STRIPE_API_KEY = _stripe_env("STRIPE_API_KEY")
STRIPE_PUBLISHABLE_KEY = _stripe_env("STRIPE_PUBLISHABLE_KEY")
STRIPE_LIVE = _stripe_env("STRIPE_LIVE").lower() == "true"

# Treat any sk_test_ key as test mode regardless of STRIPE_LIVE
IS_TEST_MODE = STRIPE_API_KEY.startswith("sk_test_") or not STRIPE_LIVE

if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY
    logger.info("stripe_configured", extra={"key_len": len(STRIPE_API_KEY), "test_mode": IS_TEST_MODE})
else:
    logger.warning("stripe_api_key_missing")

# Solomon platform fee (passed to the donor if they opt to cover)
PLATFORM_FEE_RATE = 0.019   # 1.9%
PLATFORM_FEE_FIXED = 0.30   # $0.30
MAX_DONATION_USD = 100_000  # sanity cap


def _compute_cover_fee(amount: float) -> float:
    """If the donor opts to cover processing, add 1.9% + $0.30."""
    return round(amount * PLATFORM_FEE_RATE + PLATFORM_FEE_FIXED, 2)


async def _tenant_by_slug(slug: str) -> dict:
    """Resolve a church identifier → tenant doc (without Mongo _id).

    Accepts any of three keys so the public give-page URL is forgiving across
    deployments where the seed naming has drifted (some deploys store
    ``slug='eden-church'``, others only ``subdomain='eden'``, others only
    the canonical ``id='eden-church-001'``).
    """
    t = await db.tenants.find_one(
        {"$or": [{"slug": slug}, {"subdomain": slug}, {"id": slug}]},
        {"_id": 0},
    )
    if not t:
        raise HTTPException(status_code=404, detail=f"Church not found: {slug}")
    return t


# ═══ Public configuration ══════════════════════════════════════════════════

@router.get("/stripe/elements/config")
async def stripe_elements_config():
    """Return the publishable key and test-mode flag. Frontend uses this
    before mounting Stripe Elements."""
    return {
        "publishable_key": STRIPE_PUBLISHABLE_KEY,
        "test_mode": IS_TEST_MODE,
        "configured": bool(STRIPE_API_KEY and STRIPE_PUBLISHABLE_KEY),
    }


@router.get("/churches/{slug}/public-config")
async def public_church_config(slug: str):
    """PUBLIC — no auth. Returns just the branding a guest giving page needs.
    NEVER leak financial or member data here."""
    t = await _tenant_by_slug(slug)

    fund_cursor = db.funds.find(
        {"tenant_id": t["id"], "is_active": True},
        {"_id": 0, "name": 1, "is_default": 1},
    )
    funds = await fund_cursor.to_list(None)
    fund_names = [f["name"] for f in funds] or ["General Fund"]

    return {
        "slug": t["slug"],
        "name": t["name"],
        "logo_url": t.get("logo_url"),
        "primary_color": t.get("primary_color", "#111827"),
        "accent_color": t.get("accent_color", "#3b82f6"),
        "funds": fund_names,
        "preset_amounts": [25, 50, 100, 250, 500],
        "cover_fees_default": True,
        "frequencies": ["one-time", "weekly", "monthly"],
        "website_url": t.get("website"),
        "pastor_name": t.get("pastor_name"),
        "stripe_test_mode": t.get("stripe_test_mode", IS_TEST_MODE),
        # ── Connect (BLOCKER #1) ──
        # Frontend uses these to (a) initialize Stripe.js with stripeAccount
        # so the card element talks to the connected account directly, and
        # (b) hide the giving form behind a "this church can't accept gifts
        # yet" message when status != active.
        "connected_account_id": t.get("stripe_connect_account_id"),
        "accepts_payments": t.get("stripe_connect_status") == "active",
    }


# ═══ PaymentIntent lifecycle ═══════════════════════════════════════════════

class CreatePaymentIntentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Donation amount in USD (dollars)")
    fund: str = "Tithes"
    frequency: str = "one-time"
    donor_first_name: str = ""
    donor_last_name: str = ""
    donor_email: Optional[EmailStr] = None
    cover_fees: bool = False
    church_slug: str
    message: Optional[str] = ""


@router.post("/stripe/create-payment-intent")
async def create_payment_intent(payload: CreatePaymentIntentRequest):
    """Create a Stripe PaymentIntent tied to a specific church + fund. No auth
    required — this is the guest giving path.

    Connect (BLOCKER #1): direct charge on the tenant's connected account.
    `stripe_account=` puts the charge on the connected account's statement
    (church's name on donor's bank statement), and `application_fee_amount`
    captures Solomon's cut. Tenants without an active Connect account fail
    closed with 400 — donors see "payment processing not configured for
    this church"."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured on server")

    if payload.amount <= 0 or payload.amount > MAX_DONATION_USD:
        raise HTTPException(400, f"Amount must be between $0.01 and ${MAX_DONATION_USD:,}")

    tenant = await _tenant_by_slug(payload.church_slug)

    # ── Require active Connect account (BLOCKER #1) ──
    from core.connect import (
        require_active_connect_account, calculate_application_fee, get_fee_schedule,
        PaymentConfigError,
    )
    try:
        tenant = await require_active_connect_account(db, tenant["id"])
    except PaymentConfigError as e:
        from core.errors import client_error as _ce
        raise _ce(status_code=400, user_message="Invalid payment request.", log_message="stripe_elements.bad_request", exc=e)
    connect_account_id = tenant["stripe_connect_account_id"]
    fee_schedule = get_fee_schedule(tenant)

    base_amount = round(payload.amount, 2)
    fee = _compute_cover_fee(base_amount) if payload.cover_fees else 0.0
    total = round(base_amount + fee, 2)
    amount_cents = int(round(total * 100))
    application_fee_amount = calculate_application_fee(amount_cents, fee_schedule)

    metadata = {
        "tenant_id": tenant["id"],
        "church_slug": tenant["slug"],
        "church_name": tenant["name"][:100],
        "fund": payload.fund[:100],
        "frequency": payload.frequency[:40],
        "donor_first_name": (payload.donor_first_name or "")[:100],
        "donor_last_name": (payload.donor_last_name or "")[:100],
        "donor_email": str(payload.donor_email) if payload.donor_email else "",
        "cover_fees": "true" if payload.cover_fees else "false",
        "base_amount_cents": str(int(round(base_amount * 100))),
        "fee_cents": str(int(round(fee * 100))),
        "message": (payload.message or "")[:250],
        "source": "solomon_pay_elements",
        "test_mode": "true" if IS_TEST_MODE else "false",
    }

    # statement_descriptor_suffix caps at 22 chars; strip to alphanumerics
    suffix = "".join(c for c in tenant["name"].upper() if c.isalnum() or c == " ")[:20] or "SOLOMON PAY"

    # ── Idempotency (BLOCKER #8 from production audit) ──
    # Donor double-tap on flaky cell, browser back-button retry, or our
    # own retry middleware would otherwise create N PaymentIntents for the
    # same gift. We key the request by (tenant, donor email, base amount,
    # rounded-down minute) so a true duplicate within the same minute
    # collapses to one PI on Stripe's side. Stripe stores idempotency keys
    # for 24 hours, which is more than enough.
    #
    # We deliberately include base_amount_cents AND cover_fees in the key
    # so a donor toggling "cover fees" off then on within the same minute
    # creates a NEW PI rather than reusing the previous one — the dollar
    # amount actually charged to Stripe differs (Stripe rejects same-key
    # different-body with 400 "Keys for idempotent requests can only be
    # used with the same parameters they were first used with").
    import hashlib as _hl
    import time as _t
    _key_seed = (
        f"{tenant['id']}:{(payload.donor_email or '').lower()}:"
        f"{int(round(base_amount * 100))}:{int(payload.cover_fees)}:"
        f"{int(_t.time() // 60)}"
    )
    idempotency_key = "solpay_pi_" + _hl.sha256(_key_seed.encode()).hexdigest()[:32]

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            metadata=metadata,
            statement_descriptor_suffix=suffix,
            receipt_email=metadata["donor_email"] or None,
            # ── Connect: direct charge on the tenant's connected account ──
            application_fee_amount=application_fee_amount,
            stripe_account=connect_account_id,
            idempotency_key=idempotency_key,
        )
    except stripe.error.StripeError as e:
        logger.error("stripe_create_intent_failed", extra={"exc_type": type(e).__name__, "tenant_id": tenant.get("id")})
        raise HTTPException(502, "Stripe error")

    # Pre-create a pending payment_transactions row (MANDATED by integration playbook)
    await db.payment_transactions.insert_one({
        "tenant_id": tenant["id"],
        "payment_intent_id": intent.id,
        "session_id": intent.id,          # Elements has no separate session
        "amount_cents": amount_cents,
        "currency": "usd",
        "base_amount": base_amount,
        "fee_amount": fee,
        "total_amount": total,
        "metadata": metadata,
        "status": "pending",
        "payment_status": "requires_confirmation",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "client_secret": intent.client_secret,
        "payment_intent_id": intent.id,
        "total_amount": total,
        "base_amount": base_amount,
        "fee_amount": fee,
        # Frontend must initialize Stripe(...) with stripeAccount to talk to
        # the connected account (direct charge model).
        "connected_account_id": connect_account_id,
        "application_fee_amount": application_fee_amount,
    }


class ConfirmDonationRequest(BaseModel):
    payment_intent_id: str
    church_slug: str


@router.post("/stripe/confirm-donation")
async def confirm_donation(payload: ConfirmDonationRequest):
    """Called by the frontend after stripe.confirmCardPayment() resolves with
    status=succeeded. We re-query Stripe server-side (never trust the client)
    and, if succeeded, persist the donation record exactly once."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured on server")

    tenant = await _tenant_by_slug(payload.church_slug)
    # Connect direct charges live on the connected account, so the PI must
    # be retrieved with stripe_account=. The tenant doc already has the id.
    connect_account_id = tenant.get("stripe_connect_account_id")

    try:
        if connect_account_id:
            intent = stripe.PaymentIntent.retrieve(
                payload.payment_intent_id, stripe_account=connect_account_id,
            )
        else:
            intent = stripe.PaymentIntent.retrieve(payload.payment_intent_id)
    except stripe.error.StripeError as e:
        raise HTTPException(502, "Stripe error")

    if intent.metadata.get("tenant_id") != tenant["id"]:
        # Refuse cross-tenant confirmation attempts
        raise HTTPException(403, "PaymentIntent does not belong to this church")

    if intent.status != "succeeded":
        return {
            "status": intent.status,
            "donation_id": None,
            "amount": intent.amount,
            "message": "Payment not yet succeeded.",
        }

    # Idempotency — if we already logged this intent as a donation, return it
    existing = await db.donations.find_one(
        {"stripe_payment_intent_id": intent.id},
        {"_id": 0},
    )
    if existing:
        await db.payment_transactions.update_one(
            {"payment_intent_id": intent.id},
            {"$set": {"status": "completed", "payment_status": "succeeded"}},
        )
        return {"status": "succeeded", "donation": existing, "already_recorded": True}

    # Pull the PaymentMethod for the card details
    pm_brand = None
    pm_last4 = None
    pm_id = None
    ch_id = None
    try:
        if intent.payment_method:
            if connect_account_id:
                pm = stripe.PaymentMethod.retrieve(
                    intent.payment_method, stripe_account=connect_account_id,
                )
            else:
                pm = stripe.PaymentMethod.retrieve(intent.payment_method)
            pm_id = pm.id
            if pm.type == "card" and pm.card:
                pm_brand = pm.card.brand
                pm_last4 = pm.card.last4
        if intent.latest_charge:
            ch_id = intent.latest_charge
    except stripe.error.StripeError as e:
        logger.warning("stripe_fetch_payment_method_failed", extra={"exc_type": type(e).__name__})

    md = intent.metadata or {}
    base_cents = int(md.get("base_amount_cents") or intent.amount)
    fee_cents = int(md.get("fee_cents") or 0)

    donor_email = md.get("donor_email") or ""
    donor_name = (
        f"{md.get('donor_first_name', '')} {md.get('donor_last_name', '')}"
    ).strip() or "Guest Donor"

    now = datetime.now(timezone.utc).isoformat()
    donation = {
        "id": f"don_{intent.id}",
        "tenant_id": tenant["id"],
        "donor_name": donor_name,
        "donor_email": donor_email,
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
        "donation_date": now.split("T")[0],
        "created_at": now,
        "stripe_payment_intent_id": intent.id,
        "stripe_payment_method_id": pm_id,
        "stripe_charge_id": ch_id,
        "card_brand": pm_brand,
        "card_last_four": pm_last4,
        "message": md.get("message") or "",
        "status": "succeeded",
    }
    await db.donations.insert_one(donation)
    # strip _id since insert_one mutates the dict
    donation.pop("_id", None)

    # Update fund rollup
    await db.funds.update_one(
        {"tenant_id": tenant["id"], "name": donation["fund_name"]},
        {"$inc": {"current_amount": donation["amount"]}},
    )

    # Mark transaction completed
    await db.payment_transactions.update_one(
        {"payment_intent_id": intent.id},
        {"$set": {
            "status": "completed",
            "payment_status": "succeeded",
            "donation_id": donation["id"],
            "completed_at": now,
        }},
    )

    # Bust dashboard caches so God Mode + Solomon Pay see the new gift
    # within the next request — not after the 30s/15-min TTL. Awaits the
    # full bust including MongoDB cache rows for sub-3s visibility on
    # both church-admin and platform-admin dashboards.
    from core.realtime import bust_donation_caches
    await bust_donation_caches(tenant["id"])

    return {"status": "succeeded", "donation": donation, "already_recorded": False}


@router.get("/stripe/payment-intent/{intent_id}/status")
async def get_payment_intent_status(intent_id: str):
    """Lightweight poller for the frontend status screen."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured on server")
    try:
        intent = stripe.PaymentIntent.retrieve(intent_id)
    except stripe.error.StripeError as e:
        raise HTTPException(404, "Stripe error")
    return {
        "id": intent.id,
        "status": intent.status,
        "amount": intent.amount,
        "currency": intent.currency,
    }


# ═══════════════════════════════════════════════════════════════════════
#  Recurring Giving — SetupIntent flow (BLOCKER #3)
# ═══════════════════════════════════════════════════════════════════════
class CreateRecurringSetupRequest(BaseModel):
    church_slug: str
    donor_email: str
    donor_first_name: Optional[str] = ""
    donor_last_name: Optional[str] = ""


@router.post("/stripe/recurring/setup-intent")
async def create_recurring_setup_intent(payload: CreateRecurringSetupRequest):
    """First-time donor sets up recurring giving:

      1. We resolve the church's Connect account (must be active).
      2. We create or fetch a Stripe Customer **on the connected account**
         (Connect direct-charge model — customers live on the connected
         account, not the platform).
      3. We mint a SetupIntent so the donor's card collected via Stripe
         Elements is saved to that Customer for off-session use.
      4. The frontend confirms the SetupIntent client-side, then calls
         `POST /stripe/recurring/confirm` to receive the saved
         payment_method_id and create the recurring_giving record.
    """
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured on server")
    tenant = await _tenant_by_slug(payload.church_slug)

    from core.connect import require_active_connect_account, PaymentConfigError, _run_stripe
    try:
        tenant = await require_active_connect_account(db, tenant["id"])
    except PaymentConfigError as e:
        raise HTTPException(400, detail=str(e))
    connect_account_id = tenant["stripe_connect_account_id"]

    # ── Find or create the Stripe Customer on the connected account ──
    email = (payload.donor_email or "").lower().strip()
    if not email:
        raise HTTPException(400, "Donor email is required for recurring giving")

    existing_donor = await db.recurring_donors.find_one(
        {"tenant_id": tenant["id"], "donor_email": email}, {"_id": 0}
    )
    customer_id = (existing_donor or {}).get("stripe_customer_id")

    if not customer_id:
        try:
            customer = await _run_stripe(
                stripe.Customer.create,
                email=email,
                name=f"{payload.donor_first_name} {payload.donor_last_name}".strip() or None,
                metadata={"tenant_id": tenant["id"], "source": "recurring_setup"},
                stripe_account=connect_account_id,
            )
        except stripe.error.StripeError as e:
            raise HTTPException(502, "Stripe error")
        customer_id = customer.id
        await db.recurring_donors.update_one(
            {"tenant_id": tenant["id"], "donor_email": email},
            {"$set": {
                "tenant_id": tenant["id"],
                "donor_email": email,
                "donor_first_name": payload.donor_first_name or "",
                "donor_last_name": payload.donor_last_name or "",
                "stripe_customer_id": customer_id,
                "connected_account_id": connect_account_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )

    # ── Mint the SetupIntent ──
    try:
        si = await _run_stripe(
            stripe.SetupIntent.create,
            customer=customer_id,
            payment_method_types=["card"],
            usage="off_session",
            metadata={"tenant_id": tenant["id"], "donor_email": email},
            stripe_account=connect_account_id,
        )
    except stripe.error.StripeError as e:
        raise HTTPException(502, "Stripe error")

    return {
        "client_secret": si.client_secret,
        "setup_intent_id": si.id,
        "customer_id": customer_id,
        "connected_account_id": connect_account_id,
    }


class ConfirmRecurringRequest(BaseModel):
    church_slug: str
    setup_intent_id: str
    amount: float = Field(..., gt=0)
    fund: str = "Tithes"
    frequency: str = "monthly"   # "weekly" | "biweekly" | "monthly" | "annually"
    donor_email: str
    donor_first_name: Optional[str] = ""
    donor_last_name: Optional[str] = ""
    cover_fees: bool = False


@router.post("/stripe/recurring/confirm")
async def confirm_recurring_setup(payload: ConfirmRecurringRequest):
    """After the frontend confirms the SetupIntent client-side, we:

      1. Verify the SetupIntent succeeded server-side (never trust client).
      2. Read the saved payment_method_id off the SetupIntent.
      3. Charge the first installment immediately (off_session=True).
      4. Persist a recurring_giving row keyed for the scheduler to process
         every subsequent cycle.
    """
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured on server")
    if payload.frequency not in {"weekly", "biweekly", "monthly", "annually"}:
        raise HTTPException(400, f"Invalid frequency: {payload.frequency}")

    tenant = await _tenant_by_slug(payload.church_slug)
    from core.connect import (
        require_active_connect_account, calculate_application_fee,
        get_fee_schedule, PaymentConfigError, _run_stripe,
    )
    try:
        tenant = await require_active_connect_account(db, tenant["id"])
    except PaymentConfigError as e:
        raise HTTPException(400, detail=str(e))
    connect_account_id = tenant["stripe_connect_account_id"]
    fee_schedule = get_fee_schedule(tenant)

    try:
        si = await _run_stripe(
            stripe.SetupIntent.retrieve,
            payload.setup_intent_id,
            stripe_account=connect_account_id,
        )
    except stripe.error.StripeError as e:
        raise HTTPException(502, "Stripe error")

    if si.status != "succeeded":
        raise HTTPException(400, f"SetupIntent not succeeded (status={si.status})")
    payment_method_id = si.payment_method
    customer_id = si.customer
    if not payment_method_id or not customer_id:
        raise HTTPException(400, "SetupIntent missing payment_method or customer")

    # Charge first installment off_session
    base_amount = round(payload.amount, 2)
    fee = _compute_cover_fee(base_amount) if payload.cover_fees else 0.0
    total = round(base_amount + fee, 2)
    amount_cents = int(round(total * 100))
    application_fee = calculate_application_fee(amount_cents, fee_schedule)

    from services.processor_adapter import ACTIVE_ADAPTER, ChargeStatus
    schedule_id = str(uuid.uuid4())
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    first_charge = await ACTIVE_ADAPTER.charge_card(
        tenant_id=tenant["id"],
        donor_id=(payload.donor_email or "").lower(),
        amount_cents=amount_cents,
        payment_method_id=payment_method_id,
        stripe_customer_id=customer_id,
        connected_account_id=connect_account_id,
        application_fee_amount=application_fee,
        idempotency_key=f"recur_first_{schedule_id}",
        metadata={
            "tenant_id": tenant["id"],
            "schedule_id": schedule_id,
            "fund": payload.fund,
            "frequency": payload.frequency,
            "donor_email": (payload.donor_email or "").lower(),
            "source": "recurring_first_charge",
        },
        description=f"First recurring {payload.frequency} gift to {payload.fund}",
    )
    if first_charge.status != ChargeStatus.SUCCESS:
        raise HTTPException(402, f"First charge failed: {first_charge.message}")

    # Compute next charge date based on frequency
    from services.recurring_scheduler import _calculate_next_charge_date
    next_charge_date = _calculate_next_charge_date(payload.frequency, today_str)

    # Persist the recurring schedule
    await db.recurring_giving.insert_one({
        "id": schedule_id,
        "tenant_id": tenant["id"],
        "tenant_stripe_connect_account_id": connect_account_id,
        "person_id": "",
        "donor_email": (payload.donor_email or "").lower(),
        "donor_first_name": payload.donor_first_name or "",
        "donor_last_name": payload.donor_last_name or "",
        "amount": base_amount,
        "cover_fees": bool(payload.cover_fees),
        "fund_name": payload.fund,
        "frequency": payload.frequency,
        "payment_method_type": "card",
        "stripe_customer_id": customer_id,
        "stripe_payment_method_id": payment_method_id,
        "is_active": True,
        "next_charge_date": next_charge_date,
        "last_processed_date": today_str,
        "consecutive_failures": 0,
        "last_transaction_id": first_charge.processor_reference_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })

    # Bust dashboard caches so the gift shows up immediately
    from core.realtime import bust_donation_caches
    await bust_donation_caches(tenant["id"])

    return {
        "schedule_id": schedule_id,
        "first_charge_processor_reference_id": first_charge.processor_reference_id,
        "next_charge_date": next_charge_date,
        "frequency": payload.frequency,
    }


# ═══ Balance + payouts ═════════════════════════════════════════════════════

@router.get("/stripe/balance")
async def stripe_balance():
    """Return the connected Stripe account balance. In test mode this is the
    sandbox balance; any test charge with card 4242 4242 4242 4242 funds it."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured on server")
    try:
        bal = stripe.Balance.retrieve()
    except stripe.error.StripeError as e:
        raise HTTPException(502, "Stripe error")

    available_cents = sum(a.amount for a in bal.available)
    pending_cents = sum(a.amount for a in bal.pending)
    return {
        "available_cents": available_cents,
        "pending_cents": pending_cents,
        "available": round(available_cents / 100.0, 2),
        "pending": round(pending_cents / 100.0, 2),
        # Pending funds can be paid out in test mode via the /payouts endpoint
        # (we simulate the payout if Stripe rejects for insufficient available).
        # This field drives the "Request Payout" button state in the UI.
        "payable": round((available_cents + pending_cents if IS_TEST_MODE else available_cents) / 100.0, 2),
        "currency": (bal.available[0].currency if bal.available else "usd"),
        "test_mode": IS_TEST_MODE,
    }


class PayoutRequest(BaseModel):
    amount: Optional[float] = None   # dollars; None = full available balance
    tenant_id: Optional[str] = None  # for recording against a specific church


@router.post("/stripe/payouts")
async def create_stripe_payout(payload: PayoutRequest):
    """Create a Stripe Payout (test mode simulates it). Persists a record in
    the payouts collection so the dashboard can render payout history.

    Test-mode nuance: Stripe holds test charges in `pending` for a few minutes
    before releasing to `available`. If the demo runs before that window, the
    Stripe API rejects the payout with "insufficient funds". In test mode we
    therefore fall back to simulating a payout record against the pending
    balance — so the dashboard + "Request Payout" UX is always demo-able."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured on server")

    try:
        bal = stripe.Balance.retrieve()
        available_cents = sum(a.amount for a in bal.available)
        pending_cents = sum(p.amount for p in bal.pending)
    except stripe.error.StripeError as e:
        raise HTTPException(502, "Stripe balance error")

    # Amount to pay out — default is full available; in test mode fall back
    # to pending if available is zero so the demo-time click still produces
    # a visible payout record.
    effective_balance_cents = available_cents if available_cents > 0 else (pending_cents if IS_TEST_MODE else 0)
    amount_cents = (
        int(round(payload.amount * 100))
        if payload.amount is not None
        else effective_balance_cents
    )
    if amount_cents <= 0 or amount_cents > effective_balance_cents:
        raise HTTPException(
            400,
            f"Amount must be between $0.01 and balance ${effective_balance_cents / 100:.2f} "
            f"(available=${available_cents / 100:.2f} pending=${pending_cents / 100:.2f})",
        )

    simulated = False
    try:
        payout = stripe.Payout.create(amount=amount_cents, currency="usd")
        payout_id = payout.id
        payout_status = payout.status
        arrival = payout.arrival_date
        method = payout.method
    except stripe.error.StripeError as e:
        # In test mode, synthesize a payout record so the demo still shows a
        # row in the history table. Not allowed in live mode — would be a
        # silent failure for real money.
        if not IS_TEST_MODE:
            raise HTTPException(502, "Stripe payout error")
        logger.warning("stripe_test_payout_simulated", extra={"exc_type": type(e).__name__})
        payout_id = f"po_simulated_{int(datetime.now(timezone.utc).timestamp())}"
        payout_status = "pending"
        arrival = int(datetime.now(timezone.utc).timestamp()) + 2 * 24 * 3600
        method = "standard"
        simulated = True

    record = {
        "id": payout_id,
        "tenant_id": payload.tenant_id,
        "amount": round(amount_cents / 100.0, 2),
        "amount_cents": amount_cents,
        "currency": "usd",
        "status": payout_status,
        "arrival_date": arrival,
        "method": method,
        "source": "stripe",
        "test_mode": IS_TEST_MODE,
        "simulated": simulated,
        "note": (
            "Test-mode simulation against pending balance — Stripe "
            "test charges settle in a few minutes, real charges in 2 business days."
            if simulated else None
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.payouts.insert_one(record)
    record.pop("_id", None)
    return record



# ═══════════════════════════════════════════════════════════════════════════
#  God Mode — platform-level transaction feed
#  Jacob / Shannon / Vince's "CEO view": every Stripe donation across every
#  connected church, queried straight from Stripe's API (source of truth),
#  enriched with tenant metadata from MongoDB.
# ═══════════════════════════════════════════════════════════════════════════
from core import get_current_admin_user  # noqa: E402

# In-process cache for the platform list endpoint (60 s) to avoid hammering
# Stripe on every dashboard open. Keyed by a tuple of the filter args.
_PLATFORM_TXN_CACHE: dict[tuple, tuple[float, dict]] = {}
_PLATFORM_TXN_TTL_SECONDS = 60


def _platform_fees(amount_cents: int) -> tuple[int, int, int]:
    """Return (stripe_fee, solomon_fee, church_net) in cents."""
    stripe_fee = round(amount_cents * 0.029) + 30
    solomon_fee = round(amount_cents * 0.0035)
    church_net = amount_cents - stripe_fee - solomon_fee
    return stripe_fee, solomon_fee, church_net


async def _require_platform_admin(request: Request) -> dict:
    user = await get_current_admin_user(request)
    if user.get("role") != "platform_admin":
        raise HTTPException(403, "Platform admin required")
    return user


@router.get("/platform/stripe/transactions")
async def platform_transactions(
    request: Request,
    limit: int = 50,
    starting_after: Optional[str] = None,
    church_id: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,   # YYYY-MM-DD
    date_to: Optional[str] = None,
):
    """All Stripe PaymentIntents across the platform account. Supports Stripe
    cursor pagination via starting_after=pi_xxx."""
    await _require_platform_admin(request)
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured on server")

    cache_key = (limit, starting_after, church_id, status, date_from, date_to)
    now = datetime.now(timezone.utc).timestamp()
    cached = _PLATFORM_TXN_CACHE.get(cache_key)
    if cached and now - cached[0] < _PLATFORM_TXN_TTL_SECONDS:
        return cached[1]

    # Build Stripe query params
    params: dict = {"limit": max(1, min(limit, 100))}
    if starting_after:
        params["starting_after"] = starting_after

    # Stripe 'created' filter uses unix seconds
    created: dict = {}
    if date_from:
        try:
            created["gte"] = int(datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            pass
    if date_to:
        try:
            # inclusive end-of-day
            end = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
            created["lte"] = int(end.timestamp()) + 86399
        except ValueError:
            pass
    if created:
        params["created"] = created

    try:
        intents = stripe.PaymentIntent.list(**params)
    except stripe.error.StripeError as e:
        raise HTTPException(502, "Stripe error")

    # Tenant lookup — one-shot load so we can enrich rows without per-row DB hit
    tenants = await db.tenants.find({}, {"_id": 0, "id": 1, "name": 1, "slug": 1}).to_list(None)
    tenant_by_id = {t["id"]: t for t in tenants}

    data = []
    for intent in intents.data:
        md = intent.metadata or {}
        tid = md.get("tenant_id")
        if church_id and tid != church_id:
            continue
        if status and intent.status != status:
            continue

        amount_cents = intent.amount or 0
        stripe_fee, solomon_fee, church_net = _platform_fees(amount_cents)

        # Latest charge / card — best-effort, skip on error so list endpoint is robust
        pm_type, card_last4, card_brand = "card", None, None
        try:
            if intent.latest_charge:
                ch = stripe.Charge.retrieve(intent.latest_charge)
                pm_type = ch.payment_method_details.type if ch.payment_method_details else "card"
                if ch.payment_method_details and ch.payment_method_details.card:
                    card_last4 = ch.payment_method_details.card.last4
                    card_brand = ch.payment_method_details.card.brand
        except stripe.error.StripeError:
            pass

        t = tenant_by_id.get(tid, {})
        data.append({
            "id": intent.id,
            "church_id": tid,
            "church_name": t.get("name") or md.get("church_name", "—"),
            "church_slug": t.get("slug") or md.get("church_slug"),
            "donor_name": (f"{md.get('donor_first_name','')} {md.get('donor_last_name','')}").strip() or "Guest Donor",
            "donor_email": md.get("donor_email", ""),
            "amount": amount_cents,
            "currency": intent.currency,
            "fund": md.get("fund", "—"),
            "stripe_fee": stripe_fee,
            "solomon_fee": solomon_fee,
            "church_net": church_net,
            "status": intent.status,
            "created_at": datetime.fromtimestamp(intent.created, tz=timezone.utc).isoformat(),
            "payment_method_type": pm_type,
            "card_last4": card_last4,
            "card_brand": card_brand,
            "cover_fees": md.get("cover_fees") == "true",
            "test_mode": md.get("test_mode") == "true" or IS_TEST_MODE,
        })

    result = {
        "data": data,
        "has_more": intents.has_more,
        "next_cursor": data[-1]["id"] if data and intents.has_more else None,
        "count": len(data),
    }
    _PLATFORM_TXN_CACHE[cache_key] = (now, result)

    # Fire-and-forget: backfill any Stripe PaymentIntents that never made it
    # into the donations collection (frontend confirm-donation drops due to
    # closed tabs, network drops, etc.). Keeps Christopher's /solomonpay
    # view + stats cache in lock-step with live Stripe activity. Background
    # task so this endpoint stays sub-300ms.
    try:
        from core.stripe_sync import backfill_from_intents
        asyncio.ensure_future(backfill_from_intents(intents.data))
    except Exception as e:
        logger.warning("platform_transactions_backfill_failed", extra={"exc_type": type(e).__name__})

    return result


_STATS_CACHE: dict = {"ts": 0.0, "data": None}
_STATS_TTL_SECONDS = 30.0


@router.get("/platform/stripe/transactions/stats")
async def platform_transactions_stats(request: Request):
    """Aggregate TPV + Solomon revenue across all churches. Queries our
    MongoDB donations collection (fast) rather than Stripe's list API so the
    dashboard loads instantly. Only counts payment_source=stripe rows so the
    numbers reflect real payment volume, not demo data.

    The donations collection is ~2.8M docs, so we:
      1. Fan the 6 queries out in parallel via `asyncio.gather`
      2. Cache the response for 30s so tab-switching + parallel card loads
         (Executive + Transactions tabs + PaymentMetricsRow all hit it) don't
         re-run the scans for every single consumer.
    """
    await _require_platform_admin(request)

    # Serve cached if fresh (cuts p95 from ~11s to <50ms on warm hits).
    now_ts = _time.time()
    if _STATS_CACHE["data"] is not None and (now_ts - _STATS_CACHE["ts"]) < _STATS_TTL_SECONDS:
        return _STATS_CACHE["data"]

    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    month_start = now.replace(day=1).strftime("%Y-%m-%d")

    base_match = {"payment_source": "stripe"}

    async def _bucket(date_filter):
        pipe = [
            {"$match": {**base_match, **date_filter}},
            {"$group": {
                "_id": None,
                "count": {"$sum": 1},
                "total_amount": {"$sum": {"$multiply": ["$total_charged", 100]}},
            }},
        ]
        r = await db.donations.aggregate(pipe).to_list(1)
        if not r:
            return {"count": 0, "total_amount": 0, "solomon_revenue": 0}
        total = int(r[0]["total_amount"])
        return {"count": r[0]["count"], "total_amount": total, "solomon_revenue": round(total * 0.0035)}

    # Fan out — each scans the compound index (payment_source + donation_date).
    today, this_week, this_month, all_time, active_tids, donor_emails = await asyncio.gather(
        _bucket({"donation_date": today_str}),
        _bucket({"donation_date": {"$gte": week_ago}}),
        _bucket({"donation_date": {"$gte": month_start}}),
        _bucket({}),
        db.donations.distinct("tenant_id", base_match),
        db.donations.distinct("donor_email", base_match),
    )

    payload = {
        "today": today,
        "this_week": this_week,
        "this_month": this_month,
        "all_time": all_time,
        "active_churches": len(active_tids),
        "total_donors": len(donor_emails),
    }
    _STATS_CACHE["ts"] = now_ts
    _STATS_CACHE["data"] = payload
    return payload


@router.get("/platform/stripe/transactions/daily")
async def platform_transactions_daily(request: Request, days: int = 30):
    """Daily volume for the last N days — feeds the Dashboard trend chart.
    Returns 0 for days with no activity so the chart axis is continuous."""
    await _require_platform_admin(request)
    days = max(1, min(days, 180))
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days - 1)

    pipe = [
        {"$match": {
            "payment_source": "stripe",
            "donation_date": {"$gte": start.strftime("%Y-%m-%d")},
        }},
        {"$group": {
            "_id": "$donation_date",
            "count": {"$sum": 1},
            "total_amount": {"$sum": {"$multiply": ["$total_charged", 100]}},
        }},
    ]
    rows = await db.donations.aggregate(pipe).to_list(None)
    by_date = {r["_id"]: r for r in rows}

    out = []
    for i in range(days):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        r = by_date.get(d)
        out.append({
            "date": d,
            "count": r["count"] if r else 0,
            "total_amount": int(r["total_amount"]) if r else 0,
        })
    return {"days": out}


@router.get("/platform/stripe/transactions/recent")
async def platform_transactions_recent(request: Request, limit: int = 10):
    """Most recent Stripe donations across the platform. Cheap Mongo query
    (indexed on donation_date) so the Activity Feed loads instantly — no Stripe
    API round-trip on every dashboard load."""
    await _require_platform_admin(request)
    limit = max(1, min(limit, 50))
    rows = await db.donations.find(
        {"payment_source": "stripe"},
        {
            "_id": 0,
            "id": 1,
            "tenant_id": 1,
            "donation_date": 1,
            "donor_name": 1,
            "person_name": 1,
            "donor_email": 1,
            "person_email": 1,
            "total_charged": 1,
            "amount": 1,
            "fund_name": 1,
            "created_at": 1,
            "stripe_payment_intent_id": 1,
        },
    ).sort("created_at", -1).limit(limit).to_list(limit)

    tenant_ids = list({r.get("tenant_id") for r in rows if r.get("tenant_id")})
    tenants = await db.tenants.find(
        {"id": {"$in": tenant_ids}}, {"_id": 0, "id": 1, "name": 1, "slug": 1}
    ).to_list(None)
    t_by_id = {t["id"]: t for t in tenants}

    out = []
    for r in rows:
        amount = float(r.get("total_charged") or r.get("amount") or 0)
        t = t_by_id.get(r.get("tenant_id"), {})
        out.append({
            "id": r.get("id") or r.get("stripe_payment_intent_id", ""),
            "church_id": r.get("tenant_id"),
            "church_name": t.get("name", "—"),
            "church_slug": t.get("slug"),
            "donor_name": r.get("donor_name") or r.get("person_name") or "Guest Donor",
            "donor_email": r.get("donor_email") or r.get("person_email") or "",
            "amount_cents": int(round(amount * 100)),
            "fund": r.get("fund_name", "—"),
            "created_at": r.get("created_at"),
            "donation_date": r.get("donation_date"),
        })
    return {"data": out}
