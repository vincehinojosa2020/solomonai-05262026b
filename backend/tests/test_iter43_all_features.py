"""
Iteration 43 Tests: All 4 Tasks
- Task 5: Solomon Chat (FAB, panel, send message)
- Task 8: Sunday Morning Engine (service-mode, service-checkin, attendance-streak, notification-templates)
- Task 2: Church Onboarding Wizard (POST /api/platform/churches/create)
- Task 6: Reports & Export System (11 report endpoints + CSV export)
- Regression: Health endpoint, Aivy login
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PLATFORM_ADMIN = {"email": "admin@solomon.ai", "password": "Demo2026!"}
CHURCH_ADMIN_AIVY = {"email": "avopham@gmail.com", "password": "SolomonTest2026!"}
MEMBER_VINCE = {"email": "vince@charlottesoftwareengineering.com", "password": "SolomonTest2026!"}


class TestHealthRegression:
    """Regression: Health endpoint"""
    
    def test_health_returns_200(self):
        """GET /api/health returns 200 with status ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        print(f"✓ Health check passed: status={data.get('status')}")


class TestAuthRegression:
    """Regression: Aivy login returns role=church_admin"""
    
    def test_aivy_login_returns_church_admin(self):
        """Login as Aivy returns role: church_admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN_AIVY)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data.get("role") == "church_admin", f"Expected church_admin, got {data.get('role')}"
        assert "token" in data
        assert "permissions" in data
        print(f"✓ Aivy login: role={data.get('role')}, permissions count={len(data.get('permissions', []))}")


class TestTask5SolomonChat:
    """Task 5: Solomon Chat API"""
    
    def test_solomon_chat_endpoint(self):
        """POST /api/solomon/chat returns 200 with response"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "hello"}
        )
        assert response.status_code == 200, f"Solomon chat failed: {response.text}"
        data = response.json()
        assert "response" in data or "message" in data, f"No response in data: {data}"
        print(f"✓ Solomon chat endpoint working")


class TestTask8SundayMorning:
    """Task 8: Sunday Morning Engine endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        return response.json().get("token")
    
    @pytest.fixture
    def member_token(self):
        # Use Aivy as member token (church_admin can access portal)
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN_AIVY)
        return response.json().get("token")
    
    def test_service_mode_returns_200(self, member_token):
        """GET /api/portal/service-mode returns 200"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/service-mode", headers=headers)
        assert response.status_code == 200, f"Service mode failed: {response.text}"
        data = response.json()
        assert "is_service_day" in data
        assert "current_day" in data
        assert "today" in data
        print(f"✓ Service mode: day={data.get('current_day')}, is_service_day={data.get('is_service_day')}")
    
    def test_service_checkin_returns_200(self, member_token):
        """POST /api/portal/service-checkin returns 200"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.post(
            f"{BASE_URL}/api/portal/service-checkin?check_in_type=in_person",
            headers=headers
        )
        assert response.status_code == 200, f"Service checkin failed: {response.text}"
        data = response.json()
        # Either success or already checked in
        assert data.get("success") == True or "Already checked in" in data.get("message", "")
        print(f"✓ Service checkin: {data.get('message', 'success')}")
    
    def test_attendance_streak_returns_200(self, member_token):
        """GET /api/portal/attendance-streak returns 200"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/attendance-streak", headers=headers)
        assert response.status_code == 200, f"Attendance streak failed: {response.text}"
        data = response.json()
        assert "current_streak" in data or "streak" in data
        print(f"✓ Attendance streak: {data}")
    
    def test_notification_templates_returns_6(self, admin_token):
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
        assert len(templates) == 6, f"Expected 6 templates, got {len(templates)}"
        print(f"✓ Sunday Morning templates: {len(templates)} templates found")


class TestTask2ChurchOnboarding:
    """Task 2: Church Onboarding Wizard - POST /api/platform/churches/create"""
    
    @pytest.fixture
    def platform_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        return response.json().get("token")
    
    def test_create_church_with_valid_data(self, platform_admin_token):
        """POST /api/platform/churches/create with valid data creates new church"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        
        # Generate unique email for each test run
        unique_id = str(uuid.uuid4())[:8]
        timestamp = int(time.time())
        
        church_data = {
            "name": f"Test Church {unique_id}",
            "city": "Charlotte",
            "state": "NC",
            "denomination": "Non-denominational",
            "website": "https://testchurch.com",
            "estimated_members": 150,
            "service_times": [{"day": "Sunday", "time": "09:00", "name": "Sunday Morning"}],
            "primary_color": "#2563eb",
            "subdomain": f"test-church-{timestamp}",
            "admin_name": "Test Pastor",
            "admin_email": f"test-{timestamp}@testchurch.com",
            "admin_password": "TestPass123!",
            "admin_phone": "(555) 123-4567",
            "plan": "starter"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/platform/churches/create",
            json=church_data,
            headers=headers
        )
        
        assert response.status_code in [200, 201], f"Create church failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "church_id" in data or "church_name" in data, f"Missing church_id or church_name in response: {data}"
        print(f"✓ Church created: {data.get('church_name', data.get('church_id'))}")


class TestTask6Reports:
    """Task 6: Reports & Export System - All 11 report endpoints"""
    
    def test_executive_summary_returns_200(self):
        """GET /api/reports/executive-summary returns 200"""
        response = requests.get(f"{BASE_URL}/api/reports/executive-summary")
        assert response.status_code == 200, f"Executive summary failed: {response.text}"
        data = response.json()
        # Verify structure
        assert "membership" in data or "giving" in data or "period" in data, f"Missing expected fields: {data}"
        print(f"✓ Executive summary report working")
    
    def test_kids_history_returns_200(self):
        """GET /api/reports/kids-history returns 200"""
        response = requests.get(f"{BASE_URL}/api/reports/kids-history")
        assert response.status_code == 200, f"Kids history failed: {response.text}"
        data = response.json()
        assert "summary" in data or "records" in data, f"Missing expected fields: {data}"
        print(f"✓ Kids history report working")
    
    def test_attendance_returns_200(self):
        """GET /api/reports/attendance returns 200"""
        response = requests.get(f"{BASE_URL}/api/reports/attendance")
        assert response.status_code == 200, f"Attendance failed: {response.text}"
        data = response.json()
        assert "summary" in data or "weekly" in data, f"Missing expected fields: {data}"
        print(f"✓ Attendance report working")
    
    def test_cafe_returns_200(self):
        """GET /api/reports/cafe returns 200"""
        response = requests.get(f"{BASE_URL}/api/reports/cafe")
        assert response.status_code == 200, f"Cafe failed: {response.text}"
        data = response.json()
        assert "summary" in data or "top_items" in data, f"Missing expected fields: {data}"
        print(f"✓ Cafe report working")
    
    def test_merch_returns_200(self):
        """GET /api/reports/merch returns 200"""
        response = requests.get(f"{BASE_URL}/api/reports/merch")
        assert response.status_code == 200, f"Merch failed: {response.text}"
        data = response.json()
        assert "summary" in data, f"Missing expected fields: {data}"
        print(f"✓ Merch report working")
    
    def test_groups_returns_200(self):
        """GET /api/reports/groups returns 200"""
        response = requests.get(f"{BASE_URL}/api/reports/groups")
        assert response.status_code == 200, f"Groups failed: {response.text}"
        data = response.json()
        assert "summary" in data or "groups" in data, f"Missing expected fields: {data}"
        print(f"✓ Groups report working")
    
    def test_next_steps_returns_200(self):
        """GET /api/reports/next-steps returns 200"""
        response = requests.get(f"{BASE_URL}/api/reports/next-steps")
        assert response.status_code == 200, f"Next steps failed: {response.text}"
        data = response.json()
        assert "summary" in data, f"Missing expected fields: {data}"
        print(f"✓ Next steps report working")
    
    def test_membership_returns_200(self):
        """GET /api/reports/membership returns 200"""
        response = requests.get(f"{BASE_URL}/api/reports/membership")
        assert response.status_code == 200, f"Membership failed: {response.text}"
        data = response.json()
        assert "total" in data or "by_status" in data, f"Missing expected fields: {data}"
        print(f"✓ Membership report working")
    
    def test_giving_by_fund_returns_200(self):
        """GET /api/reports/giving-by-fund returns 200"""
        # These endpoints require date parameters
        response = requests.get(f"{BASE_URL}/api/reports/giving-by-fund?start_date=2025-01-01&end_date=2026-01-31")
        assert response.status_code == 200, f"Giving by fund failed: {response.text}"
        print(f"✓ Giving by fund report working")
    
    def test_giving_by_method_returns_200(self):
        """GET /api/reports/giving-by-method returns 200"""
        response = requests.get(f"{BASE_URL}/api/reports/giving-by-method?start_date=2025-01-01&end_date=2026-01-31")
        assert response.status_code == 200, f"Giving by method failed: {response.text}"
        print(f"✓ Giving by method report working")
    
    def test_top_donors_returns_200(self):
        """GET /api/reports/top-donors returns 200"""
        response = requests.get(f"{BASE_URL}/api/reports/top-donors?start_date=2025-01-01&end_date=2026-01-31")
        assert response.status_code == 200, f"Top donors failed: {response.text}"
        print(f"✓ Top donors report working")


class TestTask6ReportsExport:
    """Task 6: Reports CSV Export"""
    
    def test_kids_history_export_csv(self):
        """GET /api/reports/kids-history/export?format=csv returns CSV content-type"""
        response = requests.get(f"{BASE_URL}/api/reports/kids-history/export?format=csv")
        assert response.status_code == 200, f"Kids history export failed: {response.text}"
        content_type = response.headers.get('Content-Type', '')
        assert 'text/csv' in content_type or 'application/csv' in content_type or 'text/plain' in content_type, \
            f"Expected CSV content-type, got: {content_type}"
        print(f"✓ Kids history CSV export working, content-type: {content_type}")
    
    def test_attendance_export_csv(self):
        """GET /api/reports/attendance/export?format=csv returns CSV"""
        response = requests.get(f"{BASE_URL}/api/reports/attendance/export?format=csv")
        assert response.status_code == 200, f"Attendance export failed: {response.text}"
        print(f"✓ Attendance CSV export working")
    
    def test_groups_export_csv(self):
        """GET /api/reports/groups/export?format=csv returns CSV"""
        response = requests.get(f"{BASE_URL}/api/reports/groups/export?format=csv")
        assert response.status_code == 200, f"Groups export failed: {response.text}"
        print(f"✓ Groups CSV export working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
