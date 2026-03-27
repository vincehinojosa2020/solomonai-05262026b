"""
Iteration 58: Phase 4 Groups Module Tests
Tests for: enrollment workflows, join requests, group events + RSVP, resources, and group chat
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "shannonnieman1030@gmail.com"
ADMIN_PASSWORD = "Demo2026!"

# Test group ID for events/resources/messages
TEST_GROUP_ID = "group_abundant_001"


class TestPhase4Setup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("session_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_api_health(self):
        """Test API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ API health check passed")


class TestGroupCRUDWithEnrollment:
    """Test group CRUD with enrollment_type and category fields"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json().get("session_token") or response.json().get("token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_create_group_with_enrollment_type(self, auth_headers):
        """POST /api/admin/groups creates group with enrollment_type and category"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "name": f"TEST_Phase4_Group_{unique_id}",
            "description": "Test group for Phase 4",
            "group_type": "Small Group",
            "enrollment_type": "request_to_join",
            "category": "discipleship",
            "is_open": True
        }
        response = requests.post(f"{BASE_URL}/api/admin/groups", json=payload, headers=auth_headers)
        assert response.status_code in [200, 201], f"Create group failed: {response.text}"
        data = response.json()
        group = data.get("group", data)
        
        # Verify enrollment_type and category are stored
        assert group.get("enrollment_type") == "request_to_join", "enrollment_type not saved"
        assert group.get("category") == "discipleship", "category not saved"
        print(f"✓ Created group with enrollment_type=request_to_join, category=discipleship")
        
        # Store group ID for cleanup
        pytest.test_group_id = group.get("id")
        return group
    
    def test_update_group_enrollment_type(self, auth_headers):
        """PUT /api/admin/groups/{id} updates enrollment_type and category"""
        if not hasattr(pytest, 'test_group_id'):
            pytest.skip("No test group created")
        
        payload = {
            "enrollment_type": "closed",
            "category": "fellowship"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/groups/{pytest.test_group_id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Update group failed: {response.text}"
        
        # Verify update persisted
        get_response = requests.get(f"{BASE_URL}/api/admin/groups/{pytest.test_group_id}", headers=auth_headers)
        if get_response.status_code == 200:
            group = get_response.json()
            assert group.get("enrollment_type") == "closed", "enrollment_type not updated"
            assert group.get("category") == "fellowship", "category not updated"
        print("✓ Updated group enrollment_type and category")
    
    def test_cleanup_test_group(self, auth_headers):
        """Cleanup test group"""
        if hasattr(pytest, 'test_group_id'):
            response = requests.delete(
                f"{BASE_URL}/api/admin/groups/{pytest.test_group_id}",
                headers=auth_headers
            )
            print(f"✓ Cleanup: deleted test group (status: {response.status_code})")


class TestJoinRequests:
    """Test join request endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json().get("session_token") or response.json().get("token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_get_all_join_requests(self, auth_headers):
        """GET /api/admin/groups/join-requests/all returns pending requests"""
        response = requests.get(
            f"{BASE_URL}/api/admin/groups/join-requests/all",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get join requests failed: {response.text}"
        data = response.json()
        assert "requests" in data, "Response missing 'requests' field"
        assert "total" in data, "Response missing 'total' field"
        print(f"✓ GET /api/admin/groups/join-requests/all returned {data['total']} requests")
    
    def test_get_group_join_requests(self, auth_headers):
        """GET /api/admin/groups/{group_id}/join-requests returns group-specific requests"""
        response = requests.get(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/join-requests",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get group join requests failed: {response.text}"
        data = response.json()
        assert "requests" in data
        print(f"✓ GET /api/admin/groups/{TEST_GROUP_ID}/join-requests returned {data.get('total', 0)} requests")


class TestGroupEvents:
    """Test group events and RSVP endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json().get("session_token") or response.json().get("token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_create_group_event(self, auth_headers):
        """POST /api/admin/groups/{groupId}/events creates a group event"""
        unique_id = str(uuid.uuid4())[:8]
        event_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        payload = {
            "title": f"TEST_Event_{unique_id}",
            "description": "Test event for Phase 4",
            "event_date": event_date,
            "event_time": "19:00",
            "location": "Room 101"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/events",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201], f"Create event failed: {response.text}"
        data = response.json()
        event = data.get("event", data)
        assert event.get("title") == payload["title"], "Event title not saved"
        assert event.get("event_date") == event_date, "Event date not saved"
        
        pytest.test_event_id = event.get("id")
        print(f"✓ Created group event: {event.get('title')}")
    
    def test_get_group_events(self, auth_headers):
        """GET /api/admin/groups/{groupId}/events returns events with RSVP counts"""
        response = requests.get(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/events",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get events failed: {response.text}"
        data = response.json()
        assert "events" in data, "Response missing 'events' field"
        
        # Check if events have RSVP counts
        if data["events"]:
            event = data["events"][0]
            assert "rsvp_counts" in event or "total_rsvps" in event, "Events should have RSVP counts"
        print(f"✓ GET /api/admin/groups/{TEST_GROUP_ID}/events returned {len(data['events'])} events")
    
    def test_rsvp_to_event(self, auth_headers):
        """POST /api/admin/groups/{groupId}/events/{eventId}/rsvp records RSVP"""
        if not hasattr(pytest, 'test_event_id'):
            pytest.skip("No test event created")
        
        payload = {
            "person_id": "test_person_001",
            "person_name": "Test Person",
            "response": "attending"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/events/{pytest.test_event_id}/rsvp",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"RSVP failed: {response.text}"
        print("✓ RSVP recorded successfully")
    
    def test_get_event_rsvps(self, auth_headers):
        """GET /api/admin/groups/{groupId}/events/{eventId}/rsvps returns RSVPs"""
        if not hasattr(pytest, 'test_event_id'):
            pytest.skip("No test event created")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/events/{pytest.test_event_id}/rsvps",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get RSVPs failed: {response.text}"
        data = response.json()
        assert "rsvps" in data, "Response missing 'rsvps' field"
        print(f"✓ GET event RSVPs returned {len(data['rsvps'])} RSVPs")
    
    def test_delete_group_event(self, auth_headers):
        """DELETE /api/admin/groups/{groupId}/events/{eventId} deletes event"""
        if not hasattr(pytest, 'test_event_id'):
            pytest.skip("No test event created")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/events/{pytest.test_event_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Delete event failed: {response.text}"
        print("✓ Deleted test event")


class TestGroupResources:
    """Test group resources endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json().get("session_token") or response.json().get("token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_add_group_resource(self, auth_headers):
        """POST /api/admin/groups/{groupId}/resources adds a resource"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "title": f"TEST_Resource_{unique_id}",
            "description": "Test resource for Phase 4",
            "resource_type": "link",
            "url": "https://example.com/test-resource"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/resources",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201], f"Add resource failed: {response.text}"
        data = response.json()
        resource = data.get("resource", data)
        assert resource.get("title") == payload["title"], "Resource title not saved"
        
        pytest.test_resource_id = resource.get("id")
        print(f"✓ Added group resource: {resource.get('title')}")
    
    def test_get_group_resources(self, auth_headers):
        """GET /api/admin/groups/{groupId}/resources lists resources"""
        response = requests.get(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/resources",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get resources failed: {response.text}"
        data = response.json()
        assert "resources" in data, "Response missing 'resources' field"
        print(f"✓ GET /api/admin/groups/{TEST_GROUP_ID}/resources returned {len(data['resources'])} resources")
    
    def test_delete_group_resource(self, auth_headers):
        """DELETE /api/admin/groups/{groupId}/resources/{resourceId} deletes resource"""
        if not hasattr(pytest, 'test_resource_id'):
            pytest.skip("No test resource created")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/resources/{pytest.test_resource_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Delete resource failed: {response.text}"
        print("✓ Deleted test resource")


class TestGroupMessages:
    """Test group chat/messages endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json().get("session_token") or response.json().get("token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_send_group_message(self, auth_headers):
        """POST /api/admin/groups/{groupId}/messages sends a message"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "content": f"TEST_Message_{unique_id}: Hello from Phase 4 testing!"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/messages",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201], f"Send message failed: {response.text}"
        data = response.json()
        message = data.get("message", data)
        assert message.get("content") == payload["content"], "Message content not saved"
        
        pytest.test_message_id = message.get("id")
        print(f"✓ Sent group message")
    
    def test_get_group_messages(self, auth_headers):
        """GET /api/admin/groups/{groupId}/messages returns messages"""
        response = requests.get(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/messages",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get messages failed: {response.text}"
        data = response.json()
        assert "messages" in data, "Response missing 'messages' field"
        print(f"✓ GET /api/admin/groups/{TEST_GROUP_ID}/messages returned {len(data['messages'])} messages")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json().get("session_token") or response.json().get("token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_cleanup_test_events(self, auth_headers):
        """Cleanup any remaining TEST_ events"""
        response = requests.get(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/events",
            headers=auth_headers
        )
        if response.status_code == 200:
            events = response.json().get("events", [])
            for event in events:
                if event.get("title", "").startswith("TEST_"):
                    requests.delete(
                        f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/events/{event['id']}",
                        headers=auth_headers
                    )
        print("✓ Cleanup: removed TEST_ events")
    
    def test_cleanup_test_resources(self, auth_headers):
        """Cleanup any remaining TEST_ resources"""
        response = requests.get(
            f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/resources",
            headers=auth_headers
        )
        if response.status_code == 200:
            resources = response.json().get("resources", [])
            for resource in resources:
                if resource.get("title", "").startswith("TEST_"):
                    requests.delete(
                        f"{BASE_URL}/api/admin/groups/{TEST_GROUP_ID}/resources/{resource['id']}",
                        headers=auth_headers
                    )
        print("✓ Cleanup: removed TEST_ resources")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
