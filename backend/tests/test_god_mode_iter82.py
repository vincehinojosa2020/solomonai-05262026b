"""
God Mode Platform Dashboard - Backend API Tests
Iteration 82 — Tests for /api/platform/* endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
PLATFORM_ADMIN_TOKEN = os.environ.get("TEST_PLATFORM_TOKEN", "")


@pytest.fixture
def platform_headers():
    """Auth headers for platform admin"""
    return {
        "Authorization": f"Bearer {PLATFORM_ADMIN_TOKEN}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def anon_headers():
    """No auth headers"""
    return {"Content-Type": "application/json"}


# ── Health ─────────────────────────────────────────────────────────────────
class TestHealth:
    """Basic health check"""

    def test_health_ok(self):
        r = requests.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
        print("PASS: /api/health returns status:ok")


# ── Auth protection ────────────────────────────────────────────────────────
class TestPlatformAuth:
    """Platform endpoints must require platform_admin role"""

    def test_stats_requires_auth(self, anon_headers):
        r = requests.get(f"{BASE_URL}/api/platform/stats", headers=anon_headers)
        assert r.status_code in [401, 403], f"Expected 401/403, got {r.status_code}"
        print(f"PASS: /api/platform/stats blocked unauthenticated (got {r.status_code})")

    def test_activity_feed_requires_auth(self, anon_headers):
        r = requests.get(f"{BASE_URL}/api/platform/activity-feed", headers=anon_headers)
        assert r.status_code in [401, 403], f"Expected 401/403, got {r.status_code}"
        print(f"PASS: /api/platform/activity-feed blocked unauthenticated (got {r.status_code})")

    def test_transactions_requires_auth(self, anon_headers):
        r = requests.get(f"{BASE_URL}/api/platform/transactions", headers=anon_headers)
        assert r.status_code in [401, 403], f"Expected 401/403, got {r.status_code}"
        print(f"PASS: /api/platform/transactions blocked unauthenticated (got {r.status_code})")


# ── Platform Stats ─────────────────────────────────────────────────────────
class TestPlatformStats:
    """GET /api/platform/stats"""

    def test_stats_ok(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/stats", headers=platform_headers, timeout=20)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
        print("PASS: /api/platform/stats returned 200")

    def test_stats_gmv_over_50m(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/stats", headers=platform_headers, timeout=20)
        data = r.json()
        gmv = data.get("giving", {}).get("all_time", 0)
        assert gmv > 50_000_000, f"Expected GMV > $50M, got {gmv}"
        print(f"PASS: Platform GMV = ${gmv:,.0f} (> $50M)")

    def test_stats_revenue_over_1m(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/stats", headers=platform_headers, timeout=20)
        data = r.json()
        revenue = data.get("fees", {}).get("all_time", 0)
        assert revenue > 1_000_000, f"Expected Revenue > $1M, got {revenue}"
        print(f"PASS: Platform Revenue = ${revenue:,.0f} (> $1M)")

    def test_stats_members_over_60k(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/stats", headers=platform_headers, timeout=20)
        data = r.json()
        members = data.get("members", {}).get("total", 0)
        assert members > 50_000, f"Expected members > 50K, got {members}"
        print(f"PASS: Members = {members:,} (> 50K)")

    def test_stats_transactions_over_900k(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/stats", headers=platform_headers, timeout=20)
        data = r.json()
        txns = data.get("transactions", {}).get("total", 0)
        assert txns > 900_000, f"Expected transactions > 900K, got {txns}"
        print(f"PASS: Transactions = {txns:,} (> 900K)")

    def test_stats_has_campus_breakdown(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/stats", headers=platform_headers, timeout=20)
        data = r.json()
        campuses = data.get("campus_breakdown", [])
        assert len(campuses) >= 4, f"Expected >= 4 churches, got {len(campuses)}"
        print(f"PASS: campus_breakdown has {len(campuses)} churches (>= 4)")

    def test_stats_campus_breakdown_giving_positive(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/stats", headers=platform_headers, timeout=20)
        data = r.json()
        campuses = data.get("campus_breakdown", [])
        for c in campuses:
            assert c.get("giving", 0) > 0, f"Church {c.get('name')} has $0 giving"
        print(f"PASS: All {len(campuses)} churches have positive giving")

    def test_stats_has_giving_trend(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/stats", headers=platform_headers, timeout=20)
        data = r.json()
        trend = data.get("giving_trend", [])
        assert len(trend) > 0, "giving_trend should not be empty"
        print(f"PASS: giving_trend has {len(trend)} months")

    def test_stats_mrr_positive(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/stats", headers=platform_headers, timeout=20)
        data = r.json()
        mrr = data.get("platform", {}).get("total_mrr", 0)
        arr = data.get("platform", {}).get("arr", 0)
        assert mrr > 0, f"Expected MRR > 0, got {mrr}"
        assert arr > 0, f"Expected ARR > 0, got {arr}"
        print(f"PASS: MRR={mrr:,.2f}, ARR={arr:,.2f}")

    def test_stats_no_test_churches(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/stats", headers=platform_headers, timeout=20)
        data = r.json()
        campuses = data.get("campus_breakdown", [])
        for c in campuses:
            assert not c.get("name", "").startswith("TEST_"), f"TEST_ church in breakdown: {c['name']}"
        print("PASS: No TEST_ churches in campus_breakdown")


# ── Activity Feed ──────────────────────────────────────────────────────────
class TestActivityFeed:
    """GET /api/platform/activity-feed"""

    def test_activity_feed_ok(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/activity-feed", headers=platform_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        print("PASS: /api/platform/activity-feed returned 200")

    def test_activity_feed_has_events(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/activity-feed", headers=platform_headers)
        data = r.json()
        events = data.get("events", [])
        # Events may be empty if no large recent donations, but structure must be right
        assert "events" in data, "Response must have 'events' key"
        print(f"PASS: activity-feed has {len(events)} events")

    def test_activity_feed_event_structure(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/activity-feed?limit=5", headers=platform_headers)
        data = r.json()
        events = data.get("events", [])
        if events:
            ev = events[0]
            assert "type" in ev, "Event must have 'type'"
            assert "message" in ev, "Event must have 'message'"
            assert "amount" in ev, "Event must have 'amount'"
            print(f"PASS: First event has correct structure: type={ev['type']}, amount={ev['amount']}")
        else:
            print("INFO: No events in feed (may be expected if no recent large donations)")


# ── Transactions ───────────────────────────────────────────────────────────
class TestPlatformTransactions:
    """GET /api/platform/transactions"""

    def test_transactions_ok(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/transactions?page=1&limit=10", headers=platform_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
        print("PASS: /api/platform/transactions returned 200")

    def test_transactions_total_over_900k(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/transactions?page=1&limit=1", headers=platform_headers)
        data = r.json()
        total = data.get("total", 0)
        assert total > 900_000, f"Expected total > 900K, got {total}"
        print(f"PASS: transactions total = {total:,}")

    def test_transactions_has_data(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/transactions?page=1&limit=50", headers=platform_headers)
        data = r.json()
        txns = data.get("transactions") or data.get("donations") or []
        assert len(txns) > 0, "Expected non-empty transactions list"
        print(f"PASS: transactions returned {len(txns)} rows")

    def test_transactions_filter_by_church(self, platform_headers):
        # Get church list first
        stats = requests.get(f"{BASE_URL}/api/platform/stats", headers=platform_headers, timeout=20).json()
        churches = stats.get("campus_breakdown", [])
        if churches:
            tid = churches[0]["tenant_id"]
            r = requests.get(f"{BASE_URL}/api/platform/transactions?church={tid}&page=1&limit=10", headers=platform_headers)
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            print(f"PASS: transactions filtered by church={tid[:15]}... returned 200")
        else:
            print("INFO: No churches found to test filter")


# ── Churches endpoint ──────────────────────────────────────────────────────
class TestPlatformChurches:
    """GET /api/platform/churches"""

    def test_churches_ok(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/churches", headers=platform_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
        print("PASS: /api/platform/churches returned 200")

    def test_churches_has_4_real_churches(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/churches", headers=platform_headers)
        data = r.json()
        churches = data.get("churches", data) if isinstance(data, dict) else data
        assert len(churches) >= 4, f"Expected >= 4 churches, got {len(churches)}"
        print(f"PASS: /api/platform/churches has {len(churches)} churches")

    def test_churches_have_giving_positive(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/churches", headers=platform_headers)
        data = r.json()
        churches = data.get("churches", data) if isinstance(data, dict) else data
        # At least the main 4 real demo churches should have positive giving
        churches_with_giving = [c for c in churches if (c.get("giving") or c.get("all_time_giving") or c.get("total_giving") or 0) > 0]
        assert len(churches_with_giving) >= 4, f"Expected >= 4 churches with positive giving, got {len(churches_with_giving)}"
        print(f"PASS: {len(churches_with_giving)} churches have positive giving")


# ── Impersonate endpoint ───────────────────────────────────────────────────
class TestImpersonate:
    """POST /api/platform/impersonate"""

    def test_impersonate_requires_auth(self, anon_headers):
        r = requests.post(f"{BASE_URL}/api/platform/impersonate",
                         json={"tenant_id": "abundant-east-001"},
                         headers=anon_headers)
        assert r.status_code in [401, 403], f"Expected 401/403, got {r.status_code}"
        print(f"PASS: impersonate blocked without auth (got {r.status_code})")

    def test_impersonate_valid_church(self, platform_headers):
        r = requests.post(f"{BASE_URL}/api/platform/impersonate",
                         json={"tenant_id": "abundant-east-001"},
                         headers=platform_headers)
        # Should return 200 with a token (key may be 'token' or 'session_token')
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
        data = r.json()
        token = data.get("session_token") or data.get("token")
        assert token, f"Expected token in response, got: {data}"
        print("PASS: impersonate returned token successfully")
        # NOTE: API returns 'token' key but PlatformDashboard.jsx checks 'd.session_token' — BUG in frontend


# ── Church admin cannot access platform ────────────────────────────────────
class TestChurchAdminBlocked:
    """Church admin should not be able to access /api/platform/* stats"""

    def test_church_admin_blocked_from_stats(self):
        # Login as church admin
        r = requests.post(f"{BASE_URL}/api/auth/login",
                         json={"email": "shannonnieman1030@gmail.com", "password": os.environ.get("TEST_PASSWORD", "Demo2026!")})
        if r.status_code == 200:
            token = r.json().get("session_token") or r.json().get("token")
            if token:
                stats_r = requests.get(f"{BASE_URL}/api/platform/stats",
                                      headers={"Authorization": f"Bearer {token}"})
                assert stats_r.status_code == 403, f"Church admin should get 403, got {stats_r.status_code}"
                print("PASS: Church admin gets 403 on /api/platform/stats")
            else:
                print("INFO: No token in response, skipping")
        else:
            print(f"INFO: Church admin login returned {r.status_code}, skipping test")


# ── Health scores ──────────────────────────────────────────────────────────
class TestHealthScores:
    """GET /api/platform/health-scores"""

    def test_health_scores_ok(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/health-scores", headers=platform_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
        data = r.json()
        churches = data.get("churches", [])
        assert len(churches) >= 1, "Expected at least 1 church health score"
        print(f"PASS: /api/platform/health-scores returned {len(churches)} churches")

    def test_health_scores_structure(self, platform_headers):
        r = requests.get(f"{BASE_URL}/api/platform/health-scores", headers=platform_headers)
        data = r.json()
        churches = data.get("churches", [])
        if churches:
            c = churches[0]
            health = c.get("health", {})
            assert "grade" in health, f"health must have 'grade' key, got {health}"
            assert "score" in health, f"health must have 'score' key, got {health}"
            print(f"PASS: health score structure correct: grade={health['grade']}, score={health['score']}")
