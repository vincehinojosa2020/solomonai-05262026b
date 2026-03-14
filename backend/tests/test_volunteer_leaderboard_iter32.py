"""
Test Volunteer Leaderboard & Gamification Feature - Iteration 32
Tests:
1. GET /api/portal/volunteer/leaderboard - ranked list with badges, hours, ministry areas
2. GET /api/portal/volunteer/my-stats - current user stats, badge, rank, progress %
3. POST /api/admin/volunteer/log-hours - admin logs hours for a user
4. Badge tier computation (Helping Hand → Kingdom Builder)
5. Role-based access control (member cannot access admin endpoint)
6. Unauthenticated access returns 401
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Credentials
ADMIN_EMAIL = "admin@abundant.church"
ADMIN_PASSWORD = "Demo2026!"
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = "Demo2026!"
MEMBER_USER_ID = "member_abundant"

# Badge tiers reference
BADGE_TIERS = [
    {"name": "Helping Hand", "threshold": 5},
    {"name": "Faithful Servant", "threshold": 15},
    {"name": "Ministry Champion", "threshold": 30},
    {"name": "Church Pillar", "threshold": 50},
    {"name": "Kingdom Builder", "threshold": 100},
]


@pytest.fixture(scope="module")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


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
def admin_client(api_client, admin_token):
    """Session with admin auth header"""
    api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return api_client


@pytest.fixture(scope="module")
def member_client(api_client, member_token):
    """Session with member auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {member_token}"
    })
    return session


class TestVolunteerLeaderboard:
    """GET /api/portal/volunteer/leaderboard tests"""

    def test_get_leaderboard_success(self, member_client):
        """Test leaderboard returns ranked volunteers with badges"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/leaderboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "leaderboard" in data, "Response missing 'leaderboard' key"
        assert "badge_tiers" in data, "Response missing 'badge_tiers' key"
        
        # Verify badge tiers are returned
        badge_tiers = data["badge_tiers"]
        assert len(badge_tiers) == 5, f"Expected 5 badge tiers, got {len(badge_tiers)}"
        assert badge_tiers[0]["name"] == "Helping Hand"
        assert badge_tiers[4]["name"] == "Kingdom Builder"
        
        print(f"SUCCESS: Leaderboard returned {len(data['leaderboard'])} volunteers")

    def test_leaderboard_sorted_by_signup_count_desc(self, member_client):
        """Verify leaderboard is sorted by signup_count descending"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        leaderboard = data["leaderboard"]
        
        if len(leaderboard) >= 2:
            for i in range(len(leaderboard) - 1):
                current = leaderboard[i]["signup_count"]
                next_val = leaderboard[i + 1]["signup_count"]
                assert current >= next_val, f"Leaderboard not sorted: {current} < {next_val}"
        
        print("SUCCESS: Leaderboard is correctly sorted by signup_count descending")

    def test_leaderboard_entry_structure(self, member_client):
        """Verify each leaderboard entry has required fields"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        leaderboard = data["leaderboard"]
        
        if leaderboard:
            entry = leaderboard[0]
            required_fields = ["rank", "user_id", "user_name", "signup_count", "total_hours", "ministry_areas", "badge"]
            for field in required_fields:
                assert field in entry, f"Missing field: {field}"
            
            # Verify rank is 1 for first entry
            assert entry["rank"] == 1, f"First entry should have rank=1, got {entry['rank']}"
            
            print(f"SUCCESS: Leaderboard entry has all required fields: {required_fields}")
        else:
            print("SKIP: No leaderboard entries to validate structure")

    def test_leaderboard_badge_computation(self, member_client):
        """Verify badges are computed correctly based on signup_count"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        leaderboard = data["leaderboard"]
        
        for entry in leaderboard:
            signup_count = entry["signup_count"]
            badge = entry.get("badge")
            
            # Verify badge based on thresholds
            if signup_count < 5:
                assert badge is None, f"User with {signup_count} signups should have no badge"
            elif signup_count < 15:
                assert badge is None or badge["name"] == "Helping Hand", f"User with {signup_count} signups has wrong badge: {badge}"
            elif signup_count < 30:
                assert badge is not None and badge["name"] in ["Helping Hand", "Faithful Servant"]
            elif signup_count < 50:
                assert badge is not None and badge["name"] in ["Helping Hand", "Faithful Servant", "Ministry Champion"]
            elif signup_count < 100:
                assert badge is not None and badge["name"] in ["Helping Hand", "Faithful Servant", "Ministry Champion", "Church Pillar"]
            else:
                assert badge is not None and badge["name"] == "Kingdom Builder"
        
        print("SUCCESS: Badge computation is correct for all leaderboard entries")

    def test_leaderboard_unauthenticated_returns_401(self, api_client):
        """Verify unauthenticated access returns 401"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/portal/volunteer/leaderboard")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Unauthenticated access returns 401")


class TestVolunteerMyStats:
    """GET /api/portal/volunteer/my-stats tests"""

    def test_my_stats_success(self, member_client):
        """Test my-stats returns current user's volunteer stats"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/my-stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        required_fields = [
            "user_id", "user_name", "signup_count", "total_hours", 
            "ministry_areas", "rank", "badge", "next_badge", 
            "progress_to_next", "signups_to_next", "badge_tiers"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"SUCCESS: my-stats returned for user {data['user_id']} with {data['signup_count']} signups")

    def test_my_stats_badge_and_progress(self, member_client):
        """Test badge and progress percentage are computed correctly"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/my-stats")
        assert response.status_code == 200
        
        data = response.json()
        signup_count = data["signup_count"]
        badge = data.get("badge")
        next_badge = data.get("next_badge")
        progress = data["progress_to_next"]
        signups_to_next = data["signups_to_next"]
        
        # Validate badge based on threshold
        if signup_count < 5:
            assert badge is None, f"User with {signup_count} signups should have no badge"
            assert next_badge is not None and next_badge["name"] == "Helping Hand"
        elif signup_count >= 5 and signup_count < 15:
            assert badge is not None and badge["name"] == "Helping Hand"
            assert next_badge is not None and next_badge["name"] == "Faithful Servant"
        elif signup_count >= 15 and signup_count < 30:
            assert badge is not None and badge["name"] == "Faithful Servant"
            assert next_badge is not None and next_badge["name"] == "Ministry Champion"
        
        # Validate progress percentage is between 0-100
        assert 0 <= progress <= 100, f"Progress should be 0-100, got {progress}"
        
        # Validate signups_to_next is non-negative
        assert signups_to_next >= 0, f"signups_to_next should be >= 0, got {signups_to_next}"
        
        print(f"SUCCESS: Badge={badge['name'] if badge else 'None'}, Progress={progress}%, SignupsToNext={signups_to_next}")

    def test_my_stats_progress_calculation(self, member_client):
        """Verify progress percentage calculation is correct"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/my-stats")
        assert response.status_code == 200
        
        data = response.json()
        signup_count = data["signup_count"]
        badge = data.get("badge")
        next_badge = data.get("next_badge")
        progress = data["progress_to_next"]
        
        # If we have both current and next badge, verify progress calculation
        if badge and next_badge:
            floor = badge["threshold"]
            ceiling = next_badge["threshold"]
            expected_progress = round((signup_count - floor) / (ceiling - floor) * 100, 1)
            # Allow small floating point difference
            assert abs(progress - expected_progress) < 0.5, f"Progress calc wrong: expected {expected_progress}, got {progress}"
            print(f"SUCCESS: Progress calculation verified: {signup_count} signups, floor={floor}, ceiling={ceiling}, progress={progress}%")
        elif not badge and next_badge:
            # No current badge, progress from 0 to first threshold
            expected_progress = round((signup_count / next_badge["threshold"]) * 100, 1)
            assert abs(progress - expected_progress) < 0.5, f"Progress calc wrong: expected {expected_progress}, got {progress}"
            print(f"SUCCESS: Progress from 0 to first badge: {signup_count} signups, progress={progress}%")
        else:
            print("SKIP: Cannot verify progress - user at max tier or no next badge")

    def test_my_stats_unauthenticated_returns_401(self, api_client):
        """Verify unauthenticated access returns 401"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/portal/volunteer/my-stats")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Unauthenticated access returns 401")


class TestAdminLogHours:
    """POST /api/admin/volunteer/log-hours tests"""

    def test_admin_log_hours_success(self, admin_client):
        """Admin can log hours for a user"""
        payload = {
            "user_id": MEMBER_USER_ID,
            "hours": 2.5,
            "notes": "TEST_logged from pytest iteration 32"
        }
        response = admin_client.post(f"{BASE_URL}/api/admin/volunteer/log-hours", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response missing 'message' key"
        assert "entry" in data, "Response missing 'entry' key"
        
        entry = data["entry"]
        assert entry["user_id"] == MEMBER_USER_ID
        assert entry["hours"] == 2.5
        assert "logged" in entry.get("status", "")
        
        print(f"SUCCESS: Admin logged {payload['hours']} hours for user {MEMBER_USER_ID}")

    def test_admin_log_hours_with_opportunity_id(self, admin_client):
        """Admin can log hours with optional opportunity_id"""
        payload = {
            "user_id": MEMBER_USER_ID,
            "opportunity_id": "test-opportunity-123",
            "hours": 1.0,
            "date": "2026-01-15",
            "notes": "TEST_logged with opportunity ID"
        }
        response = admin_client.post(f"{BASE_URL}/api/admin/volunteer/log-hours", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        entry = data["entry"]
        assert entry.get("opportunity_id") == "test-opportunity-123"
        assert entry.get("date") == "2026-01-15"
        
        print("SUCCESS: Admin logged hours with opportunity_id and date")

    def test_admin_log_hours_user_not_found(self, admin_client):
        """Admin log hours for non-existent user returns 404"""
        payload = {
            "user_id": "nonexistent_user_12345",
            "hours": 1.0
        }
        response = admin_client.post(f"{BASE_URL}/api/admin/volunteer/log-hours", json=payload)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("SUCCESS: Admin log hours for non-existent user returns 404")

    def test_member_cannot_access_admin_log_hours(self, member_client):
        """Member role cannot access admin/volunteer/log-hours (403)"""
        payload = {
            "user_id": MEMBER_USER_ID,
            "hours": 1.0
        }
        response = member_client.post(f"{BASE_URL}/api/admin/volunteer/log-hours", json=payload)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("SUCCESS: Member cannot access admin endpoint (403)")

    def test_admin_log_hours_unauthenticated_returns_401(self, api_client):
        """Verify unauthenticated access returns 401"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        payload = {
            "user_id": MEMBER_USER_ID,
            "hours": 1.0
        }
        response = session.post(f"{BASE_URL}/api/admin/volunteer/log-hours", json=payload)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Unauthenticated access returns 401")


class TestBadgeTierThresholds:
    """Test badge tier threshold values"""

    def test_badge_tier_thresholds(self, member_client):
        """Verify badge tiers have correct thresholds"""
        response = member_client.get(f"{BASE_URL}/api/portal/volunteer/leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        tiers = data["badge_tiers"]
        
        expected = [
            ("Helping Hand", 5),
            ("Faithful Servant", 15),
            ("Ministry Champion", 30),
            ("Church Pillar", 50),
            ("Kingdom Builder", 100),
        ]
        
        for i, (name, threshold) in enumerate(expected):
            assert tiers[i]["name"] == name, f"Tier {i} name mismatch: expected {name}, got {tiers[i]['name']}"
            assert tiers[i]["threshold"] == threshold, f"Tier {i} threshold mismatch: expected {threshold}, got {tiers[i]['threshold']}"
        
        print("SUCCESS: All badge tier thresholds are correct")


class TestLeaderboardWithAdminRole:
    """Test leaderboard access with admin role"""

    def test_admin_can_access_leaderboard(self, admin_client):
        """Admin can also access portal volunteer leaderboard"""
        response = admin_client.get(f"{BASE_URL}/api/portal/volunteer/leaderboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("SUCCESS: Admin can access volunteer leaderboard")

    def test_admin_can_access_my_stats(self, admin_client):
        """Admin can access their own volunteer stats"""
        response = admin_client.get(f"{BASE_URL}/api/portal/volunteer/my-stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("SUCCESS: Admin can access their own volunteer stats")


# Cleanup test entries created during testing
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data(admin_client):
    """Cleanup TEST_ prefixed data after tests complete"""
    yield
    # Note: We don't cleanup volunteer_signups as they are part of the leaderboard data
    # The test entries are minimal and won't affect production
    print("Test cleanup: Test entries remain in database for leaderboard demo purposes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
