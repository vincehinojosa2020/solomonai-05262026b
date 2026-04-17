"""Solomon AI — Stripe Connect Payment Processing
Feature-flagged: STRIPE_LIVE=true enables real Stripe, false uses simulated Solomon Pay.
"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, Dict
from pydantic import BaseModel
import uuid
import os
import logging

from core import db, get_session_token_from_request, get_current_portal_user, logger

router = APIRouter()

# ═══ Configuration ═══
STRIPE_LIVE = os.environ.get("STRIPE_LIVE", "false").lower() == "true"
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")

# Solomon platform fee: 1.9% + $0.30
PLATFORM_FEE_RATE = 0.019
PLATFORM_FEE_FIXED = 0.30

# Predefined giving amounts (backend-defined, not frontend-manipulable)
GIVING_PACKAGES = {
    "25": 25.00, "50": 50.00, "100": 100.00, "150": 150.00,
    "200": 200.00, "250": 250.00, "500": 500.00, "1000": 1000.00,
    "2500": 2500.00, "5000": 5000.00,
}


def _calculate_platform_fee(amount: float) -> float:
    """Calculate Solomon's platform fee: 1.9% + $0.30"""
    return round(amount * PLATFORM_FEE_RATE + PLATFORM_FEE_FIXED, 2)


# ═══ Checkout Session Creation ═══

class GivingCheckoutRequest(BaseModel):
    amount: Optional[float] = None
    package_id: Optional[str] = None
    fund_name: str = "General Fund"
    cover_fees: bool = False
    origin_url: str


@router.post("/stripe/checkout/giving")
async def create_giving_checkout(request: Request, payload: GivingCheckoutRequest):
    """Create a Stripe Checkout Session for church giving."""
    if not STRIPE_LIVE:
        return {
            "mode": "simulated",
            "message": "Stripe is in simulated mode (STRIPE_LIVE=false). Use Solomon Pay flow for demo giving.",
            "stripe_live": False,
        }

    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")

    # Resolve user and tenant
    user = await get_current_portal_user(request)
    tenant_id = user.get("tenant_id") or user.get("church_id", "")

    # Determine amount — from predefined packages or custom
    if payload.package_id and payload.package_id in GIVING_PACKAGES:
        amount = GIVING_PACKAGES[payload.package_id]
    elif payload.amount and payload.amount >= 1.00:
        amount = round(float(payload.amount), 2)
    else:
        raise HTTPException(status_code=400, detail="Invalid amount. Minimum donation is $1.00")

    if amount > 100000.00:
        raise HTTPException(status_code=400, detail="Maximum single donation is $100,000")

    # Cover fees: add platform fee to the amount if donor opts in
    platform_fee = _calculate_platform_fee(amount)
    total_amount = round(amount + platform_fee, 2) if payload.cover_fees else amount

    # Build success/cancel URLs from the frontend origin
    origin = payload.origin_url.rstrip("/")
    success_url = f"{origin}/portal/give?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/portal/give"

    # Metadata for tracking
    metadata = {
        "platform": "solomon_ai",
        "tenant_id": tenant_id,
        "user_id": user.get("user_id", ""),
        "fund_name": payload.fund_name,
        "base_amount": str(amount),
        "cover_fees": str(payload.cover_fees),
        "platform_fee": str(platform_fee),
    }

    try:
        from emergentintegrations.payments.stripe.checkout import (
            StripeCheckout, CheckoutSessionRequest
        )

        host_url = str(request.base_url).rstrip("/")
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

        checkout_req = CheckoutSessionRequest(
            amount=total_amount,
            currency="usd",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
        )
        session = await stripe_checkout.create_checkout_session(checkout_req)

        # Create payment_transactions record BEFORE redirect
        txn_record = {
            "id": str(uuid.uuid4()),
            "session_id": session.session_id,
            "tenant_id": tenant_id,
            "user_id": user.get("user_id", ""),
            "email": user.get("email", ""),
            "amount": amount,
            "total_charged": total_amount,
            "platform_fee": platform_fee,
            "cover_fees": payload.cover_fees,
            "fund_name": payload.fund_name,
            "currency": "usd",
            "payment_status": "initiated",
            "status": "pending",
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.payment_transactions.insert_one(txn_record)

        return {
            "url": session.url,
            "session_id": session.session_id,
            "amount": amount,
            "total_charged": total_amount,
            "platform_fee": platform_fee,
            "stripe_live": True,
        }

    except Exception as e:
        logger.error(f"Stripe checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Payment processing error: {str(e)}")


# ═══ Checkout Status Polling ═══

@router.get("/stripe/checkout/status/{session_id}")
async def get_checkout_status(request: Request, session_id: str):
    """Poll the status of a Stripe Checkout Session."""
    if not STRIPE_LIVE:
        return {"status": "simulated", "payment_status": "simulated", "stripe_live": False}

    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout

        host_url = str(request.base_url).rstrip("/")
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

        status = await stripe_checkout.get_checkout_status(session_id)

        # Update our payment_transactions record
        txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        if txn and txn.get("payment_status") != "paid":
            update_data = {
                "payment_status": status.payment_status,
                "status": "completed" if status.payment_status == "paid" else status.status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )

            # On successful payment, create donation record
            if status.payment_status == "paid" and txn.get("payment_status") != "paid":
                donation = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": txn.get("tenant_id", ""),
                    "person_id": txn.get("user_id", ""),
                    "amount": txn.get("amount", 0),
                    "fee_amount": txn.get("platform_fee", 0),
                    "net_amount": round(txn.get("amount", 0) - txn.get("platform_fee", 0), 2),
                    "fund_name": txn.get("fund_name", "General Fund"),
                    "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "payment_method": "card",
                    "processor": "stripe",
                    "stripe_session_id": session_id,
                    "status": "completed",
                    "is_recurring": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                await db.donations.insert_one(donation)

                # Send receipt email
                await _send_receipt(txn)

        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency,
            "stripe_live": True,
        }

    except Exception as e:
        logger.error(f"Stripe status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check error: {str(e)}")


# ═══ Webhook Handler ═══

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events: payment success, failure, disputes."""
    body = await request.body()
    sig = request.headers.get("Stripe-Signature", "")

    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout

        host_url = str(request.base_url).rstrip("/")
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

        event = await stripe_checkout.handle_webhook(body, sig)

        logger.info(f"Stripe webhook: {event.event_type} for session {event.session_id}")

        # Update payment_transactions
        if event.session_id:
            txn = await db.payment_transactions.find_one({"session_id": event.session_id}, {"_id": 0})

            if event.event_type in ("checkout.session.completed", "payment_intent.succeeded"):
                if txn and txn.get("payment_status") != "paid":
                    await db.payment_transactions.update_one(
                        {"session_id": event.session_id},
                        {"$set": {
                            "payment_status": "paid",
                            "status": "completed",
                            "webhook_event": event.event_type,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }}
                    )

                    # Create donation if not already created
                    existing_donation = await db.donations.find_one({"stripe_session_id": event.session_id})
                    if not existing_donation and txn:
                        donation = {
                            "id": str(uuid.uuid4()),
                            "tenant_id": txn.get("tenant_id", ""),
                            "person_id": txn.get("user_id", ""),
                            "amount": txn.get("amount", 0),
                            "fee_amount": txn.get("platform_fee", 0),
                            "net_amount": round(txn.get("amount", 0) - txn.get("platform_fee", 0), 2),
                            "fund_name": txn.get("fund_name", "General Fund"),
                            "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                            "payment_method": "card",
                            "processor": "stripe",
                            "stripe_session_id": event.session_id,
                            "status": "completed",
                            "is_recurring": False,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                        await db.donations.insert_one(donation)
                        await _send_receipt(txn)

            elif event.event_type in ("payment_intent.payment_failed", "checkout.session.expired"):
                await db.payment_transactions.update_one(
                    {"session_id": event.session_id},
                    {"$set": {
                        "payment_status": "failed",
                        "status": "failed",
                        "webhook_event": event.event_type,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }}
                )

            elif event.event_type == "charge.dispute.created":
                # Record dispute
                await db.disputes.insert_one({
                    "id": str(uuid.uuid4()),
                    "session_id": event.session_id,
                    "tenant_id": txn.get("tenant_id", "") if txn else "",
                    "amount": txn.get("amount", 0) if txn else 0,
                    "status": "open",
                    "event_type": event.event_type,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

        return {"received": True}

    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return {"received": True, "error": str(e)}


# ═══ Payment Configuration Status ═══

@router.get("/stripe/config")
async def get_stripe_config():
    """Return current Stripe configuration status (no secrets exposed)."""
    return {
        "stripe_live": STRIPE_LIVE,
        "stripe_configured": bool(STRIPE_API_KEY),
        "platform_fee_rate": f"{PLATFORM_FEE_RATE * 100}% + ${PLATFORM_FEE_FIXED:.2f}",
        "mode": "production" if STRIPE_LIVE else "simulated",
        "message": "Real Stripe payment processing is active." if STRIPE_LIVE else "Solomon Pay simulation mode. Set STRIPE_LIVE=true in .env to enable real payments.",
    }


# ═══ Receipt Email ═══

async def _send_receipt(txn: dict):
    """Send a giving receipt email via Resend."""
    resend_key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
    email = txn.get("email")
    if not resend_key or not email:
        return

    try:
        import httpx
        amount = txn.get("amount", 0)
        fund = txn.get("fund_name", "General Fund")
        now = datetime.now(timezone.utc)

        html = f"""<div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:480px;margin:0 auto;padding:32px">
            <div style="text-align:center;margin-bottom:24px">
                <span style="font-size:16px;font-weight:200;letter-spacing:6px;color:#0f172a">SOLOMON</span>
                <span style="font-size:16px;font-weight:700;color:#3b82f6"> AI</span>
            </div>
            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:24px;text-align:center;margin-bottom:24px">
                <p style="font-size:14px;color:#15803d;margin:0 0 4px">Donation Received</p>
                <p style="font-size:36px;font-weight:800;color:#0f172a;margin:0">${amount:,.2f}</p>
                <p style="font-size:13px;color:#64748b;margin:8px 0 0">{fund} &middot; {now.strftime('%B %d, %Y')}</p>
            </div>
            <div style="font-size:13px;color:#475569;line-height:1.8">
                <p>Thank you for your generous gift. This receipt confirms your donation has been processed through Solomon Pay.</p>
                <p><strong>Amount:</strong> ${amount:,.2f}<br>
                <strong>Fund:</strong> {fund}<br>
                <strong>Date:</strong> {now.strftime('%B %d, %Y')}<br>
                <strong>Method:</strong> Card</p>
                <p style="color:#94a3b8;font-size:11px;margin-top:24px">This receipt is provided for your records. Please consult your tax advisor regarding the deductibility of charitable contributions.</p>
            </div>
            <p style="color:#94a3b8;font-size:11px;text-align:center;margin-top:24px">&copy; {now.year} Solomon AI</p>
        </div>"""

        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
                json={
                    "from": f"Solomon AI <{sender}>",
                    "to": [email],
                    "subject": f"Giving Receipt — ${amount:,.2f} to {fund}",
                    "html": html,
                },
                timeout=10
            )
        logger.info(f"Receipt sent to {email} for ${amount}")
    except Exception as e:
        logger.error(f"Receipt email failed: {e}")
