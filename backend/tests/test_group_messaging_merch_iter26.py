"""
Test suite for iteration 26 features:
1. Group Messaging API (GET/POST/DELETE)
2. Merch Recommender (UI-only, tested via frontend)
3. Enhanced Events (tested via frontend)

Tests cover the 3 new features: Group messaging, Merch recommender, Events enhancements
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@abundant.church"
ADMIN_PASSWORD = "Demo2026!"
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = "Demo2026!"

# Known group ID from context
TEST_GROUP_ID = "2a459b6d-88d0-4c1a-b6cc-94e449d7c4c0"

@pytest.fixture(scope="module")
def api_client():
    """Create a requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def admin_session(api_client):
    """Login as admin and get authenticated session"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    # Session cookies are stored in the session
    return api_client

@pytest.fixture(scope="module")
def member_session():
    """Login as member and get authenticated session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": MEMBER_EMAIL,
        "password": MEMBER_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Member login failed: {response.status_code} - {response.text}")
    return session


class TestAuthenticationFlows:
    """Test login endpoints work correctly"""
    
    def test_admin_login(self, api_client):
        """Test admin can login successfully"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "user" in data or "email" in data or "user_id" in data
        print(f"[PASS] Admin login successful")

    def test_member_login(self, api_client):
        """Test member can login successfully"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        assert response.status_code == 200, f"Member login failed: {response.text}"
        data = response.json()
        assert "user" in data or "email" in data or "user_id" in data
        print(f"[PASS] Member login successful")


class TestGroupMessagingAPI:
    """Test Group Messaging endpoints (Module 6)"""
    
    def test_get_group_messages_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected"""
        # Create a fresh session without auth
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/groups/{TEST_GROUP_ID}/messages")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"[PASS] GET /groups/{{groupId}}/messages requires authentication (401)")

    def test_get_group_messages_authenticated(self, member_session):
        """Test GET /api/groups/{groupId}/messages - returns messages for authenticated member"""
        response = member_session.get(f"{BASE_URL}/api/groups/{TEST_GROUP_ID}/messages?limit=100")
        assert response.status_code == 200, f"Failed to get messages: {response.status_code} - {response.text}"
        data = response.json()
        assert "messages" in data, f"Response missing 'messages' key: {data}"
        messages = data["messages"]
        assert isinstance(messages, list), f"'messages' should be a list"
        print(f"[PASS] GET /groups/{{groupId}}/messages returns {len(messages)} messages")
        
        # Validate message structure if messages exist
        if messages:
            msg = messages[0]
            assert "id" in msg, "Message missing 'id'"
            assert "text" in msg, "Message missing 'text'"
            assert "sender_name" in msg or "sender_id" in msg, "Message missing sender info"
            print(f"[PASS] Message structure validated: id, text, sender info present")

    def test_post_group_message(self, member_session):
        """Test POST /api/groups/{groupId}/messages - sends a new message"""
        test_message = f"TEST_message_iter26_{os.urandom(4).hex()}"
        
        response = member_session.post(
            f"{BASE_URL}/api/groups/{TEST_GROUP_ID}/messages",
            json={"text": test_message}
        )
        assert response.status_code == 200, f"Failed to post message: {response.status_code} - {response.text}"
        data = response.json()
        
        # Validate response contains message info
        assert "id" in data, "Response missing message 'id'"
        assert data.get("text") == test_message, f"Message text mismatch"
        assert "sender_name" in data or "sender_id" in data, "Response missing sender info"
        
        print(f"[PASS] POST /groups/{{groupId}}/messages created message with id: {data.get('id')}")
        return data.get("id")

    def test_post_message_empty_text_rejected(self, member_session):
        """Test POST /api/groups/{groupId}/messages rejects empty text"""
        response = member_session.post(
            f"{BASE_URL}/api/groups/{TEST_GROUP_ID}/messages",
            json={"text": "  "}
        )
        assert response.status_code == 400, f"Expected 400 for empty text, got {response.status_code}"
        print(f"[PASS] POST with empty text correctly rejected (400)")

    def test_delete_message_own_message(self, member_session):
        """Test DELETE /api/groups/{groupId}/messages/{messageId} - member can delete own message"""
        # First create a message
        test_message = f"TEST_delete_me_{os.urandom(4).hex()}"
        create_response = member_session.post(
            f"{BASE_URL}/api/groups/{TEST_GROUP_ID}/messages",
            json={"text": test_message}
        )
        assert create_response.status_code == 200, f"Failed to create message for delete test"
        message_id = create_response.json().get("id")
        
        # Now delete it
        delete_response = member_session.delete(
            f"{BASE_URL}/api/groups/{TEST_GROUP_ID}/messages/{message_id}"
        )
        assert delete_response.status_code == 200, f"Failed to delete message: {delete_response.status_code} - {delete_response.text}"
        print(f"[PASS] DELETE /groups/{{groupId}}/messages/{{messageId}} - own message deleted")

    def test_delete_message_unauthenticated(self, api_client):
        """Test DELETE requires authentication"""
        session = requests.Session()
        response = session.delete(f"{BASE_URL}/api/groups/{TEST_GROUP_ID}/messages/fake-id")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"[PASS] DELETE message requires authentication (401)")

    def test_delete_nonexistent_message(self, member_session):
        """Test DELETE returns 404 for nonexistent message"""
        response = member_session.delete(
            f"{BASE_URL}/api/groups/{TEST_GROUP_ID}/messages/nonexistent-message-id-12345"
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"[PASS] DELETE nonexistent message returns 404")


class TestPortalGroupsAPI:
    """Test portal groups endpoints used by PortalGroups.jsx"""
    
    def test_get_portal_groups(self, member_session):
        """Test GET /api/portal/groups returns available groups"""
        response = member_session.get(f"{BASE_URL}/api/portal/groups")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"[PASS] GET /portal/groups returns {len(data)} groups")
        
        # Validate group structure if groups exist
        if data:
            group = data[0]
            assert "id" in group, "Group missing 'id'"
            assert "name" in group, "Group missing 'name'"
            print(f"[PASS] Group structure validated")

    def test_get_my_groups(self, member_session):
        """Test GET /api/portal/my-groups returns member's joined groups"""
        response = member_session.get(f"{BASE_URL}/api/portal/my-groups")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "groups" in data, f"Response missing 'groups': {data}"
        groups = data["groups"]
        assert isinstance(groups, list), f"Expected list"
        print(f"[PASS] GET /portal/my-groups returns {len(groups)} joined groups")
        
        # If member has joined groups, validate structure
        if groups:
            group = groups[0]
            assert "id" in group
            assert "name" in group
            print(f"[INFO] Member has joined group: {group.get('name')}")


class TestMerchAPI:
    """Test Merch endpoints used by PortalMerch.jsx"""
    
    def test_get_merch_products(self, member_session):
        """Test GET /api/portal/merch/products returns products"""
        response = member_session.get(f"{BASE_URL}/api/portal/merch/products")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "products" in data, f"Response missing 'products'"
        products = data["products"]
        assert isinstance(products, list), f"Expected list"
        print(f"[PASS] GET /portal/merch/products returns {len(products)} products")
        
        if products:
            product = products[0]
            assert "id" in product
            assert "name" in product
            assert "price" in product
            print(f"[PASS] Product structure validated: {product.get('name')}")


class TestEventsAPI:
    """Test Events endpoints used by PortalEvents.jsx"""
    
    def test_get_portal_events(self, member_session):
        """Test GET /api/portal/events returns events"""
        response = member_session.get(f"{BASE_URL}/api/portal/events")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"[PASS] GET /portal/events returns {len(data)} events")
        
        if data:
            event = data[0]
            assert "id" in event
            assert "name" in event
            print(f"[PASS] Event structure validated")

    def test_get_my_events(self, member_session):
        """Test GET /api/portal/my-events returns registered events"""
        response = member_session.get(f"{BASE_URL}/api/portal/my-events")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "events" in data, f"Response missing 'events'"
        print(f"[PASS] GET /portal/my-events returns {len(data.get('events', []))} registered events")


class TestAdminGroupDashboard:
    """Test Admin Group Leader Dashboard endpoints"""
    
    def test_get_admin_groups(self, admin_session):
        """Test GET /api/admin/groups"""
        response = admin_session.get(f"{BASE_URL}/api/admin/groups")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "groups" in data, f"Response missing 'groups'"
        groups = data["groups"]
        print(f"[PASS] GET /admin/groups returns {len(groups)} groups")

    def test_get_group_attendance(self, admin_session):
        """Test GET /api/admin/groups/{groupId}/attendance"""
        response = admin_session.get(f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/attendance?limit=8")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "sessions" in data, f"Response missing 'sessions'"
        print(f"[PASS] GET /admin/groups/{{groupId}}/attendance returns {len(data.get('sessions', []))} sessions")

    def test_get_group_at_risk(self, admin_session):
        """Test GET /api/admin/groups/{groupId}/at-risk"""
        response = admin_session.get(f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/at-risk")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "at_risk_members" in data, f"Response missing 'at_risk_members'"
        print(f"[PASS] GET /admin/groups/{{groupId}}/at-risk returns {len(data.get('at_risk_members', []))} at-risk members")

    def test_get_group_members(self, admin_session):
        """Test GET /api/admin/groups/{groupId}/members"""
        response = admin_session.get(f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/members")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "members" in data, f"Response missing 'members'"
        print(f"[PASS] GET /admin/groups/{{groupId}}/members returns {len(data.get('members', []))} members")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
