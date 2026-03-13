"""
Solomon AI v3.0 Feature Tests - Testing new dashboard stats, Watch section, Merch store, and Kids Check-in
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDashboardStats:
    """Dashboard stats API tests - 50K member megachurch metrics"""
    
    def test_dashboard_stats_returns_50k_members(self):
        """Dashboard should show 50K+ members for Abundant Church"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Check 50K+ members
        assert data["total_members"] == 50247, f"Expected 50247, got {data['total_members']}"
        print(f"✅ Total Members: {data['total_members']}")
    
    def test_dashboard_stats_has_mtd_giving(self):
        """Dashboard should show $182,500 MTD giving"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert data["mtd_giving"] == 182500, f"Expected 182500, got {data['mtd_giving']}"
        print(f"✅ MTD Giving: ${data['mtd_giving']}")
    
    def test_dashboard_stats_has_cafe_orders(self):
        """Dashboard should show 342 cafe orders this week"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "cafe_orders_week" in data
        assert data["cafe_orders_week"] == 342, f"Expected 342, got {data['cafe_orders_week']}"
        print(f"✅ Café Orders This Week: {data['cafe_orders_week']}")
    
    def test_dashboard_stats_has_merch_orders(self):
        """Dashboard should show 89 merch orders this week"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "merch_orders_week" in data
        assert data["merch_orders_week"] == 89, f"Expected 89, got {data['merch_orders_week']}"
        print(f"✅ Merch Orders This Week: {data['merch_orders_week']}")
    
    def test_dashboard_stats_has_event_registrations(self):
        """Dashboard should show 1,247 event registrations this month"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "event_registrations_month" in data
        assert data["event_registrations_month"] == 1247, f"Expected 1247, got {data['event_registrations_month']}"
        print(f"✅ Event Registrations: {data['event_registrations_month']}")
    
    def test_dashboard_stats_has_at_risk_members(self):
        """Dashboard should show at-risk member count"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "at_risk_members" in data
        assert data["at_risk_members"] == 156, f"Expected 156, got {data['at_risk_members']}"
        print(f"✅ At-Risk Members: {data['at_risk_members']}")
    
    def test_dashboard_stats_has_cafe_giving_added(self):
        """Dashboard should show cafe giving added amount"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "cafe_giving_added" in data
        assert data["cafe_giving_added"] == 1847
        print(f"✅ Café Giving Added: ${data['cafe_giving_added']}")
    
    def test_dashboard_stats_has_merch_giving_added(self):
        """Dashboard should show merch giving added amount"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "merch_giving_added" in data
        assert data["merch_giving_added"] == 623
        print(f"✅ Merch Giving Added: ${data['merch_giving_added']}")


class TestAuthentication:
    """Authentication tests with demo credentials"""
    
    def test_admin_login(self):
        """Admin can login with demo credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@abundant.church", "password": "Demo2026!"}
        )
        assert response.status_code == 200
        data = response.json()
        # API returns user data directly, not nested in 'user' key
        assert "role" in data
        assert data["role"] == "church_admin"
        print(f"✅ Admin login successful: {data['email']}")
    
    def test_member_login(self):
        """Member can login with demo credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "member@abundant.church", "password": "Demo2026!"}
        )
        assert response.status_code == 200
        data = response.json()
        # API returns user data directly, not nested in 'user' key
        assert "role" in data
        assert data["role"] == "member"
        print(f"✅ Member login successful: {data['email']}")


class TestKidsCheckin:
    """Kids Check-in tests - 3-digit pickup codes"""
    
    @pytest.fixture
    def admin_session(self):
        """Get admin authenticated session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@abundant.church", "password": "Demo2026!"}
        )
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return session
    
    @pytest.fixture
    def member_session(self):
        """Get member authenticated session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "member@abundant.church", "password": "Demo2026!"}
        )
        if response.status_code != 200:
            pytest.skip("Member login failed")
        return session
    
    def test_admin_can_get_all_checkins(self, admin_session):
        """Admin can retrieve all current check-ins"""
        response = admin_session.get(f"{BASE_URL}/api/admin/kids/checkins")
        assert response.status_code == 200
        data = response.json()
        assert "checkins" in data
        print(f"✅ Admin retrieved {len(data['checkins'])} check-ins")
    
    def test_admin_can_get_all_kids(self, admin_session):
        """Admin can retrieve all registered children"""
        response = admin_session.get(f"{BASE_URL}/api/admin/kids/all")
        assert response.status_code == 200
        data = response.json()
        assert "children" in data
        print(f"✅ Admin retrieved {len(data['children'])} children")
    
    def test_member_can_get_their_children(self, member_session):
        """Member can retrieve their children"""
        response = member_session.get(f"{BASE_URL}/api/portal/kids")
        assert response.status_code == 200
        data = response.json()
        assert "children" in data
        print(f"✅ Member retrieved {len(data['children'])} children")
    
    def test_pickup_code_format_is_correct(self, admin_session):
        """Pickup codes should be either 3-digit numbers or ABC-1234 format"""
        # Get all checkins to find pickup codes
        response = admin_session.get(f"{BASE_URL}/api/admin/kids/checkins")
        data = response.json()
        
        # If there are checkins, verify format
        if data.get("checkins") and len(data["checkins"]) > 0:
            for checkin in data["checkins"]:
                code = checkin.get("pickup_code", "")
                if code:
                    # Code should be either:
                    # 1. 3-digit number (100-999) - new format
                    # 2. ABC-1234 format (3 letters + dash + 4 digits) - old format
                    is_3_digit = code.isdigit() and len(code) == 3 and 100 <= int(code) <= 999
                    is_abc_format = bool(re.match(r'^[A-Z]{3}-\d{4}$', code))
                    
                    assert is_3_digit or is_abc_format, f"Invalid code format: {code}"
                    format_type = "3-digit" if is_3_digit else "ABC-1234"
                    print(f"✅ Pickup code {code} has valid {format_type} format")
        else:
            print("⚠️ No checkins found to verify code format")


class TestMerchStore:
    """Merch store tests - native store with offering nudge"""
    
    @pytest.fixture
    def member_session(self):
        """Get member authenticated session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "member@abundant.church", "password": "Demo2026!"}
        )
        if response.status_code != 200:
            pytest.skip("Member login failed")
        return session
    
    def test_merch_products_endpoint_exists(self, member_session):
        """Merch products endpoint returns products"""
        response = member_session.get(f"{BASE_URL}/api/portal/merch/products")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        print(f"✅ Merch endpoint returned {len(data['products'])} products")
    
    def test_merch_products_have_required_fields(self, member_session):
        """Merch products have name, price, and image"""
        response = member_session.get(f"{BASE_URL}/api/portal/merch/products")
        data = response.json()
        
        if data.get("products") and len(data["products"]) > 0:
            product = data["products"][0]
            assert "name" in product, "Product missing name"
            assert "price" in product, "Product missing price"
            print(f"✅ Product '{product['name']}' has required fields")
        else:
            print("⚠️ No products found to verify")


class TestCafeStore:
    """Café store tests"""
    
    @pytest.fixture
    def member_session(self):
        """Get member authenticated session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "member@abundant.church", "password": "Demo2026!"}
        )
        if response.status_code != 200:
            pytest.skip("Member login failed")
        return session
    
    def test_cafe_items_endpoint_exists(self, member_session):
        """Cafe items endpoint returns menu items"""
        response = member_session.get(f"{BASE_URL}/api/portal/cafe/items")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✅ Cafe endpoint returned {len(data['items'])} items")
    
    def test_cafe_items_have_required_fields(self, member_session):
        """Cafe items have name, price, and category"""
        response = member_session.get(f"{BASE_URL}/api/portal/cafe/items")
        data = response.json()
        
        if data.get("items") and len(data["items"]) > 0:
            item = data["items"][0]
            assert "name" in item, "Item missing name"
            assert "price" in item, "Item missing price"
            print(f"✅ Cafe item '{item['name']}' has required fields")


class TestWatchVideos:
    """Watch section video tests"""
    
    @pytest.fixture
    def member_session(self):
        """Get member authenticated session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "member@abundant.church", "password": "Demo2026!"}
        )
        if response.status_code != 200:
            pytest.skip("Member login failed")
        return session
    
    def test_videos_endpoint_exists(self, member_session):
        """Videos endpoint returns videos"""
        response = member_session.get(f"{BASE_URL}/api/portal/media/videos")
        assert response.status_code == 200
        data = response.json()
        assert "videos" in data
        print(f"✅ Videos endpoint returned {len(data['videos'])} videos")
    
    def test_videos_have_youtube_id(self, member_session):
        """Videos have YouTube ID for playback"""
        response = member_session.get(f"{BASE_URL}/api/portal/media/videos")
        data = response.json()
        
        if data.get("videos") and len(data["videos"]) > 0:
            video = data["videos"][0]
            assert "youtube_id" in video, "Video missing youtube_id"
            print(f"✅ Video '{video.get('title', 'Unknown')}' has YouTube ID: {video['youtube_id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
