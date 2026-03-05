"""
Test Suite for Solomon AI Agent API System - Iteration 13
Features tested:
- Admin API key management (/admin/api-keys)
- Agent Scout endpoint (/v1/agent/scout)
- Agent Visitors endpoint (/v1/agent/visitors)
- Agent Members endpoint (/v1/agent/members)
- Agent Events endpoint (/v1/agent/events)
- Agent Groups endpoint (/v1/agent/groups)
- Agent Meetings endpoint (/v1/agent/meetings)
- Agent Giving Summary endpoint (/v1/agent/giving/summary)
- Agent Notes endpoint (/v1/agent/notes)
- Public API Documentation endpoint (/v1/agent/docs)
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test API key provided for MoltBot
TEST_API_KEY = "sk_solomon_r2szMkSTj-mifBOM6qfRoHnFuakOBwJq32Hxj27Wk_U"

# Admin credentials
ADMIN_EMAIL = "admin@abundant.church"
ADMIN_PASSWORD = "Demo2026!"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_cookies(api_client):
    """Authenticate as admin and return session cookies"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.cookies
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_cookies):
    """Session with auth cookies"""
    api_client.cookies.update(auth_cookies)
    return api_client


@pytest.fixture(scope="module")
def agent_client():
    """Session with API key authentication"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TEST_API_KEY}"
    })
    return session


class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login_success(self, api_client):
        """Test admin can login with valid credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "user" in data or "email" in data, "Response should contain user info"


class TestAdminAPIKeyManagement:
    """Test API key CRUD operations via admin endpoints"""
    
    def test_list_api_keys(self, authenticated_client):
        """Admin can list API keys"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/api-keys")
        assert response.status_code == 200, f"Failed to list API keys: {response.text}"
        
        data = response.json()
        assert "api_keys" in data
        assert "available_permissions" in data
        assert isinstance(data["api_keys"], list)
        assert isinstance(data["available_permissions"], dict)
        
        # Verify permissions include expected scopes
        perms = data["available_permissions"]
        assert "members:read" in perms
        assert "events:read" in perms
        assert "groups:read" in perms
        assert "meetings:read" in perms
        assert "giving:read" in perms
    
    def test_create_api_key(self, authenticated_client):
        """Admin can create a new API key"""
        payload = {
            "name": "TEST_PyTestKey",
            "permissions": ["members:read", "events:read"],
            "rate_limit": 500,
            "expires_in_days": None
        }
        response = authenticated_client.post(
            f"{BASE_URL}/api/admin/api-keys",
            json=payload
        )
        assert response.status_code == 200, f"Failed to create API key: {response.text}"
        
        data = response.json()
        # Verify response contains the full key (only time it's shown)
        assert "api_key" in data
        assert data["api_key"].startswith("sk_solomon_")
        assert "key_id" in data
        assert data["name"] == "TEST_PyTestKey"
        assert data["permissions"] == ["members:read", "events:read"]
        assert data["rate_limit"] == 500
        assert "warning" in data
        
        # Store key_id for cleanup
        TestAdminAPIKeyManagement.created_key_id = data["key_id"]
    
    def test_revoke_api_key(self, authenticated_client):
        """Admin can revoke an API key"""
        if not hasattr(TestAdminAPIKeyManagement, 'created_key_id'):
            pytest.skip("No key to revoke (creation test may have failed)")
        
        key_id = TestAdminAPIKeyManagement.created_key_id
        response = authenticated_client.delete(f"{BASE_URL}/api/admin/api-keys/{key_id}")
        assert response.status_code == 200, f"Failed to revoke API key: {response.text}"
        
        data = response.json()
        assert data["key_id"] == key_id
        assert data["message"] == "API key revoked"
    
    def test_list_keys_requires_auth(self, api_client):
        """API key list endpoint requires authentication"""
        # Use fresh session without cookies
        fresh_session = requests.Session()
        response = fresh_session.get(f"{BASE_URL}/api/admin/api-keys")
        assert response.status_code in [401, 403], "Should require authentication"


class TestAgentAPIDocumentation:
    """Test public API documentation endpoint"""
    
    def test_docs_is_public(self, api_client):
        """API docs endpoint should be publicly accessible without auth"""
        response = api_client.get(f"{BASE_URL}/api/v1/agent/docs")
        assert response.status_code == 200, f"Docs endpoint failed: {response.text}"
        
        data = response.json()
        assert data["api_name"] == "Solomon AI Agent API"
        assert data["version"] == "1.0.0"
        assert "authentication" in data
        assert "endpoints" in data
        
        # Verify key endpoints are documented
        endpoints = data["endpoints"]
        assert "/scout" in endpoints
        assert "/visitors" in endpoints
        assert "/members" in endpoints
        assert "/events" in endpoints
        assert "/groups" in endpoints
        assert "/meetings" in endpoints
        assert "/giving/summary" in endpoints
        assert "/notes" in endpoints


class TestAgentScoutEndpoint:
    """Test agent scout/handshake endpoint"""
    
    def test_scout_requires_auth(self, api_client):
        """Scout endpoint requires API key"""
        response = api_client.get(f"{BASE_URL}/api/v1/agent/scout")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_scout_invalid_key(self, api_client):
        """Scout endpoint rejects invalid API key"""
        api_client.headers["Authorization"] = "Bearer sk_invalid_key"
        response = api_client.get(f"{BASE_URL}/api/v1/agent/scout")
        assert response.status_code == 401
        # Clean up header
        del api_client.headers["Authorization"]
    
    def test_scout_success(self, agent_client):
        """Scout endpoint returns tenant info with valid key"""
        response = agent_client.get(f"{BASE_URL}/api/v1/agent/scout")
        assert response.status_code == 200, f"Scout failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "connected"
        assert "timestamp" in data
        assert "tenant" in data
        assert "permissions" in data
        assert "rate_limit" in data
        assert "endpoints" in data
        assert data["schema_version"] == "1.0.0"
        
        # Verify tenant info
        tenant = data["tenant"]
        assert "id" in tenant
        assert "name" in tenant
        
        # Verify endpoints are listed
        endpoints = data["endpoints"]
        assert "members" in endpoints
        assert "visitors" in endpoints
        assert "events" in endpoints


class TestAgentVisitorsEndpoint:
    """Test agent visitors endpoint"""
    
    def test_visitors_requires_auth(self, api_client):
        """Visitors endpoint requires API key"""
        response = api_client.get(f"{BASE_URL}/api/v1/agent/visitors")
        assert response.status_code == 401
    
    def test_visitors_success(self, agent_client):
        """Visitors endpoint returns new members"""
        response = agent_client.get(f"{BASE_URL}/api/v1/agent/visitors?days=30&limit=50")
        assert response.status_code == 200, f"Visitors failed: {response.text}"
        
        data = response.json()
        assert "visitor_report" in data
        
        report = data["visitor_report"]
        assert "timestamp" in report
        assert "new_members" in report
        assert "total_count" in report
        assert isinstance(report["new_members"], list)
        
        # If there are members, verify schema
        if report["new_members"]:
            member = report["new_members"][0]
            assert "unique_id" in member
            assert "name" in member
            assert "outreach_status" in member


class TestAgentMembersEndpoint:
    """Test agent members endpoint"""
    
    def test_members_requires_auth(self, api_client):
        """Members endpoint requires API key"""
        response = api_client.get(f"{BASE_URL}/api/v1/agent/members")
        assert response.status_code == 401
    
    def test_members_success(self, agent_client):
        """Members endpoint returns member directory"""
        response = agent_client.get(f"{BASE_URL}/api/v1/agent/members?limit=20")
        assert response.status_code == 200, f"Members failed: {response.text}"
        
        data = response.json()
        assert "members" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        
        # Verify members schema
        if data["members"]:
            member = data["members"][0]
            assert "unique_id" in member
            assert "name" in member
            assert "outreach_status" in member


class TestAgentEventsEndpoint:
    """Test agent events endpoint"""
    
    def test_events_requires_auth(self, api_client):
        """Events endpoint requires API key"""
        response = api_client.get(f"{BASE_URL}/api/v1/agent/events")
        assert response.status_code == 401
    
    def test_events_success(self, agent_client):
        """Events endpoint returns upcoming events"""
        response = agent_client.get(f"{BASE_URL}/api/v1/agent/events?upcoming_only=true&limit=20")
        assert response.status_code == 200, f"Events failed: {response.text}"
        
        data = response.json()
        assert "events" in data
        assert "total" in data
        
        # Verify events schema
        if data["events"]:
            event = data["events"][0]
            assert "unique_id" in event
            assert "title" in event
            assert "start_time" in event


class TestAgentGroupsEndpoint:
    """Test agent groups endpoint"""
    
    def test_groups_requires_auth(self, api_client):
        """Groups endpoint requires API key"""
        response = api_client.get(f"{BASE_URL}/api/v1/agent/groups")
        assert response.status_code == 401
    
    def test_groups_success(self, agent_client):
        """Groups endpoint returns groups with member counts"""
        response = agent_client.get(f"{BASE_URL}/api/v1/agent/groups?limit=20")
        assert response.status_code == 200, f"Groups failed: {response.text}"
        
        data = response.json()
        assert "groups" in data
        assert "total" in data
        
        # Verify groups schema
        if data["groups"]:
            group = data["groups"][0]
            assert "unique_id" in group
            assert "name" in group
            assert "member_count" in group


class TestAgentMeetingsEndpoint:
    """Test agent meetings endpoint"""
    
    def test_meetings_requires_auth(self, api_client):
        """Meetings endpoint requires API key"""
        response = api_client.get(f"{BASE_URL}/api/v1/agent/meetings")
        assert response.status_code == 401
    
    def test_meetings_success(self, agent_client):
        """Meetings endpoint returns pastoral meetings"""
        response = agent_client.get(f"{BASE_URL}/api/v1/agent/meetings?limit=20")
        assert response.status_code == 200, f"Meetings failed: {response.text}"
        
        data = response.json()
        assert "meetings" in data
        assert "total" in data
        
        # Verify meetings schema
        if data["meetings"]:
            meeting = data["meetings"][0]
            assert "unique_id" in meeting
            assert "member_name" in meeting
            assert "status" in meeting
            assert "has_summary" in meeting


class TestAgentGivingSummaryEndpoint:
    """Test agent giving summary endpoint (read-only)"""
    
    def test_giving_requires_auth(self, api_client):
        """Giving summary endpoint requires API key"""
        response = api_client.get(f"{BASE_URL}/api/v1/agent/giving/summary")
        assert response.status_code == 401
    
    def test_giving_requires_permission(self, agent_client):
        """Giving summary requires giving:read permission (test key lacks this)"""
        # The test API key has: members:read, events:read, groups:read, meetings:read
        # It does NOT have giving:read, so this should return 403
        response = agent_client.get(f"{BASE_URL}/api/v1/agent/giving/summary")
        assert response.status_code == 403, f"Expected 403 permission denied, got {response.status_code}"
        
        data = response.json()
        assert "Permission denied" in data.get("detail", "")
        assert "giving:read" in data.get("detail", "")


class TestAgentNotesEndpoint:
    """Test agent notes endpoint"""
    
    def test_notes_requires_auth(self, api_client):
        """Notes endpoint requires API key"""
        response = api_client.get(f"{BASE_URL}/api/v1/agent/notes")
        assert response.status_code == 401
    
    def test_notes_requires_permission(self, agent_client):
        """Notes endpoint requires notes:read permission (test key lacks this)"""
        # The test API key has: members:read, events:read, groups:read, meetings:read
        # It does NOT have notes:read, so this should return 403
        response = agent_client.get(f"{BASE_URL}/api/v1/agent/notes?limit=20")
        assert response.status_code == 403, f"Expected 403 permission denied, got {response.status_code}"
        
        data = response.json()
        assert "Permission denied" in data.get("detail", "")
        assert "notes:read" in data.get("detail", "")


class TestAgentPermissions:
    """Test permission enforcement"""
    
    def test_permission_denied_without_scope(self, api_client):
        """Endpoint should return 403 if key lacks required permission"""
        # We need to test with a key that has limited permissions
        # The test key has: members:read, events:read, groups:read, meetings:read
        # If it doesn't have giving:read, it should fail
        # But we don't have a limited key in this test
        # So we just verify the endpoint validates properly
        pass  # Skip - would need key without giving:read


# Clean up any test data
@pytest.fixture(scope="class")
def cleanup_test_data():
    """Clean up test API keys after test class"""
    yield
    # Cleanup happens in individual tests


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
