"""
Iteration 45: Audit Trail UI, PDF Export, Admin Permission Editor
Tests for:
1. AUDIT: GET /api/admin/audit-log - returns entries array and total count
2. AUDIT: GET /api/admin/audit-log?action=donation_processed - filters correctly
3. PDF: GET /api/admin/reports/kids/history - returns 200
4. PDF: GET /api/admin/reports/giving/summary - returns 200
5. PDF: GET /api/admin/reports/attendance/summary - returns 200
6. PDF: GET /api/admin/reports/executive-summary - returns 200
7. PDF: POST /api/admin/reports/export with format=pdf - returns PDF content
8. PDF: POST /api/admin/reports/export with format=csv - returns CSV content
9. PERMS: GET /api/admin/roles/templates - returns role templates
10. PERMS: GET /api/admin/members/{user_id}/permissions - returns user permissions
11. REGRESSION: GET /api/health - returns 200
12. REGRESSION: GET /api/admin/war-room - returns 200
13. REGRESSION: POST /api/giving/process - returns success
14. REGRESSION: Aivy login returns role=church_admin
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PLATFORM_ADMIN_EMAIL = "admin@solomon.ai"
PLATFORM_ADMIN_PASSWORD = "Demo2026!"
CHURCH_ADMIN_EMAIL = "avopham@gmail.com"
CHURCH_ADMIN_PASSWORD = "SolomonTest2026!"
AIVY_USER_ID = "f1d0f1d8-de66-4fc0-a8c7-8f81f679ce22"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def platform_admin_token(self):
        """Get platform admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token") or data.get("token")
        pytest.skip(f"Platform admin login failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def church_admin_token(self):
        """Get church admin (Aivy) token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token") or data.get("token")
        pytest.skip(f"Church admin login failed: {response.status_code}")
    
    def test_aivy_login_returns_church_admin_role(self):
        """REGRESSION: Aivy login returns role=church_admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data.get("role") == "church_admin", f"Expected role=church_admin, got {data.get('role')}"
        print(f"PASS: Aivy login returns role=church_admin")


class TestRegression:
    """Regression tests for existing functionality"""
    
    def test_health_endpoint(self):
        """REGRESSION: GET /api/health returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status=ok, got {data}"
        print(f"PASS: GET /api/health returns 200 with status=ok")
    
    def test_war_room_endpoint(self, platform_admin_token):
        """REGRESSION: GET /api/admin/war-room returns 200"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/war-room", headers=headers)
        assert response.status_code == 200, f"War room failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "counters" in data or "activity_feed" in data, f"War room missing expected fields: {data.keys()}"
        print(f"PASS: GET /api/admin/war-room returns 200")
    
    def test_giving_process(self, platform_admin_token):
        """REGRESSION: POST /api/giving/process returns success"""
        headers = {"Authorization": f"Bearer {platform_admin_token}", "Content-Type": "application/json"}
        payload = {
            "amount": 25.00,
            "fund_id": "general",
            "payment_method": "card",
            "donor_name": "Test Donor",
            "donor_email": "test@example.com"
        }
        response = requests.post(f"{BASE_URL}/api/giving/process", headers=headers, json=payload)
        assert response.status_code == 200, f"Giving process failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("success") == True or data.get("status") == "success", f"Expected success, got {data}"
        print(f"PASS: POST /api/giving/process returns success")
    
    @pytest.fixture(scope="class")
    def platform_admin_token(self):
        """Get platform admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token") or data.get("token")
        pytest.skip(f"Platform admin login failed: {response.status_code}")


class TestAuditLog:
    """Audit Trail API tests"""
    
    @pytest.fixture(scope="class")
    def platform_admin_token(self):
        """Get platform admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token") or data.get("token")
        pytest.skip(f"Platform admin login failed: {response.status_code}")
    
    def test_audit_log_returns_entries_and_total(self, platform_admin_token):
        """AUDIT: GET /api/admin/audit-log returns 200 with entries array and total count"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/audit-log", headers=headers)
        assert response.status_code == 200, f"Audit log failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "entries" in data, f"Missing 'entries' field in response: {data.keys()}"
        assert "total" in data, f"Missing 'total' field in response: {data.keys()}"
        assert isinstance(data["entries"], list), f"'entries' should be a list, got {type(data['entries'])}"
        assert isinstance(data["total"], int), f"'total' should be an int, got {type(data['total'])}"
        print(f"PASS: GET /api/admin/audit-log returns entries array ({len(data['entries'])} items) and total count ({data['total']})")
    
    def test_audit_log_filter_by_action(self, platform_admin_token):
        """AUDIT: GET /api/admin/audit-log?action=donation_processed filters correctly"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/audit-log?action=donation_processed", headers=headers)
        assert response.status_code == 200, f"Audit log filter failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "entries" in data, f"Missing 'entries' field"
        # If there are entries, verify they all have the correct action
        for entry in data["entries"]:
            assert entry.get("action") == "donation_processed", f"Entry has wrong action: {entry.get('action')}"
        print(f"PASS: GET /api/admin/audit-log?action=donation_processed filters correctly ({len(data['entries'])} entries)")


class TestReportsAPI:
    """Reports API tests (PDF/CSV export)"""
    
    @pytest.fixture(scope="class")
    def platform_admin_token(self):
        """Get platform admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token") or data.get("token")
        pytest.skip(f"Platform admin login failed: {response.status_code}")
    
    def test_kids_history_report(self, platform_admin_token):
        """PDF: GET /api/admin/reports/kids/history returns 200"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/reports/kids/history", headers=headers)
        assert response.status_code == 200, f"Kids history report failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "records" in data or "summary" in data, f"Missing expected fields: {data.keys()}"
        print(f"PASS: GET /api/admin/reports/kids/history returns 200")
    
    def test_giving_summary_report(self, platform_admin_token):
        """PDF: GET /api/admin/reports/giving/summary returns 200"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/reports/giving/summary", headers=headers)
        assert response.status_code == 200, f"Giving summary report failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "by_fund" in data or "by_method" in data, f"Missing expected fields: {data.keys()}"
        print(f"PASS: GET /api/admin/reports/giving/summary returns 200")
    
    def test_attendance_summary_report(self, platform_admin_token):
        """PDF: GET /api/admin/reports/attendance/summary returns 200"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/reports/attendance/summary", headers=headers)
        assert response.status_code == 200, f"Attendance summary report failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "summary" in data or "weekly" in data, f"Missing expected fields: {data.keys()}"
        print(f"PASS: GET /api/admin/reports/attendance/summary returns 200")
    
    def test_executive_summary_report(self, platform_admin_token):
        """PDF: GET /api/admin/reports/executive-summary returns 200"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/reports/executive-summary", headers=headers)
        assert response.status_code == 200, f"Executive summary report failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "membership" in data or "giving" in data or "period" in data, f"Missing expected fields: {data.keys()}"
        print(f"PASS: GET /api/admin/reports/executive-summary returns 200")
    
    def test_export_pdf(self, platform_admin_token):
        """PDF: POST /api/admin/reports/export with format=pdf returns PDF content"""
        headers = {"Authorization": f"Bearer {platform_admin_token}", "Content-Type": "application/json"}
        payload = {"report_type": "executive", "format": "pdf"}
        response = requests.post(f"{BASE_URL}/api/admin/reports/export", headers=headers, json=payload)
        assert response.status_code == 200, f"PDF export failed: {response.status_code} - {response.text}"
        content_type = response.headers.get("Content-Type", "")
        assert "pdf" in content_type.lower() or response.content[:4] == b'%PDF', f"Expected PDF content, got {content_type}"
        print(f"PASS: POST /api/admin/reports/export with format=pdf returns PDF content ({len(response.content)} bytes)")
    
    def test_export_csv(self, platform_admin_token):
        """PDF: POST /api/admin/reports/export with format=csv returns CSV content"""
        headers = {"Authorization": f"Bearer {platform_admin_token}", "Content-Type": "application/json"}
        payload = {"report_type": "kids", "format": "csv"}
        response = requests.post(f"{BASE_URL}/api/admin/reports/export", headers=headers, json=payload)
        assert response.status_code == 200, f"CSV export failed: {response.status_code} - {response.text}"
        content_type = response.headers.get("Content-Type", "")
        assert "csv" in content_type.lower() or "text" in content_type.lower(), f"Expected CSV content, got {content_type}"
        print(f"PASS: POST /api/admin/reports/export with format=csv returns CSV content ({len(response.content)} bytes)")


class TestPermissions:
    """Permission Editor API tests"""
    
    @pytest.fixture(scope="class")
    def platform_admin_token(self):
        """Get platform admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token") or data.get("token")
        pytest.skip(f"Platform admin login failed: {response.status_code}")
    
    def test_roles_templates(self, platform_admin_token):
        """PERMS: GET /api/admin/roles/templates returns role templates"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/roles/templates", headers=headers)
        assert response.status_code == 200, f"Roles templates failed: {response.status_code} - {response.text}"
        data = response.json()
        # API returns templates directly or wrapped in "templates" key
        templates = data.get("templates", data) if isinstance(data, dict) else data
        assert isinstance(templates, dict), f"'templates' should be a dict, got {type(templates)}"
        # Check for expected role templates
        expected_roles = ["member", "church_admin"]
        for role in expected_roles:
            assert role in templates, f"Missing expected role template: {role}"
        print(f"PASS: GET /api/admin/roles/templates returns {len(templates)} role templates")
    
    def test_user_permissions(self, platform_admin_token):
        """PERMS: GET /api/admin/members/{user_id}/permissions returns user permissions"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/members/{AIVY_USER_ID}/permissions", headers=headers)
        assert response.status_code == 200, f"User permissions failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "permissions" in data or "role" in data, f"Missing expected fields: {data.keys()}"
        print(f"PASS: GET /api/admin/members/{AIVY_USER_ID}/permissions returns user permissions")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
