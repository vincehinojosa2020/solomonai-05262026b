"""
Solomon Pay — Processor Adapter Interface
==========================================
This is the ONLY file that touches the actual payment acquirer.
To go live: create a new adapter class (e.g., FinixAdapter, PayrixAdapter)
and swap it in the ACTIVE_ADAPTER assignment at the bottom of this file.

All other Solomon Pay code is processor-agnostic.
"""
import uuid
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
from typing import Optional

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
    token: str
    card_last_four: str
    card_brand: str
    exp_month: int
    exp_year: int


class ProcessorAdapter:
    """Abstract base for payment processor adapters."""

    async def charge_card(self, token: str, amount_cents: int, currency: str = "usd",
                          description: str = "", metadata: dict = None) -> ChargeResult:
        raise NotImplementedError

    async def charge_ach(self, token: str, amount_cents: int, currency: str = "usd",
                         description: str = "", metadata: dict = None) -> ChargeResult:
        raise NotImplementedError

    async def refund(self, processor_reference_id: str, amount_cents: int = None) -> RefundResult:
        raise NotImplementedError

    async def tokenize_card(self, card_number: str, exp_month: int, exp_year: int,
                            cvc: str) -> TokenResult:
        raise NotImplementedError

    async def tokenize_bank(self, routing_number: str, account_number: str,
                            account_type: str = "checking") -> TokenResult:
        raise NotImplementedError


class SimulationAdapter(ProcessorAdapter):
    """
    Simulation mode — processes all transactions locally.
    Returns success for valid-looking inputs, simulates declines for test scenarios.
    Replace this class with a real acquirer adapter to go live.
    """

    DECLINE_TEST_AMOUNTS = {4242: "Insufficient funds", 9999: "Card expired"}

    async def charge_card(self, token: str, amount_cents: int, currency: str = "usd",
                          description: str = "", metadata: dict = None) -> ChargeResult:
        # Simulate decline for test amounts
        if amount_cents in self.DECLINE_TEST_AMOUNTS:
            return ChargeResult(
                status=ChargeStatus.DECLINED,
                processor_reference_id=f"sim_declined_{uuid.uuid4().hex[:12]}",
                message=self.DECLINE_TEST_AMOUNTS[amount_cents],
            )

        ref_id = f"sim_ch_{uuid.uuid4().hex[:16]}"
        logger.info(f"[SIMULATION] Card charge: ${amount_cents/100:.2f} -> {ref_id}")

        # Extract card info from token if available
        last_four = token[-4:] if len(token) >= 4 else "0000"
        brand = "Visa" if token.startswith("tok_visa") else "Mastercard" if token.startswith("tok_mc") else "Visa"

        return ChargeResult(
            status=ChargeStatus.SUCCESS,
            processor_reference_id=ref_id,
            message="Charge successful (simulation)",
            card_last_four=last_four,
            card_brand=brand,
        )

    async def charge_ach(self, token: str, amount_cents: int, currency: str = "usd",
                         description: str = "", metadata: dict = None) -> ChargeResult:
        ref_id = f"sim_ach_{uuid.uuid4().hex[:16]}"
        logger.info(f"[SIMULATION] ACH charge: ${amount_cents/100:.2f} -> {ref_id}")

        return ChargeResult(
            status=ChargeStatus.SUCCESS,
            processor_reference_id=ref_id,
            message="ACH charge successful (simulation)",
        )

    async def refund(self, processor_reference_id: str, amount_cents: int = None) -> RefundResult:
        ref_id = f"sim_rf_{uuid.uuid4().hex[:16]}"
        logger.info(f"[SIMULATION] Refund for {processor_reference_id}: ${(amount_cents or 0)/100:.2f} -> {ref_id}")

        return RefundResult(
            status=ChargeStatus.SUCCESS,
            processor_reference_id=ref_id,
            message="Refund processed (simulation)",
        )

    async def tokenize_card(self, card_number: str, exp_month: int, exp_year: int,
                            cvc: str) -> TokenResult:
        last_four = card_number[-4:] if card_number else "0000"
        first_digit = card_number[0] if card_number else "4"
        brand = {"4": "Visa", "5": "Mastercard", "3": "Amex", "6": "Discover"}.get(first_digit, "Visa")

        return TokenResult(
            token=f"tok_{brand.lower()}_{uuid.uuid4().hex[:12]}",
            card_last_four=last_four,
            card_brand=brand,
            exp_month=exp_month,
            exp_year=exp_year,
        )

    async def tokenize_bank(self, routing_number: str, account_number: str,
                            account_type: str = "checking") -> TokenResult:
        last_four = account_number[-4:] if account_number else "0000"

        return TokenResult(
            token=f"tok_ach_{uuid.uuid4().hex[:12]}",
            card_last_four=last_four,
            card_brand="ACH",
            exp_month=0,
            exp_year=0,
        )


# ═══════════════════════════════════════════════════
# ACTIVE ADAPTER — Change this ONE line to go live
# ═══════════════════════════════════════════════════
ACTIVE_ADAPTER: ProcessorAdapter = SimulationAdapter()
