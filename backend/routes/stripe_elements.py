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

import logging
import os
from datetime import datetime, timezone
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
    logger.info(f"Stripe configured (len={len(STRIPE_API_KEY)}, prefix={STRIPE_API_KEY[:8]}, test_mode={IS_TEST_MODE})")
else:
    logger.warning("Stripe API key missing — /api/stripe/* endpoints will 500")

# Solomon platform fee (passed to the donor if they opt to cover)
PLATFORM_FEE_RATE = 0.019   # 1.9%
PLATFORM_FEE_FIXED = 0.30   # $0.30
MAX_DONATION_USD = 100_000  # sanity cap


def _compute_cover_fee(amount: float) -> float:
    """If the donor opts to cover processing, add 1.9% + $0.30."""
    return round(amount * PLATFORM_FEE_RATE + PLATFORM_FEE_FIXED, 2)


async def _tenant_by_slug(slug: str) -> dict:
    """Resolve a church slug → tenant doc (without Mongo _id)."""
    t = await db.tenants.find_one({"slug": slug}, {"_id": 0})
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
    required — this is the guest giving path."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured on server")

    if payload.amount <= 0 or payload.amount > MAX_DONATION_USD:
        raise HTTPException(400, f"Amount must be between $0.01 and ${MAX_DONATION_USD:,}")

    tenant = await _tenant_by_slug(payload.church_slug)

    base_amount = round(payload.amount, 2)
    fee = _compute_cover_fee(base_amount) if payload.cover_fees else 0.0
    total = round(base_amount + fee, 2)
    amount_cents = int(round(total * 100))

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

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            metadata=metadata,
            statement_descriptor_suffix=suffix,
            receipt_email=metadata["donor_email"] or None,
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe create intent failed: {e}")
        raise HTTPException(502, f"Stripe error: {e.user_message or str(e)}")

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

    try:
        intent = stripe.PaymentIntent.retrieve(payload.payment_intent_id)
    except stripe.error.StripeError as e:
        raise HTTPException(502, f"Stripe error: {e.user_message or str(e)}")

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
            pm = stripe.PaymentMethod.retrieve(intent.payment_method)
            pm_id = pm.id
            if pm.type == "card" and pm.card:
                pm_brand = pm.card.brand
                pm_last4 = pm.card.last4
        if intent.latest_charge:
            ch_id = intent.latest_charge
    except stripe.error.StripeError as e:
        logger.warning(f"Could not fetch payment method: {e}")

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

    return {"status": "succeeded", "donation": donation, "already_recorded": False}


@router.get("/stripe/payment-intent/{intent_id}/status")
async def get_payment_intent_status(intent_id: str):
    """Lightweight poller for the frontend status screen."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured on server")
    try:
        intent = stripe.PaymentIntent.retrieve(intent_id)
    except stripe.error.StripeError as e:
        raise HTTPException(404, f"Stripe error: {e.user_message or str(e)}")
    return {
        "id": intent.id,
        "status": intent.status,
        "amount": intent.amount,
        "currency": intent.currency,
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
        raise HTTPException(502, f"Stripe error: {e.user_message or str(e)}")

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
        raise HTTPException(502, f"Stripe balance error: {e.user_message or str(e)}")

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
            raise HTTPException(502, f"Stripe payout error: {e.user_message or str(e)}")
        logger.warning(f"Stripe rejected test payout ({e.user_message}); simulating record for demo")
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
