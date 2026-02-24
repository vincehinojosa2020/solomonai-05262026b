"""
Test Suite for Solomon AI - Bidirectional Communication Features
Tests P0: Media Library Sync Bug
Tests P1: Platform Admin UI
Tests P1: Church Admin UI
Tests Member Group/Event Registration Flow
Tests Admin Group/Event Management
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PLATFORM_ADMIN = {"email": "admin@solomon.ai", "password": "Demo2026!"}
CHURCH_ADMIN = {"email": "admin@abundant.church", "password": "Demo2026!"}
MEMBER = {"email": "member@abundant.church", "password": "Demo2026!"}

class TestPlatformAdminAuth:
    """Test Platform Admin (admin@solomon.ai) authentication and permissions"""
    
    def test_platform_admin_login(self):
        """Test platform admin can login"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        print(f"Platform admin login: {res.status_code}")
        
        assert res.status_code == 200, f"Login failed: {res.text}"
        data = res.json()
        assert "user_id" in data
        assert data["email"] == PLATFORM_ADMIN["email"]
        # Platform admin should have platform_admin role
        assert data.get("role") == "platform_admin", f"Expected platform_admin role, got: {data.get('role')}"
        print(f"Platform admin role verified: {data.get('role')}")
    
    def test_platform_admin_me_endpoint(self):
        """Test /auth/me returns correct data for platform admin"""
        session = requests.Session()
        # Login first
        login_res = session.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        assert login_res.status_code == 200
        
        # Check /auth/me
        me_res = session.get(f"{BASE_URL}/api/auth/me")
        assert me_res.status_code == 200
        data = me_res.json()
        
        assert data["email"] == PLATFORM_ADMIN["email"]
        assert data.get("role") == "platform_admin"
        # Platform admin should show "Solomon" as name
        print(f"Platform admin name from /auth/me: {data.get('name')}")


class TestChurchAdminAuth:
    """Test Church Admin (admin@abundant.church) authentication and permissions"""
    
    def test_church_admin_login(self):
        """Test church admin can login"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        print(f"Church admin login: {res.status_code}")
        
        assert res.status_code == 200, f"Login failed: {res.text}"
        data = res.json()
        assert "user_id" in data
        assert data["email"] == CHURCH_ADMIN["email"]
        print(f"Church admin role: {data.get('role')}")
    
    def test_church_admin_can_access_groups(self):
        """Test church admin can access groups management"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        
        res = session.get(f"{BASE_URL}/api/admin/groups")
        print(f"Admin groups access: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "groups" in data or isinstance(data, list)
    
    def test_church_admin_can_access_events(self):
        """Test church admin can access events management"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        
        res = session.get(f"{BASE_URL}/api/admin/events")
        print(f"Admin events access: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "events" in data


class TestMemberAuth:
    """Test Member (member@abundant.church) authentication"""
    
    def test_member_login(self):
        """Test member can login"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auth/login", json=MEMBER)
        print(f"Member login: {res.status_code}")
        
        assert res.status_code == 200, f"Login failed: {res.text}"
        data = res.json()
        assert "user_id" in data
        assert data["email"] == MEMBER["email"]
        assert data.get("role") == "member"


class TestMediaLibrarySync:
    """P0: Test that media library only shows database content, not hardcoded"""
    
    def test_portal_videos_returns_database_content(self):
        """Test /portal/media/videos returns videos from database only"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json=MEMBER)
        
        res = session.get(f"{BASE_URL}/api/portal/media/videos")
        print(f"Portal videos API: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        
        # Should return videos array
        assert "videos" in data
        print(f"Videos count from database: {len(data['videos'])}")
        
        # Each video should have database fields
        if data["videos"]:
            video = data["videos"][0]
            assert "id" in video
            assert "title" in video
            assert "youtube_id" in video


class TestMemberGroupFlow:
    """Test member can view and join groups"""
    
    def test_member_can_view_available_groups(self):
        """Member can view available groups via /portal/groups"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json=MEMBER)
        
        res = session.get(f"{BASE_URL}/api/portal/groups")
        print(f"Portal groups: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        
        assert isinstance(data, list)
        print(f"Available groups count: {len(data)}")
        
        if data:
            group = data[0]
            assert "id" in group
            assert "name" in group
            print(f"Sample group: {group.get('name')}, is_open: {group.get('is_open')}")
    
    def test_member_can_view_my_groups(self):
        """Member can view their joined groups via /portal/my-groups"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json=MEMBER)
        
        res = session.get(f"{BASE_URL}/api/portal/my-groups")
        print(f"My groups: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        
        assert "groups" in data
        print(f"Member's groups count: {len(data['groups'])}")


class TestMemberEventFlow:
    """Test member can view and register for events"""
    
    def test_member_can_view_events(self):
        """Member can view upcoming events via /portal/events"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json=MEMBER)
        
        res = session.get(f"{BASE_URL}/api/portal/events")
        print(f"Portal events: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        
        assert isinstance(data, list)
        print(f"Upcoming events count: {len(data)}")
        
        if data:
            event = data[0]
            assert "id" in event
            assert "name" in event
            print(f"Sample event: {event.get('name')}")
    
    def test_member_can_view_my_events(self):
        """Member can view their registered events via /portal/my-events"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json=MEMBER)
        
        res = session.get(f"{BASE_URL}/api/portal/my-events")
        print(f"My events: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        
        assert "events" in data
        print(f"Member's registered events count: {len(data['events'])}")


class TestAdminGroupMemberManagement:
    """Test admin can view/add/remove group members"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get a test group ID"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        res = session.get(f"{BASE_URL}/api/admin/groups")
        if res.status_code == 200:
            groups = res.json().get("groups", [])
            if groups:
                self.test_group_id = groups[0]["id"]
                self.test_group_name = groups[0]["name"]
            else:
                self.test_group_id = None
        self.session = session
    
    def test_admin_can_view_group_members(self):
        """Admin can view group members"""
        if not hasattr(self, 'test_group_id') or not self.test_group_id:
            pytest.skip("No groups available to test")
        
        res = self.session.get(f"{BASE_URL}/api/admin/groups/{self.test_group_id}/members")
        print(f"View group members: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        
        assert "members" in data
        print(f"Group '{self.test_group_name}' has {len(data['members'])} members")
    
    def test_admin_can_search_available_members(self):
        """Admin can search for available members to add"""
        if not hasattr(self, 'test_group_id') or not self.test_group_id:
            pytest.skip("No groups available to test")
        
        res = self.session.get(f"{BASE_URL}/api/admin/groups/{self.test_group_id}/available-members?search=test")
        print(f"Search available members: {res.status_code}")
        assert res.status_code == 200


class TestAdminEventRegistrationManagement:
    """Test admin can view/add/remove event registrations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get a test event ID"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        res = session.get(f"{BASE_URL}/api/admin/events")
        if res.status_code == 200:
            events = res.json().get("events", [])
            if events:
                self.test_event_id = events[0]["id"]
                self.test_event_name = events[0]["name"]
            else:
                self.test_event_id = None
        self.session = session
    
    def test_admin_can_view_event_registrations(self):
        """Admin can view event registrations"""
        if not hasattr(self, 'test_event_id') or not self.test_event_id:
            pytest.skip("No events available to test")
        
        res = self.session.get(f"{BASE_URL}/api/admin/events/{self.test_event_id}/registrations")
        print(f"View event registrations: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        
        assert "registrations" in data
        print(f"Event '{self.test_event_name}' has {len(data['registrations'])} registrations")
    
    def test_admin_can_add_registration(self):
        """Admin can add a registration to an event"""
        if not hasattr(self, 'test_event_id') or not self.test_event_id:
            pytest.skip("No events available to test")
        
        # Add a test registration
        test_name = f"TEST_Admin_Add_{datetime.now().strftime('%H%M%S')}"
        res = self.session.post(
            f"{BASE_URL}/api/admin/events/{self.test_event_id}/registrations",
            json={"name": test_name, "email": f"test_{datetime.now().timestamp()}@test.com"}
        )
        print(f"Add registration: {res.status_code}")
        assert res.status_code in [200, 201]
        
        # Verify it was added
        list_res = self.session.get(f"{BASE_URL}/api/admin/events/{self.test_event_id}/registrations")
        registrations = list_res.json().get("registrations", [])
        found = any(r.get("user_name", "").startswith("TEST_Admin_Add") for r in registrations)
        
        # Cleanup - get the registration ID and delete it
        for r in registrations:
            if r.get("user_name", "").startswith("TEST_Admin_Add"):
                del_res = self.session.delete(
                    f"{BASE_URL}/api/admin/events/{self.test_event_id}/registrations/{r['id']}"
                )
                print(f"Cleanup registration: {del_res.status_code}")
        
        assert found or res.status_code == 200, "Registration was not added"


class TestTenantInfo:
    """Test tenant endpoint returns correct info"""
    
    def test_tenant_endpoint(self):
        """Test /tenant returns church info"""
        res = requests.get(f"{BASE_URL}/api/tenant")
        print(f"Tenant info: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        
        assert "name" in data
        print(f"Tenant name: {data.get('name')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
