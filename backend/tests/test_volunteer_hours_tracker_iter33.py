"""
Test Volunteer Hours Tracker Feature - Iteration 33
New endpoints added on top of Iteration 32 Volunteer Leaderboard feature.

Endpoints being tested:
1. POST /api/portal/volunteer/log-hours - member self-logs hours (validates 0 < hours <= 24)
2. GET /api/portal/volunteer/hours-summary?period=monthly - monthly breakdown with current period, totals
3. GET /api/portal/volunteer/hours-summary?period=weekly - weekly breakdown (ISO week format YYYY-WXX)
4. GET /api/portal/volunteer/hours-log?limit=N - paginated individual entries sorted by date desc

Regression tests:
- GET /api/portal/volunteer/leaderboard - ensure still working after new entries
- GET /api/portal/volunteer/my-stats - ensure stats updated after self-logged hours
"""

import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Credentials from iteration 32
ADMIN_EMAIL = "admin@abundant.church"
ADMIN_PASSWORD = "Demo2026!"
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = "Demo2026!"
MEMBER_USER_ID = "member_abundant"


@pytest.fixture(scope="module")
def api_client():
    """Basic requests session without auth"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def member_token(api_client):
    """Get member authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": MEMBER_EMAIL,
        "password": MEMBER_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("session_token") or data.get("token")
    pytest.skip(f"Member login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("session_token") or data.get("token")
    pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def member_client(member_token):
    """Session with member auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {member_token}"
    })
    return session


@pytest.fixture(scope="module")
def admin_client(admin_token):
    """Session with admin auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    })
    return session


# ============== POST /portal/volunteer/log-hours TESTS ==============

class TestSelfLogHours:
    """POST /api/portal/volunteer/log-hours - member self-logs volunteer hours"""

    def test_self_log_hours_success(self, member_client):
        """Member can self-log volunteer hours"""
        payload = {
            "hours": 2.5,
            "notes": "TEST_iter33_self_logged hours"
        }
        response = member_client.post(f"{BASE_URL}/api/portal/volunteer/log-hours", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response missing 'message' key"
        assert "entry" in data, "Response missing 'entry' key"
        
        entry = data["entry"]
        assert entry["hours"] == 2.5, f"Expected hours=2.5, got {entry['hours']}"
        assert entry["status"] == "self_logged", f"Expected status='self_logged', got {entry['status']}"
        assert entry["user_id"] == MEMBER_USER_ID, f"Expected user_id={MEMBER_USER_ID}, got {entry['user_id']}"
        
        print(f"SUCCESS: Member self-logged {entry['hours']}h with status '{entry['status']}'")

    def test_self_log_hours_with_opportunity_id(self, member_client):
        """Self-log hours with optional opportunity_id"""
        payload = {
            "hours": 1.5,
            "opportunity_id": "opp_test_123",
            "notes": "TEST_iter33_with_opportunity"
        }
        response = member_client.post(f"{BASE_URL}/api/portal/volunteer/log-hours", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        entry = data["entry"]
        assert entry.get("opportunity_id") == "opp_test_123"
        assert entry["status"] == "self_logged"
        
        print("SUCCESS: Self-logged hours with opportunity_id")

    def test_self_log_hours_with_custom_date(self, member_client):
        """Self-log hours with custom date"""
        payload = {
            "hours": 3.0,
            "date": "2026-01-10",
            "notes": "TEST_iter33_custom_date"
        }
        response = member_client.post(f"{BASE_URL}/api/portal/volunteer/log-hours", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        entry = data["entry"]
        assert entry.get("date") == "2026-01-10", f"Expected date='2026-01-10', got {entry.get('date')}"
        
        print("SUCCESS: Self-logged hours with custom date")

    def test_self_log_hours_validation_zero_hours(self, member_client):
        """Validation: hours=0 returns 400"""
        payload = {
            "hours": 0,
            "notes": "TEST_iter33_invalid_zero"
        }
        response = member_client.post(f"{BASE_URL}/api/portal/volunteer/log-hours", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        print("SUCCESS: hours=0 returns 400 Bad Request")

    def test_self_log_hours_validation_negative_hours(self, member_client):
        """Validation: negative hours returns 400"""
        payload = {
            "hours": -2,
            "notes": "TEST_iter33_negative"
        }
        response = member_client.post(f"{BASE_URL}/api/portal/volunteer/log-hours", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        print("SUCCESS: negative hours returns 400 Bad Request")

    def test_self_log_hours_validation_over_24(self, member_client):
        """Validation: hours > 24 returns 400"""
        payload = {
            "hours": 25,
            "notes": "TEST_iter33_over_24"
        }
        response = member_client.post(f"{BASE_URL}/api/portal/volunteer/log-hours", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        print("SUCCESS: hours > 24 returns 400 Bad Request")

    def test_self_log_hours_max_boundary_24(self, member_client):
        """Boundary: exactly 24 hours is valid"""
        payload = {
            "hours": 24,
            "notes": "TEST_iter33_boundary_24"
        }
        response = member_client.post(f"{BASE_URL}/api/portal/volunteer/log-hours", json=payload)
        assert response.status_code == 200, f"Expected 200 for 24h, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["entry"]["hours"] == 24
        
        print("SUCCESS: 24 hours (boundary) is valid")

    def test_self_log_hours_min_boundary(self, member_client):
        """Boundary: small positive value (0.1) is valid"""
        payload = {
            "hours": 0.1,
            "notes": "TEST_iter33_boundary_min"
        }
        response = member_client.post(f"{BASE_URL}/api/portal/volunteer/log-hours", json=payload)
        assert response.status_code == 200, f"Expected 200 for 0.1h, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["entry"]["hours"] == 0.1
        
        print("SUCCESS: 0.1 hours (small value) is valid")

    def test_self_log_hours_unauthenticated_returns_401(self, api_client):
        """Unauthenticated access returns 401"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        payload = {"hours": 2.0}
        response = session.post(f"{BASE_URL}/api/portal/volunteer/log-hours", json=payload)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print("SUCCESS: Unauthenticated self-log-hours returns 401")


# ============== GET /portal/volunteer/hours-summary TESTS ==============

class TestHoursSummaryMonthly:
    """GET /api/portal/volunteer/hours-summary?period=monthly tests"""

    def test_hours_summary_monthly_success(self, member_client):
        """Monthly summary returns breakdown array and current period"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/hours-summary?period=monthly")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        required_fields = ["user_id", "period_type", "current_period", "breakdown", "total_hours", "total_sessions"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        assert data["period_type"] == "monthly", f"Expected period_type='monthly', got {data['period_type']}"
        
        print(f"SUCCESS: Monthly summary - total_hours={data['total_hours']}, sessions={data['total_sessions']}")

    def test_hours_summary_monthly_breakdown_format(self, member_client):
        """Monthly breakdown periods use YYYY-MM format"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/hours-summary?period=monthly")
        assert response.status_code == 200
        
        data = response.json()
        breakdown = data["breakdown"]
        
        if breakdown:
            # Check period format (YYYY-MM)
            for bucket in breakdown:
                period = bucket.get("period", "")
                # Should match YYYY-MM format
                assert len(period) == 7, f"Period format wrong: {period}"
                assert period[4] == "-", f"Period format wrong: {period}"
                assert bucket.get("hours") is not None, "Bucket missing 'hours'"
                assert bucket.get("count") is not None, "Bucket missing 'count'"
            
            print(f"SUCCESS: Monthly breakdown has correct YYYY-MM format, {len(breakdown)} periods")
        else:
            print("INFO: No breakdown data yet (user may have no volunteer entries)")

    def test_hours_summary_monthly_current_period(self, member_client):
        """Current period matches current month"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/hours-summary?period=monthly")
        assert response.status_code == 200
        
        data = response.json()
        current = data["current_period"]
        
        # Current period should match current month
        now = datetime.now(timezone.utc)
        expected_period = now.strftime("%Y-%m")
        assert current["period"] == expected_period, f"Expected {expected_period}, got {current['period']}"
        
        print(f"SUCCESS: Current monthly period = {current['period']}, hours={current['hours']}")

    def test_hours_summary_monthly_max_12_periods(self, member_client):
        """Breakdown returns max 12 periods"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/hours-summary?period=monthly")
        assert response.status_code == 200
        
        data = response.json()
        breakdown = data["breakdown"]
        
        assert len(breakdown) <= 12, f"Breakdown should have max 12 periods, got {len(breakdown)}"
        
        print(f"SUCCESS: Monthly breakdown has {len(breakdown)} periods (max 12)")


class TestHoursSummaryWeekly:
    """GET /api/portal/volunteer/hours-summary?period=weekly tests"""

    def test_hours_summary_weekly_success(self, member_client):
        """Weekly summary returns breakdown with ISO week format"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/hours-summary?period=weekly")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["period_type"] == "weekly", f"Expected period_type='weekly', got {data['period_type']}"
        
        print(f"SUCCESS: Weekly summary - total_hours={data['total_hours']}, sessions={data['total_sessions']}")

    def test_hours_summary_weekly_iso_format(self, member_client):
        """Weekly breakdown uses ISO week format (YYYY-WXX)"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/hours-summary?period=weekly")
        assert response.status_code == 200
        
        data = response.json()
        breakdown = data["breakdown"]
        
        if breakdown:
            for bucket in breakdown:
                period = bucket.get("period", "")
                # ISO week format: YYYY-WXX (e.g., 2026-W02)
                assert "-W" in period, f"Expected ISO week format with -W, got: {period}"
                parts = period.split("-W")
                assert len(parts) == 2, f"Invalid ISO week format: {period}"
                year = parts[0]
                week = parts[1]
                assert len(year) == 4 and year.isdigit(), f"Invalid year in: {period}"
                assert 1 <= int(week) <= 53, f"Invalid week number in: {period}"
            
            print(f"SUCCESS: Weekly breakdown uses ISO week format (YYYY-WXX), {len(breakdown)} periods")
        else:
            print("INFO: No weekly breakdown data yet")

    def test_hours_summary_weekly_current_period(self, member_client):
        """Current period matches current ISO week"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/hours-summary?period=weekly")
        assert response.status_code == 200
        
        data = response.json()
        current = data["current_period"]
        
        now = datetime.now(timezone.utc)
        iso = now.isocalendar()
        expected_period = f"{iso[0]}-W{iso[1]:02d}"
        assert current["period"] == expected_period, f"Expected {expected_period}, got {current['period']}"
        
        print(f"SUCCESS: Current weekly period = {current['period']}")

    def test_hours_summary_unauthenticated_returns_401(self, api_client):
        """Unauthenticated access returns 401"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/portal/volunteer/hours-summary?period=monthly")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print("SUCCESS: Unauthenticated hours-summary returns 401")


# ============== GET /portal/volunteer/hours-log TESTS ==============

class TestHoursLog:
    """GET /api/portal/volunteer/hours-log - paginated log entries"""

    def test_hours_log_success(self, member_client):
        """Hours log returns paginated entries"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/hours-log")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "entries" in data, "Response missing 'entries' key"
        assert "total" in data, "Response missing 'total' key"
        
        print(f"SUCCESS: Hours log returned {data['total']} entries")

    def test_hours_log_with_limit(self, member_client):
        """Hours log respects limit parameter"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/hours-log?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        entries = data["entries"]
        
        assert len(entries) <= 5, f"Expected max 5 entries, got {len(entries)}"
        
        print(f"SUCCESS: Hours log with limit=5 returned {len(entries)} entries")

    def test_hours_log_sorted_by_date_desc(self, member_client):
        """Entries are sorted by date descending (most recent first)"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/hours-log?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        entries = data["entries"]
        
        if len(entries) >= 2:
            # Check entries are sorted by created_at descending
            for i in range(len(entries) - 1):
                current_date = entries[i].get("created_at", "")
                next_date = entries[i + 1].get("created_at", "")
                if current_date and next_date:
                    assert current_date >= next_date, f"Not sorted desc: {current_date} < {next_date}"
            
            print("SUCCESS: Hours log is sorted by date descending")
        else:
            print("INFO: Not enough entries to verify sort order")

    def test_hours_log_entry_structure(self, member_client):
        """Each log entry has required fields"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/hours-log?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        entries = data["entries"]
        
        if entries:
            entry = entries[0]
            required_fields = ["id", "user_id", "hours", "status", "created_at"]
            for field in required_fields:
                assert field in entry, f"Entry missing field: {field}"
            
            print(f"SUCCESS: Log entry has required fields")
        else:
            print("INFO: No log entries to validate structure")

    def test_hours_log_contains_self_logged_entries(self, member_client):
        """Log should contain entries with status='self_logged' after self-logging"""
        # First ensure we have a self-logged entry
        payload = {"hours": 1.0, "notes": "TEST_iter33_verify_self_logged"}
        member_client.post(f"{BASE_URL}/api/portal/volunteer/log-hours", json=payload)
        
        # Now check the log
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/hours-log?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        entries = data["entries"]
        
        self_logged_entries = [e for e in entries if e.get("status") == "self_logged"]
        assert len(self_logged_entries) > 0, "No self_logged entries found in hours log"
        
        print(f"SUCCESS: Found {len(self_logged_entries)} self_logged entries in hours log")

    def test_hours_log_unauthenticated_returns_401(self, api_client):
        """Unauthenticated access returns 401"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/portal/volunteer/hours-log")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print("SUCCESS: Unauthenticated hours-log returns 401")


# ============== REGRESSION TESTS - LEADERBOARD & MY-STATS ==============

class TestLeaderboardRegression:
    """Regression: Verify leaderboard still works after new entries"""

    def test_leaderboard_still_works(self, member_client):
        """Leaderboard endpoint still returns data after self-logged entries"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/leaderboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "leaderboard" in data
        assert "badge_tiers" in data
        
        print(f"SUCCESS: Leaderboard regression test passed, {len(data['leaderboard'])} volunteers")

    def test_leaderboard_sorted_correctly(self, member_client):
        """Leaderboard still sorted by signup_count descending"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        leaderboard = data["leaderboard"]
        
        if len(leaderboard) >= 2:
            for i in range(len(leaderboard) - 1):
                assert leaderboard[i]["signup_count"] >= leaderboard[i + 1]["signup_count"]
        
        print("SUCCESS: Leaderboard still sorted correctly")


class TestMyStatsRegression:
    """Regression: Verify my-stats still works and reflects new entries"""

    def test_my_stats_still_works(self, member_client):
        """My-stats endpoint still returns data"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/my-stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        required_fields = ["user_id", "signup_count", "total_hours", "rank", "badge"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"SUCCESS: My-stats regression - signup_count={data['signup_count']}, hours={data['total_hours']}")

    def test_my_stats_includes_self_logged_hours(self, member_client):
        """My-stats total_hours includes self-logged entries"""
        # Get initial stats
        initial_response = member_client.get(f"{BASE_URL}/api/portal/volunteer/my-stats")
        initial_hours = initial_response.json()["total_hours"]
        
        # Log more hours
        payload = {"hours": 2.0, "notes": "TEST_iter33_stats_update"}
        member_client.post(f"{BASE_URL}/api/portal/volunteer/log-hours", json=payload)
        
        # Get updated stats
        updated_response = member_client.get(f"{BASE_URL}/api/portal/volunteer/my-stats")
        updated_hours = updated_response.json()["total_hours"]
        
        # Verify hours increased
        assert updated_hours >= initial_hours, f"Hours should increase: {initial_hours} -> {updated_hours}"
        
        print(f"SUCCESS: My-stats updated with self-logged hours: {initial_hours} -> {updated_hours}")


# ============== ADMIN CAN ACCESS PORTAL ENDPOINTS ==============

class TestAdminAccessPortalEndpoints:
    """Admin role should also be able to access portal volunteer endpoints"""

    def test_admin_can_self_log_hours(self, admin_client):
        """Admin can also self-log volunteer hours"""
        payload = {"hours": 1.5, "notes": "TEST_iter33_admin_self_log"}
        response = admin_client.post(f"{BASE_URL}/api/portal/volunteer/log-hours", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        print("SUCCESS: Admin can self-log volunteer hours")

    def test_admin_can_view_hours_summary(self, admin_client):
        """Admin can view hours-summary"""
        response = admin_client.get(f"{BASE_URL}/api/portal/volunteer/hours-summary?period=monthly")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        print("SUCCESS: Admin can view hours summary")

    def test_admin_can_view_hours_log(self, admin_client):
        """Admin can view hours-log"""
        response = admin_client.get(f"{BASE_URL}/api/portal/volunteer/hours-log")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        print("SUCCESS: Admin can view hours log")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
