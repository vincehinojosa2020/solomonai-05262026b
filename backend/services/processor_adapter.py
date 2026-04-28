"""
Solomon Pay — Processor Adapter Interface
==========================================
This is the ONLY file that touches the actual payment acquirer.

Two adapters are shipped:

* `StripeAdapter`  — production. Uses Stripe Connect direct charges with
  per-tenant `stripe_account=`, application_fee_amount captures the
  platform fee, and full off_session/confirm flow for recurring giving.
* `SimulationAdapter`  — local dev only. Refuses to activate when
  ENVIRONMENT=production. Emits `solomonpay_*` reference IDs so it never
  collides with real Stripe IDs.

Adapter selection (audit BLOCKER #3):
    PAYMENT_ADAPTER=stripe        → StripeAdapter()        [DEFAULT]
    PAYMENT_ADAPTER=simulation    → SimulationAdapter()    [dev only]
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import stripe

logger = logging.getLogger("solomonpay.adapter")


class ChargeStatus(Enum):
    SUCCESS = "success"
    DECLINED = "declined"
    ERROR = "error"


@dataclass
class ChargeResult:
    status: ChargeStatus
    processor_reference_id: str
    message: str
    card_last_four: Optional[str] = None
    card_brand: Optional[str] = None


@dataclass
class RefundResult:
    status: ChargeStatus
    processor_reference_id: str
    message: str


@dataclass
class TokenResult:
    """Legacy holder for SimulationAdapter only. Real Stripe tokens come
    back as PaymentMethod IDs from Stripe.js Elements / SetupIntents and
    are passed straight into StripeAdapter as `payment_method_id`."""
    token: str
    card_last_four: str
    card_brand: str
    exp_month: int
    exp_year: int


class PaymentConfigError(Exception):
    """Raised when a tenant cannot accept payments (no/restricted Connect
    account, no payment method on file, etc.). Caller maps to a 400."""


class ProcessorAdapter:
    """Abstract base for payment processor adapters.

    All methods are async; sync SDKs (stripe-python today) are wrapped
    via asyncio.to_thread inside the adapter.

    Recurring giving uses `charge_card`/`charge_ach` with a saved
    Stripe Customer + PaymentMethod; first-time gifts use the dedicated
    PaymentIntent flow in routes/stripe_elements.py.
    """

    name = "abstract"

    async def charge_card(
        self,
        *,
        tenant_id: str,
        donor_id: str,
        amount_cents: int,
        payment_method_id: str,
        stripe_customer_id: Optional[str],
        connected_account_id: Optional[str],
        application_fee_amount: int = 0,
        idempotency_key: Optional[str] = None,
        metadata: Optional[dict] = None,
        description: str = "",
    ) -> ChargeResult:
        raise NotImplementedError

    async def charge_ach(
        self,
        *,
        tenant_id: str,
        donor_id: str,
        amount_cents: int,
        payment_method_id: str,
        stripe_customer_id: Optional[str],
        connected_account_id: Optional[str],
        application_fee_amount: int = 0,
        idempotency_key: Optional[str] = None,
        metadata: Optional[dict] = None,
        description: str = "",
    ) -> ChargeResult:
        raise NotImplementedError

    async def refund(
        self,
        *,
        processor_reference_id: str,
        connected_account_id: Optional[str] = None,
        amount_cents: Optional[int] = None,
    ) -> RefundResult:
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────────────────
#  StripeAdapter — real money (test mode in dev, live mode in prod)
# ─────────────────────────────────────────────────────────────────────────
class StripeAdapter(ProcessorAdapter):
    """Production adapter — talks to Stripe via the official SDK with
    Connect direct-charges. ZERO code changes are required to swap from
    sk_test → sk_live; only the env value of `STRIPE_API_KEY` differs.
    """

    name = "stripe"

    def __init__(self):
        # SDK initializes from env in core.connect / routes.* — but make
        # sure it's set if this adapter is constructed early.
        if not stripe.api_key:
            stripe.api_key = os.environ.get("STRIPE_API_KEY", "")

    @staticmethod
    async def _run(fn, *args, **kwargs):
        return await asyncio.to_thread(fn, *args, **kwargs)

    @staticmethod
    def _intent_to_result(intent) -> ChargeResult:
        if intent.status == "succeeded":
            card_last4 = None
            brand = None
            charges = getattr(intent, "charges", None)
            if charges and getattr(charges, "data", None):
                pm_details = getattr(charges.data[0], "payment_method_details", None)
                if pm_details and getattr(pm_details, "card", None):
                    card_last4 = pm_details.card.last4
                    brand = pm_details.card.brand
            return ChargeResult(
                status=ChargeStatus.SUCCESS,
                processor_reference_id=intent.id,
                message="Charge succeeded",
                card_last_four=card_last4,
                card_brand=brand,
            )
        if intent.status in ("requires_payment_method", "canceled"):
            err = getattr(intent, "last_payment_error", None)
            msg = (err.message if err else f"Payment {intent.status}")
            return ChargeResult(
                status=ChargeStatus.DECLINED,
                processor_reference_id=intent.id,
                message=msg,
            )
        # requires_action / requires_confirmation / processing — for
        # off_session=True these are unexpected; treat as error.
        return ChargeResult(
            status=ChargeStatus.ERROR,
            processor_reference_id=getattr(intent, "id", "") or "",
            message=f"Unexpected intent status: {intent.status}",
        )

    async def _create_payment_intent(
        self, *,
        amount_cents: int,
        payment_method_id: str,
        stripe_customer_id: Optional[str],
        connected_account_id: Optional[str],
        application_fee_amount: int,
        idempotency_key: Optional[str],
        metadata: dict,
        payment_method_types: list,
        description: str,
    ) -> ChargeResult:
        if not connected_account_id:
            raise PaymentConfigError(
                "Tenant has no active Stripe Connect account — cannot charge."
            )
        kwargs = dict(
            amount=amount_cents,
            currency="usd",
            payment_method=payment_method_id,
            confirm=True,
            off_session=True,
            payment_method_types=payment_method_types,
            metadata=metadata,
            description=description[:500] if description else None,
            stripe_account=connected_account_id,
        )
        if stripe_customer_id:
            kwargs["customer"] = stripe_customer_id
        if application_fee_amount > 0:
            kwargs["application_fee_amount"] = application_fee_amount
        if idempotency_key:
            kwargs["idempotency_key"] = idempotency_key

        try:
            intent = await self._run(stripe.PaymentIntent.create, **kwargs)
        except stripe.error.CardError as e:
            # Hard decline — captured intent is on the exception body.
            err_intent = getattr(e, "payment_intent", None)
            ref = (err_intent or {}).get("id") if isinstance(err_intent, dict) else getattr(err_intent, "id", None)
            return ChargeResult(
                status=ChargeStatus.DECLINED,
                processor_reference_id=ref or "",
                message=e.user_message or str(e),
            )
        except stripe.error.StripeError as e:
            return ChargeResult(
                status=ChargeStatus.ERROR,
                processor_reference_id="",
                message=e.user_message or str(e),
            )
        return self._intent_to_result(intent)

    async def charge_card(self, *, tenant_id, donor_id, amount_cents,
                          payment_method_id, stripe_customer_id=None,
                          connected_account_id=None, application_fee_amount=0,
                          idempotency_key=None, metadata=None, description="") -> ChargeResult:
        md = {
            "tenant_id": tenant_id,
            "donor_id": donor_id or "",
            **(metadata or {}),
        }
        return await self._create_payment_intent(
            amount_cents=amount_cents,
            payment_method_id=payment_method_id,
            stripe_customer_id=stripe_customer_id,
            connected_account_id=connected_account_id,
            application_fee_amount=application_fee_amount,
            idempotency_key=idempotency_key,
            metadata=md,
            payment_method_types=["card"],
            description=description,
        )

    async def charge_ach(self, *, tenant_id, donor_id, amount_cents,
                         payment_method_id, stripe_customer_id=None,
                         connected_account_id=None, application_fee_amount=0,
                         idempotency_key=None, metadata=None, description="") -> ChargeResult:
        md = {
            "tenant_id": tenant_id,
            "donor_id": donor_id or "",
            **(metadata or {}),
        }
        # ACH PaymentMethods of type us_bank_account require mandate data
        # but for off_session recurring with a previously-set-up mandate,
        # Stripe carries it forward automatically.
        return await self._create_payment_intent(
            amount_cents=amount_cents,
            payment_method_id=payment_method_id,
            stripe_customer_id=stripe_customer_id,
            connected_account_id=connected_account_id,
            application_fee_amount=application_fee_amount,
            idempotency_key=idempotency_key,
            metadata=md,
            payment_method_types=["us_bank_account"],
            description=description,
        )

    async def refund(self, *, processor_reference_id, connected_account_id=None,
                     amount_cents=None) -> RefundResult:
        kwargs = {"payment_intent": processor_reference_id}
        if amount_cents is not None:
            kwargs["amount"] = amount_cents
        if connected_account_id:
            kwargs["stripe_account"] = connected_account_id
        try:
            refund = await self._run(stripe.Refund.create, **kwargs)
        except stripe.error.StripeError as e:
            return RefundResult(
                status=ChargeStatus.ERROR,
                processor_reference_id="",
                message=e.user_message or str(e),
            )
        return RefundResult(
            status=ChargeStatus.SUCCESS,
            processor_reference_id=refund.id,
            message="Refund processed",
        )


# ─────────────────────────────────────────────────────────────────────────
#  SimulationAdapter — local dev only
# ─────────────────────────────────────────────────────────────────────────
class SimulationAdapter(ProcessorAdapter):
    """LOCAL DEV ONLY. Returns success for valid-looking inputs, simulates
    declines for test scenarios. Refuses to activate if ENVIRONMENT=production
    (BLOCKER #3 from production audit)."""

    name = "simulation"

    DECLINE_TEST_AMOUNTS = {4242: "Insufficient funds", 9999: "Card expired"}

    def __init__(self):
        if os.environ.get("ENVIRONMENT", "").lower() == "production":
            raise RuntimeError(
                "SimulationAdapter cannot be used in production "
                "(set PAYMENT_ADAPTER=stripe in production env)."
            )

    async def charge_card(self, *, tenant_id, donor_id, amount_cents,
                          payment_method_id, stripe_customer_id=None,
                          connected_account_id=None, application_fee_amount=0,
                          idempotency_key=None, metadata=None, description="") -> ChargeResult:
        if amount_cents in self.DECLINE_TEST_AMOUNTS:
            return ChargeResult(
                status=ChargeStatus.DECLINED,
                processor_reference_id=f"sim_declined_{uuid.uuid4().hex[:12]}",
                message=self.DECLINE_TEST_AMOUNTS[amount_cents],
            )
        ref_id = f"sim_ch_{uuid.uuid4().hex[:16]}"
        last_four = (payment_method_id or "")[-4:] if payment_method_id else "0000"
        brand = "Visa"
        logger.info(f"[SIMULATION] charge_card ${amount_cents/100:.2f} → {ref_id}")
        return ChargeResult(
            status=ChargeStatus.SUCCESS,
            processor_reference_id=ref_id,
            message="Charge successful (simulation)",
            card_last_four=last_four,
            card_brand=brand,
        )

    async def charge_ach(self, *, tenant_id, donor_id, amount_cents,
                         payment_method_id, stripe_customer_id=None,
                         connected_account_id=None, application_fee_amount=0,
                         idempotency_key=None, metadata=None, description="") -> ChargeResult:
        ref_id = f"sim_ach_{uuid.uuid4().hex[:16]}"
        logger.info(f"[SIMULATION] charge_ach ${amount_cents/100:.2f} → {ref_id}")
        return ChargeResult(
            status=ChargeStatus.SUCCESS,
            processor_reference_id=ref_id,
            message="ACH charge successful (simulation)",
        )

    async def refund(self, *, processor_reference_id, connected_account_id=None,
                     amount_cents=None) -> RefundResult:
        ref_id = f"sim_rf_{uuid.uuid4().hex[:16]}"
        logger.info(f"[SIMULATION] refund {processor_reference_id} → {ref_id}")
        return RefundResult(
            status=ChargeStatus.SUCCESS,
            processor_reference_id=ref_id,
            message="Refund processed (simulation)",
        )


# ─────────────────────────────────────────────────────────────────────────
#  Active adapter selection — driven by env, never hardcoded
# ─────────────────────────────────────────────────────────────────────────
def _select_adapter() -> ProcessorAdapter:
    choice = (os.environ.get("PAYMENT_ADAPTER") or "stripe").lower()
    env = (os.environ.get("ENVIRONMENT") or "development").lower()
    if choice == "simulation":
        if env == "production":
            logger.error("PAYMENT_ADAPTER=simulation rejected in production — falling back to StripeAdapter")
            return StripeAdapter()
        return SimulationAdapter()
    if choice != "stripe":
        logger.warning(f"Unknown PAYMENT_ADAPTER={choice!r} — defaulting to StripeAdapter")
    return StripeAdapter()


ACTIVE_ADAPTER: ProcessorAdapter = _select_adapter()
logger.info(f"[processor_adapter] active adapter: {ACTIVE_ADAPTER.name}")
