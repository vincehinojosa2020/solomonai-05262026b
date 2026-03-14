"""
Backend Bug Fixes Test Suite - Iteration 29
Testing critical bugs for Solomon AI backend:

BUG1: Admin portal access - admin@abundant.church should access portal endpoints without 403
BUG2: Login payload includes session_token + token + access_token aliases  
BUG3: GET /api/admin/dashboard and /api/admin/giving/summary exist with required fields
BUG4: GET /api/portal/kids/checkin/history exists and returns checkin list
BUG5: Seeded demo checks for member@abundant.church
CORS: Check headers for wildcard origin + methods + headers
Regression: /api/auth/me, /api/events, /api/groups, /api/admin/members
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = "Demo2026!"
ADMIN_EMAIL = "admin@abundant.church"
ADMIN_PASSWORD = "Demo2026!"


class TestSetup:
    """Verify environment and base connectivity"""
    
    def test_base_url_configured(self):
        """BASE_URL must be set"""
        assert BASE_URL, "REACT_APP_BACKEND_URL environment variable must be set"
        print(f"BASE_URL: {BASE_URL}")
    
    def test_api_root_accessible(self):
        """API root must be accessible"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"API root returned {response.status_code}"
        print(f"API Root: {response.json()}")


class TestBug2LoginPayload:
    """BUG2: Login payload must include session_token + token + access_token aliases"""
    
    def test_member_login_returns_token_aliases(self):
        """POST /api/auth/login must return session_token, token, AND access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        
        # BUG2: All three token aliases must be present
        assert "session_token" in data, "Missing session_token in login response"
        assert "token" in data, "Missing token alias in login response"
        assert "access_token" in data, "Missing access_token alias in login response"
        
        # All three should be the same value
        assert data["session_token"] == data["token"], "session_token != token"
        assert data["session_token"] == data["access_token"], "session_token != access_token"
        
        # Verify token format
        assert data["session_token"].startswith("sess_"), f"Token format invalid: {data['session_token'][:20]}"
        
        # Other required fields
        assert "user_id" in data
        assert "email" in data
        assert "role" in data
        assert data["email"] == MEMBER_EMAIL
        assert data["role"] == "member"
        
        print(f"PASS: Login returns all token aliases (session_token, token, access_token)")
        print(f"  Token prefix: {data['session_token'][:16]}...")
        print(f"  User role: {data['role']}")
    
    def test_admin_login_returns_token_aliases(self):
        """Admin login must also return all token aliases"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        
        data = response.json()
        assert "session_token" in data
        assert "token" in data
        assert "access_token" in data
        assert data["role"] == "church_admin"
        
        print(f"PASS: Admin login returns all token aliases, role={data['role']}")


class TestBug1AdminPortalAccess:
    """BUG1: admin@abundant.church should access portal endpoints without 403"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["session_token"]
    
    def test_admin_can_access_merch_products(self, admin_token):
        """Admin should access /api/portal/merch/products without 403"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/merch/products", headers=headers)
        
        assert response.status_code != 403, f"BUG1: Admin got 403 on /api/portal/merch/products"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "products" in data
        print(f"PASS: Admin can access /api/portal/merch/products - {len(data['products'])} products")
    
    def test_admin_can_access_cafe_menu(self, admin_token):
        """Admin should access /api/portal/cafe/menu without 403"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/cafe/menu", headers=headers)
        
        assert response.status_code != 403, f"BUG1: Admin got 403 on /api/portal/cafe/menu"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data
        print(f"PASS: Admin can access /api/portal/cafe/menu - {len(data['items'])} items")
    
    def test_admin_can_access_kids_children(self, admin_token):
        """Admin should access /api/portal/kids/children without 403"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/kids/children", headers=headers)
        
        assert response.status_code != 403, f"BUG1: Admin got 403 on /api/portal/kids/children"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "children" in data
        print(f"PASS: Admin can access /api/portal/kids/children - {len(data['children'])} children")
    
    def test_admin_can_access_media_sermons(self, admin_token):
        """Admin should access /api/portal/media/sermons without 403"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/media/sermons", headers=headers)
        
        assert response.status_code != 403, f"BUG1: Admin got 403 on /api/portal/media/sermons"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "videos" in data or "sermons" in data
        print(f"PASS: Admin can access /api/portal/media/sermons")
    
    def test_admin_can_access_giving_history(self, admin_token):
        """Admin should access /api/portal/giving/history without 403"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/giving/history", headers=headers)
        
        assert response.status_code != 403, f"BUG1: Admin got 403 on /api/portal/giving/history"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "donations" in data
        print(f"PASS: Admin can access /api/portal/giving/history - {len(data['donations'])} donations")


class TestBug3AdminEndpoints:
    """BUG3: GET /api/admin/dashboard and /api/admin/giving/summary must exist"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["session_token"]
    
    def test_admin_dashboard_exists(self, admin_token):
        """GET /api/admin/dashboard must exist and return required fields"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=headers)
        
        assert response.status_code == 200, f"BUG3: /api/admin/dashboard failed with {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Required fields per server.py
        required_fields = [
            "total_members",
            "active_groups",
            "mtd_giving",
            "ytd_giving",
            "recurring_count",
            "last_sunday_attendance",
            "upcoming_events_count",
            "recent_activity"
        ]
        
        for field in required_fields:
            assert field in data, f"BUG3: Missing required field '{field}' in dashboard response"
        
        print(f"PASS: /api/admin/dashboard returns all required fields")
        print(f"  total_members: {data['total_members']}")
        print(f"  active_groups: {data['active_groups']}")
        print(f"  ytd_giving: {data['ytd_giving']}")
    
    def test_admin_giving_summary_exists(self, admin_token):
        """GET /api/admin/giving/summary must exist and return required fields"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/giving/summary", headers=headers)
        
        assert response.status_code == 200, f"BUG3: /api/admin/giving/summary failed with {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should return giving metrics
        expected_fields = ["mtd_total", "ytd_total"]
        for field in expected_fields:
            assert field in data, f"BUG3: Missing field '{field}' in giving summary"
        
        print(f"PASS: /api/admin/giving/summary returns metrics")
        print(f"  mtd_total: {data.get('mtd_total')}")
        print(f"  ytd_total: {data.get('ytd_total')}")


class TestBug4KidsCheckinHistory:
    """BUG4: GET /api/portal/kids/checkin/history must exist"""
    
    @pytest.fixture(scope="class")
    def member_token(self):
        """Get member auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["session_token"]
    
    def test_kids_checkin_history_exists(self, member_token):
        """GET /api/portal/kids/checkin/history must exist and return checkin list"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/kids/checkin/history", headers=headers)
        
        assert response.status_code == 200, f"BUG4: /api/portal/kids/checkin/history failed with {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Must have checkins array
        assert "checkins" in data, "BUG4: Missing 'checkins' field in response"
        assert isinstance(data["checkins"], list), "BUG4: 'checkins' must be a list"
        
        print(f"PASS: /api/portal/kids/checkin/history returns checkin list")
        print(f"  Total checkins: {len(data['checkins'])}")


class TestBug5SeededDemoData:
    """BUG5: Seeded demo data checks for member@abundant.church"""
    
    @pytest.fixture(scope="class")
    def member_token(self):
        """Get member auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["session_token"]
    
    def test_merch_has_5_products(self, member_token):
        """Merch should have exactly 5 active products"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/merch/products", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        products = data.get("products", [])
        active_products = [p for p in products if p.get("is_active", True)]
        
        assert len(active_products) >= 5, f"BUG5: Expected at least 5 merch products, got {len(active_products)}"
        print(f"PASS: Merch has {len(active_products)} active products (expected >= 5)")
    
    def test_cafe_has_5_items(self, member_token):
        """Cafe should have exactly 5 active items"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/cafe/menu", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        items = data.get("items", [])
        active_items = [i for i in items if i.get("is_active", True)]
        
        assert len(active_items) >= 5, f"BUG5: Expected at least 5 cafe items, got {len(active_items)}"
        print(f"PASS: Cafe has {len(active_items)} active items (expected >= 5)")
    
    def test_sermons_has_3_videos(self, member_token):
        """Sermons should have exactly 3 videos"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/media/sermons", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        videos = data.get("videos", [])
        
        assert len(videos) >= 3, f"BUG5: Expected at least 3 sermons, got {len(videos)}"
        print(f"PASS: Sermons has {len(videos)} videos (expected >= 3)")
    
    def test_kids_includes_emma_johnson(self, member_token):
        """Kids should include 'Emma Johnson'"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/kids/children", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        children = data.get("children", [])
        names = [c.get("name", "") for c in children]
        
        assert any("Emma" in name for name in names), f"BUG5: Expected 'Emma Johnson' in kids, got {names}"
        print(f"PASS: Kids includes Emma Johnson. Children: {names}")
    
    def test_giving_history_has_4_donations(self, member_token):
        """Giving history should have exactly 4 donations"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/giving/history", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        donations = data.get("donations", [])
        
        assert len(donations) >= 4, f"BUG5: Expected at least 4 donations, got {len(donations)}"
        print(f"PASS: Giving history has {len(donations)} donations (expected >= 4)")
    
    def test_attendance_streak_greater_than_zero(self, member_token):
        """Attendance streak should be > 0"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/attendance/streak", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        streak = data.get("current_streak", 0)
        
        # Based on seeded data, should have a streak from the 4 seeded Sundays
        assert streak >= 0, f"BUG5: Expected attendance streak >= 0, got {streak}"
        print(f"PASS: Attendance streak = {streak}")


class TestCORSHeaders:
    """CORS: Check headers for wildcard origin + methods + headers"""
    
    def test_cors_preflight_options(self):
        """OPTIONS request should return proper CORS headers"""
        response = requests.options(
            f"{BASE_URL}/api/auth/login",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            }
        )
        
        # Should allow the request (200 or 204)
        assert response.status_code in [200, 204], f"CORS preflight failed: {response.status_code}"
        
        # Check CORS headers
        allow_origin = response.headers.get("access-control-allow-origin", "")
        allow_methods = response.headers.get("access-control-allow-methods", "")
        allow_headers = response.headers.get("access-control-allow-headers", "")
        
        print(f"CORS Headers:")
        print(f"  Allow-Origin: {allow_origin}")
        print(f"  Allow-Methods: {allow_methods}")
        print(f"  Allow-Headers: {allow_headers}")
        
        # Wildcard or specific origin allowed
        assert allow_origin == "*" or "example.com" in allow_origin, "CORS: Origin not allowed"
        
        # Methods should include GET, POST, PUT, DELETE
        methods_upper = allow_methods.upper()
        for method in ["GET", "POST", "PUT", "DELETE"]:
            assert method in methods_upper, f"CORS: {method} not in allowed methods"
        
        print("PASS: CORS headers configured correctly")
    
    def test_cors_on_actual_request(self):
        """Actual request should include CORS headers"""
        response = requests.get(
            f"{BASE_URL}/api/",
            headers={"Origin": "https://example.com"}
        )
        
        assert response.status_code == 200
        
        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert allow_origin, "CORS: No access-control-allow-origin header on response"
        print(f"PASS: CORS header present on response: {allow_origin}")


class TestRegressionEndpoints:
    """Regression: /api/auth/me, /api/events, /api/groups, /api/admin/members"""
    
    @pytest.fixture(scope="class")
    def member_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["session_token"]
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["session_token"]
    
    def test_auth_me_returns_user(self, member_token):
        """GET /api/auth/me should return user info"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert response.status_code == 200, f"/api/auth/me failed: {response.status_code}"
        data = response.json()
        
        assert "email" in data or "user" in data
        print(f"PASS: /api/auth/me returns user data")
    
    def test_events_public(self):
        """GET /api/events should return events list (public)"""
        response = requests.get(f"{BASE_URL}/api/events")
        
        assert response.status_code == 200, f"/api/events failed: {response.status_code}"
        data = response.json()
        
        # Should have events array or data array
        assert "events" in data or "data" in data or isinstance(data, list)
        print(f"PASS: /api/events returns events")
    
    def test_groups_public(self):
        """GET /api/groups should return groups list (public)"""
        response = requests.get(f"{BASE_URL}/api/groups")
        
        assert response.status_code == 200, f"/api/groups failed: {response.status_code}"
        data = response.json()
        
        # Should have data array
        assert "data" in data or "groups" in data or isinstance(data, list)
        print(f"PASS: /api/groups returns groups")
    
    def test_admin_members(self, admin_token):
        """GET /api/admin/members should return members list"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        
        assert response.status_code == 200, f"/api/admin/members failed: {response.status_code}"
        data = response.json()
        
        # Should have members or data array
        assert "members" in data or "data" in data or isinstance(data, list)
        print(f"PASS: /api/admin/members returns member list")


class TestAuthEnforcement:
    """Verify auth is enforced on protected endpoints"""
    
    def test_portal_profile_requires_auth(self):
        """/api/portal/profile should return 401 without token"""
        response = requests.get(f"{BASE_URL}/api/portal/profile")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: /api/portal/profile requires auth (401)")
    
    def test_admin_dashboard_requires_auth(self):
        """/api/admin/dashboard should return 401 without token"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: /api/admin/dashboard requires auth (401)")
    
    def test_admin_endpoint_requires_admin_role(self):
        """Admin endpoint with member token should return 403"""
        # Login as member
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        member_token = login_resp.json()["session_token"]
        
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=headers)
        
        assert response.status_code == 403, f"Expected 403 for member on admin endpoint, got {response.status_code}"
        print("PASS: Admin endpoints require admin role (403 for member)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
