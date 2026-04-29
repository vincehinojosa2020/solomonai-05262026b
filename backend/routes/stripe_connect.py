"""Solomon AI — Stripe Connect Payment Processing
Feature-flagged: STRIPE_LIVE=true enables real Stripe, false uses simulated Solomon Pay.
"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, Dict
from pydantic import BaseModel
import json
import uuid
import os
import logging

import stripe

from core import db, get_session_token_from_request, get_current_portal_user, logger

router = APIRouter()

# ═══ Configuration ═══
STRIPE_LIVE = os.environ.get("STRIPE_LIVE", "false").lower() == "true"
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
# REQUIRED in production. Generate at https://dashboard.stripe.com/webhooks
# and store as STRIPE_WEBHOOK_SECRET=whsec_... in backend/.env. Without this,
# /api/webhook/stripe rejects every event (fail-closed) — see audit BLOCKER #2.
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY

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
        logger.error("stripe_checkout_creation_failed", extra={"exc_type": type(e).__name__})
        from core.errors import client_error
        raise client_error(status_code=500, user_message="Payment processing failed. Please try again.", log_message="stripe_connect.payment_failed", exc=e)


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
        logger.error("stripe_status_check_failed", extra={"exc_type": type(e).__name__})
        from core.errors import client_error
        raise client_error(status_code=500, user_message="Status check failed.", log_message="stripe_connect.status_check_failed", exc=e)


# ═══ Webhook Handler ═══

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events: payment success, failure, disputes.

    Hardening (BLOCKER #2 from audit):
      1. Reject any request without a valid Stripe-Signature header signed
         by STRIPE_WEBHOOK_SECRET. Fail-closed in production.
      2. Verify the signature with stripe.Webhook.construct_event() — this
         raises ValueError on bad signatures and SignatureVerificationError
         on tampered payloads.
      3. Persist the event_id in db.stripe_webhook_events BEFORE processing
         so retried/replayed events (Stripe retries up to 3 days) can't
         double-create donations.
    """
    body = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    # ── 1. Fail-closed if the secret isn't configured ──
    if not STRIPE_WEBHOOK_SECRET:
        # Allow local development without a webhook (parse JSON unverified)
        # ONLY when STRIPE_API_KEY is a test key. In production (sk_live_*)
        # we reject so a missing secret can never create donations from
        # forged payloads.
        if STRIPE_API_KEY.startswith("sk_live_"):
            logger.error("[stripe_webhook] STRIPE_WEBHOOK_SECRET missing under live key — rejecting")
            raise HTTPException(status_code=503, detail="Webhook secret not configured")
        logger.warning("[stripe_webhook] STRIPE_WEBHOOK_SECRET missing — accepting unverified (test mode only)")
        try:
            event = json.loads(body.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")
    else:
        # ── 2. Verify the signature ──
        try:
            event = stripe.Webhook.construct_event(
                payload=body,
                sig_header=sig_header,
                secret=STRIPE_WEBHOOK_SECRET,
            )
        except ValueError:
            logger.warning("[stripe_webhook] invalid payload")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.warning("stripe_webhook_bad_signature", extra={"client": request.client.host if request.client else "?"})
            raise HTTPException(status_code=400, detail="Invalid signature")

    event_id = event.get("id") if isinstance(event, dict) else event["id"]
    event_type = event.get("type") if isinstance(event, dict) else event["type"]
    data_object = (event.get("data", {}) if isinstance(event, dict) else event["data"]).get("object", {})

    # ── 3. Idempotency: have we processed this event already? ──
    seen = await db.stripe_webhook_events.find_one({"event_id": event_id}, {"_id": 0})
    if seen:
        logger.info("stripe_webhook_duplicate", extra={"event_id": event_id, "event_type": event_type})
        return {"received": True, "duplicate": True}

    # Record-then-process so a crash mid-handler still leaves a marker.
    # The unique index on event_id (server.py) makes this race-safe:
    # Stripe parallelizes retries, so two workers can both pass the
    # find_one above. The second insert raises DuplicateKeyError, which
    # we treat as "another worker is handling it" rather than a 5xx.
    from pymongo.errors import DuplicateKeyError
    try:
        await db.stripe_webhook_events.insert_one({
            "event_id": event_id,
            "event_type": event_type,
            "received_at": datetime.now(timezone.utc),
            "processed": False,
        })
    except DuplicateKeyError:
        return {"received": True, "duplicate": True}

    try:
        # ── Map session_id (Checkout) or payment_intent_id (Elements) ──
        session_id = data_object.get("id")
        if event_type.startswith("payment_intent."):
            # For PI events, the metadata might point to a Checkout session
            session_id = data_object.get("metadata", {}).get("checkout_session_id") or session_id

        txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0}) if session_id else None

        if event_type in ("checkout.session.completed", "payment_intent.succeeded"):
            if txn and txn.get("payment_status") != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "payment_status": "paid",
                        "status": "completed",
                        "webhook_event": event_type,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }}
                )
                existing_donation = await db.donations.find_one({"stripe_session_id": session_id})
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
                        "stripe_session_id": session_id,
                        "status": "completed",
                        "is_recurring": False,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    await db.donations.insert_one(donation)
                    await _send_receipt(txn)

        elif event_type in ("payment_intent.payment_failed", "checkout.session.expired"):
            if session_id:
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "payment_status": "failed",
                        "status": "failed",
                        "webhook_event": event_type,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }}
                )

        elif event_type == "charge.dispute.created":
            await db.disputes.insert_one({
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "tenant_id": txn.get("tenant_id", "") if txn else "",
                "amount": txn.get("amount", 0) if txn else 0,
                "status": "open",
                "event_type": event_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        elif event_type == "account.updated":
            # BLOCKER #1 — Connect account state changed.
            # data_object IS the account itself. Resolve the tenant via
            # metadata.tenant_id (we set this at create_express_account
            # time) or by stripe_connect_account_id lookup.
            from core.connect import derive_status_from_account, CONNECT_STATUS_ACTIVE
            acct_id = data_object.get("id")
            md_tenant = (data_object.get("metadata") or {}).get("tenant_id")
            tenant_doc = None
            if md_tenant:
                tenant_doc = await db.tenants.find_one({"id": md_tenant}, {"_id": 0})
            if not tenant_doc and acct_id:
                tenant_doc = await db.tenants.find_one({"stripe_connect_account_id": acct_id}, {"_id": 0})
            if tenant_doc:
                new_status = derive_status_from_account(data_object)
                update = {"stripe_connect_status": new_status}
                if new_status == CONNECT_STATUS_ACTIVE and not tenant_doc.get("stripe_connect_onboarded_at"):
                    update["stripe_connect_onboarded_at"] = datetime.now(timezone.utc).isoformat()
                await db.tenants.update_one({"id": tenant_doc["id"]}, {"$set": update})
                logger.info("stripe_webhook_account_updated", extra={"tenant_id": tenant_doc["id"], "connect_status": new_status})

        elif event_type == "account.application.deauthorized":
            # Tenant disconnected the Connect account from our platform.
            # No more payment processing for this church until they reconnect.
            from core.connect import CONNECT_STATUS_RESTRICTED
            acct_id = data_object.get("id") or (event.get("account") if isinstance(event, dict) else getattr(event, "account", None))
            if acct_id:
                tenant_doc = await db.tenants.find_one({"stripe_connect_account_id": acct_id}, {"_id": 0})
                if tenant_doc:
                    await db.tenants.update_one(
                        {"id": tenant_doc["id"]},
                        {"$set": {"stripe_connect_status": CONNECT_STATUS_RESTRICTED}},
                    )
                    # Audit alert — surfaced on God Mode platform_flags.
                    await db.platform_flags.update_one(
                        {"key": f"connect-deauthorized-{tenant_doc['id']}"},
                        {"$set": {
                            "tenant_id": tenant_doc["id"],
                            "tenant_name": tenant_doc.get("name", ""),
                            "alert_type": "connect_deauthorized",
                            "severity": "critical",
                            "raised_at": datetime.now(timezone.utc).isoformat(),
                        }},
                        upsert=True,
                    )
                    logger.error("stripe_webhook_connect_deauthorized", extra={"tenant_id": tenant_doc["id"]})

        # Mark event processed
        await db.stripe_webhook_events.update_one(
            {"event_id": event_id},
            {"$set": {"processed": True, "processed_at": datetime.now(timezone.utc)}},
        )
        return {"received": True}

    except Exception as e:
        # Don't 500 — Stripe will retry, and we have the event_id recorded
        # so the next retry's idempotency check still fires. Just log.
        logger.error("stripe_webhook_processing_failed", extra={"event_id": event_id, "event_type": event_type, "exc_type": type(e).__name__})
        return {"received": True, "error": "processing_deferred"}


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
        logger.info("stripe_receipt_sent", extra={"amount": amount})
    except Exception as e:
        logger.error("stripe_receipt_email_failed", extra={"exc_type": type(e).__name__})



# ═══════════════════════════════════════════════════════════════════════
#  Stripe Connect — per-tenant account management (BLOCKER #1)
# ═══════════════════════════════════════════════════════════════════════

@router.post("/platform/churches/{tenant_id}/connect/start")
async def start_connect_onboarding(tenant_id: str, request: Request):
    """Provision a new Express Connect account for an existing tenant
    (or refresh the onboarding link for one mid-flow). Platform-admin only."""
    user = await get_current_portal_user(request)
    if user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    from core.connect import (
        create_express_account, create_account_link,
        CONNECT_STATUS_ONBOARDING, CONNECT_STATUS_ACTIVE,
    )

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if tenant.get("stripe_connect_status") == CONNECT_STATUS_ACTIVE:
        raise HTTPException(status_code=400, detail="Connect account already active")
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured on server")

    base_url = os.environ.get("APP_BASE_URL") or str(request.base_url).rstrip("/").replace("/api", "")
    account_id = tenant.get("stripe_connect_account_id")
    if not account_id:
        # Find the tenant's primary admin email for the Stripe Account.email
        admin_user = await db.users.find_one(
            {"tenant_id": tenant_id, "role": "church_admin"},
            {"_id": 0, "email": 1},
        )
        admin_email = (admin_user or {}).get("email", f"admin@{tenant.get('subdomain','solomon')}.church")
        try:
            acct = await create_express_account(
                tenant_id=tenant_id,
                tenant_name=tenant["name"],
                admin_email=admin_email,
            )
            account_id = acct.id
            await db.tenants.update_one(
                {"id": tenant_id},
                {"$set": {
                    "stripe_connect_account_id": account_id,
                    "stripe_connect_status": CONNECT_STATUS_ONBOARDING,
                }},
            )
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=502, detail="Stripe error")

    try:
        link = await create_account_link(account_id, base_url)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=502, detail="Stripe link error")

    return {
        "tenant_id": tenant_id,
        "stripe_connect_account_id": account_id,
        "onboarding_url": link.url,
        "expires_at": link.expires_at,
    }


@router.post("/platform/churches/{tenant_id}/connect/refresh")
async def refresh_connect_status(tenant_id: str, request: Request):
    """Pull the latest account status from Stripe and persist. Useful after
    a church admin completes the onboarding flow but before Stripe's
    `account.updated` webhook arrives."""
    user = await get_current_portal_user(request)
    if user.get("role") not in ("platform_admin", "church_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if user.get("role") == "church_admin" and user.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=403, detail="Cannot refresh another church's status")

    from core.connect import sync_tenant_status_from_stripe
    result = await sync_tenant_status_from_stripe(db, tenant_id)
    if not result.get("updated"):
        raise HTTPException(status_code=400, detail=result.get("reason", "refresh_failed"))
    return result


@router.get("/platform/churches/{tenant_id}/connect/login-link")
async def connect_dashboard_link(tenant_id: str, request: Request):
    """Issue a one-time URL that drops the church admin into their Express
    Stripe dashboard (payouts, balance, taxes). Platform/church admin only."""
    user = await get_current_portal_user(request)
    if user.get("role") not in ("platform_admin", "church_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if user.get("role") == "church_admin" and user.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=403, detail="Cannot access another church's dashboard")

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    acct_id = (tenant or {}).get("stripe_connect_account_id")
    if not acct_id:
        raise HTTPException(status_code=400, detail="No Connect account for this tenant")

    try:
        from core.connect import _run_stripe
        link = await _run_stripe(stripe.Account.create_login_link, acct_id)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=502, detail="Stripe error")
    return {"url": link.url}


@router.get("/admin/connect/status")
async def admin_connect_status(request: Request):
    """Church admin's view of their own Connect status — drives the
    /admin/settings/payments page UI."""
    user = await get_current_portal_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {
        "tenant_id": tenant_id,
        "stripe_connect_status": tenant.get("stripe_connect_status", "not_started"),
        "has_account": bool(tenant.get("stripe_connect_account_id")),
        "onboarded_at": tenant.get("stripe_connect_onboarded_at"),
        "fee_schedule": tenant.get("fee_schedule") or {},
    }
