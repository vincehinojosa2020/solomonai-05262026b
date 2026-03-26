"""
Iteration 50: Testing new features - Landing Page, Login Update, Signup, Demo Page, War Room Upgrade
Backend API tests for:
- POST /api/waitlist/solomon-pay (Solomon Pay waitlist)
- POST /api/demo-requests (Demo request submission)
- POST /api/auth/register-church (Church self-registration)
- GET /api/admin/war-room (Enhanced war room with seed data)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestWaitlistEndpoint:
    """Tests for Solomon Pay waitlist endpoint"""
    
    def test_waitlist_success(self):
        """Test successful waitlist signup"""
        unique_email = f"test_waitlist_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/waitlist/solomon-pay", json={
            "email": unique_email,
            "church_name": "Test Church"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "waitlist" in data.get("message", "").lower()
        print(f"PASS: Waitlist signup successful for {unique_email}")
    
    def test_waitlist_duplicate_email(self):
        """Test duplicate email returns success (already on waitlist)"""
        unique_email = f"test_dup_{uuid.uuid4().hex[:8]}@example.com"
        # First signup
        requests.post(f"{BASE_URL}/api/waitlist/solomon-pay", json={
            "email": unique_email,
            "church_name": "Test Church"
        })
        # Second signup with same email
        response = requests.post(f"{BASE_URL}/api/waitlist/solomon-pay", json={
            "email": unique_email,
            "church_name": "Test Church"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("PASS: Duplicate email handled gracefully")
    
    def test_waitlist_missing_email(self):
        """Test waitlist signup without email returns 400"""
        response = requests.post(f"{BASE_URL}/api/waitlist/solomon-pay", json={
            "church_name": "Test Church"
        })
        assert response.status_code == 400
        print("PASS: Missing email returns 400")


class TestDemoRequestEndpoint:
    """Tests for demo request submission endpoint"""
    
    def test_demo_request_success(self):
        """Test successful demo request submission"""
        unique_email = f"test_demo_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/demo-requests", json={
            "first_name": "John",
            "last_name": "Doe",
            "church_name": "Grace Community Church",
            "email": unique_email,
            "phone": "555-123-4567",
            "member_count": "1,000-5,000",
            "interests": ["Replacing Planning Center", "AI assistant"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "24 hours" in data.get("message", "")
        print(f"PASS: Demo request submitted for {unique_email}")
    
    def test_demo_request_minimal_fields(self):
        """Test demo request with only required fields"""
        unique_email = f"test_demo_min_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/demo-requests", json={
            "first_name": "Jane",
            "church_name": "Faith Church",
            "email": unique_email
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("PASS: Demo request with minimal fields works")
    
    def test_demo_request_missing_required(self):
        """Test demo request missing required fields returns 400"""
        response = requests.post(f"{BASE_URL}/api/demo-requests", json={
            "first_name": "John"
            # Missing church_name and email
        })
        assert response.status_code == 400
        print("PASS: Missing required fields returns 400")


class TestRegisterChurchEndpoint:
    """Tests for church self-registration endpoint"""
    
    def test_register_church_success(self):
        """Test successful church registration"""
        unique_email = f"test_admin_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/auth/register-church", json={
            "church_name": "New Hope Church",
            "city": "Austin",
            "state": "TX",
            "denomination": "Non-denominational",
            "member_count": "200-1,000",
            "first_name": "Pastor",
            "last_name": "Smith",
            "email": unique_email,
            "password": "SecurePass123!",
            "role_title": "Lead Pastor"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "token" in data
        assert data.get("role") == "church_admin"
        assert data.get("church_name") == "New Hope Church"
        assert data.get("is_first_login") == True
        print(f"PASS: Church registration successful, token: {data.get('token')[:20]}...")
    
    def test_register_church_minimal_fields(self):
        """Test church registration with only required fields"""
        unique_email = f"test_min_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/auth/register-church", json={
            "church_name": "Simple Church",
            "first_name": "Admin",
            "email": unique_email,
            "password": "Password123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "token" in data
        print("PASS: Church registration with minimal fields works")
    
    def test_register_church_duplicate_email(self):
        """Test registration with existing email returns 409"""
        unique_email = f"test_dup_church_{uuid.uuid4().hex[:8]}@example.com"
        # First registration
        requests.post(f"{BASE_URL}/api/auth/register-church", json={
            "church_name": "First Church",
            "first_name": "Admin",
            "email": unique_email,
            "password": "Password123!"
        })
        # Second registration with same email
        response = requests.post(f"{BASE_URL}/api/auth/register-church", json={
            "church_name": "Second Church",
            "first_name": "Admin2",
            "email": unique_email,
            "password": "Password456!"
        })
        assert response.status_code == 409
        print("PASS: Duplicate email returns 409 conflict")
    
    def test_register_church_missing_required(self):
        """Test registration missing required fields returns 400"""
        response = requests.post(f"{BASE_URL}/api/auth/register-church", json={
            "church_name": "Test Church"
            # Missing email, password, first_name
        })
        assert response.status_code == 400
        print("PASS: Missing required fields returns 400")


class TestWarRoomEndpoint:
    """Tests for enhanced War Room endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for Shannon (church admin)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "shannonnieman1030@gmail.com",
            "password": "Demo2026!"
        })
        if response.status_code == 200:
            return response.json().get("session_token")
        pytest.skip("Could not authenticate as Shannon")
    
    def test_war_room_returns_data(self, auth_token):
        """Test war room returns expected data structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/war-room",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check top-level fields
        assert "timestamp" in data
        assert "church_name" in data
        assert "is_seed_data" in data
        assert "counters" in data
        assert "activity_feed" in data
        assert "giving_trend" in data
        assert "capacity" in data
        print(f"PASS: War room returns data structure, is_seed_data={data.get('is_seed_data')}")
    
    def test_war_room_counters(self, auth_token):
        """Test war room counters contain all 8 KPI fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/war-room",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        counters = response.json().get("counters", {})
        
        # Check all 8 KPI fields exist
        required_fields = [
            "members_present", "kids_checked_in", "volunteers_on_duty",
            "first_time_visitors", "given_today", "mtd_giving",
            "cafe_orders_today", "merch_sales"
        ]
        for field in required_fields:
            assert field in counters, f"Missing counter field: {field}"
        print(f"PASS: All 8 KPI counter fields present")
    
    def test_war_room_activity_feed(self, auth_token):
        """Test war room activity feed has items"""
        response = requests.get(
            f"{BASE_URL}/api/admin/war-room",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        activity_feed = data.get("activity_feed", [])
        
        # Should have activity items (seed data if no live data)
        assert len(activity_feed) > 0, "Activity feed should not be empty"
        
        # Check activity item structure
        first_item = activity_feed[0]
        assert "action" in first_item
        assert "performed_by_name" in first_item
        assert "timestamp" in first_item
        print(f"PASS: Activity feed has {len(activity_feed)} items")
    
    def test_war_room_giving_trend(self, auth_token):
        """Test war room giving trend has 5 data points"""
        response = requests.get(
            f"{BASE_URL}/api/admin/war-room",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        giving_trend = response.json().get("giving_trend", [])
        
        assert len(giving_trend) == 5, "Giving trend should have 5 data points"
        
        # Check structure
        for item in giving_trend:
            assert "label" in item
            assert "amount" in item
        
        # Last item should be "Today"
        assert giving_trend[-1].get("label") == "Today"
        print(f"PASS: Giving trend has 5 data points, last is 'Today'")
    
    def test_war_room_seed_data_values(self, auth_token):
        """Test war room seed data has realistic values"""
        response = requests.get(
            f"{BASE_URL}/api/admin/war-room",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("is_seed_data"):
            counters = data.get("counters", {})
            # Check seed data values match expected
            assert counters.get("kids_checked_in") == 47
            assert counters.get("members_present") == 312
            assert counters.get("given_today") == 28450
            assert counters.get("cafe_orders_today") == 34
            print("PASS: Seed data values match expected (47 kids, 312 members, $28,450 given)")
        else:
            print("INFO: Using live data, skipping seed value check")
    
    def test_war_room_unauthorized(self):
        """Test war room requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/war-room")
        assert response.status_code in [401, 403]
        print("PASS: War room requires authentication")


class TestLoginEndpoint:
    """Tests for login endpoint (existing but verify it works)"""
    
    def test_login_shannon(self):
        """Test login as Shannon (church admin)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "shannonnieman1030@gmail.com",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data
        assert data.get("name") is not None
        print(f"PASS: Shannon login successful, role={data.get('role')}")
    
    def test_login_platform_admin(self):
        """Test login as platform admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@solomonai.us",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("role") == "platform_admin"
        print("PASS: Platform admin login successful")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 404]
        print("PASS: Invalid credentials rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
