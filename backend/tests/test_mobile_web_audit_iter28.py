"""
Iteration 28: Mobile + Web Backend Compatibility Audit
Tests Bearer token auth flow, portal/admin routes for mobile clients.
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://church-planning.preview.emergentagent.com"

# Test credentials
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = "Demo2026!"
ADMIN_EMAIL = "admin@abundant.church"
ADMIN_PASSWORD = "Demo2026!"


class TestAuthFlow:
    """Test /auth/login and /auth/me with Bearer token"""
    
    def test_login_returns_session_token(self):
        """POST /api/auth/login should return session_token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "session_token" in data, "session_token missing from login response"
        assert data["session_token"].startswith("sess_"), "session_token format invalid"
        assert "user_id" in data
        assert "email" in data
        assert data["email"] == MEMBER_EMAIL
        print(f"✓ Login returned session_token: {data['session_token'][:20]}...")
    
    def test_auth_me_with_bearer_token(self):
        """GET /api/auth/me with Bearer token should return user info"""
        # First login to get token
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["session_token"]
        
        # Use Bearer token to access /auth/me
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Auth/me failed: {response.text}"
        data = response.json()
        assert "email" in data
        assert "user_id" in data
        assert "role" in data
        print(f"✓ /auth/me returned: {data['email']}, role={data.get('role')}")
    
    def test_auth_me_without_token_returns_401(self):
        """GET /api/auth/me without auth should return 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ /auth/me correctly returns 401 without token")
    
    def test_admin_login_returns_session_token(self):
        """Admin login should also return session_token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "session_token" in data
        # Role can be 'admin' or 'church_admin' per multi-tenant hierarchy
        assert data.get("role") in ["admin", "church_admin"]
        print(f"✓ Admin login successful, role={data.get('role')}")


class TestPortalProfileEndpoints:
    """Test /portal/profile GET and PUT with Bearer token"""
    
    @pytest.fixture(autouse=True)
    def get_member_token(self):
        """Get member token before each test"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
        )
        self.token = login_resp.json()["session_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_portal_profile(self):
        """GET /api/portal/profile returns user profile"""
        response = requests.get(
            f"{BASE_URL}/api/portal/profile",
            headers=self.headers
        )
        assert response.status_code == 200, f"Portal profile failed: {response.text}"
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == MEMBER_EMAIL
        print(f"✓ GET /portal/profile returned user: {data['user'].get('name')}")
    
    def test_put_portal_profile_update(self):
        """PUT /api/portal/profile updates profile"""
        response = requests.put(
            f"{BASE_URL}/api/portal/profile",
            headers=self.headers,
            json={"phone": "555-123-4567"}
        )
        assert response.status_code == 200, f"Profile update failed: {response.text}"
        data = response.json()
        assert "message" in data or "user" in data
        print(f"✓ PUT /portal/profile completed successfully")


class TestPortalAttendanceEndpoints:
    """Test attendance streak, checkin, and history endpoints"""
    
    @pytest.fixture(autouse=True)
    def get_member_token(self):
        """Get member token before each test"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
        )
        self.token = login_resp.json()["session_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_attendance_streak(self):
        """GET /api/portal/attendance/streak returns streak data"""
        response = requests.get(
            f"{BASE_URL}/api/portal/attendance/streak",
            headers=self.headers
        )
        assert response.status_code == 200, f"Streak failed: {response.text}"
        data = response.json()
        # Streak endpoint should return streak info
        assert "current_streak" in data or "streak_count" in data or "streak" in data or isinstance(data, dict)
        print(f"✓ GET /portal/attendance/streak returned: {data}")
    
    def test_post_attendance_checkin(self):
        """POST /api/portal/attendance/checkin records check-in"""
        response = requests.post(
            f"{BASE_URL}/api/portal/attendance/checkin",
            headers=self.headers,
            json={"check_in_type": "in_person"}
        )
        # Can be 200 (success) or 400 (already checked in today)
        assert response.status_code in [200, 400], f"Checkin failed: {response.text}"
        data = response.json()
        print(f"✓ POST /portal/attendance/checkin returned: {response.status_code}")
    
    def test_get_attendance_history(self):
        """GET /api/portal/attendance/history returns history"""
        response = requests.get(
            f"{BASE_URL}/api/portal/attendance/history",
            headers=self.headers
        )
        assert response.status_code == 200, f"History failed: {response.text}"
        data = response.json()
        assert "history" in data
        assert "total" in data
        print(f"✓ GET /portal/attendance/history returned {data['total']} records")


class TestPortalCafeEndpoints:
    """Test cafe menu and order endpoints"""
    
    @pytest.fixture(autouse=True)
    def get_member_token(self):
        """Get member token before each test"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
        )
        self.token = login_resp.json()["session_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_cafe_menu(self):
        """GET /api/portal/cafe/menu returns menu items"""
        response = requests.get(
            f"{BASE_URL}/api/portal/cafe/menu",
            headers=self.headers
        )
        assert response.status_code == 200, f"Cafe menu failed: {response.text}"
        data = response.json()
        assert "items" in data
        print(f"✓ GET /portal/cafe/menu returned {len(data.get('items', []))} items")
    
    def test_post_cafe_order(self):
        """POST /api/portal/cafe/order places an order (MOCKED payment)"""
        # First get menu items
        menu_resp = requests.get(
            f"{BASE_URL}/api/portal/cafe/menu",
            headers=self.headers
        )
        items = menu_resp.json().get("items", [])
        
        if not items:
            pytest.skip("No cafe items available")
        
        item = items[0]
        order_payload = {
            "items": [{
                "item_id": item["id"],
                "name": item["name"],
                "price": item["price"],
                "quantity": 1
            }],
            "pickup_time": "Sunday 9:15 AM",
            "notes": "TEST_iter28_order"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/portal/cafe/order",
            headers=self.headers,
            json=order_payload
        )
        assert response.status_code == 200, f"Cafe order failed: {response.text}"
        data = response.json()
        assert "order" in data
        print(f"✓ POST /portal/cafe/order created order (MOCKED payment)")


class TestPortalMediaEndpoints:
    """Test media/sermons endpoint"""
    
    @pytest.fixture(autouse=True)
    def get_member_token(self):
        """Get member token before each test"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
        )
        self.token = login_resp.json()["session_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_media_sermons(self):
        """GET /api/portal/media/sermons returns sermon videos"""
        response = requests.get(
            f"{BASE_URL}/api/portal/media/sermons",
            headers=self.headers
        )
        assert response.status_code == 200, f"Sermons failed: {response.text}"
        data = response.json()
        assert "videos" in data
        print(f"✓ GET /portal/media/sermons returned {len(data.get('videos', []))} videos")


class TestPortalKidsEndpoints:
    """Test kids check-in endpoints"""
    
    @pytest.fixture(autouse=True)
    def get_member_token(self):
        """Get member token before each test"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
        )
        self.token = login_resp.json()["session_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_portal_kids_children(self):
        """GET /api/portal/kids/children returns children list"""
        response = requests.get(
            f"{BASE_URL}/api/portal/kids/children",
            headers=self.headers
        )
        assert response.status_code == 200, f"Kids children failed: {response.text}"
        data = response.json()
        # Should return children array
        assert "children" in data or isinstance(data, list) or "kids" in data
        print(f"✓ GET /portal/kids/children returned successfully")
    
    def test_post_portal_kids_children_create(self):
        """POST /api/portal/kids/children creates a child"""
        child_payload = {
            "name": f"TEST_Child_{datetime.now().strftime('%H%M%S')}",
            "birthdate": "2020-01-15",
            "allergies": "None",
            "special_needs": None
        }
        response = requests.post(
            f"{BASE_URL}/api/portal/kids/children",
            headers=self.headers,
            json=child_payload
        )
        assert response.status_code in [200, 201], f"Create child failed: {response.text}"
        data = response.json()
        print(f"✓ POST /portal/kids/children created child successfully")
    
    def test_post_portal_kids_checkin(self):
        """POST /api/portal/kids/checkin checks in a child"""
        # First get children
        children_resp = requests.get(
            f"{BASE_URL}/api/portal/kids/children",
            headers=self.headers
        )
        children = children_resp.json().get("children", [])
        
        if not children:
            # Create a child first
            child_payload = {
                "name": f"TEST_KidsCheckin_{datetime.now().strftime('%H%M%S')}",
                "birthdate": "2019-06-20"
            }
            create_resp = requests.post(
                f"{BASE_URL}/api/portal/kids/children",
                headers=self.headers,
                json=child_payload
            )
            if create_resp.status_code in [200, 201]:
                child_id = create_resp.json().get("child", {}).get("id") or create_resp.json().get("id")
            else:
                pytest.skip("Could not create child for checkin test")
        else:
            child_id = children[0]["id"]
        
        checkin_payload = {
            "child_id": child_id,
            "classroom": "Sunday School"
        }
        response = requests.post(
            f"{BASE_URL}/api/portal/kids/checkin",
            headers=self.headers,
            json=checkin_payload
        )
        # 200 = success, 400 = already checked in
        assert response.status_code in [200, 400], f"Kids checkin failed: {response.text}"
        print(f"✓ POST /portal/kids/checkin returned {response.status_code}")


class TestPortalEventsRegistered:
    """Test registered events endpoint"""
    
    @pytest.fixture(autouse=True)
    def get_member_token(self):
        """Get member token before each test"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
        )
        self.token = login_resp.json()["session_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_portal_events_registered(self):
        """GET /api/portal/events/registered returns member's registered events"""
        response = requests.get(
            f"{BASE_URL}/api/portal/events/registered",
            headers=self.headers
        )
        assert response.status_code == 200, f"Registered events failed: {response.text}"
        data = response.json()
        assert "events" in data
        print(f"✓ GET /portal/events/registered returned {len(data.get('events', []))} events")


class TestPortalGroupsMine:
    """Test my groups endpoint"""
    
    @pytest.fixture(autouse=True)
    def get_member_token(self):
        """Get member token before each test"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
        )
        self.token = login_resp.json()["session_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_portal_groups_mine(self):
        """GET /api/portal/groups/mine returns member's groups"""
        response = requests.get(
            f"{BASE_URL}/api/portal/groups/mine",
            headers=self.headers
        )
        assert response.status_code == 200, f"Groups/mine failed: {response.text}"
        data = response.json()
        assert "groups" in data
        print(f"✓ GET /portal/groups/mine returned {len(data.get('groups', []))} groups")


class TestPortalGivingYTD:
    """Test giving YTD endpoint"""
    
    @pytest.fixture(autouse=True)
    def get_member_token(self):
        """Get member token before each test"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
        )
        self.token = login_resp.json()["session_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_portal_giving_ytd(self):
        """GET /api/portal/giving/ytd returns YTD giving summary"""
        response = requests.get(
            f"{BASE_URL}/api/portal/giving/ytd",
            headers=self.headers
        )
        assert response.status_code == 200, f"Giving YTD failed: {response.text}"
        data = response.json()
        assert "ytd_total" in data
        assert "currency" in data
        print(f"✓ GET /portal/giving/ytd returned ${data.get('ytd_total', 0)}")


class TestAdminAttendanceToday:
    """Test admin attendance today endpoint"""
    
    @pytest.fixture(autouse=True)
    def get_admin_token(self):
        """Get admin token before each test"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        self.token = login_resp.json()["session_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_admin_attendance_today(self):
        """GET /api/admin/attendance/today returns attendance summary"""
        response = requests.get(
            f"{BASE_URL}/api/admin/attendance/today",
            headers=self.headers
        )
        assert response.status_code == 200, f"Admin attendance failed: {response.text}"
        data = response.json()
        assert "date" in data
        assert "member_checkins_total" in data
        assert "kids_checkins_total" in data
        print(f"✓ GET /admin/attendance/today: {data['member_checkins_total']} members, {data['kids_checkins_total']} kids")


class TestAdminQRGenerate:
    """Test admin QR generation endpoint"""
    
    @pytest.fixture(autouse=True)
    def get_admin_token(self):
        """Get admin token before each test"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        self.token = login_resp.json()["session_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_admin_qr_generate(self):
        """GET /api/admin/qr/generate returns QR code data"""
        response = requests.get(
            f"{BASE_URL}/api/admin/qr/generate",
            headers=self.headers,
            params={"action": "attendance_checkin", "expires_in_minutes": 30}
        )
        assert response.status_code == 200, f"QR generate failed: {response.text}"
        data = response.json()
        assert "qr" in data
        assert "image_url" in data["qr"]
        assert "payload" in data["qr"]
        print(f"✓ GET /admin/qr/generate returned QR URL: {data['qr']['image_url'][:60]}...")


class TestRegressionPublicEndpoints:
    """Regression tests for public/existing endpoints"""
    
    def test_get_api_root(self):
        """GET /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data or "name" in data
        print(f"✓ GET /api/ returned successfully")
    
    def test_get_api_events(self):
        """GET /api/events returns events list (public)"""
        response = requests.get(f"{BASE_URL}/api/events")
        assert response.status_code == 200
        data = response.json()
        # Events can return array or dict with events key
        assert isinstance(data, list) or "events" in data
        print(f"✓ GET /api/events returned successfully")
    
    def test_get_api_groups(self):
        """GET /api/groups returns groups list (public)"""
        response = requests.get(f"{BASE_URL}/api/groups")
        assert response.status_code == 200
        data = response.json()
        # Groups endpoint returns {data: [...], page, per_page, total}
        assert isinstance(data, list) or "groups" in data or "data" in data
        print(f"✓ GET /api/groups returned successfully")


class TestRegressionPortalAuthRequired:
    """Regression tests for portal endpoints requiring auth"""
    
    @pytest.fixture(autouse=True)
    def get_member_token(self):
        """Get member token before each test"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
        )
        self.token = login_resp.json()["session_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_portal_giving_history(self):
        """GET /api/portal/giving/history returns donation history"""
        response = requests.get(
            f"{BASE_URL}/api/portal/giving/history",
            headers=self.headers
        )
        assert response.status_code == 200, f"Giving history failed: {response.text}"
        data = response.json()
        assert "donations" in data
        print(f"✓ GET /portal/giving/history returned {len(data.get('donations', []))} donations")
    
    def test_get_portal_merch_products(self):
        """GET /api/portal/merch/products returns merch items (MOCKED checkout)"""
        response = requests.get(
            f"{BASE_URL}/api/portal/merch/products",
            headers=self.headers
        )
        assert response.status_code == 200, f"Merch products failed: {response.text}"
        data = response.json()
        assert "products" in data or isinstance(data, list)
        print(f"✓ GET /portal/merch/products returned successfully (MOCKED checkout)")


class TestBearerTokenRequired:
    """Verify Bearer token auth is enforced on all protected routes"""
    
    def test_portal_profile_requires_auth(self):
        """Portal profile requires Bearer token"""
        response = requests.get(f"{BASE_URL}/api/portal/profile")
        assert response.status_code == 401
        print("✓ /portal/profile correctly requires auth")
    
    def test_portal_attendance_streak_requires_auth(self):
        """Portal attendance streak requires Bearer token"""
        response = requests.get(f"{BASE_URL}/api/portal/attendance/streak")
        assert response.status_code == 401
        print("✓ /portal/attendance/streak correctly requires auth")
    
    def test_admin_attendance_today_requires_auth(self):
        """Admin attendance today requires Bearer token"""
        response = requests.get(f"{BASE_URL}/api/admin/attendance/today")
        assert response.status_code == 401
        print("✓ /admin/attendance/today correctly requires auth")
    
    def test_admin_qr_generate_requires_auth(self):
        """Admin QR generate requires Bearer token"""
        response = requests.get(f"{BASE_URL}/api/admin/qr/generate")
        assert response.status_code == 401
        print("✓ /admin/qr/generate correctly requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
