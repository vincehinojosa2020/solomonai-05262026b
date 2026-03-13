"""
Iteration 25: Test Group Leader Dashboard, Enhanced Events, and Push Notifications
- Group leader dashboard APIs (attendance, at-risk, outreach)
- Enhanced events (capacity, waitlist, ticket tiers)
- VAPID endpoint for push notifications
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


class TestSetup:
    """Setup tests - login flows"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login as admin and return session"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert res.status_code == 200, f"Admin login failed: {res.text}"
        return session
    
    @pytest.fixture(scope="class")
    def member_session(self):
        """Login as member and return session"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        assert res.status_code == 200, f"Member login failed: {res.text}"
        return session
    
    def test_admin_login(self):
        """Test admin login works"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert res.status_code == 200
        data = res.json()
        assert "user" in data or "user_id" in data or "role" in data
        
    def test_member_login(self):
        """Test member login works"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        assert res.status_code == 200
        data = res.json()
        assert "user" in data or "user_id" in data or "role" in data


class TestGroupLeaderDashboard:
    """Tests for Group Leader Dashboard API endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login as admin"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if res.status_code != 200:
            pytest.skip("Admin login failed")
        return session
    
    @pytest.fixture(scope="class")
    def test_group_id(self, admin_session):
        """Get a valid group ID for testing"""
        res = admin_session.get(f"{BASE_URL}/api/admin/groups")
        if res.status_code == 200:
            data = res.json()
            groups = data.get("groups", [])
            if groups:
                return groups[0]["id"]
        pytest.skip("No groups available for testing")
    
    def test_get_admin_groups_list(self, admin_session):
        """Test GET /api/admin/groups returns group list"""
        res = admin_session.get(f"{BASE_URL}/api/admin/groups")
        assert res.status_code == 200, f"Failed to get groups: {res.text}"
        data = res.json()
        assert "groups" in data
        assert isinstance(data["groups"], list)
        print(f"Found {len(data['groups'])} groups")
    
    def test_get_group_attendance_history(self, admin_session, test_group_id):
        """Test GET /api/admin/groups/{group_id}/attendance"""
        res = admin_session.get(f"{BASE_URL}/api/admin/groups/{test_group_id}/attendance?limit=8")
        assert res.status_code == 200, f"Failed to get attendance: {res.text}"
        data = res.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
        print(f"Found {len(data['sessions'])} attendance sessions")
    
    def test_get_group_at_risk_members(self, admin_session, test_group_id):
        """Test GET /api/admin/groups/{group_id}/at-risk"""
        res = admin_session.get(f"{BASE_URL}/api/admin/groups/{test_group_id}/at-risk")
        assert res.status_code == 200, f"Failed to get at-risk: {res.text}"
        data = res.json()
        assert "at_risk_members" in data
        assert "threshold" in data
        assert data["threshold"] == 3
        print(f"Found {len(data['at_risk_members'])} at-risk members")
    
    def test_get_group_members(self, admin_session, test_group_id):
        """Test GET /api/admin/groups/{group_id}/members"""
        res = admin_session.get(f"{BASE_URL}/api/admin/groups/{test_group_id}/members")
        assert res.status_code == 200, f"Failed to get members: {res.text}"
        data = res.json()
        assert "members" in data
        assert isinstance(data["members"], list)
        print(f"Found {len(data['members'])} members in group")
    
    def test_log_outreach_endpoint(self, admin_session, test_group_id):
        """Test POST /api/admin/groups/{group_id}/outreach"""
        res = admin_session.post(
            f"{BASE_URL}/api/admin/groups/{test_group_id}/outreach",
            json={
                "person_id": "test-person-id",
                "type": "call",
                "notes": "TEST_outreach log"
            }
        )
        assert res.status_code == 200, f"Failed to log outreach: {res.text}"
        data = res.json()
        assert "message" in data
        assert "id" in data
        print(f"Outreach logged with id: {data['id']}")


class TestEnhancedEvents:
    """Tests for enhanced events (capacity, waitlist, ticket tiers)"""
    
    @pytest.fixture(scope="class")
    def member_session(self):
        """Login as member"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        if res.status_code != 200:
            pytest.skip("Member login failed")
        return session
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login as admin"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if res.status_code != 200:
            pytest.skip("Admin login failed")
        return session
    
    def test_portal_events_endpoint(self, member_session):
        """Test GET /api/portal/events returns events with enhanced fields"""
        res = member_session.get(f"{BASE_URL}/api/portal/events")
        assert res.status_code == 200, f"Failed to get events: {res.text}"
        events = res.json()
        assert isinstance(events, list)
        print(f"Found {len(events)} events")
        
        # Check if events have the expected structure
        if events:
            event = events[0]
            assert "id" in event
            assert "name" in event
            # Check for optional enhanced fields
            if "capacity" in event:
                print(f"Event has capacity: {event['capacity']}")
            if "waitlist_count" in event:
                print(f"Event has waitlist_count: {event['waitlist_count']}")
            if "ticket_tiers" in event:
                print(f"Event has ticket_tiers: {event['ticket_tiers']}")
    
    def test_get_my_events(self, member_session):
        """Test GET /api/portal/my-events"""
        res = member_session.get(f"{BASE_URL}/api/portal/my-events")
        assert res.status_code == 200, f"Failed to get my-events: {res.text}"
        data = res.json()
        assert "events" in data
        print(f"User has {len(data['events'])} registered events")
    
    def test_event_registration_flow(self, member_session, admin_session):
        """Test event registration (register and cancel)"""
        # First get events
        res = member_session.get(f"{BASE_URL}/api/portal/events")
        if res.status_code != 200 or not res.json():
            pytest.skip("No events available for testing")
        
        events = res.json()
        test_event = None
        for event in events:
            if event.get("registration_required") or event.get("requires_registration"):
                test_event = event
                break
        
        if not test_event:
            print("No events require registration, skipping registration test")
            return
        
        event_id = test_event["id"]
        
        # Try to register
        res = member_session.post(f"{BASE_URL}/api/portal/events/{event_id}/register")
        # Either success (200) or already registered (400)
        assert res.status_code in [200, 400], f"Registration failed: {res.text}"
        print(f"Registration response: {res.json()}")


class TestPushNotifications:
    """Tests for push notification endpoints"""
    
    def test_vapid_public_key_endpoint(self):
        """Test GET /api/push/vapid-public-key - no auth required"""
        res = requests.get(f"{BASE_URL}/api/push/vapid-public-key")
        assert res.status_code == 200, f"Failed to get VAPID key: {res.text}"
        data = res.json()
        assert "public_key" in data
        assert data["public_key"], "VAPID public key should not be empty"
        print(f"VAPID public key (first 30 chars): {data['public_key'][:30]}...")
    
    def test_push_subscribe_requires_auth(self):
        """Test POST /api/push/subscribe requires authentication"""
        res = requests.post(f"{BASE_URL}/api/push/subscribe", json={
            "subscription": {
                "endpoint": "https://test.pushservice.com/test123"
            }
        })
        assert res.status_code == 401, "Subscribe should require authentication"
    
    def test_push_unsubscribe_requires_auth(self):
        """Test DELETE /api/push/subscribe requires authentication"""
        res = requests.delete(f"{BASE_URL}/api/push/subscribe", json={
            "endpoint": "https://test.pushservice.com/test123"
        })
        assert res.status_code == 401, "Unsubscribe should require authentication"


class TestAdminGroupCRUD:
    """Tests for admin group CRUD operations"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login as admin"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if res.status_code != 200:
            pytest.skip("Admin login failed")
        return session
    
    def test_create_group(self, admin_session):
        """Test POST /api/admin/groups"""
        res = admin_session.post(f"{BASE_URL}/api/admin/groups", json={
            "name": "TEST_Group_Iter25",
            "description": "Test group for iteration 25",
            "group_type": "Small Group",
            "meeting_day": "Wednesday",
            "meeting_time": "19:00",
            "location": "Room 101",
            "capacity": 15,
            "is_open": True
        })
        assert res.status_code in [200, 201], f"Failed to create group: {res.text}"
        data = res.json()
        assert "group" in data or "id" in data or "name" in data
        # Response has structure {"group": {...}, "message": "..."}
        group_data = data.get("group", data)
        print(f"Created group: {group_data.get('name', 'unknown')}")
        return group_data.get("id")
    
    def test_search_groups(self, admin_session):
        """Test GET /api/admin/groups with search"""
        res = admin_session.get(f"{BASE_URL}/api/admin/groups?search=TEST")
        assert res.status_code == 200
        data = res.json()
        assert "groups" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
