"""Iteration 107 — Week-1 'Stop the Bleeding' production audit verification.

Covers BLOCKERS #2 (webhook), #4 (tokenize deletion), #5 (auth debug guard),
#6 (seed prod guards), #8 (PI idempotency_key), plus regressions on auth/login
and /api/health.
"""
import os
import json
import time
import uuid
import hashlib
import subprocess

import pytest
import requests
import stripe
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://startup-automation.preview.emergentagent.com").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "solomonai")

ADMIN_EMAIL = "admin@solomonai.us"
ADMIN_PASSWORD = os.environ.get("TEST_PASSWORD", "Demo2026!")
EDEN_EMAIL = "christopher@eden-x.io"
EDEN_PASSWORD = os.environ.get("TEST_EDEN_PASSWORD", "EdenChurch2026!")

# Read STRIPE secret key directly from backend/.env so confirm-donation test works
def _read_env(key: str) -> str:
    try:
        with open("/app/backend/.env") as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


@pytest.fixture(scope="module")
def db():
    return MongoClient(MONGO_URL)[DB_NAME]


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ─────────────────────────────────────────────────────────────────────
# 1. Health regression
# ─────────────────────────────────────────────────────────────────────
class TestHealth:
    def test_health_ok(self, session):
        r = session.get(f"{BASE_URL}/api/health", timeout=10)
        assert r.status_code == 200
        assert r.json().get("status") == "ok"


# ─────────────────────────────────────────────────────────────────────
# 2. BLOCKER #4 — tokenize endpoints deleted
# ─────────────────────────────────────────────────────────────────────
class TestTokenizeDeleted:
    def test_tokenize_card_returns_404(self, session):
        r = session.post(f"{BASE_URL}/api/solomonpay/tokenize",
                         json={"card_number": "4242", "exp_month": 12, "exp_year": 2030, "cvc": "123"})
        assert r.status_code == 404, f"tokenize should be deleted, got {r.status_code}: {r.text[:200]}"

    def test_tokenize_bank_returns_404(self, session):
        r = session.post(f"{BASE_URL}/api/solomonpay/tokenize-bank",
                         json={"routing_number": "110000000", "account_number": "000123456789"})
        assert r.status_code == 404, f"tokenize-bank should be deleted, got {r.status_code}: {r.text[:200]}"


# ─────────────────────────────────────────────────────────────────────
# 3. BLOCKER #2 — Stripe webhook hardening + idempotency
# ─────────────────────────────────────────────────────────────────────
class TestStripeWebhook:
    def test_webhook_dev_fallback_no_secret(self, session, db):
        """With STRIPE_WEBHOOK_SECRET unset (current state) + sk_test_*: returns 200."""
        # confirm precondition
        secret = _read_env("STRIPE_WEBHOOK_SECRET")
        if secret:
            pytest.skip("STRIPE_WEBHOOK_SECRET is currently SET — skipping dev-fallback test")

        event_id = f"evt_test_iter107_{uuid.uuid4().hex[:12]}"
        payload = {
            "id": event_id, "type": "payment_intent.succeeded",
            "data": {"object": {"id": f"pi_fake_{uuid.uuid4().hex[:8]}", "metadata": {}}},
        }
        r = session.post(f"{BASE_URL}/api/webhook/stripe", json=payload, timeout=10)
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        assert body.get("received") is True

        # event_id should be persisted
        time.sleep(0.5)
        rec = db.stripe_webhook_events.find_one({"event_id": event_id})
        assert rec is not None, "event_id was not inserted into stripe_webhook_events"

    def test_webhook_idempotency_duplicate(self, session, db):
        """Second call with same event_id returns duplicate:true."""
        secret = _read_env("STRIPE_WEBHOOK_SECRET")
        if secret:
            pytest.skip("STRIPE_WEBHOOK_SECRET set — dev path skipped")

        event_id = f"evt_test_dup_iter107_{uuid.uuid4().hex[:12]}"
        payload = {
            "id": event_id, "type": "payment_intent.succeeded",
            "data": {"object": {"id": f"pi_fake_{uuid.uuid4().hex[:8]}", "metadata": {}}},
        }
        r1 = session.post(f"{BASE_URL}/api/webhook/stripe", json=payload, timeout=10)
        assert r1.status_code == 200
        assert r1.json().get("duplicate") is not True

        r2 = session.post(f"{BASE_URL}/api/webhook/stripe", json=payload, timeout=10)
        assert r2.status_code == 200
        assert r2.json().get("duplicate") is True, f"second call should be duplicate, got {r2.json()}"

    def test_stripe_webhook_events_unique_index(self, db):
        idxs = db.stripe_webhook_events.index_information()
        # Look for a unique index on event_id
        found_unique = any(
            spec.get("unique") and spec.get("key") == [("event_id", 1)]
            for spec in idxs.values()
        )
        assert found_unique, f"No unique index on event_id: {idxs}"


# ─────────────────────────────────────────────────────────────────────
# 4. BLOCKER #2 — webhook with secret SET — bad/missing signature → 400
# Done by temporarily flipping the env, restarting backend.
# ─────────────────────────────────────────────────────────────────────
class TestStripeWebhookWithSecret:
    SECRET_VALUE = "whsec_test_iter107_xyz"

    @pytest.fixture(scope="class", autouse=True)
    def flip_secret(self):
        # flip ON
        env_path = "/app/backend/.env"
        with open(env_path) as f:
            original = f.read()
        new = original.replace("STRIPE_WEBHOOK_SECRET=\n", f"STRIPE_WEBHOOK_SECRET={self.SECRET_VALUE}\n")
        if new == original:
            # Maybe value not empty — try replacing existing value
            import re
            new = re.sub(r"^STRIPE_WEBHOOK_SECRET=.*$", f"STRIPE_WEBHOOK_SECRET={self.SECRET_VALUE}", original, flags=re.M)
        with open(env_path, "w") as f:
            f.write(new)
        subprocess.run(["sudo", "supervisorctl", "restart", "backend"], capture_output=True)
        time.sleep(5)
        yield
        # restore
        with open(env_path, "w") as f:
            f.write(original)
        subprocess.run(["sudo", "supervisorctl", "restart", "backend"], capture_output=True)
        time.sleep(5)

    def test_no_signature_header_returns_400(self):
        r = requests.post(
            f"{BASE_URL}/api/webhook/stripe",
            data=json.dumps({"id": "evt_test_none", "type": "x", "data": {"object": {}}}),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        assert r.status_code == 400, f"expected 400 with no Stripe-Signature, got {r.status_code}: {r.text[:200]}"

    def test_bogus_signature_returns_400(self):
        r = requests.post(
            f"{BASE_URL}/api/webhook/stripe",
            data=json.dumps({"id": "evt_test_bogus", "type": "x", "data": {"object": {}}}),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=1234567890,v1=deadbeef",
            },
            timeout=10,
        )
        assert r.status_code == 400, f"expected 400 with bogus sig, got {r.status_code}: {r.text[:200]}"


# ─────────────────────────────────────────────────────────────────────
# 5. BLOCKER #8 — PaymentIntent idempotency_key
# ─────────────────────────────────────────────────────────────────────
class TestPaymentIntentIdempotency:
    PAYLOAD = {
        "amount": 1.00,
        "donor_email": "TEST_idempotency_iter107@example.com",
        "fund": "General Fund",
        "frequency": "one_time",
        "church_slug": "eden-church",
        "cover_fees": False,
    }

    def test_same_payload_same_pi_id(self, session):
        r1 = session.post(f"{BASE_URL}/api/stripe/create-payment-intent", json=self.PAYLOAD, timeout=15)
        assert r1.status_code == 200, r1.text[:300]
        pi1 = r1.json().get("payment_intent_id") or r1.json().get("id")

        r2 = session.post(f"{BASE_URL}/api/stripe/create-payment-intent", json=self.PAYLOAD, timeout=15)
        assert r2.status_code == 200, r2.text[:300]
        pi2 = r2.json().get("payment_intent_id") or r2.json().get("id")

        assert pi1 and pi2
        assert pi1 == pi2, f"idempotent calls should return same PI; got {pi1} vs {pi2}"

    def test_cover_fees_toggle_creates_new_pi(self, session):
        payload_no_fees = dict(self.PAYLOAD, donor_email="TEST_iter107_nofees@example.com")
        r1 = session.post(f"{BASE_URL}/api/stripe/create-payment-intent", json=payload_no_fees, timeout=15)
        assert r1.status_code == 200, r1.text[:300]
        pi1 = r1.json().get("payment_intent_id") or r1.json().get("id")

        payload_with_fees = dict(payload_no_fees, cover_fees=True)
        r2 = session.post(f"{BASE_URL}/api/stripe/create-payment-intent", json=payload_with_fees, timeout=15)
        # Must not idempotency-conflict (Stripe returns 400 if same key + diff body)
        assert r2.status_code == 200, f"cover_fees toggle failed: {r2.status_code} {r2.text[:300]}"
        pi2 = r2.json().get("payment_intent_id") or r2.json().get("id")

        assert pi1 != pi2, f"cover_fees toggle should yield NEW PI; got same {pi1}"


# ─────────────────────────────────────────────────────────────────────
# 6. Auth regression — login still works for both seed admins
# ─────────────────────────────────────────────────────────────────────
class TestAuthRegression:
    def test_login_platform_admin(self, session):
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=10)
        assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
        body = r.json()
        assert body.get("session_token") or body.get("user")

    def test_login_eden_church_admin(self, session):
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": EDEN_EMAIL, "password": EDEN_PASSWORD}, timeout=10)
        assert r.status_code == 200, f"eden login failed: {r.status_code} {r.text[:200]}"


# ─────────────────────────────────────────────────────────────────────
# 7. BLOCKER #5 — debug endpoints reachable in dev (ENVIRONMENT=development)
# ─────────────────────────────────────────────────────────────────────
class TestAuthDebugInDev:
    def test_verify_accounts_works_in_dev(self, session):
        r = session.get(f"{BASE_URL}/api/auth/debug/verify-accounts", timeout=10)
        assert r.status_code == 200, f"debug/verify-accounts should work in dev: {r.status_code} {r.text[:200]}"
        body = r.json()
        assert "accounts" in body

    def test_test_login_works_in_dev(self, session):
        r = session.post(f"{BASE_URL}/api/auth/debug/test-login",
                         json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=10)
        assert r.status_code == 200, f"debug/test-login should work in dev: {r.status_code} {r.text[:200]}"


# ─────────────────────────────────────────────────────────────────────
# 8. Regression — confirm-donation cache-bust path (iter106 carry-forward)
# ─────────────────────────────────────────────────────────────────────
class TestConfirmDonationStripeFlow:
    def test_real_stripe_pi_confirm_donation(self, session, db):
        stripe_key = _read_env("STRIPE_API_KEY")
        if not stripe_key.startswith("sk_test_"):
            pytest.skip("Stripe test key not available")
        stripe.api_key = stripe_key

        # 1. Create PI via our endpoint
        donor = f"TEST_iter107_confirm_{uuid.uuid4().hex[:6]}@example.com"
        payload = {
            "amount": 1.00, "donor_email": donor, "fund": "General Fund",
            "frequency": "one_time", "church_slug": "eden-church", "cover_fees": False,
        }
        r = session.post(f"{BASE_URL}/api/stripe/create-payment-intent", json=payload, timeout=15)
        assert r.status_code == 200, r.text[:300]
        pi_id = r.json().get("payment_intent_id") or r.json().get("id")
        assert pi_id

        # 2. Confirm with test card via Stripe SDK
        try:
            confirmed = stripe.PaymentIntent.confirm(pi_id, payment_method="pm_card_visa")
        except stripe.error.StripeError as e:
            pytest.fail(f"Stripe confirm failed: {e}")
        assert confirmed.status in ("succeeded", "requires_capture"), f"PI status={confirmed.status}"

        # 3. Call confirm-donation
        r2 = session.post(f"{BASE_URL}/api/stripe/confirm-donation",
                          json={"payment_intent_id": pi_id, "church_slug": "eden-church"}, timeout=15)
        assert r2.status_code == 200, f"confirm-donation failed: {r2.status_code} {r2.text[:300]}"

        # 4. Verify donation row inserted
        time.sleep(1)
        donation = db.donations.find_one({"donor_email": donor}) or db.donations.find_one({"stripe_payment_intent_id": pi_id})
        assert donation is not None, f"No donation persisted for {donor}/{pi_id}"

        # cleanup
        db.donations.delete_many({"donor_email": donor})
        db.payment_transactions.delete_many({"payment_intent_id": pi_id})


# ─────────────────────────────────────────────────────────────────────
# 9. BLOCKER #6 — _prod_guard refuses in production
# ─────────────────────────────────────────────────────────────────────
class TestProdGuard:
    def test_prod_guard_refuses_when_env_production(self):
        result = subprocess.run(
            ["python", "-c",
             "import os, sys; sys.path.insert(0, '/app/backend');"
             "os.environ['ENVIRONMENT']='production';"
             "from scripts._prod_guard import refuse_in_production;"
             "refuse_in_production('test')"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0, f"prod_guard should refuse, returncode={result.returncode}"
        assert "Refusing" in (result.stderr + result.stdout)

    def test_prod_guard_passes_in_dev(self):
        result = subprocess.run(
            ["python", "-c",
             "import os, sys; sys.path.insert(0, '/app/backend');"
             "os.environ['ENVIRONMENT']='development';"
             "from scripts._prod_guard import refuse_in_production;"
             "refuse_in_production('test')"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0

    def test_emergency_seed_skips_in_production(self):
        # simulate by importing and calling with ENVIRONMENT=production
        result = subprocess.run(
            ["python", "-c",
             "import os, sys, asyncio; sys.path.insert(0, '/app/backend');"
             "os.environ['ENVIRONMENT']='production';"
             "from scripts.emergency_seed import emergency_seed_if_empty;"
             "r = asyncio.run(emergency_seed_if_empty()); print(r)"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0, result.stderr[-300:]
        assert "skipped" in result.stdout and "production" in result.stdout, result.stdout
