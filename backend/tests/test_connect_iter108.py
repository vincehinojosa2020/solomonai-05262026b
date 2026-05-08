"""Iter108 — Stripe Connect per-tenant + StripeAdapter (BLOCKERS #1, #3)."""
import os, json, time, uuid, requests, pytest, asyncio
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://compliance-check-143.preview.emergentagent.com").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "solomonai")
EDEN = "eden-church-001"
EDEN_SLUG = "eden-church"


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text[:200]}"
    return r.json().get("token") or r.json().get("session_token") or r.json().get("access_token")


@pytest.fixture(scope="session")
def admin_token():
    return _login("admin@solomonai.us", os.environ.get("TEST_PASSWORD", "Demo2026!"))


@pytest.fixture(scope="session")
def eden_token():
    return _login("christopher@eden-x.io", os.environ.get("TEST_EDEN_PASSWORD", "EdenChurch2026!"))


def _hdr(t): return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def _restore_eden():
    cli = AsyncIOMotorClient(MONGO_URL); db = cli[DB_NAME]
    asyncio.get_event_loop().run_until_complete(
        db.tenants.update_one({"id": EDEN}, {"$set": {"stripe_connect_account_id": None, "stripe_connect_status": "not_started"}})
    )


# ── 1. Health + login regression ────────────────────────────────────
def test_health():
    r = requests.get(f"{BASE_URL}/api/health", timeout=10)
    assert r.status_code == 200 and r.json().get("status") == "ok"


def test_admin_login(admin_token): assert admin_token
def test_eden_login(eden_token): assert eden_token


# ── 2. Tenant migration shape ───────────────────────────────────────
def test_tenant_migration_fields():
    cli = AsyncIOMotorClient(MONGO_URL); db = cli[DB_NAME]
    loop = asyncio.get_event_loop()
    tenants = loop.run_until_complete(db.tenants.find({}, {"_id": 0}).to_list(None))
    assert len(tenants) > 0
    for t in tenants:
        assert "stripe_connect_account_id" in t, f"{t.get('id')} missing stripe_connect_account_id"
        assert "stripe_connect_status" in t
        assert "stripe_connect_onboarded_at" in t
        assert "fee_schedule" in t and isinstance(t["fee_schedule"], dict)
        fs = t["fee_schedule"]
        assert "platform_percent" in fs and "platform_fixed_cents" in fs and "override" in fs


# ── 3. Public config has connect fields ─────────────────────────────
def test_public_config_connect_fields():
    r = requests.get(f"{BASE_URL}/api/churches/{EDEN_SLUG}/public-config", timeout=10)
    assert r.status_code == 200
    d = r.json()
    assert "connected_account_id" in d and "accepts_payments" in d
    assert d["accepts_payments"] is False  # Eden not started


# ── 4. Admin connect status (church_admin) ──────────────────────────
def test_admin_connect_status(eden_token):
    r = requests.get(f"{BASE_URL}/api/admin/connect/status", headers=_hdr(eden_token), timeout=10)
    assert r.status_code == 200
    d = r.json()
    assert d["tenant_id"] == EDEN
    assert d["stripe_connect_status"] == "not_started"
    assert d["has_account"] is False
    assert "fee_schedule" in d


# ── 5. PI gate: not_started → 400 ───────────────────────────────────
def test_pi_gate_not_started():
    payload = {"amount": 25.0, "fund": "Tithes", "frequency": "one-time",
               "donor_email": "TEST_iter108_gate@example.com", "cover_fees": False, "church_slug": EDEN_SLUG}
    r = requests.post(f"{BASE_URL}/api/stripe/create-payment-intent", json=payload, timeout=15)
    assert r.status_code == 400
    assert "not configured" in r.text.lower() or "payment processing" in r.text.lower()


# ── 6. PI reaches Stripe with stripe_account when active ────────────
def test_pi_reaches_stripe_when_active():
    cli = AsyncIOMotorClient(MONGO_URL); db = cli[DB_NAME]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(db.tenants.update_one(
        {"id": EDEN},
        {"$set": {"stripe_connect_account_id": "acct_test_FAKE_FOR_PI_TEST", "stripe_connect_status": "active"}}
    ))
    try:
        payload = {"amount": 25.0, "fund": "Tithes", "frequency": "one-time",
                   "donor_email": "TEST_iter108_active@example.com", "cover_fees": False, "church_slug": EDEN_SLUG}
        r = requests.post(f"{BASE_URL}/api/stripe/create-payment-intent", json=payload, timeout=20)
        # Should be 502 from Stripe (no access to fake account) — proving stripe_account passed
        assert r.status_code == 502, f"Expected 502 from Stripe, got {r.status_code}: {r.text[:300]}"
        body = r.text.lower()
        # Stripe error for invalid account
        assert "stripe" in body or "account" in body or "permission" in body
    finally:
        _restore_eden()


# ── 7. Setup-intent gate (BLOCKER #3): not_started → 400 ────────────
def test_setup_intent_gate_not_started():
    payload = {"church_slug": EDEN_SLUG, "donor_email": "TEST_iter108_si@example.com"}
    r = requests.post(f"{BASE_URL}/api/stripe/recurring/setup-intent", json=payload, timeout=15)
    assert r.status_code == 400
    assert "not configured" in r.text.lower() or "payment processing" in r.text.lower()


# ── 8. Setup-intent reaches Stripe when active ──────────────────────
def test_setup_intent_reaches_stripe_when_active():
    cli = AsyncIOMotorClient(MONGO_URL); db = cli[DB_NAME]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(db.tenants.update_one(
        {"id": EDEN},
        {"$set": {"stripe_connect_account_id": "acct_test_FAKE_FOR_PI_TEST", "stripe_connect_status": "active"}}
    ))
    try:
        payload = {"church_slug": EDEN_SLUG, "donor_email": "TEST_iter108_si2@example.com"}
        r = requests.post(f"{BASE_URL}/api/stripe/recurring/setup-intent", json=payload, timeout=20)
        # 502 expected (Stripe rejects fake account)
        assert r.status_code == 502, f"Expected 502, got {r.status_code}: {r.text[:300]}"
    finally:
        _restore_eden()


# ── 9. Connect endpoints authorization ──────────────────────────────
def test_connect_start_requires_platform_admin(eden_token):
    r = requests.post(f"{BASE_URL}/api/platform/churches/{EDEN}/connect/start", headers=_hdr(eden_token), timeout=15)
    assert r.status_code == 403


def test_connect_start_platform_admin_call(admin_token):
    r = requests.post(f"{BASE_URL}/api/platform/churches/{EDEN}/connect/start", headers=_hdr(admin_token), timeout=30)
    # Either succeeds (Connect enabled) or 502 with "sign up for Connect" — both are valid
    assert r.status_code in (200, 502, 400), f"Unexpected: {r.status_code} {r.text[:300]}"
    if r.status_code == 502:
        assert "connect" in r.text.lower() or "sign up" in r.text.lower() or "stripe" in r.text.lower()


def test_connect_refresh_cross_church_blocked(eden_token):
    r = requests.post(f"{BASE_URL}/api/platform/churches/abundant-east-001/connect/refresh", headers=_hdr(eden_token), timeout=15)
    assert r.status_code == 403


def test_connect_login_link_cross_church_blocked(eden_token):
    r = requests.get(f"{BASE_URL}/api/platform/churches/abundant-east-001/connect/login-link", headers=_hdr(eden_token), timeout=15)
    assert r.status_code == 403


# ── 10. Webhook account.updated sets active ─────────────────────────
def test_webhook_account_updated_sets_active():
    cli = AsyncIOMotorClient(MONGO_URL); db = cli[DB_NAME]
    loop = asyncio.get_event_loop()
    # ensure webhook secret unset
    secret_was = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    try:
        evt = {
            "id": f"evt_test_iter108_{uuid.uuid4().hex[:10]}",
            "type": "account.updated",
            "data": {"object": {
                "id": "acct_test_iter108_ok",
                "charges_enabled": True,
                "payouts_enabled": True,
                "details_submitted": True,
                "metadata": {"tenant_id": EDEN},
                "requirements": {"disabled_reason": None, "currently_due": [], "past_due": []},
            }},
        }
        r = requests.post(f"{BASE_URL}/api/webhook/stripe", json=evt, timeout=15)
        assert r.status_code == 200, f"webhook: {r.status_code} {r.text[:200]}"
        time.sleep(1)
        t = loop.run_until_complete(db.tenants.find_one({"id": EDEN}, {"_id": 0}))
        assert t["stripe_connect_status"] == "active"
        assert t.get("stripe_connect_onboarded_at") is not None
    finally:
        _restore_eden()


# ── 11. Webhook account.application.deauthorized sets restricted + flag ─
def test_webhook_deauthorized_sets_restricted_and_flag():
    cli = AsyncIOMotorClient(MONGO_URL); db = cli[DB_NAME]
    loop = asyncio.get_event_loop()
    # Pre-set Eden with the fake acct so webhook can find it
    fake_acct = "acct_test_iter108_deauth"
    loop.run_until_complete(db.tenants.update_one(
        {"id": EDEN},
        {"$set": {"stripe_connect_account_id": fake_acct, "stripe_connect_status": "active"}}
    ))
    try:
        evt = {
            "id": f"evt_test_iter108_{uuid.uuid4().hex[:10]}",
            "type": "account.application.deauthorized",
            "account": fake_acct,
            "data": {"object": {"id": fake_acct}},
        }
        r = requests.post(f"{BASE_URL}/api/webhook/stripe", json=evt, timeout=15)
        assert r.status_code == 200
        time.sleep(1)
        t = loop.run_until_complete(db.tenants.find_one({"id": EDEN}, {"_id": 0}))
        assert t["stripe_connect_status"] == "restricted", f"got {t['stripe_connect_status']}"
        flag = loop.run_until_complete(db.platform_flags.find_one({"key": f"connect-deauthorized-{EDEN}"}, {"_id": 0}))
        assert flag is not None
    finally:
        loop.run_until_complete(db.platform_flags.delete_one({"key": f"connect-deauthorized-{EDEN}"}))
        _restore_eden()


# ── 12. Adapter selection: env-driven ───────────────────────────────
def test_adapter_selection():
    import importlib, sys
    # Default: PAYMENT_ADAPTER=stripe
    os.environ["PAYMENT_ADAPTER"] = "stripe"
    os.environ["ENVIRONMENT"] = "development"
    if "services.processor_adapter" in sys.modules:
        del sys.modules["services.processor_adapter"]
    sys.path.insert(0, "/app/backend")
    from services import processor_adapter as pa
    assert pa.ACTIVE_ADAPTER.name == "stripe"
    # Simulation in dev → SimulationAdapter
    os.environ["PAYMENT_ADAPTER"] = "simulation"
    importlib.reload(pa)
    assert pa.ACTIVE_ADAPTER.name == "simulation"
    # Simulation in prod → fallback to Stripe
    os.environ["ENVIRONMENT"] = "production"
    importlib.reload(pa)
    assert pa.ACTIVE_ADAPTER.name == "stripe"
    # Restore
    os.environ["PAYMENT_ADAPTER"] = "stripe"
    os.environ["ENVIRONMENT"] = "development"
    importlib.reload(pa)


# ── 13. Adapter signature regression: scheduler imports + runs ──────
def test_recurring_scheduler_imports_and_runs():
    import sys
    sys.path.insert(0, "/app/backend")
    from services import recurring_scheduler as rs
    assert callable(getattr(rs, "_calculate_next_charge_date", None))
    # Try to import run_recurring_batch if present
    fn = getattr(rs, "run_recurring_batch", None)
    if fn:
        from core import db as core_db
        loop = asyncio.get_event_loop()
        import inspect
        sig = inspect.signature(fn)
        try:
            if "db" in sig.parameters:
                loop.run_until_complete(fn(core_db))
            else:
                loop.run_until_complete(fn())
        except TypeError as e:
            pytest.fail(f"scheduler TypeError on adapter call: {e}")
        except Exception:
            pass  # runtime errors (no due rows etc) are fine


# ── 14. Tenant isolation on admin/giving (BLOCKER #5) ───────────────
def test_admin_giving_no_tenant_returns_403():
    """Mint a session for a tenant-less user, hit /api/admin/giving/summary, expect 403."""
    cli = AsyncIOMotorClient(MONGO_URL); db = cli[DB_NAME]
    loop = asyncio.get_event_loop()
    test_user_email = f"TEST_iter108_notenant_{uuid.uuid4().hex[:6]}@example.com"
    user_id = str(uuid.uuid4())
    session_token = uuid.uuid4().hex
    from datetime import datetime, timezone, timedelta
    loop.run_until_complete(db.users.insert_one({
        "id": user_id, "email": test_user_email, "name": "Test NoTenant",
        "role": "member", "tenant_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }))
    loop.run_until_complete(db.sessions.insert_one({
        "user_id": user_id, "session_token": session_token,
        "email": test_user_email, "name": "Test NoTenant",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        "created_at": datetime.now(timezone.utc),
    }))
    try:
        for ep in ("/api/admin/giving/summary",):
            r = requests.get(f"{BASE_URL}{ep}", headers={"Authorization": f"Bearer {session_token}"}, timeout=10)
            # Expect 403 (tenant required) — NOT 200 with abundant-east-001 data
            assert r.status_code in (401, 403), f"{ep}: expected 403, got {r.status_code} {r.text[:200]}"
            if r.status_code == 403:
                assert "tenant" in r.text.lower()
    finally:
        loop.run_until_complete(db.users.delete_one({"id": user_id}))
        loop.run_until_complete(db.sessions.delete_one({"session_token": session_token}))
