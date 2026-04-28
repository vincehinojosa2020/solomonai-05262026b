"""Backend tests for God Mode Prompts 1-4 (iteration 101)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://exec-metrics-hub.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@solomonai.us"
ADMIN_PASS = os.environ.get("TEST_PASSWORD", "Demo2026!")


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"no token in: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ---- /api/platform/churches must expose stripe_status, stripe_total_processed, stripe_txn_count
def test_platform_churches_has_stripe_fields(headers):
    r = requests.get(f"{BASE_URL}/api/platform/churches", headers=headers, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    items = body.get("data") or body.get("items") or body if isinstance(body, list) else body.get("churches", [])
    if isinstance(body, dict) and "data" in body:
        items = body["data"]
    assert isinstance(items, list) and len(items) > 0
    sample = items[0]
    for key in ("stripe_status", "stripe_total_processed", "stripe_txn_count"):
        assert key in sample, f"missing key {key} in {list(sample.keys())}"

    eden = next((c for c in items if (c.get("slug") == "eden-church" or "eden" in (c.get("name") or "").lower()
                                      or c.get("tenant_id") == "eden-church-001")), None)
    assert eden, "Eden Church not found"
    assert eden["stripe_status"] == "connected", f"Eden status: {eden['stripe_status']}"
    assert eden["stripe_total_processed"] > 0, f"Eden processed: {eden['stripe_total_processed']}"
    assert eden["stripe_txn_count"] >= 1

    other = next((c for c in items if c != eden and c.get("stripe_status") == "not_connected"), None)
    assert other, "expected at least one non-Eden church with not_connected"


# ---- /api/platform/stripe/transactions/recent
def test_stripe_transactions_recent(headers):
    r = requests.get(f"{BASE_URL}/api/platform/stripe/transactions/recent", headers=headers, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "data" in body, f"no data key: {body}"
    rows = body["data"]
    assert isinstance(rows, list) and len(rows) >= 1, f"expected >=1 Eden row: {rows}"
    row = rows[0]
    for key in ("amount_cents", "church_name", "donor_name", "fund", "donation_date", "church_slug"):
        assert key in row, f"missing {key} in {row}"


# ---- /api/platform/stripe/transactions/daily?days=30
def test_stripe_transactions_daily(headers):
    r = requests.get(f"{BASE_URL}/api/platform/stripe/transactions/daily?days=30", headers=headers, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "days" in body, body
    days = body["days"]
    assert isinstance(days, list) and len(days) == 30, f"got {len(days)}"
    d = days[0]
    for key in ("date", "count", "total_amount"):
        assert key in d, f"missing {key} in {d}"


# ---- /api/platform/stripe/transactions/stats
def test_stripe_transactions_stats(headers):
    r = requests.get(f"{BASE_URL}/api/platform/stripe/transactions/stats", headers=headers, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    for bucket in ("today", "this_week", "this_month", "all_time"):
        assert bucket in body, f"missing bucket {bucket}: {list(body.keys())}"
        b = body[bucket]
        for k in ("count", "total_amount", "solomon_revenue"):
            assert k in b, f"{bucket}: missing {k}"
    assert "active_churches" in body
    assert "total_donors" in body
