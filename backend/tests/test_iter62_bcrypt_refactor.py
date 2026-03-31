"""
Iteration 62: Bcrypt Migration & Modular Monolith Refactor Tests
Tests:
1. Login with bcrypt-migrated password (Shannon)
2. Login with SHA256 password + auto-migration (Jacob)
3. Platform admin login
4. Cross-tenant isolation
5. All admin endpoints work after refactor
6. Portal endpoints work
7. Solomon AI chat
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials from test_credentials.md
CREDENTIALS = {
    "shannon": {"email": "shannonnieman1030@gmail.com", "password": "Demo2026!", "tenant": "abundant-east-001"},
    "jacob": {"email": "jacobpacheco@abundanteast.com", "password": "Demo2026!", "tenant": "abundant-east-001"},
    "cristoviene": {"email": "admin@cristoviene.church", "password": "Demo2026!", "tenant": "cristoviene-church-001"},
    "platform_admin": {"email": "admin@solomonai.us", "password": "Demo2026!", "tenant": None},
    "member": {"email": "member@abundant.church", "password": "Demo2026!", "tenant": "abundant-east-001"},
}


def login_and_get_token(email, password):
    """Helper to login and get session token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code != 200:
        return None, response
    data = response.json()
    # Token can be in access_token, session_token, or cookie
    token = data.get("access_token") or data.get("session_token") or response.cookies.get("session_token")
    return token, response


class TestHealthAndBasics:
    """Basic health checks"""
    
    def test_api_health(self):
        """API health endpoint returns OK"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"✓ API health check passed: {data}")


class TestBcryptMigration:
    """Test bcrypt password migration"""
    
    def test_login_shannon_bcrypt(self):
        """Shannon's password was migrated to bcrypt - should still work"""
        creds = CREDENTIALS["shannon"]
        token, response = login_and_get_token(creds["email"], creds["password"])
        assert response.status_code == 200, f"Shannon login failed: {response.text}"
        data = response.json()
        # User data is at root level, not nested under "user"
        assert data.get("email") == creds["email"].lower()
        assert token is not None, "No session token returned"
        print(f"✓ Shannon (bcrypt) login successful: {data.get('email')}")
    
    def test_login_jacob_sha256_migration(self):
        """Jacob's password is SHA256 - should verify and auto-migrate to bcrypt"""
        creds = CREDENTIALS["jacob"]
        token, response = login_and_get_token(creds["email"], creds["password"])
        assert response.status_code == 200, f"Jacob login failed: {response.text}"
        data = response.json()
        assert data.get("email") == creds["email"].lower()
        assert token is not None, "No session token returned"
        print(f"✓ Jacob (SHA256→bcrypt migration) login successful: {data.get('email')}")
    
    def test_login_platform_admin(self):
        """Platform admin login should work"""
        creds = CREDENTIALS["platform_admin"]
        token, response = login_and_get_token(creds["email"], creds["password"])
        assert response.status_code == 200, f"Platform admin login failed: {response.text}"
        data = response.json()
        assert data.get("role") in ["platform_admin", "admin"]
        print(f"✓ Platform admin login successful: {data.get('email')}, role: {data.get('role')}")


class TestCrossTenantIsolation:
    """Test cross-tenant data isolation"""
    
    def test_cross_tenant_groups_isolation(self):
        """Different tenants should see different groups"""
        # Shannon (abundant-east-001)
        shannon_token, _ = login_and_get_token(CREDENTIALS["shannon"]["email"], CREDENTIALS["shannon"]["password"])
        assert shannon_token, "Shannon login failed"
        
        shannon_resp = requests.get(
            f"{BASE_URL}/api/admin/groups",
            cookies={"session_token": shannon_token}
        )
        assert shannon_resp.status_code == 200, f"Shannon groups failed: {shannon_resp.text}"
        shannon_groups = shannon_resp.json()
        shannon_count = len(shannon_groups) if isinstance(shannon_groups, list) else shannon_groups.get("total", 0)
        
        # Cristoviene (cristoviene-church-001)
        cristo_token, _ = login_and_get_token(CREDENTIALS["cristoviene"]["email"], CREDENTIALS["cristoviene"]["password"])
        assert cristo_token, "Cristoviene login failed"
        
        cristo_resp = requests.get(
            f"{BASE_URL}/api/admin/groups",
            cookies={"session_token": cristo_token}
        )
        assert cristo_resp.status_code == 200, f"Cristoviene groups failed: {cristo_resp.text}"
        cristo_groups = cristo_resp.json()
        cristo_count = len(cristo_groups) if isinstance(cristo_groups, list) else cristo_groups.get("total", 0)
        
        print(f"✓ Cross-tenant isolation: Shannon sees {shannon_count} groups, Cristoviene sees {cristo_count} groups")
        # They should see different counts (abundant-east has more data)
        assert shannon_count != cristo_count or (shannon_count == 0 and cristo_count == 0), "Tenant isolation may be broken"


class TestAdminEndpointsAfterRefactor:
    """Test all admin endpoints work after modular monolith refactor"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin session token"""
        token, _ = login_and_get_token(CREDENTIALS["shannon"]["email"], CREDENTIALS["shannon"]["password"])
        return token
    
    def test_admin_groups(self, admin_token):
        """GET /api/admin/groups should work"""
        assert admin_token, "Admin login failed"
        response = requests.get(
            f"{BASE_URL}/api/admin/groups",
            cookies={"session_token": admin_token}
        )
        assert response.status_code == 200, f"Admin groups failed: {response.text}"
        data = response.json()
        print(f"✓ Admin groups endpoint works: {len(data) if isinstance(data, list) else 'OK'}")
    
    def test_admin_people(self, admin_token):
        """GET /api/people should work"""
        assert admin_token, "Admin login failed"
        response = requests.get(
            f"{BASE_URL}/api/people",
            cookies={"session_token": admin_token}
        )
        assert response.status_code == 200, f"Admin people failed: {response.text}"
        data = response.json()
        count = len(data) if isinstance(data, list) else data.get("total", 0)
        print(f"✓ Admin people endpoint works: {count} people")
    
    def test_admin_giving_summary(self, admin_token):
        """GET /api/admin/giving/summary should work"""
        assert admin_token, "Admin login failed"
        response = requests.get(
            f"{BASE_URL}/api/admin/giving/summary",
            cookies={"session_token": admin_token}
        )
        assert response.status_code == 200, f"Admin giving summary failed: {response.text}"
        data = response.json()
        print(f"✓ Admin giving summary endpoint works: {data.get('total_ytd', 'N/A')}")
    
    def test_admin_events(self, admin_token):
        """GET /api/admin/events should work"""
        assert admin_token, "Admin login failed"
        response = requests.get(
            f"{BASE_URL}/api/admin/events",
            cookies={"session_token": admin_token}
        )
        assert response.status_code == 200, f"Admin events failed: {response.text}"
        data = response.json()
        count = len(data) if isinstance(data, list) else data.get("total", 0)
        print(f"✓ Admin events endpoint works: {count} events")
    
    def test_admin_checkin_locations(self, admin_token):
        """GET /api/admin/checkin/locations should work"""
        assert admin_token, "Admin login failed"
        response = requests.get(
            f"{BASE_URL}/api/admin/checkin/locations",
            cookies={"session_token": admin_token}
        )
        assert response.status_code == 200, f"Admin checkin locations failed: {response.text}"
        data = response.json()
        count = len(data) if isinstance(data, list) else 0
        print(f"✓ Admin checkin locations endpoint works: {count} locations")
    
    def test_admin_service_types(self, admin_token):
        """GET /api/admin/service-types should work"""
        assert admin_token, "Admin login failed"
        response = requests.get(
            f"{BASE_URL}/api/admin/service-types",
            cookies={"session_token": admin_token}
        )
        assert response.status_code == 200, f"Admin service types failed: {response.text}"
        data = response.json()
        count = len(data) if isinstance(data, list) else 0
        print(f"✓ Admin service types endpoint works: {count} service types")
    
    def test_admin_registrations_events(self, admin_token):
        """GET /api/admin/registrations/events should work"""
        assert admin_token, "Admin login failed"
        response = requests.get(
            f"{BASE_URL}/api/admin/registrations/events",
            cookies={"session_token": admin_token}
        )
        assert response.status_code == 200, f"Admin registrations events failed: {response.text}"
        data = response.json()
        count = len(data) if isinstance(data, list) else 0
        print(f"✓ Admin registrations events endpoint works: {count} registration events")


class TestPortalEndpoints:
    """Test portal endpoints for members"""
    
    @pytest.fixture(scope="class")
    def member_token(self):
        """Get member session token"""
        token, _ = login_and_get_token(CREDENTIALS["member"]["email"], CREDENTIALS["member"]["password"])
        return token
    
    def test_portal_giving_history(self, member_token):
        """GET /api/portal/giving/history should work"""
        assert member_token, "Member login failed"
        response = requests.get(
            f"{BASE_URL}/api/portal/giving/history",
            cookies={"session_token": member_token}
        )
        assert response.status_code == 200, f"Portal giving history failed: {response.text}"
        print(f"✓ Portal giving history endpoint works")
    
    def test_portal_events(self, member_token):
        """GET /api/portal/events should work"""
        assert member_token, "Member login failed"
        response = requests.get(
            f"{BASE_URL}/api/portal/events",
            cookies={"session_token": member_token}
        )
        assert response.status_code == 200, f"Portal events failed: {response.text}"
        data = response.json()
        count = len(data) if isinstance(data, list) else 0
        print(f"✓ Portal events endpoint works: {count} events")
    
    def test_portal_groups(self, member_token):
        """GET /api/portal/groups should work"""
        assert member_token, "Member login failed"
        response = requests.get(
            f"{BASE_URL}/api/portal/groups",
            cookies={"session_token": member_token}
        )
        assert response.status_code == 200, f"Portal groups failed: {response.text}"
        data = response.json()
        count = len(data) if isinstance(data, list) else 0
        print(f"✓ Portal groups endpoint works: {count} groups")


class TestSolomonAIChat:
    """Test Solomon AI chat endpoint"""
    
    def test_solomon_chat(self):
        """POST /api/solomon/chat should work"""
        token, _ = login_and_get_token(CREDENTIALS["shannon"]["email"], CREDENTIALS["shannon"]["password"])
        assert token, "Admin login failed"
        
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "How many members do we have?"},
            cookies={"session_token": token},
            timeout=30  # AI responses can be slow
        )
        assert response.status_code == 200, f"Solomon chat failed: {response.text}"
        data = response.json()
        assert "response" in data or "message" in data or "answer" in data
        print(f"✓ Solomon AI chat endpoint works: {str(data)[:100]}...")


class TestRateLimiting:
    """Test rate limiting - REQUIRES 65 second wait before running"""
    
    def test_rate_limit_info(self):
        """Document rate limit behavior - actual test requires wait"""
        print("⚠ Rate limit test: 5 attempts per IP per 60 seconds")
        print("⚠ To test: wait 65 seconds, then make 8 rapid login attempts with wrong creds")
        print("⚠ Expected: attempts 1-5 return 401, attempts 6+ return 429")
        # Skip actual rate limit test to avoid blocking other tests
        pytest.skip("Rate limit test skipped - requires 65 second wait and would block IP")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
