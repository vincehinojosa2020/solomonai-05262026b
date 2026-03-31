"""
Iteration 63: Post-Refactor API Tests
Tests for Solomon AI Church Management Platform after massive modular monolith refactoring.
server.py went from 17,828 lines to 255 lines with 492 routes across 30 domain files.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from /app/memory/test_credentials.md
PLATFORM_ADMIN = {"email": "admin@solomonai.us", "password": "Demo2026!"}
CHURCH_ADMIN = {"email": "shannonnieman1030@gmail.com", "password": "Demo2026!"}
PORTAL_MEMBER = {"email": "member@abundant.church", "password": "Demo2026!"}


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """GET /api/health returns ok status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print(f"✓ Health check passed: {data}")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_platform_admin_login(self):
        """Platform admin login via /api/auth/login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == PLATFORM_ADMIN["email"]
        assert data["role"] == "platform_admin"
        assert "session_token" in data
        print(f"✓ Platform admin login: {data['name']} ({data['role']})")
    
    def test_church_admin_login(self):
        """Church admin login via /api/auth/login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == CHURCH_ADMIN["email"]
        assert data["role"] == "church_admin"
        assert "tenant_id" in data
        assert "session_token" in data
        print(f"✓ Church admin login: {data['name']} (tenant: {data['tenant_id']})")
    
    def test_portal_member_login(self):
        """Portal member login via /api/auth/login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PORTAL_MEMBER)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == PORTAL_MEMBER["email"]
        assert data["role"] == "member"
        assert "session_token" in data
        print(f"✓ Portal member login: {data['name']} ({data['role']})")
    
    def test_invalid_credentials(self):
        """Invalid credentials return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")


@pytest.fixture
def admin_session():
    """Get authenticated session for church admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
    if response.status_code != 200:
        pytest.skip("Church admin login failed")
    token = response.json().get("session_token")
    session = requests.Session()
    session.cookies.set("session_token", token)
    return session


@pytest.fixture
def member_session():
    """Get authenticated session for portal member"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=PORTAL_MEMBER)
    if response.status_code != 200:
        pytest.skip("Portal member login failed")
    token = response.json().get("session_token")
    session = requests.Session()
    session.cookies.set("session_token", token)
    return session


class TestAdminEndpoints:
    """Admin API endpoint tests - requires church admin auth"""
    
    def test_admin_members(self, admin_session):
        """GET /api/admin/members returns member list"""
        response = admin_session.get(f"{BASE_URL}/api/admin/members")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert data["total"] > 0
        print(f"✓ Admin members: {data['total']} members")
    
    def test_admin_groups(self, admin_session):
        """GET /api/admin/groups returns groups list"""
        response = admin_session.get(f"{BASE_URL}/api/admin/groups")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert data["total"] > 0
        print(f"✓ Admin groups: {data['total']} groups")
    
    def test_admin_events(self, admin_session):
        """GET /api/admin/events returns events list"""
        response = admin_session.get(f"{BASE_URL}/api/admin/events")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        print(f"✓ Admin events: {data['total']} events")
    
    def test_admin_giving_summary(self, admin_session):
        """GET /api/admin/giving/summary returns giving data"""
        response = admin_session.get(f"{BASE_URL}/api/admin/giving/summary")
        assert response.status_code == 200
        data = response.json()
        assert "ytd_total" in data
        assert "mtd_total" in data
        print(f"✓ Admin giving summary: YTD ${data['ytd_total']}, MTD ${data['mtd_total']}")
    
    def test_admin_services_plans(self, admin_session):
        """GET /api/admin/services/plans returns services"""
        response = admin_session.get(f"{BASE_URL}/api/admin/services/plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        print(f"✓ Admin services: {len(data['plans'])} service plans")


class TestPortalEndpoints:
    """Portal (member-facing) API endpoint tests"""
    
    def test_portal_profile(self, member_session):
        """GET /api/portal/profile returns member profile"""
        response = member_session.get(f"{BASE_URL}/api/portal/profile")
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "person" in data
        assert "giving" in data
        print(f"✓ Portal profile: {data['user']['name']}")
    
    def test_portal_me(self, member_session):
        """GET /api/portal/me returns member profile (alias)"""
        response = member_session.get(f"{BASE_URL}/api/portal/me")
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        print(f"✓ Portal me: {data['user']['email']}")
    
    def test_portal_groups(self, member_session):
        """GET /api/portal/groups returns member's groups"""
        response = member_session.get(f"{BASE_URL}/api/portal/groups")
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        print(f"✓ Portal groups: {len(data['groups'])} groups")
    
    def test_portal_events(self, member_session):
        """GET /api/portal/events returns upcoming events"""
        response = member_session.get(f"{BASE_URL}/api/portal/events")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        print(f"✓ Portal events: {len(data['events'])} events")
    
    def test_portal_giving_history(self, member_session):
        """GET /api/portal/giving/history returns giving history"""
        response = member_session.get(f"{BASE_URL}/api/portal/giving/history")
        assert response.status_code == 200
        data = response.json()
        assert "donations" in data
        print(f"✓ Portal giving history: {len(data['donations'])} donations")


class TestCrossTenantIsolation:
    """Verify tenant data isolation after refactor"""
    
    def test_tenant_isolation_groups(self):
        """Different tenants see different group counts"""
        # Login as Shannon (abundant-east-001)
        resp1 = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        token1 = resp1.json().get("session_token")
        
        # Login as Cristoviene admin
        resp2 = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@cristoviene.church",
            "password": "Demo2026!"
        })
        if resp2.status_code != 200:
            pytest.skip("Cristoviene admin login failed")
        token2 = resp2.json().get("session_token")
        
        # Get groups for each tenant
        session1 = requests.Session()
        session1.cookies.set("session_token", token1)
        groups1 = session1.get(f"{BASE_URL}/api/admin/groups").json()
        
        session2 = requests.Session()
        session2.cookies.set("session_token", token2)
        groups2 = session2.get(f"{BASE_URL}/api/admin/groups").json()
        
        # Abundant East should have many groups, Cristoviene should have fewer
        assert groups1["total"] != groups2["total"], "Tenant isolation may be broken"
        print(f"✓ Tenant isolation: Abundant East has {groups1['total']} groups, Cristoviene has {groups2['total']} groups")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
