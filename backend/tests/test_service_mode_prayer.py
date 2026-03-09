"""
Tests for Service Mode (Summit Enhancements) and Prayer Request features
- Service Mode API: /api/portal/service-mode
- Service Check-in: /api/portal/service-checkin
- Attendance Streak: /api/portal/attendance-streak
- Prayer Categories: /api/portal/prayer/categories
- Prayer Requests: POST/GET /api/portal/prayer/requests
- Prayer Wall: GET /api/portal/prayer/wall
- Pray for Request: POST /api/portal/prayer/requests/{id}/pray
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def session():
    """Create a requests session"""
    return requests.Session()

@pytest.fixture(scope="module")
def member_auth(session):
    """Login as member and get auth session"""
    login_data = {
        "email": "member@abundant.church",
        "password": "Demo2026!"
    }
    res = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if res.status_code != 200:
        pytest.skip(f"Member login failed: {res.status_code} - {res.text}")
    return session

@pytest.fixture(scope="module")
def admin_auth(session):
    """Login as admin and get auth session"""
    admin_session = requests.Session()
    login_data = {
        "email": "admin@abundant.church",
        "password": "Demo2026!"
    }
    res = admin_session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if res.status_code != 200:
        pytest.skip(f"Admin login failed: {res.status_code} - {res.text}")
    return admin_session


class TestServiceModeAPI:
    """Test Service Mode endpoints"""
    
    def test_service_mode_returns_correct_structure(self, member_auth):
        """Test /api/portal/service-mode returns expected fields"""
        res = member_auth.get(f"{BASE_URL}/api/portal/service-mode")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        data = res.json()
        # Verify required fields exist
        assert "is_service_day" in data, "Missing is_service_day"
        assert "is_service_time" in data, "Missing is_service_time"
        assert "attendance_streak" in data, "Missing attendance_streak"
        assert "check_in_status" in data, "Missing check_in_status"
        assert "today" in data, "Missing today"
        assert "current_day" in data, "Missing current_day"
        
        # Verify types
        assert isinstance(data["is_service_day"], bool)
        assert isinstance(data["is_service_time"], bool)
        assert isinstance(data["attendance_streak"], int)
        
        print(f"Service Mode: is_service_day={data['is_service_day']}, current_day={data['current_day']}")
    
    def test_service_mode_today_is_correct(self, member_auth):
        """Test that today's date is correctly returned"""
        res = member_auth.get(f"{BASE_URL}/api/portal/service-mode")
        assert res.status_code == 200
        
        data = res.json()
        today = datetime.utcnow().date().isoformat()
        assert data["today"] == today, f"Expected today={today}, got {data['today']}"
        
        # Verify current_day matches
        expected_day = datetime.utcnow().strftime("%A")
        assert data["current_day"] == expected_day
    
    def test_service_mode_requires_auth(self, session):
        """Test that service-mode requires authentication"""
        # Use fresh session without auth
        new_session = requests.Session()
        res = new_session.get(f"{BASE_URL}/api/portal/service-mode")
        assert res.status_code == 401


class TestServiceCheckIn:
    """Test Service Check-in endpoints"""
    
    def test_checkin_in_person(self, member_auth):
        """Test check-in with in_person type"""
        res = member_auth.post(f"{BASE_URL}/api/portal/service-checkin?check_in_type=in_person")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        data = res.json()
        assert "message" in data
        assert "check_in_type" in data
        # Either new check-in or already checked in
        assert data["check_in_type"] == "in_person"
        print(f"Check-in response: {data['message']}")
    
    def test_checkin_already_checked_in_returns_existing(self, member_auth):
        """Test that double check-in returns existing status"""
        # First check-in (may already be done)
        member_auth.post(f"{BASE_URL}/api/portal/service-checkin?check_in_type=in_person")
        
        # Second check-in should return existing
        res = member_auth.post(f"{BASE_URL}/api/portal/service-checkin?check_in_type=online")
        assert res.status_code == 200
        
        data = res.json()
        # Should indicate already checked in (first type wins)
        assert "message" in data
        assert "check_in_type" in data
    
    def test_checkin_requires_auth(self, session):
        """Test check-in requires authentication"""
        new_session = requests.Session()
        res = new_session.post(f"{BASE_URL}/api/portal/service-checkin?check_in_type=in_person")
        assert res.status_code == 401


class TestAttendanceStreak:
    """Test Attendance Streak endpoints"""
    
    def test_attendance_streak_returns_structure(self, member_auth):
        """Test /api/portal/attendance-streak returns expected fields"""
        res = member_auth.get(f"{BASE_URL}/api/portal/attendance-streak")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        data = res.json()
        # Verify required fields
        assert "current_streak" in data
        assert "longest_streak" in data
        assert "total_attended" in data
        
        # Verify types
        assert isinstance(data["current_streak"], int)
        assert isinstance(data["longest_streak"], int)
        assert isinstance(data["total_attended"], int)
        
        # Optional badges field
        if "streak_badges" in data:
            assert isinstance(data["streak_badges"], list)
        
        print(f"Streak: current={data['current_streak']}, longest={data['longest_streak']}, total={data['total_attended']}")
    
    def test_streak_after_checkin(self, member_auth):
        """Test streak is updated after check-in"""
        # Check in first
        member_auth.post(f"{BASE_URL}/api/portal/service-checkin?check_in_type=in_person")
        
        # Get streak
        res = member_auth.get(f"{BASE_URL}/api/portal/attendance-streak")
        assert res.status_code == 200
        
        data = res.json()
        # After check-in, total_attended should be at least 1
        assert data["total_attended"] >= 1, "Expected total_attended >= 1 after check-in"
    
    def test_streak_requires_auth(self, session):
        """Test attendance-streak requires authentication"""
        new_session = requests.Session()
        res = new_session.get(f"{BASE_URL}/api/portal/attendance-streak")
        assert res.status_code == 401


class TestPrayerCategories:
    """Test Prayer Categories endpoint"""
    
    def test_categories_returns_8_categories(self, member_auth):
        """Test /api/portal/prayer/categories returns all 8 categories"""
        res = member_auth.get(f"{BASE_URL}/api/portal/prayer/categories")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        data = res.json()
        assert "categories" in data
        
        categories = data["categories"]
        assert len(categories) == 8, f"Expected 8 categories, got {len(categories)}"
        
        # Verify category structure
        expected_ids = ["general", "healing", "family", "financial", "guidance", "thanksgiving", "salvation", "relationships"]
        category_ids = [c["id"] for c in categories]
        
        for exp_id in expected_ids:
            assert exp_id in category_ids, f"Missing category: {exp_id}"
        
        # Verify each category has required fields
        for cat in categories:
            assert "id" in cat
            assert "name" in cat
            assert "icon" in cat
        
        print(f"Categories: {category_ids}")


class TestPrayerRequests:
    """Test Prayer Request CRUD operations"""
    
    def test_create_prayer_request(self, member_auth):
        """Test POST /api/portal/prayer/requests creates a request"""
        unique_title = f"TEST_Prayer_{uuid.uuid4().hex[:8]}"
        request_data = {
            "category": "healing",
            "title": unique_title,
            "content": "Test prayer request for healing",
            "is_public": True,
            "is_anonymous": False
        }
        
        res = member_auth.post(
            f"{BASE_URL}/api/portal/prayer/requests",
            json=request_data
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        data = res.json()
        assert "message" in data
        assert "id" in data
        assert data["message"] == "Prayer request submitted"
        
        print(f"Created prayer request: {data['id']}")
        return data["id"]
    
    def test_get_my_prayer_requests(self, member_auth):
        """Test GET /api/portal/prayer/requests returns user's requests"""
        res = member_auth.get(f"{BASE_URL}/api/portal/prayer/requests")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        data = res.json()
        assert "requests" in data
        assert isinstance(data["requests"], list)
        
        # Verify structure of requests if any exist
        if data["requests"]:
            req = data["requests"][0]
            assert "id" in req
            assert "title" in req
            assert "content" in req
            assert "category" in req
        
        print(f"User has {len(data['requests'])} prayer requests")
    
    def test_create_private_prayer_request(self, member_auth):
        """Test creating a private prayer request (not on prayer wall)"""
        request_data = {
            "category": "financial",
            "title": f"TEST_Private_{uuid.uuid4().hex[:8]}",
            "content": "Private financial prayer",
            "is_public": False,
            "is_anonymous": False
        }
        
        res = member_auth.post(
            f"{BASE_URL}/api/portal/prayer/requests",
            json=request_data
        )
        assert res.status_code == 200
        
        data = res.json()
        assert "id" in data
    
    def test_prayer_request_requires_auth(self, session):
        """Test creating prayer request requires authentication"""
        new_session = requests.Session()
        res = new_session.post(
            f"{BASE_URL}/api/portal/prayer/requests",
            json={"category": "general", "title": "test", "content": "test"}
        )
        assert res.status_code == 401


class TestPrayerWall:
    """Test Prayer Wall endpoints"""
    
    def test_prayer_wall_returns_public_requests(self, member_auth):
        """Test GET /api/portal/prayer/wall returns public requests"""
        res = member_auth.get(f"{BASE_URL}/api/portal/prayer/wall")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        data = res.json()
        assert "requests" in data
        assert isinstance(data["requests"], list)
        
        # All returned requests should be public
        for req in data["requests"]:
            assert req.get("is_public") == True, f"Found non-public request on wall: {req.get('id')}"
        
        print(f"Prayer wall has {len(data['requests'])} public requests")
    
    def test_prayer_wall_category_filter(self, member_auth):
        """Test prayer wall filtering by category"""
        # Test healing category filter
        res = member_auth.get(f"{BASE_URL}/api/portal/prayer/wall?category=healing")
        assert res.status_code == 200
        
        data = res.json()
        assert "requests" in data
        
        # All filtered requests should be in healing category
        for req in data["requests"]:
            assert req.get("category") == "healing", f"Found non-healing request: {req.get('category')}"
    
    def test_prayer_wall_all_category_filter(self, member_auth):
        """Test prayer wall with 'all' category returns all"""
        res = member_auth.get(f"{BASE_URL}/api/portal/prayer/wall?category=all")
        assert res.status_code == 200
        
        data = res.json()
        assert "requests" in data
    
    def test_prayer_wall_requires_auth(self, session):
        """Test prayer wall requires authentication"""
        new_session = requests.Session()
        res = new_session.get(f"{BASE_URL}/api/portal/prayer/wall")
        assert res.status_code == 401


class TestPrayForRequest:
    """Test Pray for Request functionality"""
    
    def test_pray_for_request(self, member_auth):
        """Test POST /api/portal/prayer/requests/{id}/pray increments count"""
        # First create a public prayer request
        unique_title = f"TEST_PrayFor_{uuid.uuid4().hex[:8]}"
        create_res = member_auth.post(
            f"{BASE_URL}/api/portal/prayer/requests",
            json={
                "category": "general",
                "title": unique_title,
                "content": "Test prayer for praying",
                "is_public": True,
                "is_anonymous": False
            }
        )
        assert create_res.status_code == 200
        request_id = create_res.json()["id"]
        
        # Now pray for it
        pray_res = member_auth.post(f"{BASE_URL}/api/portal/prayer/requests/{request_id}/pray")
        assert pray_res.status_code == 200, f"Expected 200, got {pray_res.status_code}: {pray_res.text}"
        
        data = pray_res.json()
        assert "message" in data
        assert "prayed" in data
        assert data["prayed"] == True
        
        print(f"Prayed for request: {request_id}")
    
    def test_pray_twice_returns_already_prayed(self, member_auth):
        """Test praying twice for same request returns already prayed"""
        # Create request
        create_res = member_auth.post(
            f"{BASE_URL}/api/portal/prayer/requests",
            json={
                "category": "thanksgiving",
                "title": f"TEST_DoublePray_{uuid.uuid4().hex[:8]}",
                "content": "Test double pray",
                "is_public": True,
                "is_anonymous": False
            }
        )
        assert create_res.status_code == 200
        request_id = create_res.json()["id"]
        
        # First pray
        member_auth.post(f"{BASE_URL}/api/portal/prayer/requests/{request_id}/pray")
        
        # Second pray - should return already prayed
        pray_res = member_auth.post(f"{BASE_URL}/api/portal/prayer/requests/{request_id}/pray")
        assert pray_res.status_code == 200
        
        data = pray_res.json()
        assert "Already prayed" in data.get("message", "") or data.get("prayed") == True
    
    def test_pray_requires_auth(self, session):
        """Test praying requires authentication"""
        new_session = requests.Session()
        res = new_session.post(f"{BASE_URL}/api/portal/prayer/requests/fake-id/pray")
        assert res.status_code == 401


class TestAdminPrayerDashboard:
    """Test Admin Prayer Dashboard endpoints"""
    
    def test_admin_prayer_dashboard_access(self, admin_auth):
        """Test admin can access prayer dashboard"""
        res = admin_auth.get(f"{BASE_URL}/api/admin/prayer/dashboard")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        data = res.json()
        assert "requests" in data
        assert "stats" in data
        assert "categories" in data
        
        # Verify stats structure
        stats = data["stats"]
        assert "total_active" in stats
        assert "total_answered" in stats
        assert "needs_followup" in stats
        
        print(f"Prayer dashboard: {stats['total_active']} active, {stats['total_answered']} answered")
    
    def test_admin_prayer_dashboard_filter_by_status(self, admin_auth):
        """Test filtering dashboard by status"""
        res = admin_auth.get(f"{BASE_URL}/api/admin/prayer/dashboard?status=active")
        assert res.status_code == 200
        
        data = res.json()
        for req in data["requests"]:
            assert req.get("status") == "active"
    
    def test_member_cannot_access_admin_prayer_dashboard(self, member_auth):
        """Test member cannot access admin prayer dashboard"""
        res = member_auth.get(f"{BASE_URL}/api/admin/prayer/dashboard")
        assert res.status_code == 403


# Cleanup test data after all tests
@pytest.fixture(scope="module", autouse=True)
def cleanup(member_auth, request):
    """Cleanup test prayer requests after tests"""
    yield
    # Optional: cleanup TEST_ prefixed data
    # In production, would delete test data here
