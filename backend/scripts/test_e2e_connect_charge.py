"""
End-to-end test (TEST MODE):
  1. Hit /api/stripe/create-payment-intent for $1.00 on a tenant
  2. Server-side confirm with stripe.PaymentIntent.confirm using a test
     PaymentMethod attached to the connected account
  3. Hit /api/stripe/confirm-donation to insert the donation row
  4. Verify the donation row exists in db.donations
  5. Print the PaymentIntent id (visible at https://dashboard.stripe.com/test/connect/accounts/<acct_id>/payments)
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            override=True)

import stripe  # noqa: E402
import urllib.request  # noqa: E402

from core import db  # noqa: E402

stripe.api_key = os.environ["STRIPE_API_KEY"]
# Use localhost — server-side script doesn't need ingress.
API_URL = "http://localhost:8001"
SLUG = sys.argv[1] if len(sys.argv) > 1 else "eden-church"


def post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{API_URL}/api{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


async def main() -> None:
    print(f"\n══ End-to-end Connect PI test against /{SLUG} ══\n")

    # ── 1. Create the PI via our public API ──
    print("STEP 1 — POST /api/stripe/create-payment-intent ($1.00)")
    create_resp = post("/stripe/create-payment-intent", {
        "amount": 1.00,
        "fund": "Tithes",
        "frequency": "one-time",
        "donor_first_name": "E2E",
        "donor_last_name": "Test",
        "donor_email": "e2e-connect-test@solomonai.us",
        "cover_fees": False,
        "church_slug": SLUG,
    })
    pi_id = create_resp["payment_intent_id"]
    client_secret = create_resp["client_secret"]
    connected_acct = create_resp["connected_account_id"]
    app_fee = create_resp["application_fee_amount"]
    total = create_resp["total_amount"]
    print(f"   ✓ PI created:           {pi_id}")
    print(f"   ✓ Connected account:    {connected_acct}")
    print(f"   ✓ Total amount:         ${total:.2f} (${app_fee/100:.2f} application_fee)")

    # ── 2. Server-side confirm with Stripe's reserved test PaymentMethod ──
    # `pm_card_visa` is a magic test ID Stripe accepts on any connected
    # account in test mode. Using raw PAN is blocked at Stripe's API
    # boundary (which is also why BLOCKER #4 in our audit removed our
    # raw-PAN endpoint).
    print("\nSTEP 2 — Server-side confirm with pm_card_visa (Stripe reserved test PM)")
    confirmed = stripe.PaymentIntent.confirm(
        pi_id,
        payment_method="pm_card_visa",
        stripe_account=connected_acct,
    )
    print(f"   ✓ PI status:            {confirmed.status}")
    print(f"   ✓ PI amount:            ${confirmed.amount/100:.2f}")
    print(f"   ✓ application_fee:      ${(confirmed.application_fee_amount or 0)/100:.2f}")
    if confirmed.status != "succeeded":
        print(f"   ✗ unexpected status — last_payment_error: {confirmed.last_payment_error}")
        return

    # ── 3. Tell our backend to record the donation ──
    print("\nSTEP 3 — POST /api/stripe/confirm-donation")
    confirm_resp = post("/stripe/confirm-donation", {
        "payment_intent_id": pi_id,
        "church_slug": SLUG,
    })
    print(f"   ✓ status:               {confirm_resp.get('status')}")
    donation = confirm_resp.get("donation") or {}
    donation_id = donation.get("id")
    print(f"   ✓ donation.id:          {donation_id}")
    print(f"   ✓ donation.amount:      ${donation.get('amount'):.2f}")
    print(f"   ✓ donation.fee_amount:  ${donation.get('fee_amount',0):.2f}")
    print(f"   ✓ donation.net_amount:  ${donation.get('net_amount',0):.2f}")

    # ── 4. Verify the row landed in MongoDB ──
    print("\nSTEP 4 — verify donation row in db.donations")
    row = await db.donations.find_one(
        {"stripe_payment_intent_id": pi_id}, {"_id": 0}
    )
    if not row:
        print("   ✗ NOT FOUND — donation row missing")
        return
    print(f"   ✓ found row id={row['id']}")
    print(f"     tenant_id:    {row['tenant_id']}")
    print(f"     payment_source: {row.get('payment_source')}")
    print(f"     stripe_payment_intent_id: {row['stripe_payment_intent_id']}")
    print(f"     payment_method: {row.get('payment_method')}")
    print(f"     amount/total/net: ${row['amount']:.2f} / ${row.get('total_amount',row['amount']):.2f} / ${row.get('net_amount',0):.2f}")

    print("\n══ ✅  END-TO-END VERIFIED  ══")
    print(f"\nVerify on Stripe dashboard:")
    print(f"  https://dashboard.stripe.com/test/connect/accounts/{connected_acct}/payments")
    print(f"\nPaymentIntent ID: {pi_id}\n")


if __name__ == "__main__":
    asyncio.run(main())
