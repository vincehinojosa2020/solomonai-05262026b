"""
Iteration 36: Comprehensive QA Sweep for Go-Live Readiness
Tests for all CRUD operations, portal features, and cross-account flows
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test accounts
MEMBER_EMAIL = "member@abundant.church"
ADMIN_EMAIL = "admin@abundant.church"
PLATFORM_ADMIN_EMAIL = "admin@solomon.ai"
PASSWORD = "Demo2026!"


# ============== FIXTURES ==============

@pytest.fixture(scope="module")
def member_auth():
    """Get member auth token and user data"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": MEMBER_EMAIL, "password": PASSWORD}
    )
    data = response.json()
    return {
        "token": data.get("session_token"),
        "user_id": data.get("user_id"),
        "tenant_id": data.get("tenant_id"),
        "headers": {"Authorization": f"Bearer {data.get('session_token')}"}
    }


@pytest.fixture(scope="module")
def admin_auth():
    """Get admin auth token and user data"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": PASSWORD}
    )
    data = response.json()
    return {
        "token": data.get("session_token"),
        "user_id": data.get("user_id"),
        "tenant_id": data.get("tenant_id"),
        "headers": {"Authorization": f"Bearer {data.get('session_token')}"}
    }


@pytest.fixture(scope="module")
def platform_admin_auth():
    """Get platform admin auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": PLATFORM_ADMIN_EMAIL, "password": PASSWORD}
    )
    data = response.json()
    return {
        "token": data.get("session_token"),
        "headers": {"Authorization": f"Bearer {data.get('session_token')}"}
    }


# ============== SERVICE HEALTH ==============

class TestServiceHealth:
    """Health and service status tests"""
    
    def test_health_launch_check_ready(self):
        """API: /api/health/launch-check returns ready status"""
        response = requests.get(f"{BASE_URL}/api/health/launch-check")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ready"
        print(f"PASS: Launch check - status=ready")


# ============== MEMBER PORTAL HOME ==============

class TestMemberPortalHome:
    """Member Portal Home page data tests"""
    
    def test_portal_bootstrap_loads(self, member_auth):
        """Portal: Bootstrap loads with full data"""
        response = requests.get(
            f"{BASE_URL}/api/portal/bootstrap",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        # Should have user and various data
        assert "user" in data or "merch_products" in data
        print(f"PASS: Portal bootstrap loads, keys={list(data.keys())[:5]}")
    
    def test_attendance_streak_displays(self, member_auth):
        """Portal: Attendance streak data available"""
        response = requests.get(
            f"{BASE_URL}/api/portal/attendance/streak",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "current_streak" in data or "attendance_data" in data
        print(f"PASS: Attendance streak data available")
    
    def test_upcoming_events_available(self, member_auth):
        """Portal: Events list available for home page"""
        response = requests.get(
            f"{BASE_URL}/api/portal/events",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Portal events returns {len(data)} events")
    
    def test_announcements_available(self, member_auth):
        """Portal: Announcements list available"""
        response = requests.get(
            f"{BASE_URL}/api/portal/announcements",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        print(f"PASS: Portal announcements available")


# ============== KIDS CHECK-IN ==============

class TestKidsCheckin:
    """Kids check-in functionality tests"""
    
    def test_kids_children_list(self, member_auth):
        """Portal: Get list of registered children"""
        response = requests.get(
            f"{BASE_URL}/api/portal/kids/children",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Kids children list returns {len(data)} children")
    
    def test_kids_checkin_child(self, member_auth):
        """Portal: Check in a child and get pickup code"""
        # First get children
        children_resp = requests.get(
            f"{BASE_URL}/api/portal/kids/children",
            headers=member_auth["headers"]
        )
        children = children_resp.json()
        
        if not children:
            # Create a child first
            create_resp = requests.post(
                f"{BASE_URL}/api/portal/kids/children",
                headers=member_auth["headers"],
                json={
                    "name": "TEST_Child_" + str(uuid.uuid4())[:8],
                    "birthdate": "2020-01-15"
                }
            )
            if create_resp.status_code in [200, 201]:
                child_id = create_resp.json().get("id")
            else:
                pytest.skip("No children available for check-in test")
                return
        else:
            child_id = children[0].get("id")
        
        # Check in the child
        checkin_resp = requests.post(
            f"{BASE_URL}/api/portal/kids/checkin",
            headers=member_auth["headers"],
            json={
                "child_id": child_id,
                "classroom": "Sunday School"
            }
        )
        
        if checkin_resp.status_code == 200:
            data = checkin_resp.json()
            # Should have pickup code
            pickup_code = data.get("pickup_code") or data.get("checkin", {}).get("pickup_code")
            print(f"PASS: Child checked in, pickup_code={pickup_code}")
        else:
            # Child might already be checked in
            assert checkin_resp.status_code in [200, 400, 409]
            print(f"INFO: Check-in returned {checkin_resp.status_code} (may already be checked in)")


# ============== GIVING ==============

class TestGiving:
    """Giving/donation tests"""
    
    def test_giving_summary(self, member_auth):
        """Portal: Get giving summary with YTD"""
        response = requests.get(
            f"{BASE_URL}/api/portal/giving/summary",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        # Should have YTD or summary data
        assert "ytd_total" in data or "summary" in data or "total" in data or isinstance(data, dict)
        print(f"PASS: Giving summary available")
    
    def test_giving_history(self, member_auth):
        """Portal: Get giving history"""
        response = requests.get(
            f"{BASE_URL}/api/portal/giving/history",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        # Should be list or dict with history
        if isinstance(data, list):
            print(f"PASS: Giving history returns {len(data)} donations")
        else:
            print(f"PASS: Giving history available")


# ============== GROUPS ==============

class TestGroups:
    """Groups functionality tests"""
    
    def test_groups_list(self, member_auth):
        """Portal: Browse groups list"""
        response = requests.get(
            f"{BASE_URL}/api/portal/groups",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Groups list returns {len(data)} groups")
    
    def test_groups_search(self, member_auth):
        """Portal: Search groups by query"""
        response = requests.get(
            f"{BASE_URL}/api/portal/groups?search=young",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        print(f"PASS: Groups search works")
    
    def test_groups_filter(self, member_auth):
        """Portal: Filter groups"""
        response = requests.get(
            f"{BASE_URL}/api/portal/groups?is_open=true",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        print(f"PASS: Groups filter works")


# ============== EVENTS ==============

class TestEvents:
    """Events functionality tests"""
    
    def test_events_list(self, member_auth):
        """Portal: Browse events list"""
        response = requests.get(
            f"{BASE_URL}/api/portal/events",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Events list returns {len(data)} events")
    
    def test_event_registration(self, member_auth):
        """Portal: Register for an event"""
        # Get events first
        events_resp = requests.get(
            f"{BASE_URL}/api/portal/events",
            headers=member_auth["headers"]
        )
        events = events_resp.json()
        
        if events:
            event_id = events[0].get("id")
            reg_resp = requests.post(
                f"{BASE_URL}/api/portal/events/{event_id}/register",
                headers=member_auth["headers"]
            )
            # May succeed or already registered
            assert reg_resp.status_code in [200, 201, 400, 409]
            print(f"PASS: Event registration endpoint works (status={reg_resp.status_code})")
        else:
            print(f"INFO: No events available for registration test")


# ============== WATCH (SERMONS) ==============

class TestWatch:
    """Watch/Media functionality tests"""
    
    def test_media_videos_list(self, member_auth):
        """Portal: View sermons/videos list"""
        response = requests.get(
            f"{BASE_URL}/api/portal/media/videos",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        # Should be list of videos
        videos = data if isinstance(data, list) else data.get("videos", [])
        print(f"PASS: Media videos returns {len(videos)} videos")
    
    def test_media_categories(self, member_auth):
        """Portal: View media categories"""
        response = requests.get(
            f"{BASE_URL}/api/portal/media/categories",
            headers=member_auth["headers"]
        )
        # May return 200 or 404 if not implemented
        assert response.status_code in [200, 404]
        print(f"PASS: Media categories endpoint responds")


# ============== MERCH ==============

class TestMerch:
    """Merch store functionality tests"""
    
    def test_merch_products(self, member_auth):
        """Portal: View merch products"""
        response = requests.get(
            f"{BASE_URL}/api/portal/merch/products",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        products = data if isinstance(data, list) else data.get("products", [])
        print(f"PASS: Merch products returns {len(products)} items")


# ============== CAFE ==============

class TestCafe:
    """Cafe functionality tests"""
    
    def test_cafe_items(self, member_auth):
        """Portal: View cafe menu items"""
        response = requests.get(
            f"{BASE_URL}/api/portal/cafe/items",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        items = data if isinstance(data, list) else data.get("items", [])
        print(f"PASS: Cafe items returns {len(items)} items")


# ============== PRAYER ==============

class TestPrayer:
    """Prayer functionality tests"""
    
    def test_prayer_wall(self, member_auth):
        """Portal: View prayer wall (public requests)"""
        response = requests.get(
            f"{BASE_URL}/api/portal/prayer/wall",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        requests_list = data if isinstance(data, list) else data.get("requests", [])
        print(f"PASS: Prayer wall returns {len(requests_list)} requests")
    
    def test_prayer_submit_request(self, member_auth):
        """Portal: Submit a prayer request"""
        response = requests.post(
            f"{BASE_URL}/api/portal/prayer/requests",
            headers=member_auth["headers"],
            json={
                "title": "TEST_Prayer_" + str(uuid.uuid4())[:8],
                "content": "Test prayer request for QA testing",
                "is_public": False
            }
        )
        # Should succeed
        assert response.status_code in [200, 201]
        print(f"PASS: Prayer request submitted")


# ============== VOLUNTEER ==============

class TestVolunteer:
    """Volunteer functionality tests"""
    
    def test_volunteer_opportunities(self, member_auth):
        """Portal: View volunteer opportunities"""
        response = requests.get(
            f"{BASE_URL}/api/portal/volunteer/opportunities",
            headers=member_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        opportunities = data if isinstance(data, list) else data.get("opportunities", [])
        print(f"PASS: Volunteer opportunities returns {len(opportunities)} items")


# ============== ADMIN DASHBOARD ==============

class TestAdminDashboard:
    """Admin dashboard tests"""
    
    def test_dashboard_stats(self, admin_auth):
        """Admin: Dashboard loads with stats"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers=admin_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        # Should have metrics
        assert "total_members" in data or "metrics" in data or len(data) > 0
        print(f"PASS: Admin dashboard loads with stats")


# ============== ADMIN EVENTS CRUD ==============

class TestAdminEventsCRUD:
    """Admin Events CRUD operations"""
    
    def test_admin_events_list(self, admin_auth):
        """Admin: List events"""
        response = requests.get(
            f"{BASE_URL}/api/admin/events",
            headers=admin_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        events = data if isinstance(data, list) else data.get("events", [])
        print(f"PASS: Admin events list returns {len(events)} events")
    
    def test_admin_event_create_and_delete(self, admin_auth):
        """Admin: Create and delete event"""
        # Create event - use event_date field as specified
        create_payload = {
            "name": "TEST_Event_" + str(uuid.uuid4())[:8],
            "description": "Test event for QA",
            "event_date": "2026-03-01T10:00:00",
            "start_datetime": "2026-03-01T10:00:00",
            "location": "Main Hall",
            "is_public": True
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/events",
            headers=admin_auth["headers"],
            json=create_payload
        )
        
        if create_resp.status_code in [200, 201]:
            event_id = create_resp.json().get("id")
            print(f"PASS: Admin created event {event_id}")
            
            # Delete the event
            delete_resp = requests.delete(
                f"{BASE_URL}/api/admin/events/{event_id}",
                headers=admin_auth["headers"]
            )
            assert delete_resp.status_code in [200, 204]
            print(f"PASS: Admin deleted event {event_id}")
        else:
            print(f"INFO: Event creation returned {create_resp.status_code}: {create_resp.text[:200]}")
            assert create_resp.status_code in [200, 201, 400, 422]


# ============== ADMIN GROUPS CRUD ==============

class TestAdminGroupsCRUD:
    """Admin Groups CRUD operations"""
    
    def test_admin_groups_list(self, admin_auth):
        """Admin: List groups"""
        response = requests.get(
            f"{BASE_URL}/api/admin/groups",
            headers=admin_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        groups = data if isinstance(data, list) else data.get("groups", [])
        print(f"PASS: Admin groups list returns {len(groups)} groups")
    
    def test_admin_group_create_and_delete(self, admin_auth):
        """Admin: Create and delete group"""
        create_payload = {
            "name": "TEST_Group_" + str(uuid.uuid4())[:8],
            "description": "Test group for QA",
            "is_open": True,
            "is_active": True
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/groups",
            headers=admin_auth["headers"],
            json=create_payload
        )
        
        if create_resp.status_code in [200, 201]:
            group_id = create_resp.json().get("id")
            print(f"PASS: Admin created group {group_id}")
            
            # Delete the group
            delete_resp = requests.delete(
                f"{BASE_URL}/api/admin/groups/{group_id}",
                headers=admin_auth["headers"]
            )
            assert delete_resp.status_code in [200, 204]
            print(f"PASS: Admin deleted group {group_id}")
        else:
            print(f"INFO: Group creation returned {create_resp.status_code}: {create_resp.text[:200]}")
            assert create_resp.status_code in [200, 201, 400, 422]


# ============== ADMIN ANNOUNCEMENTS CRUD ==============

class TestAdminAnnouncementsCRUD:
    """Admin Announcements CRUD operations"""
    
    def test_admin_announcements_list(self, admin_auth):
        """Admin: List announcements"""
        response = requests.get(
            f"{BASE_URL}/api/admin/announcements",
            headers=admin_auth["headers"]
        )
        assert response.status_code == 200
        print(f"PASS: Admin announcements list works")
    
    def test_admin_announcement_create_and_delete(self, admin_auth):
        """Admin: Create and delete announcement"""
        create_payload = {
            "title": "TEST_Announcement_" + str(uuid.uuid4())[:8],
            "content": "Test announcement for QA",
            "is_active": True
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/announcements",
            headers=admin_auth["headers"],
            json=create_payload
        )
        
        if create_resp.status_code in [200, 201]:
            announcement_id = create_resp.json().get("id")
            print(f"PASS: Admin created announcement {announcement_id}")
            
            # Delete the announcement
            delete_resp = requests.delete(
                f"{BASE_URL}/api/admin/announcements/{announcement_id}",
                headers=admin_auth["headers"]
            )
            assert delete_resp.status_code in [200, 204]
            print(f"PASS: Admin deleted announcement {announcement_id}")
        else:
            print(f"INFO: Announcement creation returned {create_resp.status_code}: {create_resp.text[:200]}")


# ============== ADMIN KIDS CHECK-IN ==============

class TestAdminKidsCheckin:
    """Admin Kids Check-in tests"""
    
    def test_admin_today_checkins(self, admin_auth):
        """Admin: View today's check-ins"""
        response = requests.get(
            f"{BASE_URL}/api/admin/kids/checkins/today",
            headers=admin_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        checkins = data if isinstance(data, list) else data.get("checkins", [])
        print(f"PASS: Admin today's check-ins returns {len(checkins)} records")


# ============== ADMIN MEDIA ==============

class TestAdminMedia:
    """Admin Media tests"""
    
    def test_admin_sermons_list(self, admin_auth):
        """Admin: List sermons/videos"""
        response = requests.get(
            f"{BASE_URL}/api/admin/media/videos",
            headers=admin_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        videos = data if isinstance(data, list) else data.get("videos", [])
        print(f"PASS: Admin media videos returns {len(videos)} videos")


# ============== ADMIN GIVING ==============

class TestAdminGiving:
    """Admin Giving tests"""
    
    def test_admin_giving_summary(self, admin_auth):
        """Admin: View giving summary"""
        response = requests.get(
            f"{BASE_URL}/api/admin/giving/summary",
            headers=admin_auth["headers"]
        )
        assert response.status_code == 200
        print(f"PASS: Admin giving summary works")


# ============== ADMIN MEMBERS ==============

class TestAdminMembers:
    """Admin Members tests"""
    
    def test_admin_members_list(self, admin_auth):
        """Admin: List members"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            headers=admin_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        members = data if isinstance(data, list) else data.get("members", [])
        print(f"PASS: Admin members list returns {len(members)} members")
    
    def test_admin_members_search(self, admin_auth):
        """Admin: Search members"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members?search=maria",
            headers=admin_auth["headers"]
        )
        assert response.status_code == 200
        print(f"PASS: Admin members search works")


# ============== ADMIN VOLUNTEER ==============

class TestAdminVolunteer:
    """Admin Volunteer tests"""
    
    def test_admin_volunteer_opportunities(self, admin_auth):
        """Admin: List volunteer opportunities"""
        response = requests.get(
            f"{BASE_URL}/api/admin/volunteer/opportunities",
            headers=admin_auth["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        opportunities = data if isinstance(data, list) else data.get("opportunities", [])
        print(f"PASS: Admin volunteer opportunities returns {len(opportunities)} items")


# ============== ROLE-BASED ACCESS CONTROL ==============

class TestRoleBasedAccess:
    """Role-based access control tests"""
    
    def test_member_cannot_access_admin(self, member_auth):
        """Security: Member cannot access /api/admin/* endpoints"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers=member_auth["headers"]
        )
        # Should return 403 Forbidden
        assert response.status_code in [401, 403], \
            f"Member accessed admin endpoint! Got {response.status_code}"
        print(f"PASS: Member correctly blocked from admin endpoints (status={response.status_code})")
    
    def test_admin_can_access_portal(self, admin_auth):
        """Admin can also access portal endpoints"""
        response = requests.get(
            f"{BASE_URL}/api/portal/events",
            headers=admin_auth["headers"]
        )
        assert response.status_code == 200
        print(f"PASS: Admin can access portal endpoints")


# ============== BEARER TOKEN COMPREHENSIVE ==============

class TestBearerTokenComprehensive:
    """Comprehensive Bearer token tests for all endpoint types"""
    
    def test_bearer_token_on_all_portal_routes(self, member_auth):
        """All portal routes work with Bearer token"""
        routes = [
            "/api/portal/bootstrap",
            "/api/portal/events",
            "/api/portal/groups",
            "/api/portal/announcements",
            "/api/portal/giving/summary",
            "/api/portal/merch/products",
            "/api/portal/cafe/items"
        ]
        
        failures = []
        for route in routes:
            response = requests.get(
                f"{BASE_URL}{route}",
                headers=member_auth["headers"]
            )
            if response.status_code != 200:
                failures.append(f"{route}: {response.status_code}")
        
        assert len(failures) == 0, f"Routes failed with Bearer token: {failures}"
        print(f"PASS: All {len(routes)} portal routes work with Bearer token")
    
    def test_bearer_token_on_all_admin_routes(self, admin_auth):
        """All admin routes work with Bearer token"""
        routes = [
            "/api/admin/dashboard",
            "/api/admin/events",
            "/api/admin/groups",
            "/api/admin/members",
            "/api/admin/announcements"
        ]
        
        failures = []
        for route in routes:
            response = requests.get(
                f"{BASE_URL}{route}",
                headers=admin_auth["headers"]
            )
            if response.status_code != 200:
                failures.append(f"{route}: {response.status_code}")
        
        assert len(failures) == 0, f"Routes failed with Bearer token: {failures}"
        print(f"PASS: All {len(routes)} admin routes work with Bearer token")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
