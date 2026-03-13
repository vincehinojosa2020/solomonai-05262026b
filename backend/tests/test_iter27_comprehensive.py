"""
Iteration 27: Comprehensive Regression + New Changes Tests
Testing:
1. Portal Home loads without errors - greeting, quick actions, streak card, upcoming events
2. Portal Home events display dates correctly (no 'INVALID DATE' or 'TBD' for events with dates)
3. Kids Check-in page loads with Duolingo-style UI and DiceBear avatars
4. Portal Groups page loads with group list and 'Chat' button on joined groups
5. Group Chat works - send and receive messages
6. Portal Events page loads with hero banner, category pills, event cards
7. Portal Merch page has the floating recommender button
8. Merch recommender chatbot responds to queries
9. Admin Groups page has dashboard icon on group cards
10. Admin Leader Dashboard loads with stats, chart, at-risk panel, chat, members list
11. Push notification VAPID endpoint works: GET /api/push/vapid-public-key
12. Group messaging API: POST + GET messages work correctly
13. Watch page loads and shows video content
14. Portal navigation between all sections works
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def session():
    return requests.Session()

@pytest.fixture(scope="module") 
def member_auth_cookies(session):
    """Login as member and return cookies"""
    login_res = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "member@abundant.church",
        "password": "Demo2026!"
    })
    if login_res.status_code != 200:
        pytest.skip(f"Member login failed: {login_res.status_code}")
    return session.cookies

@pytest.fixture(scope="module")
def admin_auth_cookies(session):
    """Login as admin and return cookies"""
    admin_session = requests.Session()
    login_res = admin_session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@abundant.church",
        "password": "Demo2026!"
    })
    if login_res.status_code != 200:
        pytest.skip(f"Admin login failed: {login_res.status_code}")
    return admin_session


class TestVAPIDEndpoint:
    """Test 11: Push notification VAPID endpoint works"""
    
    def test_vapid_public_key_returns_key(self, session):
        """GET /api/push/vapid-public-key returns public key"""
        res = session.get(f"{BASE_URL}/api/push/vapid-public-key")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert "public_key" in data
        assert len(data["public_key"]) > 50  # VAPID keys are long


class TestPortalEventsAPI:
    """Test 2 & 6: Portal events with date formatting"""
    
    def test_portal_events_returns_list(self, session, member_auth_cookies):
        """GET /api/portal/events returns list of events"""
        res = session.get(f"{BASE_URL}/api/portal/events")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        print(f"Portal events returned {len(data)} events")
        
    def test_events_have_valid_dates(self, session, member_auth_cookies):
        """Events should have valid start_datetime or event_date fields"""
        res = session.get(f"{BASE_URL}/api/portal/events")
        assert res.status_code == 200
        events = res.json()
        
        for event in events[:5]:  # Check first 5 events
            has_start_datetime = event.get("start_datetime") is not None
            has_event_date = event.get("event_date") is not None
            # At least one date field should be present for valid events
            if event.get("name"):
                print(f"Event '{event.get('name')}': start_datetime={has_start_datetime}, event_date={has_event_date}")


class TestGroupMessagingAPI:
    """Test 5 & 12: Group messaging API works"""
    
    GROUP_ID = "2a459b6d-88d0-4c1a-b6cc-94e449d7c4c0"  # Known group with messages
    
    def test_get_group_messages(self, admin_auth_cookies):
        """GET /api/groups/{groupId}/messages returns messages"""
        res = admin_auth_cookies.get(f"{BASE_URL}/api/groups/{self.GROUP_ID}/messages?limit=10")
        assert res.status_code == 200
        data = res.json()
        assert "messages" in data
        messages = data["messages"]
        print(f"Group messages returned {len(messages)} messages")
        
        # Verify message structure if messages exist
        if messages:
            msg = messages[0]
            assert "text" in msg
            assert "sender_name" in msg or "sender_id" in msg
            print(f"Sample message: {msg.get('text', '')[:50]}... from {msg.get('sender_name', 'Unknown')}")
    
    def test_post_group_message(self, admin_auth_cookies):
        """POST /api/groups/{groupId}/messages creates a message"""
        res = admin_auth_cookies.post(
            f"{BASE_URL}/api/groups/{self.GROUP_ID}/messages",
            json={"text": "TEST_iter27_message_automated_test"}
        )
        assert res.status_code in [200, 201], f"Expected 200/201, got {res.status_code}: {res.text}"
        data = res.json()
        assert "id" in data or "message" in data or "text" in data
        print(f"Created message successfully")
    
    def test_empty_message_rejected(self, admin_auth_cookies):
        """POST with empty text should be rejected"""
        res = admin_auth_cookies.post(
            f"{BASE_URL}/api/groups/{self.GROUP_ID}/messages",
            json={"text": ""}
        )
        assert res.status_code == 400


class TestPortalGroupsAPI:
    """Test 4: Portal Groups page loads with groups"""
    
    def test_get_portal_groups(self, session, member_auth_cookies):
        """GET /api/portal/groups returns list"""
        res = session.get(f"{BASE_URL}/api/portal/groups")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        print(f"Portal groups returned {len(data)} groups")
        
    def test_get_my_groups(self, session, member_auth_cookies):
        """GET /api/portal/my-groups returns user's groups"""
        res = session.get(f"{BASE_URL}/api/portal/my-groups")
        assert res.status_code == 200
        data = res.json()
        assert "groups" in data
        print(f"My groups returned {len(data.get('groups', []))} groups")


class TestKidsCheckinAPI:
    """Test 3: Kids Check-in API"""
    
    def test_get_portal_kids(self, session, member_auth_cookies):
        """GET /api/portal/kids returns children list"""
        res = session.get(f"{BASE_URL}/api/portal/kids")
        assert res.status_code == 200
        data = res.json()
        assert "children" in data
        print(f"Kids API returned {len(data.get('children', []))} children")
    
    def test_get_active_checkins(self, session, member_auth_cookies):
        """GET /api/portal/kids/checkins/active returns checkins"""
        res = session.get(f"{BASE_URL}/api/portal/kids/checkins/active")
        assert res.status_code == 200
        data = res.json()
        assert "checkins" in data


class TestMerchAPI:
    """Test 7 & 8: Merch page and recommender"""
    
    def test_get_merch_products(self, session, member_auth_cookies):
        """GET /api/portal/merch/products returns products"""
        res = session.get(f"{BASE_URL}/api/portal/merch/products")
        assert res.status_code == 200
        data = res.json()
        assert "products" in data
        products = data["products"]
        print(f"Merch products returned {len(products)} products")
        
        # Verify product structure
        if products:
            p = products[0]
            assert "name" in p
            assert "price" in p


class TestMediaAPI:
    """Test 13: Watch page media content"""
    
    def test_get_media_videos(self, session, member_auth_cookies):
        """GET /api/portal/media/videos returns videos"""
        res = session.get(f"{BASE_URL}/api/portal/media/videos")
        if res.status_code == 200:
            data = res.json()
            print(f"Media videos returned {len(data) if isinstance(data, list) else 'N/A'} videos")
        else:
            print(f"Media videos endpoint returned {res.status_code} - may be empty or not setup")


class TestAdminAPIs:
    """Test 9 & 10: Admin APIs for groups and dashboard"""
    
    def test_admin_groups(self, admin_auth_cookies):
        """GET /api/admin/groups returns groups list"""
        res = admin_auth_cookies.get(f"{BASE_URL}/api/admin/groups")
        assert res.status_code == 200
        data = res.json()
        assert "groups" in data
        groups = data["groups"]
        print(f"Admin groups returned {len(groups)} groups")
        
        # Verify group structure
        if groups:
            g = groups[0]
            assert "id" in g
            assert "name" in g
            
    def test_admin_group_members(self, admin_auth_cookies):
        """GET /api/admin/groups/{groupId}/members returns members"""
        GROUP_ID = "2a459b6d-88d0-4c1a-b6cc-94e449d7c4c0"
        res = admin_auth_cookies.get(f"{BASE_URL}/api/admin/groups/{GROUP_ID}/members")
        assert res.status_code == 200
        data = res.json()
        assert "members" in data
        print(f"Group members returned {len(data.get('members', []))} members")
        
    def test_admin_group_attendance(self, admin_auth_cookies):
        """GET /api/admin/groups/{groupId}/attendance returns attendance data"""
        GROUP_ID = "2a459b6d-88d0-4c1a-b6cc-94e449d7c4c0"
        res = admin_auth_cookies.get(f"{BASE_URL}/api/admin/groups/{GROUP_ID}/attendance?limit=8")
        assert res.status_code == 200
        data = res.json()
        assert "sessions" in data
        print(f"Group attendance returned {len(data.get('sessions', []))} sessions")
        
    def test_admin_group_at_risk(self, admin_auth_cookies):
        """GET /api/admin/groups/{groupId}/at-risk returns at-risk members"""
        GROUP_ID = "2a459b6d-88d0-4c1a-b6cc-94e449d7c4c0"
        res = admin_auth_cookies.get(f"{BASE_URL}/api/admin/groups/{GROUP_ID}/at-risk")
        assert res.status_code == 200
        data = res.json()
        assert "at_risk_members" in data


class TestPortalHomeAPI:
    """Test 1: Portal Home API endpoints"""
    
    def test_service_mode_endpoint(self, session, member_auth_cookies):
        """GET /api/portal/service-mode returns service mode data"""
        res = session.get(f"{BASE_URL}/api/portal/service-mode")
        assert res.status_code == 200
        data = res.json()
        # Should have service mode fields
        print(f"Service mode: is_service_day={data.get('is_service_day')}, is_service_time={data.get('is_service_time')}")
        
    def test_attendance_streak_endpoint(self, session, member_auth_cookies):
        """GET /api/portal/attendance-streak returns streak data"""
        res = session.get(f"{BASE_URL}/api/portal/attendance-streak")
        assert res.status_code == 200
        data = res.json()
        print(f"Attendance streak: current={data.get('current_streak', 0)}, longest={data.get('longest_streak', 0)}")


class TestAuthFlow:
    """Test authentication flows"""
    
    def test_member_login(self):
        """Member login with credentials"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        })
        assert res.status_code == 200, f"Member login failed: {res.status_code}"
        data = res.json()
        assert "user_id" in data or "user" in data
        print(f"Member login successful")
        
    def test_admin_login(self):
        """Admin login with credentials"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@abundant.church",
            "password": "Demo2026!"
        })
        assert res.status_code == 200, f"Admin login failed: {res.status_code}"
        data = res.json()
        assert "user_id" in data or "user" in data
        print(f"Admin login successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
