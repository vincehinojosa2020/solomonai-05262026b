"""Iteration 105 — DELETE /api/platform/churches/{tenant_id} (cascading) + platform_stats_cache.updated_at.

Tests:
  AUTH    : 401 unauth, 403 for church_admin
  404     : non-existent tenant_id
  PROTECT : eden-church-001 → 400 'protected'
  DRY-RUN : create fresh tenant → ?dry_run=true returns would_delete plan, tenant still exists
  DELETE  : real delete cleans tenants, users, dashboard_stats_cache, user_sessions
  CACHE   : after delete, tenant drops from platform_stats_cache.campus_breakdown and updated_at
            ISO string is refreshed
  AUDIT   : audit_log gets church_deleted entry
  REGRESS : GET /api/platform/churches still lists Eden connected with ~$102,
            Competitive Intel seed/pin/digest still work, POST churches/create still refreshes cache.
"""
import os
import time
import uuid
from datetime import datetime

import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient


def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        with open("/app/frontend/.env") as fh:
            for line in fh:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    url = line.split("=", 1)[1].strip()
                    break
    assert url, "REACT_APP_BACKEND_URL not set"
    return url.rstrip("/")


def _load_mongo():
    url, name = None, None
    with open("/app/backend/.env") as fh:
        for line in fh:
            if line.startswith("MONGO_URL="):
                url = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("DB_NAME="):
                name = line.split("=", 1)[1].strip().strip('"')
    return url, name


BASE_URL = _load_backend_url()
ADMIN_EMAIL = "admin@solomonai.us"
ADMIN_PASSWORD = "Demo2026!"
CHURCH_ADMIN_EMAIL = "christopher@eden-x.io"
CHURCH_ADMIN_PASSWORD = "EdenChurch2026!"
MONGO_URL, DB_NAME = _load_mongo()


def _login(email: str, password: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": email, "password": password}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"Login failed for {email}: {r.status_code} {r.text[:200]}")
    token = r.json().get("session_token") or r.json().get("token")
    assert token, f"No token in login response: {r.json()}"
    s.headers.update({"Authorization": f"Bearer {token}"})
    s.cookies.set("session_token", token)
    return s


@pytest.fixture(scope="module")
def admin_session():
    return _login(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def church_admin_session():
    return _login(CHURCH_ADMIN_EMAIL, CHURCH_ADMIN_PASSWORD)


_CREATED_TENANTS: list[str] = []


def _create_tenant(admin_session) -> tuple[str, str, str]:
    """Returns (tenant_id, subdomain, admin_email)."""
    unique = uuid.uuid4().hex[:8]
    subdomain = f"del-test-{unique}"
    admin_email = f"del-test-{unique}@example.com"
    payload = {
        "name": f"Delete Test Church {unique}",
        "subdomain": subdomain,
        "admin_email": admin_email,
        "admin_name": "Del Admin",
        "admin_password": "Demo2026!",
        "city": "Del City",
        "state": "CA",
    }
    r = admin_session.post(f"{BASE_URL}/api/platform/churches/create",
                           json=payload, timeout=30)
    assert r.status_code in (200, 201), f"Onboarding failed: {r.status_code} {r.text[:300]}"
    tid = r.json().get("tenant_id")
    assert tid
    _CREATED_TENANTS.append(tid)
    return tid, subdomain, admin_email


# ─── AUTH ────────────────────────────────────────────────────────────────
class TestAuth:
    def test_unauthenticated_returns_401(self):
        r = requests.delete(f"{BASE_URL}/api/platform/churches/some-tenant-x", timeout=15)
        assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text[:200]}"

    def test_church_admin_returns_403(self, church_admin_session):
        # Use a non-protected tenant id so it doesn't short-circuit on 400 protection.
        r = church_admin_session.delete(f"{BASE_URL}/api/platform/churches/nonexistent-xyz", timeout=15)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text[:200]}"


# ─── 404 ──────────────────────────────────────────────────────────────────
class TestNotFound:
    def test_nonexistent_tenant_returns_404(self, admin_session):
        tid = f"definitely-missing-{uuid.uuid4().hex[:6]}"
        r = admin_session.delete(f"{BASE_URL}/api/platform/churches/{tid}", timeout=15)
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text[:200]}"
        assert "not found" in r.json().get("detail", "").lower()


# ─── PROTECTED ────────────────────────────────────────────────────────────
class TestProtected:
    def test_eden_church_protected(self, admin_session):
        r = admin_session.delete(f"{BASE_URL}/api/platform/churches/eden-church-001", timeout=15)
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text[:200]}"
        detail = r.json().get("detail", "").lower()
        assert "protect" in detail, f"Expected 'protected' in detail, got: {detail}"

    def test_eden_church_still_exists(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/platform/churches", timeout=20)
        assert r.status_code == 200
        churches = r.json() if isinstance(r.json(), list) else r.json().get("churches", [])
        eden = next((c for c in churches if c.get("tenant_id") == "eden-church-001"
                     or c.get("id") == "eden-church-001"), None)
        assert eden is not None, "Eden church vanished after protection test!"


# ─── DRY RUN ──────────────────────────────────────────────────────────────
class TestDryRun:
    def test_dry_run_returns_plan_without_delete(self, admin_session):
        tid, _, _ = _create_tenant(admin_session)

        r = admin_session.delete(f"{BASE_URL}/api/platform/churches/{tid}?dry_run=true", timeout=20)
        assert r.status_code == 200, f"Dry run failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        assert body.get("dry_run") is True
        assert body.get("tenant_id") == tid
        assert "name" in body
        wd = body.get("would_delete")
        assert isinstance(wd, dict) and wd, f"would_delete empty/invalid: {wd}"
        assert wd.get("tenants") == 1, f"tenants count should be 1, got {wd.get('tenants')}"
        assert wd.get("users", 0) >= 1, f"users count should be >=1 for new tenant, got {wd.get('users')}"

        # Tenant must still exist
        r2 = admin_session.get(f"{BASE_URL}/api/platform/churches", timeout=20)
        churches = r2.json() if isinstance(r2.json(), list) else r2.json().get("churches", [])
        found = any(c.get("tenant_id") == tid or c.get("id") == tid for c in churches)
        assert found, "Tenant disappeared after dry_run!"


# ─── REAL DELETE + CACHE + AUDIT ──────────────────────────────────────────
class TestRealDeleteAndCache:
    def test_real_delete_cascades_and_refreshes_cache(self, admin_session):
        # Capture cache updated_at before
        pre_stats = admin_session.get(f"{BASE_URL}/api/platform/stats", timeout=20).json()
        pre_updated_at = pre_stats.get("updated_at")
        # Even if None pre-fix, we just care about the post value being a populated ISO string.

        tid, _, admin_email = _create_tenant(admin_session)

        # Wait for background cache rebuild from create (retry up to ~30s)
        pre_tids: set = set()
        cb_stats: dict = {}
        for _ in range(6):
            time.sleep(5)
            cb_stats = admin_session.get(f"{BASE_URL}/api/platform/stats", timeout=20).json()
            cb = cb_stats.get("campus_breakdown", [])
            pre_tids = {row.get("tenant_id") or row.get("id") or row.get("campus_id") for row in cb}
            if tid in pre_tids:
                break
        assert tid in pre_tids, f"New tenant {tid} not in campus_breakdown after ~30s: {pre_tids}"
        pre_delete_updated_at = cb_stats.get("updated_at")

        # Real delete
        r = admin_session.delete(f"{BASE_URL}/api/platform/churches/{tid}", timeout=30)
        assert r.status_code == 200, f"Delete failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        assert body.get("success") is True
        assert body.get("tenant_id") == tid
        assert "name" in body
        deleted = body.get("deleted")
        assert isinstance(deleted, dict) and deleted
        assert deleted.get("tenants") == 1
        assert deleted.get("users", 0) >= 1
        # Remove from cleanup list so we don't double-delete
        if tid in _CREATED_TENANTS:
            _CREATED_TENANTS.remove(tid)

        # Verify Mongo — tenant, users, dashboard_stats_cache gone
        client = AsyncIOMotorClient(MONGO_URL)
        try:
            db = client[DB_NAME]
            import asyncio

            async def _check():
                tenant_doc = await db.tenants.find_one({"id": tid}, {"_id": 0})
                users_count = await db.users.count_documents({"tenant_id": tid})
                dash_count = await db.dashboard_stats_cache.count_documents({"tenant_id": tid})
                sess_count = await db.user_sessions.count_documents({"tenant_id": tid})
                audit = await db.audit_log.find_one(
                    {"action": "church_deleted", "tenant_id": tid}, {"_id": 0}
                )
                return tenant_doc, users_count, dash_count, sess_count, audit

            tenant_doc, users_count, dash_count, sess_count, audit = asyncio.get_event_loop().run_until_complete(_check())
            assert tenant_doc is None, f"tenant doc still present: {tenant_doc}"
            assert users_count == 0, f"users for tenant still present: {users_count}"
            assert dash_count == 0, f"dashboard_stats_cache rows still present: {dash_count}"
            assert sess_count == 0, f"user_sessions rows still present: {sess_count}"
            assert audit is not None, "audit_log missing church_deleted entry"
        finally:
            client.close()

        # Wait for background cache rebuild
        time.sleep(12)

        # Tenant gone from campus_breakdown and updated_at refreshed
        post_stats = admin_session.get(f"{BASE_URL}/api/platform/stats", timeout=20).json()
        cb_after = post_stats.get("campus_breakdown", [])
        post_tids = {row.get("tenant_id") or row.get("id") or row.get("campus_id") for row in cb_after}
        assert tid not in post_tids, f"Deleted tenant {tid} still in campus_breakdown: {post_tids}"

        post_updated_at = post_stats.get("updated_at")
        assert post_updated_at, f"updated_at missing/empty on platform_stats_cache: {post_updated_at!r}"
        # Must be parseable ISO timestamp
        parsed = datetime.fromisoformat(post_updated_at.replace("Z", "+00:00"))
        assert parsed is not None

        # If pre_delete_updated_at was present & ISO, post must be >=
        if pre_delete_updated_at:
            try:
                pre_parsed = datetime.fromisoformat(pre_delete_updated_at.replace("Z", "+00:00"))
                assert parsed >= pre_parsed, \
                    f"updated_at did not advance: pre={pre_delete_updated_at} post={post_updated_at}"
            except ValueError:
                pass  # pre couldn't parse, accept post-only


# ─── REGRESSIONS ──────────────────────────────────────────────────────────
class TestRegressions:
    def test_eden_church_connected_with_total(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/platform/churches", timeout=20)
        assert r.status_code == 200
        data = r.json()
        churches = data if isinstance(data, list) else data.get("churches", [])
        assert len(churches) >= 1, f"No churches returned: {data}"
        eden = next((c for c in churches if c.get("tenant_id") == "eden-church-001"
                     or c.get("id") == "eden-church-001"), None)
        assert eden is not None, f"Eden not found. tenants: {[c.get('tenant_id') or c.get('id') for c in churches]}"
        status = eden.get("stripe_status") or eden.get("status")
        assert status == "connected", f"Eden not connected: {eden}"
        total = eden.get("stripe_total_processed") or eden.get("total_processed") or 0
        # ~$102 (10200 cents). Accept either cents or dollars representation.
        assert total in range(10000, 10500) or (100 <= total <= 105), \
            f"Eden total not ~$102 (got {total})"

    def test_competitive_intel_digest(self, admin_session):
        # Seed catalog (idempotent)
        sr = admin_session.post(f"{BASE_URL}/api/admin/competitive/seed", timeout=30)
        assert sr.status_code == 200, f"Seed failed: {sr.status_code} {sr.text[:200]}"

        # Ensure at least one pin exists so digest has a target
        rank = 21
        pin = admin_session.post(f"{BASE_URL}/api/admin/competitive/pins",
                                 json={"rank": rank}, timeout=20)
        assert pin.status_code in (200, 201, 409), f"Pin failed: {pin.status_code} {pin.text[:200]}"

        # Generate digest (Claude call — allow up to 60s)
        r = admin_session.post(f"{BASE_URL}/api/admin/competitive/digest",
                               json={"rank": rank}, timeout=90)
        assert r.status_code == 200, f"Digest failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        digest = body.get("digest", "")
        assert len(digest) >= 200, f"Digest too short: {len(digest)} chars"
        # Clean up pin to leave state neutral
        admin_session.delete(f"{BASE_URL}/api/admin/competitive/pins/{rank}", timeout=15)

    def test_create_still_refreshes_cache(self, admin_session):
        """Regression: POST /api/platform/churches/create still auto-refreshes cache."""
        tid, _, _ = _create_tenant(admin_session)
        time.sleep(10)
        r = admin_session.get(f"{BASE_URL}/api/platform/stats", timeout=20)
        assert r.status_code == 200
        cb = r.json().get("campus_breakdown", [])
        tids = {row.get("tenant_id") or row.get("id") or row.get("campus_id") for row in cb}
        assert tid in tids, f"Fresh tenant {tid} not in breakdown after onboarding+10s"


# ─── CLEANUP ──────────────────────────────────────────────────────────────
def test_zz_cleanup_via_delete_endpoint():
    """Dogfood the DELETE endpoint by cleaning up any tenants we created."""
    if not _CREATED_TENANTS:
        return
    s = _login(ADMIN_EMAIL, ADMIN_PASSWORD)
    for tid in list(_CREATED_TENANTS):
        try:
            r = s.delete(f"{BASE_URL}/api/platform/churches/{tid}", timeout=30)
            if r.status_code == 200:
                _CREATED_TENANTS.remove(tid)
        except Exception as e:
            print(f"cleanup {tid} failed: {e}")
    assert not _CREATED_TENANTS, f"Tenants not cleaned: {_CREATED_TENANTS}"
