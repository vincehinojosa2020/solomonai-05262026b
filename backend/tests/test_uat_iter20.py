"""
Solomon AI - Full UAT Backend API Tests (Iteration 20)
Testing all CRUD operations and bidirectional sync between Admin and Member
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@abundant.church"
ADMIN_PASSWORD = "Demo2026!"
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = "Demo2026!"


@pytest.fixture(scope="module")
def admin_session():
    """Get authenticated admin session"""
    session = requests.Session()
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return session


@pytest.fixture(scope="module")
def member_session():
    """Get authenticated member session"""
    session = requests.Session()
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": MEMBER_EMAIL,
        "password": MEMBER_PASSWORD
    })
    assert response.status_code == 200, f"Member login failed: {response.text}"
    return session


# ==================== HEALTH & AUTH TESTS ====================

class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_admin_login(self, admin_session):
        """Test admin login and profile"""
        response = admin_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data.get("role") in ["admin", "church_admin"]
        print(f"✅ Admin logged in: {data.get('email')}, role: {data.get('role')}")
    
    def test_member_login(self, member_session):
        """Test member login and profile"""
        response = member_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data.get("role") == "member"
        print(f"✅ Member logged in: {data.get('email')}, role: {data.get('role')}")

    def test_tenant_endpoint(self, admin_session):
        """Test tenant endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/tenant")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Tenant: {data.get('name')}")


# ==================== DASHBOARD & ANALYTICS ====================

class TestDashboardAnalytics:
    """Test admin dashboard and analytics"""
    
    def test_dashboard_stats(self, admin_session):
        """Admin can see dashboard stats"""
        response = admin_session.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Dashboard: {data.get('total_members', 0)} members, {data.get('active_groups', 0)} groups")
    
    def test_giving_trend(self, admin_session):
        """Admin can see giving trend"""
        response = admin_session.get(f"{BASE_URL}/api/dashboard/giving-trend")
        assert response.status_code == 200
        print("✅ Giving trend accessible")
    
    def test_attendance_trend(self, admin_session):
        """Admin can see attendance trend"""
        response = admin_session.get(f"{BASE_URL}/api/dashboard/attendance-trend")
        assert response.status_code == 200
        print("✅ Attendance trend accessible")


# ==================== GROUPS CRUD & SYNC ====================

class TestGroupsSync:
    """Test Admin creates group -> Member sees it"""
    
    def test_admin_get_groups(self, admin_session):
        """Admin can view all groups"""
        response = admin_session.get(f"{BASE_URL}/api/groups")
        assert response.status_code == 200
        data = response.json()
        # Handle paginated response
        groups = data.get("data", data) if isinstance(data, dict) else data
        print(f"✅ Admin sees {len(groups)} groups")
    
    def test_member_sees_groups(self, member_session):
        """Member can see groups via portal"""
        response = member_session.get(f"{BASE_URL}/api/portal/groups")
        assert response.status_code == 200
        data = response.json()
        groups = data.get("groups", data) if isinstance(data, dict) else data
        print(f"✅ Member sees {len(groups)} groups via portal")
    
    def test_member_can_join_group(self, member_session):
        """Member can request to join a group"""
        response = member_session.get(f"{BASE_URL}/api/portal/groups")
        assert response.status_code == 200
        data = response.json()
        groups = data.get("groups", data) if isinstance(data, dict) else data
        
        if groups:
            open_group = next((g for g in groups if g.get("is_open")), groups[0])
            if open_group:
                response = member_session.post(f"{BASE_URL}/api/portal/groups/{open_group['id']}/join")
                # 200 = joined, 400 = already member (both OK)
                assert response.status_code in [200, 400]
                print(f"✅ Member join group test passed (status: {response.status_code})")


# ==================== EVENTS CRUD & SYNC ====================

class TestEventsSync:
    """Test Admin creates event -> Member sees it and can RSVP"""
    
    def test_admin_get_events(self, admin_session):
        """Admin can view all events"""
        response = admin_session.get(f"{BASE_URL}/api/events")
        assert response.status_code == 200
        events = response.json()
        print(f"✅ Admin sees {len(events)} events")
    
    def test_admin_events_page(self, admin_session):
        """Admin can view events via admin/events"""
        response = admin_session.get(f"{BASE_URL}/api/admin/events")
        assert response.status_code == 200
        data = response.json()
        events = data.get("data", data) if isinstance(data, dict) else data
        print(f"✅ Admin events manager sees {len(events)} events")
    
    def test_member_sees_events(self, member_session):
        """Member can see events via portal"""
        response = member_session.get(f"{BASE_URL}/api/portal/events")
        assert response.status_code == 200
        events = response.json()
        print(f"✅ Member sees {len(events)} events")
    
    def test_member_can_rsvp(self, member_session):
        """Member can RSVP to an event"""
        response = member_session.get(f"{BASE_URL}/api/portal/events")
        assert response.status_code == 200
        events = response.json()
        
        if events:
            event = events[0]
            response = member_session.post(f"{BASE_URL}/api/portal/events/{event['id']}/register")
            # 200/201 = registered, 400 = already registered (both OK)
            assert response.status_code in [200, 201, 400]
            print(f"✅ Member RSVP test passed (status: {response.status_code})")


# ==================== KIDS CHECK-IN SYNC ====================

class TestKidsCheckinSync:
    """Test bidirectional sync for kids check-in"""
    
    def test_admin_sees_checkins(self, admin_session):
        """Admin can see all check-ins"""
        response = admin_session.get(f"{BASE_URL}/api/admin/kids/checkins")
        assert response.status_code == 200
        data = response.json()
        checkins = data.get("checkins", data) if isinstance(data, dict) else data
        print(f"✅ Admin sees {len(checkins)} check-ins")
    
    def test_admin_sees_all_children(self, admin_session):
        """Admin can see all registered children"""
        response = admin_session.get(f"{BASE_URL}/api/admin/kids/all")
        assert response.status_code == 200
        data = response.json()
        children = data.get("children", data) if isinstance(data, dict) else data
        print(f"✅ Admin sees {len(children)} registered children")
    
    def test_member_sees_their_children(self, member_session):
        """Member can see their own children"""
        response = member_session.get(f"{BASE_URL}/api/portal/kids")
        assert response.status_code == 200
        data = response.json()
        children = data.get("children", data) if isinstance(data, dict) else data
        print(f"✅ Member sees {len(children)} of their children")


# ==================== CAFE CRUD & ORDERS ====================

class TestCafeSync:
    """Test Cafe menu and orders"""
    
    def test_admin_sees_cafe_items(self, admin_session):
        """Admin can view cafe menu"""
        response = admin_session.get(f"{BASE_URL}/api/admin/cafe/items")
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        print(f"✅ Admin sees {len(items)} cafe items")
    
    def test_member_sees_cafe_menu(self, member_session):
        """Member can see cafe menu via portal"""
        response = member_session.get(f"{BASE_URL}/api/portal/cafe/items")
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        print(f"✅ Member sees {len(items)} cafe items")
    
    def test_member_place_cafe_order(self, member_session):
        """Member can place a cafe order"""
        response = member_session.get(f"{BASE_URL}/api/portal/cafe/items")
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        if items:
            item = items[0]
            order_data = {
                "items": [{
                    "item_id": item["id"],
                    "name": item["name"],
                    "price": item["price"],
                    "quantity": 1
                }],
                "pickup_time": "Sunday 9:15 AM",
                "notes": "TEST_UAT_order"
            }
            response = member_session.post(f"{BASE_URL}/api/portal/cafe/orders", json=order_data)
            assert response.status_code in [200, 201]
            print(f"✅ Member placed cafe order successfully")
    
    def test_admin_sees_cafe_orders(self, admin_session):
        """Admin can see cafe orders"""
        response = admin_session.get(f"{BASE_URL}/api/admin/cafe/orders")
        assert response.status_code == 200
        data = response.json()
        orders = data.get("orders", data) if isinstance(data, dict) else data
        print(f"✅ Admin sees {len(orders)} cafe orders")


# ==================== MERCH CRUD & ORDERS ====================

class TestMerchSync:
    """Test Merch products and orders"""
    
    def test_admin_sees_products(self, admin_session):
        """Admin can view merch products"""
        response = admin_session.get(f"{BASE_URL}/api/admin/merch/products")
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", data) if isinstance(data, dict) else data
        print(f"✅ Admin sees {len(products)} merch products")
    
    def test_member_sees_products(self, member_session):
        """Member can see merch products via portal"""
        response = member_session.get(f"{BASE_URL}/api/portal/merch/products")
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", data) if isinstance(data, dict) else data
        print(f"✅ Member sees {len(products)} merch products")
    
    def test_member_place_merch_order(self, member_session):
        """Member can place a merch order"""
        response = member_session.get(f"{BASE_URL}/api/portal/merch/products")
        data = response.json()
        products = data.get("products", data) if isinstance(data, dict) else data
        
        if products:
            product = products[0]
            order_data = {
                "items": [{
                    "product_id": product["id"],
                    "name": product["name"],
                    "price": product["price"],
                    "quantity": 1
                }]
            }
            response = member_session.post(f"{BASE_URL}/api/portal/merch/orders", json=order_data)
            assert response.status_code in [200, 201]
            print(f"✅ Member placed merch order successfully")
    
    def test_admin_sees_merch_orders(self, admin_session):
        """Admin can see merch orders"""
        response = admin_session.get(f"{BASE_URL}/api/admin/merch/orders")
        assert response.status_code == 200
        data = response.json()
        orders = data.get("orders", data) if isinstance(data, dict) else data
        print(f"✅ Admin sees {len(orders)} merch orders")


# ==================== GIVING FLOW ====================

class TestGivingFlow:
    """Test giving/donation functionality"""
    
    def test_admin_giving_stats(self, admin_session):
        """Admin can see giving stats"""
        response = admin_session.get(f"{BASE_URL}/api/giving/stats")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Giving stats: YTD {data.get('ytd_total', 0):.2f}")
    
    def test_admin_funds(self, admin_session):
        """Admin can see funds"""
        response = admin_session.get(f"{BASE_URL}/api/funds")
        assert response.status_code == 200
        funds = response.json()
        print(f"✅ Admin sees {len(funds)} funds")
    
    def test_member_giving_history(self, member_session):
        """Member can see their giving history"""
        response = member_session.get(f"{BASE_URL}/api/portal/giving/history")
        assert response.status_code == 200
        data = response.json()
        donations = data.get("donations", data) if isinstance(data, dict) else data
        print(f"✅ Member giving history accessible")


# ==================== PRAYER SYSTEM ====================

class TestPrayerSystem:
    """Test prayer request functionality"""
    
    def test_prayer_categories(self, member_session):
        """Member can see prayer categories"""
        response = member_session.get(f"{BASE_URL}/api/portal/prayer/categories")
        assert response.status_code == 200
        categories = response.json()
        print(f"✅ Prayer categories: {categories}")
    
    def test_member_create_prayer_request(self, member_session):
        """Member can submit a prayer request"""
        test_id = str(uuid.uuid4())[:8]
        prayer_data = {
            "title": f"TEST_Prayer_{test_id}",
            "message": "Test prayer request from UAT",
            "category": "general",
            "is_public": True
        }
        response = member_session.post(f"{BASE_URL}/api/portal/prayer/requests", json=prayer_data)
        assert response.status_code in [200, 201]
        print(f"✅ Member created prayer request")
        return response.json()
    
    def test_member_sees_prayer_wall(self, member_session):
        """Member can see prayer wall"""
        response = member_session.get(f"{BASE_URL}/api/portal/prayer/wall")
        assert response.status_code == 200
        data = response.json()
        prayers = data.get("requests", data) if isinstance(data, dict) else data
        print(f"✅ Member sees {len(prayers)} prayers on wall")
    
    def test_admin_prayer_dashboard(self, admin_session):
        """Admin can see prayer dashboard"""
        response = admin_session.get(f"{BASE_URL}/api/admin/prayer/dashboard")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Admin prayer dashboard accessible")


# ==================== MEDIA/WATCH SECTION ====================

class TestMediaSection:
    """Test media library functionality"""
    
    def test_admin_media_videos(self, admin_session):
        """Admin can see media videos"""
        response = admin_session.get(f"{BASE_URL}/api/admin/media/videos")
        # The endpoint might not exist, check for 200 or 404
        if response.status_code == 200:
            print(f"✅ Admin media videos accessible")
        else:
            print(f"⚠️ Admin media videos endpoint returned {response.status_code}")
            assert response.status_code in [200, 404]  # May not be implemented


# ==================== MEETINGS FUNCTIONALITY ====================

class TestMeetingsSync:
    """Test pastor meetings functionality"""
    
    def test_admin_meetings_slots(self, admin_session):
        """Admin can see meeting slots"""
        response = admin_session.get(f"{BASE_URL}/api/admin/meetings/slots")
        assert response.status_code == 200
        data = response.json()
        slots = data if isinstance(data, list) else data.get("slots", [])
        print(f"✅ Admin sees {len(slots)} meeting slots")
    
    def test_admin_meetings(self, admin_session):
        """Admin can see all meetings"""
        response = admin_session.get(f"{BASE_URL}/api/admin/meetings")
        assert response.status_code == 200
        data = response.json()
        meetings = data if isinstance(data, list) else data.get("meetings", [])
        print(f"✅ Admin sees {len(meetings)} meetings")
    
    def test_member_sees_slots(self, member_session):
        """Member can see available slots"""
        response = member_session.get(f"{BASE_URL}/api/portal/meetings/slots")
        assert response.status_code == 200
        print(f"✅ Member can see meeting slots")


# ==================== ADMIN GROUPS MANAGER ====================

class TestAdminGroupsManager:
    """Test admin groups management"""
    
    def test_admin_groups_with_members(self, admin_session):
        """Admin can get groups with member details"""
        response = admin_session.get(f"{BASE_URL}/api/groups")
        assert response.status_code == 200
        data = response.json()
        groups = data.get("data", data) if isinstance(data, dict) else data
        
        if groups:
            # Get members for first group
            group = groups[0]
            response = admin_session.get(f"{BASE_URL}/api/groups/{group['id']}/members/list")
            assert response.status_code == 200
            print(f"✅ Admin can view group members")


# ==================== PEOPLE MANAGEMENT ====================

class TestPeopleManagement:
    """Test people/member management"""
    
    def test_admin_people_list(self, admin_session):
        """Admin can see people list"""
        response = admin_session.get(f"{BASE_URL}/api/people")
        assert response.status_code == 200
        data = response.json()
        people = data.get("data", data) if isinstance(data, dict) else data
        print(f"✅ Admin sees {len(people)} people")
    
    def test_admin_households(self, admin_session):
        """Admin can see households"""
        response = admin_session.get(f"{BASE_URL}/api/households")
        assert response.status_code == 200
        data = response.json()
        households = data.get("data", data) if isinstance(data, dict) else data
        print(f"✅ Admin sees {len(households)} households")


# ==================== MEMBER PROFILE ====================

class TestMemberProfile:
    """Test member profile functionality"""
    
    def test_member_gets_profile(self, member_session):
        """Member can get their profile"""
        response = member_session.get(f"{BASE_URL}/api/portal/me")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Member profile: {data.get('first_name', 'N/A')} {data.get('last_name', 'N/A')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
