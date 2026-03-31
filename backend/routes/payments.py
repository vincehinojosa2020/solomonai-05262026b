"""Solomon AI — Payments, SolomonPay, Stripe Webhook Routes"""
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid
import logging
import os

from core import db, DEFAULT_TENANT_ID, logger
from core.helpers import serialize_doc
from models.schemas import Donation, Fund, User, LeadCaptureRequest, SavePaymentMethodRequest, SolomonPayProcessRequest

try:
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
    )
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

router = APIRouter()

@router.get("/payments/config")
async def get_payment_config():
    """Get the Stripe publishable key for frontend"""
    publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY")
    return {
        "publishable_key": publishable_key,
        "currency": "usd",
        "payment_methods": ["card"]
    }

# Donation packages (FIXED - never accept amounts from frontend)
DONATION_PACKAGES = {
    "tithe_10": 10.00,
    "tithe_25": 25.00,
    "tithe_50": 50.00,
    "tithe_100": 100.00,
    "tithe_250": 250.00,
    "tithe_500": 500.00,
    "tithe_1000": 1000.00,
    "custom": None,  # Custom amounts handled separately with validation
}

class DonationRequest(BaseModel):
    package_id: str = "custom"
    custom_amount: Optional[float] = None
    fund_id: Optional[str] = None
    origin_url: str
    recurring: bool = False
    donor_name: Optional[str] = None
    donor_email: Optional[str] = None

class CheckoutStatusRequest(BaseModel):
    session_id: str


@router.post("/payments/donate")
async def create_donation_checkout(request: Request, donation: DonationRequest):
    """Create a Stripe checkout session for donations"""
    try:
        stripe_api_key = os.environ.get("STRIPE_API_KEY")
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Payment processing not configured")
        
        # Get logged in user if available
        session_token = get_session_token_from_request(request)
        user_email = None
        user_id = None
        if session_token:
            session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
            if session:
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    user_email = user.get("email")
                    user_id = user.get("user_id")
        
        # Determine amount
        if donation.package_id == "custom":
            if not donation.custom_amount or donation.custom_amount < 1.0:
                raise HTTPException(status_code=400, detail="Custom amount must be at least $1.00")
            if donation.custom_amount > 100000.0:
                raise HTTPException(status_code=400, detail="Amount exceeds maximum allowed")
            amount = float(donation.custom_amount)
        else:
            amount = DONATION_PACKAGES.get(donation.package_id)
            if amount is None:
                raise HTTPException(status_code=400, detail="Invalid donation package")
        
        # Build success/cancel URLs from frontend origin
        success_url = f"{donation.origin_url}?status=success&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{donation.origin_url}?status=cancelled"
        
        # Initialize Stripe
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        
        # Create metadata
        metadata = {
            "tenant_id": DEFAULT_TENANT_ID,
            "fund_id": donation.fund_id or "general",
            "donor_name": donation.donor_name or "Anonymous",
            "donor_email": user_email or donation.donor_email or "",
            "user_id": user_id or "",
            "recurring": str(donation.recurring),
            "source": "web_portal"
        }
        
        # Create checkout session
        checkout_request = CheckoutSessionRequest(
            amount=amount,
            currency="usd",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            payment_methods=["card"]  # Add "crypto" if user requests
        )
        
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Store transaction record
        transaction = {
            "id": f"txn_{uuid.uuid4().hex[:12]}",
            "tenant_id": DEFAULT_TENANT_ID,
            "session_id": session.session_id,
            "amount": amount,
            "currency": "usd",
            "fund_id": donation.fund_id or "general",
            "donor_name": donation.donor_name,
            "donor_email": donation.donor_email,
            "payment_status": "pending",
            "payment_method": "stripe",
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc)
        }
        await db.payment_transactions.insert_one(transaction)
        
        return {
            "checkout_url": session.url,
            "session_id": session.session_id
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (400, 401, etc.)
        raise
    except Exception as e:
        logger.error(f"Donation checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str):
    """Check the status of a Stripe checkout session"""
    try:
        stripe_api_key = os.environ.get("STRIPE_API_KEY")
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Payment processing not configured")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction in database
        if status.payment_status == "paid":
            # Find and update transaction
            transaction = await db.payment_transactions.find_one(
                {"session_id": session_id},
                {"_id": 0}
            )
            
            if transaction and transaction.get("payment_status") != "paid":
                # Update to paid
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "payment_status": "paid",
                        "paid_at": datetime.now(timezone.utc)
                    }}
                )
                
                # Create donation record
                donation = {
                    "id": f"donation_{uuid.uuid4().hex[:12]}",
                    "tenant_id": DEFAULT_TENANT_ID,
                    "person_id": None,  # Link to person if logged in
                    "fund_id": transaction.get("fund_id", "general"),
                    "fund_name": "General Fund",  # Lookup from funds
                    "amount": status.amount_total / 100,  # Convert from cents
                    "payment_method": "card",
                    "payment_status": "completed",
                    "transaction_id": session_id,
                    "donor_name": transaction.get("donor_name"),
                    "donor_email": transaction.get("donor_email"),
                    "donation_date": datetime.now(timezone.utc).isoformat(),
                    "notes": "Online donation via Stripe",
                    "created_at": datetime.now(timezone.utc)
                }
                await db.donations.insert_one(donation)
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount": status.amount_total / 100,  # Convert from cents
            "currency": status.currency
        }
        
    except Exception as e:
        logger.error(f"Payment status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for payment confirmations"""
    try:
        stripe_api_key = os.environ.get("STRIPE_API_KEY")
        if not stripe_api_key:
            return {"status": "ignored", "reason": "no_api_key"}
        
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        logger.info(f"Stripe webhook: {webhook_response.event_type} - {webhook_response.session_id}")
        
        # Update transaction based on webhook
        if webhook_response.payment_status == "paid":
            # Get the transaction
            transaction = await db.payment_transactions.find_one(
                {"session_id": webhook_response.session_id},
                {"_id": 0}
            )
            
            if transaction:
                # Update transaction status
                await db.payment_transactions.update_one(
                    {"session_id": webhook_response.session_id},
                    {"$set": {
                        "payment_status": "paid",
                        "webhook_received_at": datetime.now(timezone.utc)
                    }}
                )
                
                # Create donation record
                donor_email = transaction.get("donor_email") or transaction.get("metadata", {}).get("donor_email")
                if donor_email:
                    person = await db.people.find_one({"email": donor_email}, {"_id": 0})
                    person_id = person["id"] if person else None
                else:
                    person_id = None
                
                donation = {
                    "id": f"don_{uuid.uuid4().hex[:12]}",
                    "tenant_id": DEFAULT_TENANT_ID,
                    "person_id": person_id,
                    "amount": transaction.get("amount", 0),
                    "fund_id": transaction.get("fund_id", "general"),
                    "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "payment_method": "stripe",
                    "transaction_id": webhook_response.session_id,
                    "donor_name": transaction.get("donor_name", "Anonymous"),
                    "donor_email": donor_email,
                    "status": "completed",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.donations.insert_one(donation)
                logger.info(f"Created donation record: {donation['id']}")
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return {"status": "error", "message": str(e)}

# ============== SAVED PAYMENT METHODS ==============


@router.get("/payments/methods")
async def get_saved_payment_methods(request: Request):
    """Get saved payment methods for the current user"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Get saved payment methods from database
    methods = await db.payment_methods.find(
        {"user_id": user["user_id"], "is_active": True},
        {"_id": 0}
    ).to_list(10)
    
    return {"payment_methods": methods}

class SavePaymentMethodRequest(BaseModel):
    card_last_four: str
    card_brand: str
    card_exp_month: int
    card_exp_year: int
    stripe_payment_method_id: Optional[str] = None
    is_default: bool = False


@router.post("/payments/methods")
async def save_payment_method(request: Request, method_data: SavePaymentMethodRequest):
    """Save a new payment method for the current user"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # If setting as default, unset other defaults
    if method_data.is_default:
        await db.payment_methods.update_many(
            {"user_id": user["user_id"]},
            {"$set": {"is_default": False}}
        )
    
    payment_method = {
        "id": str(uuid.uuid4()),
        "user_id": user["user_id"],
        "tenant_id": user.get("tenant_id"),
        "card_last_four": method_data.card_last_four,
        "card_brand": method_data.card_brand,
        "card_exp_month": method_data.card_exp_month,
        "card_exp_year": method_data.card_exp_year,
        "stripe_payment_method_id": method_data.stripe_payment_method_id,
        "is_default": method_data.is_default,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.payment_methods.insert_one(payment_method)
    
    return {"message": "Payment method saved", "payment_method": {k: v for k, v in payment_method.items() if k != "_id"}}


@router.delete("/payments/methods/{method_id}")
async def delete_payment_method(request: Request, method_id: str):
    """Delete a saved payment method"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Soft delete - just mark as inactive
    result = await db.payment_methods.update_one(
        {"id": method_id, "user_id": session["user_id"]},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    return {"message": "Payment method removed"}


@router.put("/payments/methods/{method_id}/default")
async def set_default_payment_method(request: Request, method_id: str):
    """Set a payment method as the default"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Unset all defaults first
    await db.payment_methods.update_many(
        {"user_id": session["user_id"]},
        {"$set": {"is_default": False}}
    )
    
    # Set the new default
    result = await db.payment_methods.update_one(
        {"id": method_id, "user_id": session["user_id"], "is_active": True},
        {"$set": {"is_default": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    return {"message": "Default payment method updated"}


# ============== SOLOMONPAY ENDPOINTS ==============

class SolomonPayProcessRequest(BaseModel):
    card_last_four: str
    card_brand: str
    card_exp_month: str
    card_exp_year: str
    cardholder_name: str
    billing_zip: str
    save_card: bool = False
    amount: float
    context: str = "donation"
    fund_id: Optional[str] = None
    fund_name: Optional[str] = None
    frequency: Optional[str] = "one-time"
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/solomonpay/process")
async def solomonpay_process(request: Request, payload: SolomonPayProcessRequest):
    """Process a SolomonPay payment (beta - all transactions stay pending)"""
    user = None
    user_id = "anonymous"
    tenant_id = DEFAULT_TENANT_ID
    try:
        user = await get_current_portal_user(request)
        if user:
            user_id = user.get("user_id", "anonymous")
            tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    except Exception:
        pass

    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if len(payload.card_last_four) != 4:
        raise HTTPException(status_code=400, detail="Invalid card data")

    payment_method_id = None
    if payload.save_card and user_id != "anonymous":
        if payload.save_card:
            await db.payment_methods.update_many(
                {"user_id": user_id}, {"$set": {"is_default": False}}
            )
        pm = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "tenant_id": tenant_id,
            "card_last_four": payload.card_last_four,
            "card_brand": payload.card_brand,
            "card_exp_month": payload.card_exp_month,
            "card_exp_year": payload.card_exp_year,
            "cardholder_name": payload.cardholder_name,
            "billing_zip": payload.billing_zip,
            "is_default": True,
            "is_active": True,
            "provider": "solomonpay",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payment_methods.insert_one(pm)
        payment_method_id = pm["id"]

    txn_id = f"sp_txn_{uuid.uuid4().hex[:12]}"
    transaction = {
        "id": txn_id,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "amount": round(payload.amount, 2),
        "currency": "USD",
        "status": "pending",
        "payment_method_id": payment_method_id,
        "card_last_four": payload.card_last_four,
        "card_brand": payload.card_brand,
        "cardholder_name": payload.cardholder_name,
        "description": payload.description or f"SolomonPay {payload.context}",
        "context": payload.context,
        "fund_id": payload.fund_id,
        "fund_name": payload.fund_name,
        "frequency": payload.frequency,
        "metadata": payload.metadata or {},
        "provider": "solomonpay",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.solomonpay_transactions.insert_one(transaction)

    if payload.context == "donation" and user_id != "anonymous":
        donation = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": user_id,
            "person_name": payload.cardholder_name,
            "amount": round(payload.amount, 2),
            "fund": payload.fund_name or "General Fund",
            "fund_id": payload.fund_id or "general",
            "frequency": payload.frequency or "one-time",
            "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "payment_method": "solomonpay",
            "transaction_id": txn_id,
            "status": "pending",
            "source": "solomonpay",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.donations.insert_one(donation)

    return {
        "success": True,
        "transaction_id": txn_id,
        "status": "pending",
        "amount": round(payload.amount, 2),
        "message": "Payment recorded. Transaction will be processed when SolomonPay goes live."
    }


@router.get("/solomonpay/transactions")
async def get_solomonpay_transactions(request: Request, limit: int = 50):
    """Get SolomonPay transactions for admin view"""
    user = await get_current_portal_user(request)
    if not user or user.get("role") not in ["church_admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    txns = await db.solomonpay_transactions.find(
        {"tenant_id": tenant_id}, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return {"transactions": txns}

# ============== LEAD CAPTURE ==============

class LeadCaptureRequest(BaseModel):
    church_name: str
    name: str
    email: str
    phone: Optional[str] = None
    current_software: Optional[str] = None
    church_size: Optional[str] = None

