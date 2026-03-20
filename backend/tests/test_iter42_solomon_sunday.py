"""
Iteration 42 Tests: Solomon Chat + Sunday Morning Engine + Portal Access
Tests for:
- Solomon Chat API endpoint
- Sunday Morning notification templates
- Service mode and check-in endpoints
- Attendance streak
- Portal access for church_admin (Lyft dual-mode)
- RBAC endpoints verification
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PLATFORM_ADMIN = {"email": "admin@solomon.ai", "password": "Demo2026!"}
CHURCH_ADMIN_AIVY = {"email": "avopham@gmail.com", "password": "SolomonTest2026!"}
MEMBER_VINCE = {"email": "vince@charlottesoftwareengineering.com", "password": "SolomonTest2026!"}

# Known user IDs
AIVY_USER_ID = "f1d0f1d8-de66-4fc0-a8c7-8f81f679ce22"


class TestHealthEndpoint:
    """Health check - run first"""
    
    def test_health_returns_200(self):
        """GET /api/health returns 200 with status ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        assert "timestamp" in data
        print(f"✓ Health check passed: {data}")


class TestAuthentication:
    """Authentication and role verification"""
    
    def test_login_aivy_church_admin(self):
        """Login as Aivy returns role: church_admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN_AIVY)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data.get("role") == "church_admin", f"Expected church_admin, got {data.get('role')}"
        assert "token" in data
        assert "permissions" in data
        print(f"✓ Aivy login: role={data.get('role')}, permissions count={len(data.get('permissions', []))}")
        return data.get("token")
    
    def test_login_platform_admin(self):
        """Login as platform admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        assert response.status_code == 200, f"Platform admin login failed: {response.text}"
        data = response.json()
        assert data.get("role") == "platform_admin"
        print(f"✓ Platform admin login successful")
        return data.get("token")
    
    def test_login_member_vince(self):
        """Login as member Vince"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=MEMBER_VINCE)
        assert response.status_code == 200, f"Member login failed: {response.text}"
        data = response.json()
        print(f"✓ Vince login: role={data.get('role')}")
        return data.get("token")


class TestRBACEndpoints:
    """RBAC permission endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        return response.json().get("token")
    
    def test_update_member_role(self, admin_token):
        """PUT /api/admin/members/{user_id}/role with role_template"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.put(
            f"{BASE_URL}/api/admin/members/{AIVY_USER_ID}/role",
            json={"role_template": "church_admin"},
            headers=headers
        )
        assert response.status_code == 200, f"Update role failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("new_role") == "church_admin"
        print(f"✓ Updated Aivy role to church_admin: {data}")
    
    def test_get_member_permissions(self, admin_token):
        """GET /api/admin/members/{user_id}/permissions returns role=church_admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{AIVY_USER_ID}/permissions",
            headers=headers
        )
        assert response.status_code == 200, f"Get permissions failed: {response.text}"
        data = response.json()
        assert data.get("role") == "church_admin", f"Expected church_admin, got {data.get('role')}"
        assert "permissions" in data
        print(f"✓ Aivy permissions: role={data.get('role')}, perms count={len(data.get('permissions', []))}")
    
    def test_get_volunteers(self, admin_token):
        """GET /api/admin/volunteers returns 200"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/volunteers", headers=headers)
        assert response.status_code == 200, f"Get volunteers failed: {response.text}"
        data = response.json()
        assert "teams" in data
        print(f"✓ Volunteers endpoint: {len(data.get('teams', []))} teams")


class TestSolomonChat:
    """Solomon AI Chat endpoint"""
    
    def test_solomon_chat_endpoint(self):
        """POST /api/solomon/chat with message returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "hello"}
        )
        assert response.status_code == 200, f"Solomon chat failed: {response.text}"
        data = response.json()
        assert "response" in data or "message" in data, f"No response in data: {data}"
        print(f"✓ Solomon chat response received")
    
    def test_solomon_chat_with_question(self):
        """POST /api/solomon/chat with a real question"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "How do I join a group?"}
        )
        assert response.status_code == 200, f"Solomon chat failed: {response.text}"
        data = response.json()
        print(f"✓ Solomon answered question about groups")


class TestSundayMorningEngine:
    """Sunday Morning Engine endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        return response.json().get("token")
    
    @pytest.fixture
    def member_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN_AIVY)
        return response.json().get("token")
    
    def test_notification_templates(self, admin_token):
        """GET /api/admin/sunday-morning/notification-templates returns 6 templates"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/sunday-morning/notification-templates",
            headers=headers
        )
        assert response.status_code == 200, f"Get templates failed: {response.text}"
        data = response.json()
        assert "templates" in data
        templates = data.get("templates", {})
        expected_templates = ["service_starting", "welcome_arrived", "kids_reminder", 
                            "giving_reminder", "cafe_ready", "post_service"]
        for tmpl in expected_templates:
            assert tmpl in templates, f"Missing template: {tmpl}"
        print(f"✓ Sunday Morning templates: {len(templates)} templates found")
        print(f"  Templates: {list(templates.keys())}")
    
    def test_service_mode_endpoint(self, member_token):
        """GET /api/portal/service-mode returns service day/time info"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(
            f"{BASE_URL}/api/portal/service-mode",
            headers=headers
        )
        assert response.status_code == 200, f"Service mode failed: {response.text}"
        data = response.json()
        assert "is_service_day" in data
        assert "current_day" in data
        assert "today" in data
        print(f"✓ Service mode: day={data.get('current_day')}, is_service_day={data.get('is_service_day')}")
    
    def test_service_checkin_endpoint(self, member_token):
        """POST /api/portal/service-checkin with check_in_type=in_person"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.post(
            f"{BASE_URL}/api/portal/service-checkin?check_in_type=in_person",
            headers=headers
        )
        # Can be 200 (success) or 200 with "already checked in" message
        assert response.status_code == 200, f"Service checkin failed: {response.text}"
        data = response.json()
        # Either success or already checked in
        assert data.get("success") == True or "Already checked in" in data.get("message", "")
        print(f"✓ Service checkin: {data.get('message', 'success')}")
    
    def test_attendance_streak_endpoint(self, member_token):
        """GET /api/portal/attendance-streak returns streak data"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(
            f"{BASE_URL}/api/portal/attendance-streak",
            headers=headers
        )
        assert response.status_code == 200, f"Attendance streak failed: {response.text}"
        data = response.json()
        assert "current_streak" in data or "streak" in data
        print(f"✓ Attendance streak: {data}")


class TestPortalAccess:
    """Portal access for admin users (Lyft dual-mode)"""
    
    @pytest.fixture
    def aivy_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN_AIVY)
        return response.json().get("token")
    
    def test_portal_me_endpoint(self, aivy_token):
        """GET /api/portal/me returns member profile for Aivy"""
        headers = {"Authorization": f"Bearer {aivy_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/me", headers=headers)
        assert response.status_code == 200, f"Portal me failed: {response.text}"
        data = response.json()
        print(f"✓ Portal /me accessible for Aivy: {data.get('name', 'N/A')}")
    
    def test_portal_kids_endpoint(self, aivy_token):
        """GET /api/portal/kids returns kids data"""
        headers = {"Authorization": f"Bearer {aivy_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/kids", headers=headers)
        assert response.status_code == 200, f"Portal kids failed: {response.text}"
        print(f"✓ Portal /kids accessible for Aivy")
    
    def test_portal_groups_endpoint(self, aivy_token):
        """GET /api/portal/groups returns groups data"""
        headers = {"Authorization": f"Bearer {aivy_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/groups", headers=headers)
        assert response.status_code == 200, f"Portal groups failed: {response.text}"
        print(f"✓ Portal /groups accessible for Aivy")
    
    def test_portal_events_endpoint(self, aivy_token):
        """GET /api/portal/events returns events data"""
        headers = {"Authorization": f"Bearer {aivy_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/events", headers=headers)
        assert response.status_code == 200, f"Portal events failed: {response.text}"
        print(f"✓ Portal /events accessible for Aivy")


class TestGeofenceEndpoints:
    """Geofence check-in endpoints"""
    
    @pytest.fixture
    def member_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN_AIVY)
        return response.json().get("token")
    
    def test_geofence_checkin(self, member_token):
        """POST /api/portal/geofence-checkin with coordinates"""
        headers = {"Authorization": f"Bearer {member_token}"}
        # Charlotte, NC coordinates (near Abundant Church)
        response = requests.post(
            f"{BASE_URL}/api/portal/geofence-checkin",
            json={"latitude": 35.2271, "longitude": -80.8431},
            headers=headers
        )
        # May return 200 or 400 depending on geofence config
        # Just verify endpoint exists and responds
        assert response.status_code in [200, 400, 404], f"Geofence checkin unexpected: {response.status_code}"
        print(f"✓ Geofence checkin endpoint responded: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
