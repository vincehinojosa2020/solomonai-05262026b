"""
Solomon AI — Iteration 76 Refactoring Regression Tests
Tests that structural refactoring (seed.py split, helpers_ai.py extraction, 
frontend component extraction) did NOT break existing functionality.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PLATFORM_ADMIN = {"email": "admin@solomonai.us", "password": os.environ.get("TEST_PASSWORD", "Demo2026!")}
CHURCH_ADMIN = {"email": "shannonnieman1030@gmail.com", "password": os.environ.get("TEST_PASSWORD", "Demo2026!")}
PORTAL_MEMBER = {"email": "member@abundant.church", "password": os.environ.get("TEST_PASSWORD", "Demo2026!")}


class TestHealthEndpoints:
    """Health check endpoints"""
    
    def test_health_check(self):
        """Backend health returns 200"""
        res = requests.get(f"{BASE_URL}/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        print("✓ Health check passed")
    
    def test_tenant_info(self):
        """Tenant info endpoint works"""
        res = requests.get(f"{BASE_URL}/api/tenant")
        assert res.status_code == 200
        data = res.json()
        assert "name" in data or "church_name" in data
        print(f"✓ Tenant info: {data.get('name', data.get('church_name', 'Unknown'))}")


class TestAuthentication:
    """Authentication flows for all 3 credential types"""
    
    def test_platform_admin_login(self):
        """Platform admin can login"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data or "token" in data or "session_token" in data
        # Role is at top level, not nested
        assert data.get("role") == "platform_admin" or data.get("name") == "Solomon Platform Admin"
        print("✓ Platform admin login successful")
    
    def test_church_admin_login(self):
        """Church admin can login"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        assert res.status_code == 200
        data = res.json()
        assert "token" in data or "session_token" in data
        print("✓ Church admin login successful")
        return data.get("token") or data.get("session_token")
    
    def test_portal_member_login(self):
        """Portal member can login"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json=PORTAL_MEMBER)
        assert res.status_code == 200
        data = res.json()
        assert "token" in data or "session_token" in data
        print("✓ Portal member login successful")
        return data.get("token") or data.get("session_token")


class TestDashboardAPIs:
    """Dashboard and stats APIs"""
    
    @pytest.fixture
    def admin_token(self):
        res = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        if res.status_code == 200:
            data = res.json()
            return data.get("access_token") or data.get("token") or data.get("session_token")
        pytest.skip("Auth failed")
    
    def test_dashboard_stats(self, admin_token):
        """Dashboard stats endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "total_members" in data or "active_members" in data
        print("✓ Dashboard stats loaded")
    
    def test_giving_stats(self, admin_token):
        """Giving stats endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/giving/stats", headers=headers)
        assert res.status_code == 200
        print("✓ Giving stats loaded")
    
    def test_attendance_trend(self, admin_token):
        """Attendance trend endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/dashboard/attendance-trend", headers=headers)
        assert res.status_code == 200
        print("✓ Attendance trend loaded")


class TestSeedDataIntegrity:
    """Verify seed data still exists after refactoring"""
    
    @pytest.fixture
    def admin_token(self):
        res = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        if res.status_code == 200:
            data = res.json()
            return data.get("access_token") or data.get("token") or data.get("session_token")
        pytest.skip("Auth failed")
    
    def test_funds_exist(self, admin_token):
        """Giving funds exist"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/giving/funds", headers=headers)
        assert res.status_code == 200
        data = res.json()
        funds = data.get("funds", data) if isinstance(data, dict) else data
        assert len(funds) > 0, "No funds found"
        print(f"✓ Found {len(funds)} giving funds")
    
    def test_members_exist(self, admin_token):
        """Members exist in database"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/people", headers=headers)
        assert res.status_code == 200
        data = res.json()
        people = data.get("people", data) if isinstance(data, dict) else data
        assert len(people) > 0, "No members found"
        print(f"✓ Found {len(people)} members")
    
    def test_groups_exist(self, admin_token):
        """Groups exist"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/groups", headers=headers)
        assert res.status_code == 200
        data = res.json()
        groups = data.get("groups", data) if isinstance(data, dict) else data
        assert len(groups) > 0, "No groups found"
        print(f"✓ Found {len(groups)} groups")


class TestServicesAPI:
    """Services page APIs"""
    
    @pytest.fixture
    def admin_token(self):
        res = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        if res.status_code == 200:
            data = res.json()
            return data.get("access_token") or data.get("token") or data.get("session_token")
        pytest.skip("Auth failed")
    
    def test_service_plans(self, admin_token):
        """Service plans endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/services/plans", headers=headers)
        assert res.status_code == 200
        print("✓ Service plans loaded")
    
    def test_service_types(self, admin_token):
        """Service types endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/services/types", headers=headers)
        assert res.status_code == 200
        print("✓ Service types loaded")


class TestKidsCheckinAPI:
    """Kids Check-in APIs (tests extracted modals work)"""
    
    @pytest.fixture
    def admin_token(self):
        res = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        if res.status_code == 200:
            data = res.json()
            return data.get("access_token") or data.get("token") or data.get("session_token")
        pytest.skip("Auth failed")
    
    def test_kids_checkins(self, admin_token):
        """Kids checkins endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/kids/checkins", headers=headers)
        assert res.status_code == 200
        print("✓ Kids checkins loaded")
    
    def test_all_kids(self, admin_token):
        """All kids endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/kids/all", headers=headers)
        assert res.status_code == 200
        print("✓ All kids loaded")


class TestPathwaysAPI:
    """Abundant Pathways APIs (tests extracted dialogs work)"""
    
    @pytest.fixture
    def admin_token(self):
        res = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        if res.status_code == 200:
            data = res.json()
            return data.get("access_token") or data.get("token") or data.get("session_token")
        pytest.skip("Auth failed")
    
    def test_pathways_courses(self, admin_token):
        """Pathways courses endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/pathways/courses", headers=headers)
        assert res.status_code == 200
        data = res.json()
        courses = data.get("courses", [])
        print(f"✓ Pathways courses loaded ({len(courses)} courses)")
    
    def test_next_steps_approvals(self, admin_token):
        """Next steps approvals endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/next-steps/approvals", headers=headers)
        assert res.status_code == 200
        print("✓ Next steps approvals loaded")


class TestPlatformAdminAPIs:
    """Platform admin (Godmode) APIs"""
    
    @pytest.fixture
    def platform_token(self):
        res = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        if res.status_code == 200:
            data = res.json()
            return data.get("access_token") or data.get("token") or data.get("session_token")
        pytest.skip("Platform auth failed")
    
    def test_platform_stats(self, platform_token):
        """Platform stats endpoint works"""
        headers = {"Authorization": f"Bearer {platform_token}"}
        res = requests.get(f"{BASE_URL}/api/platform/stats", headers=headers)
        assert res.status_code == 200
        print("✓ Platform stats loaded")
    
    def test_platform_organizations(self, platform_token):
        """Platform organizations endpoint works"""
        headers = {"Authorization": f"Bearer {platform_token}"}
        res = requests.get(f"{BASE_URL}/api/platform/organizations", headers=headers)
        assert res.status_code == 200
        print("✓ Platform organizations loaded")


class TestPortalAPIs:
    """Portal member APIs"""
    
    @pytest.fixture
    def member_token(self):
        res = requests.post(f"{BASE_URL}/api/auth/login", json=PORTAL_MEMBER)
        if res.status_code == 200:
            data = res.json()
            return data.get("access_token") or data.get("token") or data.get("session_token")
        pytest.skip("Member auth failed")
    
    def test_portal_media(self, member_token):
        """Portal media endpoint works"""
        headers = {"Authorization": f"Bearer {member_token}"}
        res = requests.get(f"{BASE_URL}/api/portal/media", headers=headers)
        assert res.status_code == 200
        print("✓ Portal media loaded")
    
    def test_portal_prayer(self, member_token):
        """Portal prayer wall endpoint works"""
        headers = {"Authorization": f"Bearer {member_token}"}
        res = requests.get(f"{BASE_URL}/api/portal/prayer", headers=headers)
        assert res.status_code == 200
        print("✓ Portal prayer wall loaded")
    
    def test_portal_merch(self, member_token):
        """Portal merch endpoint works"""
        headers = {"Authorization": f"Bearer {member_token}"}
        res = requests.get(f"{BASE_URL}/api/portal/merch", headers=headers)
        assert res.status_code == 200
        print("✓ Portal merch loaded")
    
    def test_portal_directory(self, member_token):
        """Portal directory endpoint works"""
        headers = {"Authorization": f"Bearer {member_token}"}
        res = requests.get(f"{BASE_URL}/api/portal/directory", headers=headers)
        assert res.status_code == 200
        print("✓ Portal directory loaded")


class TestSolomonAI:
    """Solomon AI chat API"""
    
    @pytest.fixture
    def member_token(self):
        res = requests.post(f"{BASE_URL}/api/auth/login", json=PORTAL_MEMBER)
        if res.status_code == 200:
            data = res.json()
            return data.get("access_token") or data.get("token") or data.get("session_token")
        pytest.skip("Member auth failed")
    
    def test_solomon_chat(self, member_token):
        """Solomon AI chat endpoint works"""
        headers = {"Authorization": f"Bearer {member_token}", "Content-Type": "application/json"}
        res = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            headers=headers,
            json={"message": "Hello Solomon, what can you help me with?"}
        )
        assert res.status_code == 200
        data = res.json()
        assert "response" in data or "message" in data or "reply" in data
        print("✓ Solomon AI chat responded")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
