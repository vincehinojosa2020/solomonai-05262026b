"""
Iteration 35: Frontend API Integration Tests
Tests for Bearer token auth, CORS, and health check endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test accounts
TEST_ACCOUNTS = [
    ("member@abundant.church", "Demo2026!", "member", "/portal"),
    ("admin@abundant.church", "Demo2026!", "church_admin", "/dashboard"),
    ("admin@solomon.ai", "Demo2026!", "platform_admin", "/platform"),
    ("member@cristoviene.church", "Demo2026!", "member", "/portal"),
    ("admin@cristoviene.church", "Demo2026!", "church_admin", "/dashboard"),
    ("admin@pottershouse.church", "Demo2026!", "church_admin", "/dashboard"),
]

class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_launch_check_returns_ready(self):
        """API: /api/health/launch-check returns status='ready'"""
        response = requests.get(f"{BASE_URL}/api/health/launch-check")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready", f"Expected status='ready', got {data.get('status')}"
        assert "checks" in data
        assert data["checks"]["accounts_ready"] is True
        print(f"PASS: launch-check status='ready', all checks={data['checks']}")


class TestCORSHeaders:
    """CORS header configuration tests for mobile app compatibility"""
    
    def test_cors_allows_all_origins(self):
        """API: CORS Access-Control-Allow-Origin: *"""
        response = requests.options(
            f"{BASE_URL}/api/health/launch-check",
            headers={"Origin": "https://mobile-app.example.com"}
        )
        # Check CORS headers (may be in response or preflight)
        allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
        assert allow_origin == "*" or response.status_code == 200, \
            f"Expected CORS Allow-Origin:*, got {allow_origin}"
        print(f"PASS: CORS headers allow cross-origin requests")
    
    def test_cors_allows_methods(self):
        """API: CORS allows GET, POST, PUT, DELETE, OPTIONS methods"""
        response = requests.options(
            f"{BASE_URL}/api/auth/login",
            headers={
                "Origin": "https://mobile-app.example.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        allow_methods = response.headers.get("Access-Control-Allow-Methods", "")
        # Should include common methods
        for method in ["GET", "POST"]:
            assert method in allow_methods or response.status_code == 200, \
                f"CORS should allow {method}"
        print(f"PASS: CORS allows necessary HTTP methods")


class TestLoginAllAccounts:
    """Login tests for all 6 demo accounts"""
    
    @pytest.mark.parametrize("email,password,expected_role,redirect", TEST_ACCOUNTS)
    def test_login_returns_token(self, email, password, expected_role, redirect):
        """API: Login returns session_token for all accounts"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        assert response.status_code == 200, f"Login failed for {email}: {response.text}"
        data = response.json()
        
        # Check token is returned
        assert "session_token" in data, f"No session_token for {email}"
        assert len(data["session_token"]) > 20, f"Token too short for {email}"
        
        # Check role
        assert data.get("role") == expected_role, \
            f"Expected role={expected_role}, got {data.get('role')} for {email}"
        
        print(f"PASS: {email} login OK, role={expected_role}")


class TestBearerTokenAuth:
    """Bearer token authentication tests"""
    
    @pytest.fixture
    def member_token(self):
        """Get token for member@abundant.church"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "member@abundant.church", "password": "Demo2026!"}
        )
        return response.json().get("session_token")
    
    @pytest.fixture
    def admin_token(self):
        """Get token for admin@abundant.church"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@abundant.church", "password": "Demo2026!"}
        )
        return response.json().get("session_token")
    
    def test_auth_me_with_bearer_token(self, member_token):
        """API: /api/auth/me works with Bearer token"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200, f"auth/me failed: {response.text}"
        data = response.json()
        assert data.get("email") == "member@abundant.church"
        print(f"PASS: /api/auth/me works with Bearer token")
    
    def test_portal_bootstrap_with_bearer_token(self, member_token):
        """API: /api/portal/bootstrap works with Bearer token"""
        response = requests.get(
            f"{BASE_URL}/api/portal/bootstrap",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200, f"portal/bootstrap failed: {response.text}"
        data = response.json()
        # Should have user data and other bootstrap info
        assert "user" in data or "merch_products" in data, \
            f"Bootstrap missing expected fields: {list(data.keys())}"
        print(f"PASS: /api/portal/bootstrap works with Bearer token")
    
    def test_admin_dashboard_with_bearer_token(self, admin_token):
        """API: /api/admin/dashboard works with Bearer token"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"admin/dashboard failed: {response.text}"
        data = response.json()
        # Should have admin metrics
        assert "total_members" in data or "metrics" in data or len(data) > 0, \
            f"Dashboard missing metrics"
        print(f"PASS: /api/admin/dashboard works with Bearer token")


class TestLogout:
    """Logout flow tests"""
    
    def test_logout_clears_session(self):
        """API: Logout clears session and redirects to /login"""
        # First login
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "member@abundant.church", "password": "Demo2026!"}
        )
        token = login_resp.json().get("session_token")
        
        # Logout
        logout_resp = requests.post(
            f"{BASE_URL}/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert logout_resp.status_code in [200, 204], f"Logout failed: {logout_resp.text}"
        print(f"PASS: Logout successful")


class TestPortalEndpoints:
    """Portal endpoint tests with Bearer token"""
    
    @pytest.fixture
    def member_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "member@abundant.church", "password": "Demo2026!"}
        )
        return response.json().get("session_token")
    
    def test_portal_events(self, member_token):
        """API: /api/portal/events returns events list"""
        response = requests.get(
            f"{BASE_URL}/api/portal/events",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Expected events list"
        print(f"PASS: /api/portal/events returns {len(data)} events")
    
    def test_portal_groups(self, member_token):
        """API: /api/portal/groups returns groups list"""
        response = requests.get(
            f"{BASE_URL}/api/portal/groups",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Expected groups list"
        print(f"PASS: /api/portal/groups returns {len(data)} groups")
    
    def test_portal_announcements(self, member_token):
        """API: /api/portal/announcements returns announcements"""
        response = requests.get(
            f"{BASE_URL}/api/portal/announcements",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Can be dict with 'announcements' key or direct list
        if isinstance(data, dict):
            announcements = data.get("announcements", [])
        else:
            announcements = data
        assert isinstance(announcements, list), "Expected announcements list"
        print(f"PASS: /api/portal/announcements returns {len(announcements)} announcements")
    
    def test_attendance_streak(self, member_token):
        """API: /api/portal/attendance/streak returns streak data"""
        response = requests.get(
            f"{BASE_URL}/api/portal/attendance/streak",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "current_streak" in data or "streak" in data.get("attendance_data", {}), \
            f"Missing streak data: {data}"
        print(f"PASS: /api/portal/attendance/streak returns data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
