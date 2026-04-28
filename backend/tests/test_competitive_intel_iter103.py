"""Iteration 103 — Competitive Intel module + cache auto-refresh regression.

Scope:
1. POST /api/admin/competitive/seed — idempotent, platform_admin only
2. GET  /api/admin/competitive/top-churches — filters q, vendor
3. POST /api/admin/competitive/pins — pin rank=21 (Potter's House), 409 on dup, 400 at limit
4. GET  /api/admin/competitive/pins — returns pin + attached church
5. DELETE /api/admin/competitive/pins/{rank}
6. POST /api/admin/competitive/digest — Claude-generated ≥200 chars, required sections
7. Cache auto-refresh after church onboarding — tenant visible in /api/platform/churches
"""
import os
import time
import uuid

import pytest
import requests

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        try:
            with open("/app/frontend/.env") as fh:
                for line in fh:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip()
                        break
        except Exception:
            pass
    assert url, "REACT_APP_BACKEND_URL not set"
    return url.rstrip("/")


BASE_URL = _load_backend_url()
ADMIN_EMAIL = "admin@solomonai.us"
ADMIN_PASSWORD = os.environ.get("TEST_PASSWORD", "Demo2026!")


# ─── Fixtures ──────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text[:200]}")
    data = r.json()
    token = data.get("session_token") or data.get("token")
    assert token, f"No session token in login response: {data}"
    s.headers.update({"Authorization": f"Bearer {token}"})
    # Some backends rely on cookie-session; set both
    s.cookies.set("session_token", token)
    return s


@pytest.fixture(scope="module")
def anon_session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ─── 1. Seed (idempotent, admin-only) ──────────────────────────────────────
class TestSeedCatalog:
    def test_seed_requires_auth(self, anon_session):
        r = anon_session.post(f"{BASE_URL}/api/admin/competitive/seed")
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"

    def test_seed_idempotent(self, admin_session):
        r1 = admin_session.post(f"{BASE_URL}/api/admin/competitive/seed")
        assert r1.status_code == 200, r1.text
        d1 = r1.json()
        assert "seeded" in d1 and "total_in_catalog" in d1
        assert d1["seeded"] == 80
        assert d1["total_in_catalog"] >= 80

        # Call again — must not duplicate
        r2 = admin_session.post(f"{BASE_URL}/api/admin/competitive/seed")
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["total_in_catalog"] == d1["total_in_catalog"], "Seed should be idempotent"


# ─── 2. Top-churches (search + vendor filter) ──────────────────────────────
class TestTopChurches:
    def test_default_list(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/competitive/top-churches?limit=5")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data and "churches" in data and "vendors" in data
        assert data["total"] >= 80
        assert len(data["churches"]) == 5
        # churches sorted by rank asc
        ranks = [c["rank"] for c in data["churches"]]
        assert ranks == sorted(ranks)
        # vendor breakdown
        assert isinstance(data["vendors"], list) and len(data["vendors"]) > 0
        assert all("name" in v and "count" in v for v in data["vendors"])

    def test_filter_by_q(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/competitive/top-churches?q=church&limit=200")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        # Every returned row should match q in name/city/state (case-insensitive)
        for c in data["churches"]:
            blob = f"{c.get('name','')} {c.get('city','')} {c.get('state','')}".lower()
            assert "church" in blob, f"Row {c['rank']} does not match q=church: {blob}"

    def test_filter_by_vendor(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/competitive/top-churches?vendor=Pushpay&limit=200")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        for c in data["churches"]:
            assert c.get("vendor") == "Pushpay"


# ─── 3. Pins (CRUD + limits) ───────────────────────────────────────────────
class TestPins:
    RANK = 21  # Potter's House

    def _cleanup(self, session, rank):
        session.delete(f"{BASE_URL}/api/admin/competitive/pins/{rank}")

    def test_pin_and_list(self, admin_session):
        # Ensure clean slate for rank=21
        self._cleanup(admin_session, self.RANK)

        r = admin_session.post(f"{BASE_URL}/api/admin/competitive/pins", json={"rank": self.RANK})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["church"]["rank"] == self.RANK
        assert "Potter" in body["church"]["name"]

        # List includes it with attached catalog entry
        lr = admin_session.get(f"{BASE_URL}/api/admin/competitive/pins")
        assert lr.status_code == 200
        pins = lr.json()["pins"]
        target = [p for p in pins if p["rank"] == self.RANK]
        assert len(target) == 1
        assert target[0]["church"]["rank"] == self.RANK

    def test_pin_duplicate_409(self, admin_session):
        # rank=21 already pinned from previous test
        r = admin_session.post(f"{BASE_URL}/api/admin/competitive/pins", json={"rank": self.RANK})
        assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"

    def test_pin_limit_400(self, admin_session):
        # Check current pin count, fill up to 5, then attempt 6th → 400
        lr = admin_session.get(f"{BASE_URL}/api/admin/competitive/pins")
        pinned_ranks = {p["rank"] for p in lr.json()["pins"]}
        # pick additional ranks to reach 5 total
        fill_candidates = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        added = []
        for cand in fill_candidates:
            if len(pinned_ranks) >= 5:
                break
            if cand in pinned_ranks:
                continue
            rr = admin_session.post(f"{BASE_URL}/api/admin/competitive/pins", json={"rank": cand})
            if rr.status_code == 200:
                pinned_ranks.add(cand)
                added.append(cand)
        assert len(pinned_ranks) == 5, f"Could not reach 5 pins: {pinned_ranks}"

        # Try 6th
        sixth = next(c for c in fill_candidates if c not in pinned_ranks)
        r = admin_session.post(f"{BASE_URL}/api/admin/competitive/pins", json={"rank": sixth})
        assert r.status_code == 400, f"Expected 400 at pin-limit, got {r.status_code}: {r.text}"

        # cleanup extras we added
        for c in added:
            admin_session.delete(f"{BASE_URL}/api/admin/competitive/pins/{c}")

    def test_unpin(self, admin_session):
        r = admin_session.delete(f"{BASE_URL}/api/admin/competitive/pins/{self.RANK}")
        assert r.status_code == 200, r.text
        assert r.json().get("unpinned") == self.RANK
        # Verify gone
        lr = admin_session.get(f"{BASE_URL}/api/admin/competitive/pins")
        pins = lr.json()["pins"]
        assert not any(p["rank"] == self.RANK for p in pins)


# ─── 4. Claude digest ──────────────────────────────────────────────────────
class TestDigest:
    RANK = 21

    def test_digest_generation(self, admin_session):
        # Ensure pinned first
        admin_session.post(f"{BASE_URL}/api/admin/competitive/pins", json={"rank": self.RANK})
        r = admin_session.post(
            f"{BASE_URL}/api/admin/competitive/digest",
            json={"rank": self.RANK},
            timeout=90,
        )
        assert r.status_code == 200, f"Digest failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        assert body["rank"] == self.RANK
        digest = body.get("digest", "")
        assert isinstance(digest, str) and len(digest) >= 200, f"Digest too short ({len(digest)} chars)"

        expected = [
            "Why this church matters",
            "weak spots",
            "differentiated pitch",
            "decision makers",
            "Best time",
            "Recommended next action",
        ]
        low = digest.lower()
        missing = [s for s in expected if s.lower() not in low]
        assert not missing, f"Digest missing sections: {missing}. Digest head: {digest[:500]}"

        # Persisted to pin
        lr = admin_session.get(f"{BASE_URL}/api/admin/competitive/pins")
        pin = next(p for p in lr.json()["pins"] if p["rank"] == self.RANK)
        assert pin.get("last_digest"), "Digest not persisted to pin.last_digest"

        # cleanup
        admin_session.delete(f"{BASE_URL}/api/admin/competitive/pins/{self.RANK}")


# ─── 5. Cache auto-refresh after church onboarding ─────────────────────────
class TestCacheAutoRefresh:
    def test_new_tenant_appears_in_cache(self, admin_session):
        unique = uuid.uuid4().hex[:8]
        payload = {
            "name": f"Cache Test Church {unique}",
            "subdomain": f"cache-test-{unique}",
            "admin_email": f"cache-{unique}@example.com",
            "admin_name": "Cache Test Admin",
            "admin_password": os.environ.get("TEST_PASSWORD", "Demo2026!"),
            "city": "Test City",
            "state": "CA",
        }
        r = admin_session.post(f"{BASE_URL}/api/platform/churches/create", json=payload, timeout=30)
        if r.status_code not in (200, 201):
            pytest.skip(f"Onboarding endpoint returned {r.status_code}: {r.text[:200]}")
        created_tenant_id = r.json().get("tenant_id")
        assert created_tenant_id, f"No tenant_id in response: {r.json()}"

        # Poll /api/platform/churches up to ~10s
        found = False
        for _ in range(10):
            time.sleep(1)
            lr = admin_session.get(f"{BASE_URL}/api/platform/churches", timeout=15)
            if lr.status_code != 200:
                continue
            data = lr.json()
            churches = data if isinstance(data, list) else data.get("churches", [])
            if any(c.get("tenant_id") == created_tenant_id or c.get("id") == created_tenant_id for c in churches):
                found = True
                break
        assert found, f"Newly onboarded tenant {created_tenant_id} did not appear in /api/platform/churches within 10s"

        # Also verify platform_stats_cache has the new tenant in campus_breakdown
        # NOTE: current implementation filters to tenants with dashboard_stats_cache.total_members>10
        # so a brand-new tenant may not show up until it has members. We still assert here per the
        # review request's expected cache auto-refresh behavior.
        sr = admin_session.get(f"{BASE_URL}/api/platform/stats", timeout=15)
        assert sr.status_code == 200
        stats = sr.json()
        cb = stats.get("campus_breakdown", [])
        in_cache = any(
            c.get("tenant_id") == created_tenant_id or c.get("id") == created_tenant_id
            for c in cb
        )
        if not in_cache:
            pytest.fail(
                f"platform_stats_cache.campus_breakdown missing new tenant {created_tenant_id}. "
                f"Root cause: _get_real_campuses_fast() filters to tenants with "
                f"dashboard_stats_cache.total_members>10; newly onboarded tenants have no such cache."
            )
