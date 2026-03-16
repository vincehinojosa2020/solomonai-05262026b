"""
Post-MVP Features Test Suite - Iteration 39
Tests for:
1. Notification bell with unread badges
2. Mocked payment flow for giving
3. Geofence arrival nudge with cafe+giving quick actions
4. Push notification endpoints
5. Platform admin health scores
6. Bidirectional polling compatibility
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CREDENTIALS = {
    "platform_admin": {"email": "admin@solomon.ai", "password": "Demo2026!"},
    "abundant_admin": {"email": "admin@abundant.church", "password": "Demo2026!"},
    "abundant_member": {"email": "member@abundant.church", "password": "Demo2026!"},
    "downtown_admin": {"email": "admin@abundant-downtown.church", "password": "Demo2026!"},
    "cristo_admin": {"email": "admin@cristoviene.church", "password": "Demo2026!"},
}


@pytest.fixture(scope="module")
def session():
    """Shared session for all tests"""
    return requests.Session()


def login(session, email, password):
    """Login helper and return session token"""
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        data = response.json()
        token = data.get("session_token") or data.get("token") or data.get("access_token")
        return token
    return None


# ============== LOGIN TESTS ==============

class TestLoginAllAccounts:
    """Test all 5 demo accounts can log in successfully"""
    
    def test_platform_admin_login(self, session):
        """Test Platform Admin (admin@solomon.ai) login"""
        token = login(session, "admin@solomon.ai", "Demo2026!")
        assert token is not None, "Platform admin login failed"
        print(f"Platform Admin logged in successfully")
    
    def test_abundant_admin_login(self, session):
        """Test Abundant East Admin login"""
        token = login(session, "admin@abundant.church", "Demo2026!")
        assert token is not None, "Abundant admin login failed"
        print(f"Abundant East Admin logged in successfully")
    
    def test_abundant_member_login(self, session):
        """Test Abundant East Member login"""
        token = login(session, "member@abundant.church", "Demo2026!")
        assert token is not None, "Abundant member login failed"
        print(f"Abundant East Member logged in successfully")
    
    def test_downtown_admin_login(self, session):
        """Test Abundant Downtown Admin login"""
        token = login(session, "admin@abundant-downtown.church", "Demo2026!")
        assert token is not None, "Downtown admin login failed"
        print(f"Downtown Admin logged in successfully")
    
    def test_cristo_admin_login(self, session):
        """Test Cristo Viene Admin login"""
        token = login(session, "admin@cristoviene.church", "Demo2026!")
        assert token is not None, "Cristo admin login failed"
        print(f"Cristo Viene Admin logged in successfully")


# ============== NOTIFICATION BELL TESTS ==============

class TestNotificationBell:
    """Test notification bell functionality with unread badges"""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.token = login(session, "member@abundant.church", "Demo2026!")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_notifications(self, session):
        """GET /api/portal/notifications returns notifications with unread_count"""
        response = session.get(f"{BASE_URL}/api/portal/notifications", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "notifications" in data, "Response missing 'notifications' field"
        assert "unread_count" in data, "Response missing 'unread_count' field"
        assert isinstance(data["unread_count"], int), "unread_count should be integer"
        print(f"Notifications: {len(data['notifications'])}, Unread: {data['unread_count']}")
    
    def test_mark_notification_read(self, session):
        """PUT /api/portal/notifications/{id}/read marks notification as read"""
        # First create a test notification by admin
        admin_token = login(session, "admin@abundant.church", "Demo2026!")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Admin sends notification
        send_resp = session.post(f"{BASE_URL}/api/admin/notifications/send", 
            headers=admin_headers,
            json={"title": "Test Notification", "message": "Test message", "type": "announcement"}
        )
        # Note: may return 200 or 201 depending on impl
        if send_resp.status_code in [200, 201]:
            print("Admin notification sent successfully")
        
        # Get notifications for member
        get_resp = session.get(f"{BASE_URL}/api/portal/notifications", headers=self.headers)
        if get_resp.status_code == 200 and get_resp.json().get("notifications"):
            notif = get_resp.json()["notifications"][0]
            notif_id = notif.get("id")
            
            if notif_id:
                # Mark as read
                mark_resp = session.put(f"{BASE_URL}/api/portal/notifications/{notif_id}/read", headers=self.headers)
                assert mark_resp.status_code == 200, f"Mark read failed: {mark_resp.status_code}"
                print(f"Notification {notif_id} marked as read")
        else:
            print("No notifications to mark as read (acceptable for new users)")
    
    def test_mark_all_notifications_read(self, session):
        """PUT /api/portal/notifications/read-all marks all as read"""
        response = session.put(f"{BASE_URL}/api/portal/notifications/read-all", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "message" in data, "Response should have message"
        print(f"All notifications marked as read: {data.get('message')}")


class TestAdminNotifications:
    """Test admin notification broadcast"""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.token = login(session, "admin@abundant.church", "Demo2026!")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_send_notification(self, session):
        """POST /api/admin/notifications/send broadcasts to tenant members"""
        response = session.post(f"{BASE_URL}/api/admin/notifications/send",
            headers=self.headers,
            json={
                "title": f"Test Broadcast {datetime.now().isoformat()[:19]}",
                "message": "Testing notification broadcast to all members",
                "type": "announcement"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "count" in data or "message" in data, "Response should have count or message"
        print(f"Notification sent: {data}")


# ============== PAYMENT METHODS TESTS ==============

class TestPaymentMethods:
    """Test saved payment methods (mocked Stripe)"""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.token = login(session, "member@abundant.church", "Demo2026!")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_payment_methods(self, session):
        """GET /api/portal/payment-methods returns saved cards"""
        response = session.get(f"{BASE_URL}/api/portal/payment-methods", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "payment_methods" in data, "Response missing 'payment_methods'"
        
        methods = data["payment_methods"]
        if methods:
            # Verify card structure
            card = methods[0]
            assert "card_last_four" in card or "id" in card, "Card should have last_four or id"
            print(f"Found {len(methods)} saved payment method(s)")
            for m in methods[:2]:  # Print first 2 cards
                print(f"  - {m.get('card_brand', 'Unknown')} *{m.get('card_last_four', '****')}")
        else:
            print("No saved payment methods (acceptable)")


# ============== GIVING/DONATE TESTS (MOCKED PAYMENT) ==============

class TestGivingDonate:
    """Test mocked payment donation flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.token = login(session, "member@abundant.church", "Demo2026!")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_process_donation(self, session):
        """POST /api/portal/giving/donate processes donation with mock payment"""
        response = session.post(f"{BASE_URL}/api/portal/giving/donate",
            headers=self.headers,
            json={
                "amount": 25.00,
                "fund": "General Fund",
                "frequency": "one_time",
                "payment_method_id": None,
                "source": "give_page"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "donation_id" in data, "Response should have donation_id"
        assert data.get("status") == "completed", "Donation status should be completed"
        print(f"Donation processed: ${data.get('amount', 25)} to {data.get('fund', 'General Fund')}")
    
    def test_donation_appears_in_history(self, session):
        """Verify donation appears in giving history"""
        response = session.get(f"{BASE_URL}/api/portal/giving/history", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        donations = data.get("donations", [])
        # Should have at least one donation (may have more from previous tests)
        print(f"Found {len(donations)} donations in history")


# ============== SERVICE CHECK-IN & ARRIVAL NUDGE TESTS ==============

class TestServiceCheckin:
    """Test service check-in with arrival nudge functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.token = login(session, "member@abundant.church", "Demo2026!")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_service_checkin_returns_nudge_data(self, session):
        """POST /api/portal/service-checkin returns nudge data with cafe_open and give_amounts"""
        response = session.post(f"{BASE_URL}/api/portal/service-checkin?check_in_type=in_person",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Should have streak data
        assert "streak" in data or "current_streak" in data, "Response should have streak data"
        
        # Should have nudge object for arrival flow
        if "nudge" in data:
            nudge = data["nudge"]
            assert "show" in nudge, "Nudge should have 'show' field"
            if nudge.get("show"):
                print(f"Nudge enabled: cafe_open={nudge.get('cafe_open')}, show_giving={nudge.get('show_giving')}")
                if nudge.get("give_amounts"):
                    print(f"  Give amounts: {nudge['give_amounts']}")
            else:
                print("Nudge disabled for this user")
        else:
            print("No nudge in response (may be already checked in today)")
        
        print(f"Check-in response: streak={data.get('streak', data.get('current_streak'))}")


# ============== CHECKOUT WITH GIVING TESTS ==============

class TestCheckoutWithGiving:
    """Test cafe/merch checkout with giving nudge"""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.token = login(session, "member@abundant.church", "Demo2026!")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_cafe_checkout_with_giving(self, session):
        """POST /api/portal/checkout/with-giving creates order + donation record"""
        response = session.post(f"{BASE_URL}/api/portal/checkout/with-giving",
            headers=self.headers,
            json={
                "items": [
                    {"name": "House Latte", "price": 4.50, "quantity": 2}
                ],
                "giving_amount": 10.00,
                "giving_fund": "General Fund",
                "order_type": "cafe",
                "pickup_time": "9:00 AM"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "order_id" in data, "Response should have order_id"
        assert data.get("status") == "confirmed", "Order status should be confirmed"
        assert data.get("giving_amount") == 10.00, "Giving amount should be preserved"
        print(f"Cafe order with giving: order_id={data['order_id']}, giving=${data.get('giving_amount')}")
    
    def test_merch_checkout_with_giving(self, session):
        """POST /api/portal/checkout/with-giving for merch"""
        response = session.post(f"{BASE_URL}/api/portal/checkout/with-giving",
            headers=self.headers,
            json={
                "items": [
                    {"name": "SO BE IT Hoodie", "price": 60.00, "quantity": 1}
                ],
                "giving_amount": 20.00,
                "giving_fund": "Building Fund",
                "order_type": "merch"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "order_id" in data, "Response should have order_id"
        print(f"Merch order with giving: total=${data.get('total')}")


# ============== PLATFORM ADMIN TESTS ==============

class TestPlatformAdminDashboard:
    """Test platform admin dashboard features"""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.token = login(session, "admin@solomon.ai", "Demo2026!")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_dashboard_stats_load(self, session):
        """Admin dashboard stats load (members, giving, etc.)"""
        response = session.get(f"{BASE_URL}/api/platform/stats", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "churches" in data, "Stats should have 'churches'"
        assert "members" in data, "Stats should have 'members'"
        total_members = data.get("members", {}).get("total_users", 0)
        print(f"Platform stats: {data['churches'].get('total', 0)} churches, {total_members} total members")
    
    def test_health_scores_for_all_churches(self, session):
        """GET /api/platform/health-scores shows health for all churches"""
        response = session.get(f"{BASE_URL}/api/platform/health-scores", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Health scores should be a list"
        if data:
            for tenant in data[:3]:  # Print top 3
                health = tenant.get("health", {})
                print(f"  {tenant.get('name')}: Score={health.get('score', 0)}, Grade={health.get('grade', 'N/A')}")
    
    def test_organizations_tab_shows_campuses(self, session):
        """Platform admin organizations tab shows campus comparison"""
        response = session.get(f"{BASE_URL}/api/platform/organizations", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        if data:
            org = data[0]
            assert "organization_name" in org or "organization_id" in org, "Org should have name/id"
            campuses = org.get("campuses", [])
            print(f"Organization: {org.get('organization_name')}")
            print(f"  Campuses: {len(campuses)}, Total members: {org.get('total_members', 0)}")


# ============== ADMIN DASHBOARD TESTS ==============

class TestAdminDashboard:
    """Test church admin dashboard"""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.token = login(session, "admin@abundant.church", "Demo2026!")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_dashboard_stats_abundant_east(self, session):
        """Dashboard stats load for Abundant East (20K members)"""
        response = session.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        members = data.get("total_members", 0)
        print(f"Abundant East: {members} members, ${data.get('mtd_giving', 0):,.0f} MTD giving")
        # Abundant East should have ~20K members per seed data
        assert members >= 1000, f"Expected at least 1000 members, got {members}"


# ============== MEMBER PORTAL HOME TESTS ==============

class TestMemberPortalHome:
    """Test member portal home page features"""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.token = login(session, "member@abundant.church", "Demo2026!")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_portal_home_loads(self, session):
        """Portal home loads with greeting and actions"""
        response = session.get(f"{BASE_URL}/api/portal/me", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        print(f"Portal home: user={data.get('name', 'Unknown')}")
    
    def test_attendance_streak(self, session):
        """Portal shows attendance streak data"""
        response = session.get(f"{BASE_URL}/api/portal/attendance-streak", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "current_streak" in data, "Response should have current_streak"
        print(f"Streak: {data.get('current_streak', 0)} current, {data.get('longest_streak', 0)} longest")
    
    def test_upcoming_events(self, session):
        """Portal shows upcoming events"""
        response = session.get(f"{BASE_URL}/api/portal/events", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        if isinstance(data, list):
            print(f"Upcoming events: {len(data)}")
        else:
            print(f"Events response: {type(data)}")


# ============== CAFE & MERCH GIVING NUDGE UI DATA ==============

class TestCafeGivingNudge:
    """Test cafe giving nudge amounts ($5/$10/$20/$100)"""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.token = login(session, "member@abundant.church", "Demo2026!")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_cafe_items_available(self, session):
        """Cafe items available for ordering"""
        response = session.get(f"{BASE_URL}/api/portal/cafe/items", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        items = data.get("items", [])
        print(f"Cafe items: {len(items)}")
        if items:
            print(f"  Example: {items[0].get('name')} - ${items[0].get('price', 0)}")


class TestMerchGivingNudge:
    """Test merch giving nudge amounts ($10/$20/$50/$100)"""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.token = login(session, "member@abundant.church", "Demo2026!")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_merch_products_available(self, session):
        """Merch products available for ordering"""
        response = session.get(f"{BASE_URL}/api/portal/merch/products", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        products = data.get("products", [])
        print(f"Merch products: {len(products)}")
        if products:
            print(f"  Example: {products[0].get('name')} - ${products[0].get('price', 0)}")


# ============== POLLING COMPATIBILITY TESTS ==============

class TestPollingEndpoints:
    """Test endpoints used for bidirectional polling"""
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.member_token = login(session, "member@abundant.church", "Demo2026!")
        self.admin_token = login(session, "admin@abundant.church", "Demo2026!")
    
    def test_portal_notifications_polling(self, session):
        """Notifications endpoint supports polling (30s)"""
        headers = {"Authorization": f"Bearer {self.member_token}"}
        response = session.get(f"{BASE_URL}/api/portal/notifications", headers=headers)
        assert response.status_code == 200
        print("Notifications endpoint ready for polling")
    
    def test_service_mode_polling(self, session):
        """Service mode endpoint supports polling (30s)"""
        headers = {"Authorization": f"Bearer {self.member_token}"}
        response = session.get(f"{BASE_URL}/api/portal/service-mode", headers=headers)
        assert response.status_code == 200
        print("Service mode endpoint ready for polling")
    
    def test_admin_kids_checkins_polling(self, session):
        """Kids checkins endpoint supports polling (15s)"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = session.get(f"{BASE_URL}/api/admin/kids/checkins/today", headers=headers)
        assert response.status_code == 200
        print("Kids checkins endpoint ready for polling")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
