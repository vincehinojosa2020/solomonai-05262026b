"""
Test Suite: User Journey - Register > Login > Donate > View History
Testing the complete user flow for SAMSON Church Management System
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user for this iteration
TEST_USER_EMAIL = f"testuser_iter9_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "TestPass2026!"
TEST_USER_FIRST_NAME = "TestUser"
TEST_USER_LAST_NAME = "Iter9"


class TestUserRegistration:
    """Test user registration flow"""
    
    def test_01_check_email_availability(self):
        """Check if email is available for registration"""
        response = requests.post(
            f"{BASE_URL}/api/auth/check-email",
            json={"email": TEST_USER_EMAIL}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("available") == True
        print(f"✓ Email {TEST_USER_EMAIL} is available for registration")

    def test_02_register_new_user(self):
        """Register a new member account"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "confirm_password": TEST_USER_PASSWORD,
                "first_name": TEST_USER_FIRST_NAME,
                "last_name": TEST_USER_LAST_NAME,
                "phone": "5551234567"
            }
        )
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        assert "user_id" in data
        assert data.get("email") == TEST_USER_EMAIL.lower()
        assert data.get("role") == "member"
        assert "message" in data
        # Store session cookie for later tests
        TestUserRegistration.session_cookie = response.cookies.get("session_token")
        print(f"✓ User registered successfully: {data.get('name')}")
        print(f"✓ Welcome email should be sent (check backend logs)")

    def test_03_registration_duplicate_email(self):
        """Test that duplicate email registration fails"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "confirm_password": TEST_USER_PASSWORD,
                "first_name": "Duplicate",
                "last_name": "User"
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data.get("detail", "").lower()
        print(f"✓ Duplicate registration correctly rejected")

    def test_04_registration_weak_password(self):
        """Test that weak password registration fails"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": f"weakpass_{uuid.uuid4().hex[:6]}@example.com",
                "password": "weak",
                "confirm_password": "weak",
                "first_name": "Weak",
                "last_name": "Password"
            }
        )
        assert response.status_code == 400
        print(f"✓ Weak password correctly rejected")

    def test_05_registration_password_mismatch(self):
        """Test that password mismatch registration fails"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": f"mismatch_{uuid.uuid4().hex[:6]}@example.com",
                "password": TEST_USER_PASSWORD,
                "confirm_password": "DifferentPassword2026!",
                "first_name": "Password",
                "last_name": "Mismatch"
            }
        )
        assert response.status_code == 400
        print(f"✓ Password mismatch correctly rejected")


class TestUserLogin:
    """Test user login flow"""

    def test_01_login_demo_member(self):
        """Login with demo member credentials"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "member@abundant.org",
                "password": "Demo2026!"
            }
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data.get("role") == "member"
        assert data.get("email") == "member@abundant.org"
        TestUserLogin.member_session = session
        print(f"✓ Demo member login successful: {data.get('name')}")

    def test_02_login_demo_admin(self):
        """Login with demo admin credentials"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "admin@abundant.org",
                "password": "Demo2026!"
            }
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data.get("role") == "admin"
        print(f"✓ Demo admin login successful: {data.get('name')}")

    def test_03_login_invalid_credentials(self):
        """Test invalid login credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "invalid@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        print(f"✓ Invalid credentials correctly rejected")

    def test_04_get_current_user(self):
        """Get current user from session"""
        session = TestUserLogin.member_session
        response = session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data.get("email") == "member@abundant.org"
        print(f"✓ Current user retrieved: {data.get('name')}")


class TestMemberPortal:
    """Test member portal access"""

    def test_01_portal_me(self):
        """Get member portal profile"""
        session = TestUserLogin.member_session
        response = session.get(f"{BASE_URL}/api/portal/me")
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "giving" in data
        print(f"✓ Portal profile retrieved")

    def test_02_portal_events(self):
        """Get portal events"""
        response = requests.get(f"{BASE_URL}/api/portal/events")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Portal events retrieved: {len(data)} events")

    def test_03_portal_groups(self):
        """Get portal groups"""
        response = requests.get(f"{BASE_URL}/api/portal/groups")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Portal groups retrieved: {len(data)} groups")

    def test_04_giving_history(self):
        """Get member giving history"""
        session = TestUserLogin.member_session
        response = session.get(f"{BASE_URL}/api/portal/giving/history")
        assert response.status_code == 200
        data = response.json()
        assert "donations" in data
        print(f"✓ Giving history retrieved: {len(data.get('donations', []))} donations")


class TestDonationFlow:
    """Test donation/giving flow with Stripe"""

    def test_01_get_payment_config(self):
        """Get Stripe publishable key"""
        response = requests.get(f"{BASE_URL}/api/payments/config")
        assert response.status_code == 200
        data = response.json()
        assert "publishable_key" in data
        assert data.get("publishable_key") is not None
        assert data.get("publishable_key").startswith("pk_")
        print(f"✓ Stripe config retrieved (key starts with pk_)")

    def test_02_get_funds(self):
        """Get available funds for donation"""
        response = requests.get(f"{BASE_URL}/api/funds")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        TestDonationFlow.fund_id = data[0].get("id") if data else "general"
        print(f"✓ Funds retrieved: {len(data)} funds")

    def test_03_create_donation_checkout_session(self):
        """Create Stripe checkout session for donation"""
        session = TestUserLogin.member_session
        response = session.post(
            f"{BASE_URL}/api/payments/donate",
            json={
                "package_id": "custom",
                "custom_amount": 25.00,
                "fund_id": TestDonationFlow.fund_id,
                "origin_url": "https://qa-security-ux.preview.emergentagent.com/portal/give",
                "recurring": False,
                "donor_name": "Test Donor",
                "donor_email": "member@abundant.org"
            }
        )
        assert response.status_code == 200, f"Checkout creation failed: {response.text}"
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data
        assert data.get("checkout_url").startswith("https://checkout.stripe.com")
        TestDonationFlow.session_id = data.get("session_id")
        print(f"✓ Stripe checkout session created: {data.get('session_id')[:20]}...")
        print(f"✓ Checkout URL: {data.get('checkout_url')[:50]}...")

    def test_04_donation_validation_min_amount(self):
        """Test donation minimum amount validation"""
        session = TestUserLogin.member_session
        response = session.post(
            f"{BASE_URL}/api/payments/donate",
            json={
                "package_id": "custom",
                "custom_amount": 0.50,  # Less than $1 minimum
                "fund_id": "general",
                "origin_url": "https://qa-security-ux.preview.emergentagent.com/portal/give",
                "recurring": False
            }
        )
        assert response.status_code == 400
        print(f"✓ Minimum amount validation working")

    def test_05_donation_validation_max_amount(self):
        """Test donation maximum amount validation"""
        session = TestUserLogin.member_session
        response = session.post(
            f"{BASE_URL}/api/payments/donate",
            json={
                "package_id": "custom",
                "custom_amount": 150000.00,  # Exceeds $100,000 max
                "fund_id": "general",
                "origin_url": "https://qa-security-ux.preview.emergentagent.com/portal/give",
                "recurring": False
            }
        )
        assert response.status_code == 400
        print(f"✓ Maximum amount validation working")

    def test_06_donation_package_preset(self):
        """Test preset donation package"""
        session = TestUserLogin.member_session
        response = session.post(
            f"{BASE_URL}/api/payments/donate",
            json={
                "package_id": "tithe_50",  # Preset $50 package
                "fund_id": "general",
                "origin_url": "https://qa-security-ux.preview.emergentagent.com/portal/give",
                "recurring": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        print(f"✓ Preset package checkout working")


class TestDashboardAPIs:
    """Test admin dashboard APIs (MOCKED data)"""

    def test_01_dashboard_stats(self):
        """Get dashboard stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_members" in data
        assert "mtd_giving" in data
        assert "active_groups" in data
        print(f"✓ Dashboard stats: {data.get('total_members')} members, ${data.get('mtd_giving')} MTD (MOCKED)")

    def test_02_giving_trend(self):
        """Get giving trend data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/giving-trend")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Giving trend: {len(data)} months (MOCKED)")

    def test_03_attendance_trend(self):
        """Get attendance trend data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/attendance-trend")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Attendance trend: {len(data)} weeks (MOCKED)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
