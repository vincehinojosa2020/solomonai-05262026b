"""
Iteration 49: Solomon AI Demo Features Testing
Tests for 6 critical demo features:
A) Campus Switcher 'All Campuses' aggregate view
B) Platform God Mode visual upgrade
C) Manual Kids Check-In button/modal
D) Cafe Enterprise Redesign
E) CSV Member Import 4-step wizard
F) Communications page with Compose/Sent/Scheduled/Templates
"""

import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CHURCH_ADMIN_EMAIL = "shannonnieman1030@gmail.com"
CHURCH_ADMIN_PASSWORD = "Demo2026!"
PLATFORM_ADMIN_EMAIL = "admin@solomonai.us"
PLATFORM_ADMIN_PASSWORD = "Demo2026!"
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = "Demo2026!"


class TestAuthentication:
    """Test authentication for all user types"""
    
    def test_church_admin_login(self):
        """Test Shannon (church admin) can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Church admin login failed: {response.text}"
        data = response.json()
        # Token is returned as 'access_token' or 'token'
        assert "access_token" in data or "token" in data, "No token in response"
        # User data is at root level, not nested
        assert data.get("email") == CHURCH_ADMIN_EMAIL
        print(f"✓ Church admin login successful: {data.get('name')}")
    
    def test_platform_admin_login(self):
        """Test platform admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Platform admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "No token in response"
        assert data.get("role") == "platform_admin"
        print(f"✓ Platform admin login successful")
    
    def test_member_login(self):
        """Test member can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        assert response.status_code == 200, f"Member login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "No token in response"
        print(f"✓ Member login successful: {data.get('name')}")


@pytest.fixture(scope="session")
def church_admin_token():
    """Get auth token for church admin (Shannon)"""
    import time
    time.sleep(1)  # Rate limit protection
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": CHURCH_ADMIN_EMAIL,
        "password": CHURCH_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip("Church admin authentication failed")


@pytest.fixture(scope="session")
def platform_admin_token():
    """Get auth token for platform admin"""
    import time
    time.sleep(1)  # Rate limit protection
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": PLATFORM_ADMIN_EMAIL,
        "password": PLATFORM_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip("Platform admin authentication failed")


@pytest.fixture(scope="session")
def member_token():
    """Get auth token for member"""
    import time
    time.sleep(1)  # Rate limit protection
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MEMBER_EMAIL,
        "password": MEMBER_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip("Member authentication failed")


class TestFeatureA_AggregateDashboard:
    """Feature A: Campus Switcher 'All Campuses' aggregate view"""
    
    def test_aggregate_dashboard_endpoint(self, church_admin_token):
        """Test GET /api/admin/dashboard/aggregate returns campus stats"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/dashboard/aggregate", headers=headers)
        
        assert response.status_code == 200, f"Aggregate dashboard failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_members" in data, "Missing total_members"
        assert "total_groups" in data, "Missing total_groups"
        assert "total_kids_today" in data, "Missing total_kids_today"
        assert "total_giving_mtd" in data, "Missing total_giving_mtd"
        assert "campuses" in data, "Missing campuses array"
        assert "campus_count" in data, "Missing campus_count"
        
        # Verify data types
        assert isinstance(data["total_members"], int)
        assert isinstance(data["campuses"], list)
        
        print(f"✓ Aggregate dashboard: {data['campus_count']} campuses, {data['total_members']} total members")
    
    def test_aggregate_dashboard_requires_auth(self):
        """Test aggregate dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard/aggregate")
        assert response.status_code == 401, "Should require authentication"


class TestFeatureB_PlatformGodMode:
    """Feature B: Platform God Mode visual upgrade"""
    
    def test_platform_stats_endpoint(self, platform_admin_token):
        """Test platform stats endpoint for God Mode KPIs"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/stats", headers=headers)
        
        assert response.status_code == 200, f"Platform stats failed: {response.text}"
        data = response.json()
        
        # Verify KPI data structure
        assert "churches" in data, "Missing churches stats"
        assert "members" in data, "Missing members stats"
        assert "giving" in data, "Missing giving stats"
        
        print(f"✓ Platform stats: {data.get('churches', {}).get('total', 0)} churches")
    
    def test_platform_organizations_endpoint(self, platform_admin_token):
        """Test organizations endpoint for Org->Campus hierarchy"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/organizations", headers=headers)
        
        assert response.status_code == 200, f"Organizations failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return list of organizations"
        print(f"✓ Organizations endpoint: {len(data)} organizations")
    
    def test_tenants_list_endpoint(self, platform_admin_token):
        """Test tenants list for platform admin"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/tenants", headers=headers)
        
        assert response.status_code == 200, f"Tenants list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return list of tenants"
        print(f"✓ Tenants list: {len(data)} tenants")


class TestFeatureC_ManualKidsCheckin:
    """Feature C: Manual Kids Check-In button/modal"""
    
    def test_kids_all_endpoint(self, church_admin_token):
        """Test GET /api/admin/kids/all returns all registered kids"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/kids/all", headers=headers)
        
        assert response.status_code == 200, f"Kids all failed: {response.text}"
        data = response.json()
        assert "children" in data, "Missing children array"
        print(f"✓ Kids all endpoint: {len(data.get('children', []))} registered children")
    
    def test_kids_checkins_endpoint(self, church_admin_token):
        """Test GET /api/admin/kids/checkins returns current checkins"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/kids/checkins?status=checked_in", headers=headers)
        
        assert response.status_code == 200, f"Kids checkins failed: {response.text}"
        data = response.json()
        assert "checkins" in data, "Missing checkins array"
        print(f"✓ Kids checkins endpoint: {len(data.get('checkins', []))} currently checked in")


class TestFeatureD_CafeEnterprise:
    """Feature D: Cafe Enterprise Redesign"""
    
    def test_cafe_items_endpoint(self, member_token):
        """Test GET /api/portal/cafe/items returns menu items"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/cafe/items", headers=headers)
        
        assert response.status_code == 200, f"Cafe items failed: {response.text}"
        data = response.json()
        assert "items" in data, "Missing items array"
        print(f"✓ Cafe items endpoint: {len(data.get('items', []))} menu items")
    
    def test_cafe_settings_endpoint(self, member_token):
        """Test GET /api/portal/cafe/settings returns cafe settings"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/cafe/settings", headers=headers)
        
        assert response.status_code == 200, f"Cafe settings failed: {response.text}"
        data = response.json()
        # Settings may be null if not configured
        print(f"✓ Cafe settings endpoint: {'configured' if data.get('settings') else 'not configured'}")


class TestFeatureE_CSVMemberImport:
    """Feature E: CSV Member Import 4-step wizard"""
    
    def test_csv_parse_endpoint(self, church_admin_token):
        """Test POST /api/admin/members/import/parse with CSV file"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        
        # Create a test CSV file
        csv_content = "First Name,Last Name,Email,Phone\nTest,User,test_import@example.com,555-1234\nJohn,Doe,john_import@example.com,555-5678"
        files = {"file": ("test_members.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/members/import/parse",
            headers=headers,
            files=files
        )
        
        assert response.status_code == 200, f"CSV parse failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "headers" in data, "Missing headers"
        assert "preview" in data, "Missing preview"
        assert "total_rows" in data, "Missing total_rows"
        assert "system_fields" in data, "Missing system_fields"
        
        # Verify headers were detected
        assert "First Name" in data["headers"], "First Name header not detected"
        assert "Last Name" in data["headers"], "Last Name header not detected"
        assert data["total_rows"] == 2, f"Expected 2 rows, got {data['total_rows']}"
        
        print(f"✓ CSV parse: {len(data['headers'])} headers, {data['total_rows']} rows")
    
    def test_csv_execute_endpoint(self, church_admin_token):
        """Test POST /api/admin/members/import/execute with mapping"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        
        # Create a test CSV file with unique emails
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        csv_content = f"First Name,Last Name,Email\nTest{unique_id},Import,test_exec_{unique_id}@example.com"
        files = {"file": ("test_import.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        # Mapping from CSV columns to system fields
        mapping = {
            "first_name": "First Name",
            "last_name": "Last Name",
            "email": "Email"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/members/import/execute",
            headers=headers,
            files=files,
            data={"mapping": str(mapping).replace("'", '"')}
        )
        
        assert response.status_code == 200, f"CSV execute failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "imported" in data, "Missing imported count"
        assert "skipped" in data, "Missing skipped count"
        assert "total_processed" in data, "Missing total_processed"
        
        print(f"✓ CSV execute: {data['imported']} imported, {data['skipped']} skipped")


class TestFeatureF_Communications:
    """Feature F: Communications page with Compose/Sent/Scheduled/Templates"""
    
    def test_communications_send_endpoint(self, church_admin_token):
        """Test POST /api/admin/communications/send creates communication"""
        headers = {
            "Authorization": f"Bearer {church_admin_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "channel": "email",
            "subject": "Test Communication",
            "body": "This is a test message from iteration 49 testing.",
            "recipient_type": "all"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/communications/send",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 200, f"Communications send failed: {response.text}"
        data = response.json()
        
        assert "message" in data, "Missing message"
        assert "communication" in data, "Missing communication object"
        assert data["communication"]["status"] == "sent", "Status should be 'sent'"
        
        print(f"✓ Communications send: {data['message']}")
    
    def test_communications_send_scheduled(self, church_admin_token):
        """Test scheduling a communication for later"""
        headers = {
            "Authorization": f"Bearer {church_admin_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "channel": "email",
            "subject": "Scheduled Test",
            "body": "This is a scheduled test message.",
            "recipient_type": "all",
            "scheduled_at": "2026-02-01T10:00:00"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/communications/send",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 200, f"Scheduled send failed: {response.text}"
        data = response.json()
        
        assert data["communication"]["status"] == "scheduled", "Status should be 'scheduled'"
        print(f"✓ Communications scheduled: {data['message']}")
    
    def test_communications_list_endpoint(self, church_admin_token):
        """Test GET /api/admin/communications/list returns sent/scheduled comms"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/communications/list",
            headers=headers
        )
        
        assert response.status_code == 200, f"Communications list failed: {response.text}"
        data = response.json()
        
        assert "communications" in data, "Missing communications array"
        assert isinstance(data["communications"], list)
        
        # Count sent vs scheduled
        sent = len([c for c in data["communications"] if c.get("status") == "sent"])
        scheduled = len([c for c in data["communications"] if c.get("status") == "scheduled"])
        
        print(f"✓ Communications list: {sent} sent, {scheduled} scheduled")
    
    def test_communications_list_filter_by_status(self, church_admin_token):
        """Test filtering communications by status"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/communications/list?status=sent",
            headers=headers
        )
        
        assert response.status_code == 200, f"Filtered list failed: {response.text}"
        data = response.json()
        
        # All returned should be 'sent' status
        for comm in data.get("communications", []):
            assert comm.get("status") == "sent", f"Expected 'sent' status, got {comm.get('status')}"
        
        print(f"✓ Communications filter: {len(data.get('communications', []))} sent communications")


class TestDashboardEndpoints:
    """Test standard dashboard endpoints still work"""
    
    def test_dashboard_stats(self, church_admin_token):
        """Test dashboard stats endpoint"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        print("✓ Dashboard stats endpoint working")
    
    def test_dashboard_activity(self, church_admin_token):
        """Test dashboard activity endpoint"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/activity", headers=headers)
        assert response.status_code == 200, f"Dashboard activity failed: {response.text}"
        print("✓ Dashboard activity endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
