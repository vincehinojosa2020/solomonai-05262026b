"""
Iteration 47: Phase A Frontend Pages Backend API Tests
Tests for: Services/Worship Planning, Households, Volunteers, Portal Directory, Branding Settings
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "shannonnieman1030@gmail.com"
ADMIN_PASSWORD = "Demo2026!"

class TestPhaseABackendAPIs:
    """Test all Phase A backend APIs"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token") or data.get("token")
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    # ============== SERVICES / WORSHIP PLANNING ==============
    
    def test_get_service_plans(self, auth_headers):
        """Test GET /api/admin/services/plans"""
        response = requests.get(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "plans" in data, "Response should contain 'plans' key"
        print(f"✓ GET /api/admin/services/plans - Found {len(data['plans'])} plans")
    
    def test_create_service_plan(self, auth_headers):
        """Test POST /api/admin/services/plans"""
        payload = {
            "title": "TEST_Sunday Morning Worship",
            "date": "2026-02-01",
            "service_type": "sunday_morning"
        }
        response = requests.post(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("id"), "Response should contain plan ID"
        assert data.get("title") == payload["title"], "Title should match"
        assert data.get("date") == payload["date"], "Date should match"
        assert data.get("status") == "draft", "Initial status should be draft"
        print(f"✓ POST /api/admin/services/plans - Created plan: {data['id']}")
        return data["id"]
    
    def test_update_service_plan(self, auth_headers):
        """Test PUT /api/admin/services/plans/{plan_id}"""
        # First create a plan
        create_payload = {
            "title": "TEST_Plan for Update",
            "date": "2026-02-02",
            "service_type": "sunday_evening"
        }
        create_response = requests.post(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers, json=create_payload)
        assert create_response.status_code == 200
        plan_id = create_response.json()["id"]
        
        # Update the plan with items
        update_payload = {
            "status": "confirmed",
            "items": [
                {"id": "item-1", "title": "Opening Prayer", "type": "prayer", "order": 0},
                {"id": "item-2", "title": "Way Maker", "type": "song", "order": 1}
            ]
        }
        response = requests.put(f"{BASE_URL}/api/admin/services/plans/{plan_id}", headers=auth_headers, json=update_payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "confirmed", "Status should be updated"
        assert len(data.get("items", [])) == 2, "Should have 2 items"
        print(f"✓ PUT /api/admin/services/plans/{plan_id} - Updated with 2 items")
    
    # ============== HOUSEHOLDS ==============
    
    def test_get_households(self, auth_headers):
        """Test GET /api/admin/households"""
        response = requests.get(f"{BASE_URL}/api/admin/households", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "households" in data, "Response should contain 'households' key"
        assert "total" in data, "Response should contain 'total' key"
        print(f"✓ GET /api/admin/households - Found {data['total']} households")
    
    def test_create_household(self, auth_headers):
        """Test POST /api/admin/households"""
        payload = {
            "household_name": "TEST_Smith Family",
            "address": {
                "street": "123 Main St",
                "city": "Dallas",
                "state": "TX",
                "zip": "75001"
            }
        }
        response = requests.post(f"{BASE_URL}/api/admin/households", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("id"), "Response should contain household ID"
        assert data.get("household_name") == payload["household_name"], "Name should match"
        assert data.get("address", {}).get("city") == "Dallas", "Address city should match"
        print(f"✓ POST /api/admin/households - Created household: {data['id']}")
        return data["id"]
    
    def test_update_household(self, auth_headers):
        """Test PUT /api/admin/households/{household_id}"""
        # First create a household
        create_payload = {
            "household_name": "TEST_Johnson Family",
            "address": {"street": "456 Oak Ave", "city": "Austin", "state": "TX", "zip": "78701"}
        }
        create_response = requests.post(f"{BASE_URL}/api/admin/households", headers=auth_headers, json=create_payload)
        assert create_response.status_code == 200
        household_id = create_response.json()["id"]
        
        # Update the household
        update_payload = {
            "household_name": "TEST_Johnson-Williams Family",
            "member_ids": ["member-1", "member-2"]
        }
        response = requests.put(f"{BASE_URL}/api/admin/households/{household_id}", headers=auth_headers, json=update_payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("household_name") == update_payload["household_name"], "Name should be updated"
        print(f"✓ PUT /api/admin/households/{household_id} - Updated household")
    
    # ============== VOLUNTEERS ==============
    
    def test_get_volunteer_teams(self, auth_headers):
        """Test GET /api/admin/volunteers"""
        response = requests.get(f"{BASE_URL}/api/admin/volunteers", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "teams" in data, "Response should contain 'teams' key"
        print(f"✓ GET /api/admin/volunteers - Found {len(data['teams'])} teams")
    
    def test_create_volunteer_team(self, auth_headers):
        """Test POST /api/admin/volunteers/teams"""
        payload = {
            "team_name": "TEST_Worship Team",
            "ministry": "Worship",
            "description": "Sunday morning worship band and vocalists"
        }
        response = requests.post(f"{BASE_URL}/api/admin/volunteers/teams", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        assert data.get("team", {}).get("team_name") == payload["team_name"], "Team name should match"
        print(f"✓ POST /api/admin/volunteers/teams - Created team: {data['team']['id']}")
    
    def test_get_volunteer_schedule(self, auth_headers):
        """Test GET /api/admin/volunteers/schedule"""
        response = requests.get(f"{BASE_URL}/api/admin/volunteers/schedule", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "schedule" in data, "Response should contain 'schedule' key"
        assert "roles" in data, "Response should contain 'roles' key"
        print(f"✓ GET /api/admin/volunteers/schedule - Found {len(data['schedule'])} entries")
    
    def test_create_volunteer_schedule_entry(self, auth_headers):
        """Test POST /api/admin/volunteers/schedule"""
        payload = {
            "date": "2026-02-01",
            "role": "Sound Tech",
            "user_name": "John Doe",
            "user_id": "test-user-123"
        }
        response = requests.post(f"{BASE_URL}/api/admin/volunteers/schedule", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("id"), "Response should contain entry ID"
        assert data.get("role") == payload["role"], "Role should match"
        assert data.get("user_name") == payload["user_name"], "User name should match"
        print(f"✓ POST /api/admin/volunteers/schedule - Created entry: {data['id']}")
    
    # ============== PORTAL DIRECTORY ==============
    
    def test_get_portal_directory(self, auth_headers):
        """Test GET /api/portal/directory"""
        response = requests.get(f"{BASE_URL}/api/portal/directory", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "members" in data, "Response should contain 'members' key"
        assert "total" in data, "Response should contain 'total' key"
        print(f"✓ GET /api/portal/directory - Found {data['total']} members")
    
    def test_portal_directory_search(self, auth_headers):
        """Test GET /api/portal/directory with search"""
        response = requests.get(f"{BASE_URL}/api/portal/directory?search=test", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "members" in data, "Response should contain 'members' key"
        print(f"✓ GET /api/portal/directory?search=test - Found {len(data['members'])} matching members")
    
    # ============== BRANDING SETTINGS ==============
    
    def test_get_branding(self, auth_headers):
        """Test GET /api/admin/settings/branding"""
        response = requests.get(f"{BASE_URL}/api/admin/settings/branding", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "tenant_id" in data, "Response should contain 'tenant_id'"
        # Should have branding fields
        print(f"✓ GET /api/admin/settings/branding - App name: {data.get('app_name', 'N/A')}")
    
    def test_update_branding(self, auth_headers):
        """Test PUT /api/admin/settings/branding"""
        payload = {
            "app_name": "TEST_Abundant Church",
            "tagline": "Life. Community. Purpose.",
            "primary_color": "#4f6ef7",
            "logo_url": "https://example.com/logo.png",
            "app_store_description": "Connect with your church family"
        }
        response = requests.put(f"{BASE_URL}/api/admin/settings/branding", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        assert data.get("app_name") == payload["app_name"], "App name should match"
        print(f"✓ PUT /api/admin/settings/branding - Updated branding")
        
        # Verify the update persisted
        get_response = requests.get(f"{BASE_URL}/api/admin/settings/branding", headers=auth_headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data.get("app_name") == payload["app_name"], "App name should persist"
        print(f"✓ Verified branding update persisted")


class TestUnauthorizedAccess:
    """Test that endpoints require authentication"""
    
    def test_services_requires_auth(self):
        """Test that services endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/admin/services/plans")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/admin/services/plans requires auth")
    
    def test_households_requires_auth(self):
        """Test that households endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/admin/households")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/admin/households requires auth")
    
    def test_volunteers_requires_auth(self):
        """Test that volunteers endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/admin/volunteers")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/admin/volunteers requires auth")
    
    def test_directory_requires_auth(self):
        """Test that directory endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/portal/directory")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/portal/directory requires auth")
    
    def test_branding_requires_auth(self):
        """Test that branding endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/admin/settings/branding")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/admin/settings/branding requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
