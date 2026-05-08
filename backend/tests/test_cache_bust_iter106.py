"""Iteration 106 — verify P0 cache-bust on /api/stripe/confirm-donation,
plus regression checks against the platform Stripe endpoints.

The handler at /app/backend/routes/stripe_elements.py:347-351 must invalidate
both _STATS_CACHE and _PLATFORM_TXN_CACHE after persisting a donation so that
the very next /api/platform/stripe/transactions/stats call reflects the new
gift instead of serving stale 30s-cached data.
"""
import os
import time

import pytest
import requests
import stripe
from dotenv import dotenv_values

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL", "https://compliance-check-143.preview.emergentagent.com"
).rstrip("/")
ADMIN_EMAIL = "admin@solomonai.us"
ADMIN_PASS = os.environ.get("TEST_PASSWORD", "Demo2026!")
EDEN_SLUG = "eden-church"

# Pull live test key the same way the backend does so we can drive a real
# PaymentIntent through to succeeded.
_DOTENV = dotenv_values("/app/backend/.env")
_KEY = (_DOTENV.get("STRIPE_API_KEY") or os.environ.get("STRIPE_API_KEY") or "").strip().strip("\"'")


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"no token: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ── Backend basics ────────────────────────────────────────────────────────
def test_health():
    r = requests.get(f"{BASE_URL}/api/health", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok", body


# ── P0 regressions ────────────────────────────────────────────────────────
def test_stats_requires_auth():
    r = requests.get(f"{BASE_URL}/api/platform/stripe/transactions/stats", timeout=15)
    assert r.status_code in (401, 403), r.text


def test_stats_full_payload(headers):
    r = requests.get(
        f"{BASE_URL}/api/platform/stripe/transactions/stats", headers=headers, timeout=20
    )
    assert r.status_code == 200, r.text
    body = r.json()
    for bucket in ("today", "this_week", "this_month", "all_time"):
        assert bucket in body, f"missing {bucket}"
        for k in ("count", "total_amount", "solomon_revenue"):
            assert k in body[bucket], f"{bucket} missing {k}"
    assert "active_churches" in body
    assert "total_donors" in body
    assert isinstance(body["active_churches"], int)
    assert isinstance(body["total_donors"], int)


def test_recent_endpoint(headers):
    r = requests.get(
        f"{BASE_URL}/api/platform/stripe/transactions/recent", headers=headers, timeout=20
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "data" in body and isinstance(body["data"], list)
    if body["data"]:
        row = body["data"][0]
        for key in ("amount_cents", "church_name", "donor_name", "fund", "donation_date"):
            assert key in row


def test_platform_churches_stripe_fields(headers):
    r = requests.get(f"{BASE_URL}/api/platform/churches", headers=headers, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    items = (
        body.get("churches") or body.get("data") or body.get("items")
        if isinstance(body, dict) else body
    )
    assert isinstance(items, list) and items, f"no churches in {body if not isinstance(body,dict) else list(body.keys())}"
    sample = items[0]
    for key in ("stripe_status", "stripe_total_processed", "stripe_txn_count"):
        assert key in sample, f"missing {key} in {list(sample.keys())}"


# ── P0 cache-bust verification ────────────────────────────────────────────
@pytest.mark.skipif(not _KEY.startswith("sk_test_"), reason="needs Stripe test key")
def test_confirm_donation_busts_stats_cache(headers):
    """End-to-end: warm the stats cache, drive a real $1.00 test payment to
    succeeded via stripe SDK, hit /confirm-donation, then re-fetch /stats
    *immediately* (well within the 30s TTL) and assert the new gift was
    counted — proving the cache was busted."""
    stripe.api_key = _KEY

    # 1) Warm the cache & record the all_time count baseline.
    r0 = requests.get(
        f"{BASE_URL}/api/platform/stripe/transactions/stats", headers=headers, timeout=20
    )
    assert r0.status_code == 200, r0.text
    before = r0.json()["all_time"]["count"]

    # 2) Re-fetch immediately to confirm we're being served from cache (same value).
    r0b = requests.get(
        f"{BASE_URL}/api/platform/stripe/transactions/stats", headers=headers, timeout=20
    )
    assert r0b.status_code == 200
    assert r0b.json()["all_time"]["count"] == before, "cache should be warm"

    # 3) Create a PaymentIntent through the public Solomon Pay endpoint.
    create = requests.post(
        f"{BASE_URL}/api/stripe/create-payment-intent",
        json={
            "amount": 1.0,
            "fund": "Tithes",
            "frequency": "one-time",
            "donor_first_name": "Cache",
            "donor_last_name": "BustTest",
            "donor_email": "TEST_cache_bust_iter106@example.com",
            "cover_fees": False,
            "church_slug": EDEN_SLUG,
            "message": "iter106 cache-bust test",
        },
        timeout=20,
    )
    assert create.status_code == 200, create.text
    pi_id = create.json()["payment_intent_id"]

    # 4) Confirm the PaymentIntent with Stripe's test bypass payment method
    #    (pm_card_visa always succeeds in test mode without 3DS).
    confirmed = stripe.PaymentIntent.confirm(pi_id, payment_method="pm_card_visa")
    assert confirmed.status == "succeeded", f"intent status: {confirmed.status}"

    # 5) Hit our confirm-donation endpoint — this is the path that should
    #    bust the cache after persisting the donation row.
    cd = requests.post(
        f"{BASE_URL}/api/stripe/confirm-donation",
        json={"payment_intent_id": pi_id, "church_slug": EDEN_SLUG},
        timeout=20,
    )
    assert cd.status_code == 200, cd.text
    assert cd.json().get("status") == "succeeded", cd.json()

    # 6) Immediately re-fetch /stats. If the cache was busted, all_time.count
    #    should have incremented. If not, it would still equal `before`.
    time.sleep(0.5)  # allow async fund roll-up to flush
    r1 = requests.get(
        f"{BASE_URL}/api/platform/stripe/transactions/stats", headers=headers, timeout=20
    )
    assert r1.status_code == 200, r1.text
    after = r1.json()["all_time"]["count"]

    assert after >= before + 1, (
        f"cache was NOT busted: before={before} after={after} pi={pi_id}"
    )
