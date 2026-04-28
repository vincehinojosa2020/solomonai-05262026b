"""Solomon AI — Solomon Pay Payment Processing Routes
No third-party payment processors. Solomon Pay IS the processor.
Uses PROCESSOR_ADAPTER for actual card/ACH charge calls.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import logging

from core import db, DEFAULT_TENANT_ID, get_session_token_from_request, get_current_portal_user, logger
from core.helpers import serialize_doc
from services.processor_adapter import ACTIVE_ADAPTER, ChargeStatus

router = APIRouter()

# ═══════ Fee Constants ═══════
CARD_FEE_RATE = 0.019       # 1.9%
CARD_FEE_FLAT = 0.30        # $0.30
ACH_FEE_RATE = 0.008        # 0.8%
ACH_FEE_FLAT = 0.30         # $0.30


def calculate_fee(amount: float, method: str = "card") -> float:
    """Calculate Solomon Pay processing fee."""
    if method == "ach":
        return round(amount * ACH_FEE_RATE + ACH_FEE_FLAT, 2)
    return round(amount * CARD_FEE_RATE + CARD_FEE_FLAT, 2)


def calculate_cover_fee_amount(intended_amount: float, method: str = "card") -> float:
    """Calculate total charge when donor covers the fee."""
    rate = CARD_FEE_RATE if method == "card" else ACH_FEE_RATE
    flat = CARD_FEE_FLAT if method == "card" else ACH_FEE_FLAT
    return round((intended_amount + flat) / (1 - rate), 2)


# ═══════ Config ═══════

@router.get("/payments/config")
async def get_payment_config():
    """Get Solomon Pay configuration for frontend."""
    return {
        "processor": "solomonpay",
        "currency": "usd",
        "payment_methods": ["card", "ach"],
        "card_fee": f"{CARD_FEE_RATE*100}% + ${CARD_FEE_FLAT}",
        "ach_fee": f"{ACH_FEE_RATE*100}% + ${ACH_FEE_FLAT}",
        "cover_fee_enabled": True,
    }


# ═══════ Solomon Pay — Process Payment ═══════

class SolomonPayChargeRequest(BaseModel):
    amount: float = Field(..., gt=0, le=100000)
    payment_method_type: str = "card"  # card | ach
    token: Optional[str] = None  # Tokenized payment method
    payment_method_id: Optional[str] = None  # Saved payment method
    fund_id: Optional[str] = None
    fund_name: Optional[str] = "General Fund"
    cover_fees: bool = False
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None  # weekly | biweekly | monthly | annually
    description: Optional[str] = None


@router.post("/solomonpay/process")
async def solomonpay_charge(request: Request, payload: SolomonPayChargeRequest):
    """Process a payment through Solomon Pay."""
    user = None
    user_id = "anonymous"
    tenant_id = DEFAULT_TENANT_ID
    person_id = None
    try:
        user = await get_current_portal_user(request)
        if user:
            user_id = user.get("user_id", "anonymous")
            tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
            person_id = user.get("person_id")
    except Exception:
        pass

    # Calculate fees
    intended_amount = payload.amount
    if payload.cover_fees:
        charge_amount = calculate_cover_fee_amount(intended_amount, payload.payment_method_type)
    else:
        charge_amount = intended_amount

    fee = calculate_fee(charge_amount, payload.payment_method_type)
    net_amount = round(charge_amount - fee, 2)

    # Resolve token
    token = payload.token
    if payload.payment_method_id:
        pm = await db.payment_methods.find_one(
            {"id": payload.payment_method_id, "user_id": user_id, "is_active": True}, {"_id": 0}
        )
        if not pm:
            raise HTTPException(status_code=400, detail="Payment method not found")
        token = pm.get("token", f"tok_{pm.get('card_brand','visa').lower()}_{pm['card_last_four']}")

    if not token:
        raise HTTPException(status_code=400, detail="Payment token or saved method required")

    # Process through adapter
    amount_cents = int(round(charge_amount * 100))
    if payload.payment_method_type == "ach":
        result = await ACTIVE_ADAPTER.charge_ach(
            token=token, amount_cents=amount_cents,
            description=payload.description or "Solomon Pay donation",
            metadata={"tenant_id": tenant_id, "fund": payload.fund_name},
        )
    else:
        result = await ACTIVE_ADAPTER.charge_card(
            token=token, amount_cents=amount_cents,
            description=payload.description or "Solomon Pay donation",
            metadata={"tenant_id": tenant_id, "fund": payload.fund_name},
        )

    # Determine status
    if result.status == ChargeStatus.SUCCESS:
        status = "completed"
    elif result.status == ChargeStatus.DECLINED:
        status = "declined"
    else:
        status = "failed"

    # Record in transaction ledger
    txn_id = f"sp_txn_{uuid.uuid4().hex[:12]}"
    txn_doc = {
        "id": txn_id,
        "tenant_id": tenant_id,
        "type": "charge",
        "amount": charge_amount,
        "fee_amount": fee if status == "completed" else 0,
        "net_amount": net_amount if status == "completed" else 0,
        "status": status,
        "payment_method_type": payload.payment_method_type,
        "payment_method_last_four": result.card_last_four or "",
        "card_brand": result.card_brand or "",
        "donor_person_id": person_id,
        "fund_id": payload.fund_id,
        "fund_name": payload.fund_name,
        "processor_reference_id": result.processor_reference_id,
        "cover_fees": payload.cover_fees,
        "intended_amount": intended_amount,
        "description": payload.description,
        "created_at": datetime.now(timezone.utc),
        "completed_at": datetime.now(timezone.utc) if status == "completed" else None,
    }
    await db.solomonpay_transactions.insert_one(txn_doc)

    # Create donation record on success
    donation_id = None
    if status == "completed":
        donation_id = str(uuid.uuid4())
        donation = {
            "id": donation_id,
            "tenant_id": tenant_id,
            "person_id": person_id or user_id,
            "fund_id": payload.fund_id,
            "fund_name": payload.fund_name or "General Fund",
            "amount": charge_amount,
            "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "payment_method": payload.payment_method_type,
            "is_recurring": payload.is_recurring,
            "status": "completed",
            "source": "solomonpay",
            "fee_amount": fee,
            "net_amount": net_amount,
            "cover_fees": payload.cover_fees,
            "transaction_id": txn_id,
            "created_at": datetime.now(timezone.utc),
        }
        await db.donations.insert_one(donation)

    if status == "declined":
        raise HTTPException(status_code=402, detail=result.message)
    if status == "failed":
        raise HTTPException(status_code=500, detail="Payment processing error")

    return {
        "success": True,
        "transaction_id": txn_id,
        "donation_id": donation_id,
        "status": status,
        "amount": charge_amount,
        "fee": fee,
        "net_amount": net_amount,
        "message": "Payment processed successfully via Solomon Pay",
    }


# ═══════ Tokenization ═══════
# REMOVED 2026-04-28 — BLOCKER #4 from production audit.
#
# Previous endpoints `/solomonpay/tokenize` and `/solomonpay/tokenize-bank`
# accepted raw PAN + CVC + routing/account numbers in the HTTP request body,
# putting Solomon AI in PCI-DSS Level 1 scope (CDE) and creating MSB exposure
# on ACH. There is NO replacement — all card capture must go through
# Stripe.js Elements (already used at PublicGivingPage.jsx and PortalGive.jsx
# via /api/stripe/create-payment-intent + stripe.confirmCardPayment), and
# bank capture must go through Stripe Financial Connections / Plaid Link.
#
# The frontend never called these endpoints (verified: grep "/solomonpay/tokenize"
# /app/frontend/src/ returns 0 hits). They are deleted to remove attack
# surface. Do NOT reintroduce raw-card endpoints under any flag.


# ═══════ Refunds ═══════

class RefundRequest(BaseModel):
    amount: Optional[float] = None  # None = full refund


@router.post("/solomonpay/refund/{donation_id}")
async def process_refund(request: Request, donation_id: str, payload: RefundRequest):
    """Process a full or partial refund."""
    user = await get_current_portal_user(request)
    if not user or user.get("role") not in ["church_admin", "admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    donation = await db.donations.find_one({"id": donation_id}, {"_id": 0})
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    if donation.get("status") == "refunded":
        raise HTTPException(status_code=400, detail="Already refunded")

    refund_amount = payload.amount or donation["amount"]
    if refund_amount > donation["amount"]:
        raise HTTPException(status_code=400, detail="Refund exceeds original amount")

    # Find original transaction
    orig_txn = await db.solomonpay_transactions.find_one(
        {"id": donation.get("transaction_id")}, {"_id": 0}
    )
    processor_ref = orig_txn.get("processor_reference_id", "") if orig_txn else ""

    # Process refund through adapter
    amount_cents = int(round(refund_amount * 100))
    result = await ACTIVE_ADAPTER.refund(
        processor_reference_id=processor_ref,
        amount_cents=amount_cents,
    )

    if result.status != ChargeStatus.SUCCESS:
        raise HTTPException(status_code=500, detail=f"Refund failed: {result.message}")

    # Record refund in ledger
    refund_txn_id = f"sp_rf_{uuid.uuid4().hex[:12]}"
    await db.solomonpay_transactions.insert_one({
        "id": refund_txn_id,
        "tenant_id": donation["tenant_id"],
        "type": "refund",
        "amount": -refund_amount,
        "fee_amount": 0,  # Solomon Pay retains original fee
        "net_amount": -refund_amount,
        "status": "completed",
        "related_donation_id": donation_id,
        "related_transaction_id": donation.get("transaction_id"),
        "processor_reference_id": result.processor_reference_id,
        "created_at": datetime.now(timezone.utc),
        "completed_at": datetime.now(timezone.utc),
    })

    # Update donation status
    new_status = "refunded" if refund_amount >= donation["amount"] else "partially_refunded"
    await db.donations.update_one(
        {"id": donation_id},
        {"$set": {
            "status": new_status,
            "refund_amount": refund_amount,
            "refunded_at": datetime.now(timezone.utc).isoformat(),
        }}
    )

    return {
        "success": True,
        "refund_transaction_id": refund_txn_id,
        "refund_amount": refund_amount,
        "donation_status": new_status,
    }


# ═══════ Saved Payment Methods ═══════

@router.get("/payments/methods")
async def get_saved_payment_methods(request: Request):
    """Get saved payment methods for current user."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    methods = await db.payment_methods.find(
        {"user_id": session["user_id"], "is_active": True}, {"_id": 0}
    ).to_list(10)
    return {"payment_methods": methods}


class SavePaymentMethodBody(BaseModel):
    token: str
    card_last_four: str
    card_brand: str
    exp_month: int
    exp_year: int
    is_default: bool = False
    method_type: str = "card"  # card | ach


@router.post("/payments/methods")
async def save_payment_method(request: Request, body: SavePaymentMethodBody):
    """Save a tokenized payment method."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if body.is_default:
        await db.payment_methods.update_many(
            {"user_id": user["user_id"]}, {"$set": {"is_default": False}}
        )

    pm = {
        "id": str(uuid.uuid4()),
        "user_id": user["user_id"],
        "tenant_id": user.get("tenant_id"),
        "token": body.token,
        "card_last_four": body.card_last_four,
        "card_brand": body.card_brand,
        "exp_month": body.exp_month,
        "exp_year": body.exp_year,
        "method_type": body.method_type,
        "is_default": body.is_default,
        "is_active": True,
        "provider": "solomonpay",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.payment_methods.insert_one(pm)

    return {"message": "Payment method saved", "payment_method": {k: v for k, v in pm.items() if k != "_id"}}


@router.delete("/payments/methods/{method_id}")
async def delete_payment_method(request: Request, method_id: str):
    """Remove a saved payment method."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    result = await db.payment_methods.update_one(
        {"id": method_id, "user_id": session["user_id"]},
        {"$set": {"is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return {"message": "Payment method removed"}


@router.put("/payments/methods/{method_id}/default")
async def set_default_payment_method(request: Request, method_id: str):
    """Set a payment method as default."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    await db.payment_methods.update_many(
        {"user_id": session["user_id"]}, {"$set": {"is_default": False}}
    )
    result = await db.payment_methods.update_one(
        {"id": method_id, "user_id": session["user_id"], "is_active": True},
        {"$set": {"is_default": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return {"message": "Default payment method updated"}


# ═══════ Transaction List (Admin) ═══════

@router.get("/solomonpay/transactions")
async def get_solomonpay_transactions(request: Request, limit: int = 50):
    """Get Solomon Pay transaction ledger for admin."""
    user = await get_current_portal_user(request)
    if not user or user.get("role") not in ["church_admin", "admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    txns = await db.solomonpay_transactions.find(
        {"tenant_id": tenant_id}, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return {"transactions": txns}
