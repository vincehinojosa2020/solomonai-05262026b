"""
Iteration 54: SolomonPay and Lead Capture Testing
Tests for:
- POST /api/solomonpay/process - payment processing (all stay pending)
- GET /api/solomonpay/transactions - admin transaction list
- POST /api/leads/capture - lead capture from landing page
- GET /api/admin/leads - admin leads list
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PLATFORM_ADMIN = {"email": "admin@solomonai.us", "password": "Demo2026!"}
CHURCH_ADMIN = {"email": "shannonnieman1030@gmail.com", "password": "Demo2026!"}
MEMBER = {"email": "member@abundant.church", "password": "Demo2026!"}


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def platform_admin_token(api_client):
    """Get platform admin auth token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Platform admin authentication failed")


@pytest.fixture(scope="module")
def church_admin_token(api_client):
    """Get church admin auth token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Church admin authentication failed")


@pytest.fixture(scope="module")
def member_token(api_client):
    """Get member auth token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json=MEMBER)
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Member authentication failed")


class TestSolomonPayProcess:
    """Tests for POST /api/solomonpay/process endpoint"""

    def test_process_payment_success_visa(self, api_client, member_token):
        """Test successful payment processing with Visa card"""
        payload = {
            "card_last_four": "4242",
            "card_brand": "Visa",
            "card_exp_month": "12",
            "card_exp_year": "28",
            "cardholder_name": "Test User",
            "billing_zip": "12345",
            "save_card": False,
            "amount": 100.00,
            "context": "donation",
            "fund_id": "general",
            "fund_name": "General Fund",
            "frequency": "one-time",
            "description": "Test donation"
        }
        response = api_client.post(
            f"{BASE_URL}/api/solomonpay/process",
            json=payload,
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data.get("success") is True
        assert "transaction_id" in data
        assert data["transaction_id"].startswith("sp_txn_")
        assert data.get("status") == "pending"
        assert data.get("amount") == 100.00
        assert "message" in data
        print(f"SUCCESS: Visa payment processed - Transaction ID: {data['transaction_id']}")

    def test_process_payment_mastercard(self, api_client, member_token):
        """Test payment processing with Mastercard"""
        payload = {
            "card_last_four": "5555",
            "card_brand": "Mastercard",
            "card_exp_month": "06",
            "card_exp_year": "27",
            "cardholder_name": "MC Test User",
            "billing_zip": "54321",
            "save_card": False,
            "amount": 50.00,
            "context": "donation"
        }
        response = api_client.post(
            f"{BASE_URL}/api/solomonpay/process",
            json=payload,
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("status") == "pending"
        print(f"SUCCESS: Mastercard payment processed - Transaction ID: {data['transaction_id']}")

    def test_process_payment_amex(self, api_client, member_token):
        """Test payment processing with Amex card"""
        payload = {
            "card_last_four": "3782",
            "card_brand": "Amex",
            "card_exp_month": "03",
            "card_exp_year": "29",
            "cardholder_name": "Amex Test User",
            "billing_zip": "90210",
            "save_card": False,
            "amount": 250.00,
            "context": "donation"
        }
        response = api_client.post(
            f"{BASE_URL}/api/solomonpay/process",
            json=payload,
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("status") == "pending"
        print(f"SUCCESS: Amex payment processed - Transaction ID: {data['transaction_id']}")

    def test_process_payment_validates_positive_amount(self, api_client, member_token):
        """Test that amount must be positive"""
        payload = {
            "card_last_four": "4242",
            "card_brand": "Visa",
            "card_exp_month": "12",
            "card_exp_year": "28",
            "cardholder_name": "Test User",
            "billing_zip": "12345",
            "save_card": False,
            "amount": 0,  # Invalid - must be positive
            "context": "donation"
        }
        response = api_client.post(
            f"{BASE_URL}/api/solomonpay/process",
            json=payload,
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400 for zero amount, got {response.status_code}"
        print("SUCCESS: Zero amount correctly rejected with 400")

    def test_process_payment_validates_negative_amount(self, api_client, member_token):
        """Test that negative amount is rejected"""
        payload = {
            "card_last_four": "4242",
            "card_brand": "Visa",
            "card_exp_month": "12",
            "card_exp_year": "28",
            "cardholder_name": "Test User",
            "billing_zip": "12345",
            "save_card": False,
            "amount": -50.00,  # Invalid - negative
            "context": "donation"
        }
        response = api_client.post(
            f"{BASE_URL}/api/solomonpay/process",
            json=payload,
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400 for negative amount, got {response.status_code}"
        print("SUCCESS: Negative amount correctly rejected with 400")

    def test_process_payment_cafe_context(self, api_client, member_token):
        """Test payment with cafe_order context"""
        payload = {
            "card_last_four": "4242",
            "card_brand": "Visa",
            "card_exp_month": "12",
            "card_exp_year": "28",
            "cardholder_name": "Cafe Customer",
            "billing_zip": "12345",
            "save_card": False,
            "amount": 15.50,
            "context": "cafe_order",
            "description": "Cafe order - Latte, Muffin"
        }
        response = api_client.post(
            f"{BASE_URL}/api/solomonpay/process",
            json=payload,
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("status") == "pending"
        print(f"SUCCESS: Cafe order payment processed - Transaction ID: {data['transaction_id']}")

    def test_process_payment_merch_context(self, api_client, member_token):
        """Test payment with merch_order context"""
        payload = {
            "card_last_four": "5555",
            "card_brand": "Mastercard",
            "card_exp_month": "09",
            "card_exp_year": "26",
            "cardholder_name": "Merch Buyer",
            "billing_zip": "33333",
            "save_card": False,
            "amount": 45.00,
            "context": "merch_order",
            "description": "Merch order - Church T-Shirt"
        }
        response = api_client.post(
            f"{BASE_URL}/api/solomonpay/process",
            json=payload,
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("status") == "pending"
        print(f"SUCCESS: Merch order payment processed - Transaction ID: {data['transaction_id']}")

    def test_process_payment_without_auth(self, api_client):
        """Test payment processing without authentication (anonymous)"""
        payload = {
            "card_last_four": "4242",
            "card_brand": "Visa",
            "card_exp_month": "12",
            "card_exp_year": "28",
            "cardholder_name": "Anonymous Donor",
            "billing_zip": "12345",
            "save_card": False,
            "amount": 25.00,
            "context": "donation"
        }
        response = api_client.post(
            f"{BASE_URL}/api/solomonpay/process",
            json=payload
        )
        
        # Should still work for anonymous donations
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("status") == "pending"
        print(f"SUCCESS: Anonymous payment processed - Transaction ID: {data['transaction_id']}")

    def test_process_payment_with_save_card(self, api_client, member_token):
        """Test payment with save_card option"""
        payload = {
            "card_last_four": "1234",
            "card_brand": "Visa",
            "card_exp_month": "11",
            "card_exp_year": "30",
            "cardholder_name": "Save Card User",
            "billing_zip": "55555",
            "save_card": True,  # Save card for future use
            "amount": 75.00,
            "context": "donation"
        }
        response = api_client.post(
            f"{BASE_URL}/api/solomonpay/process",
            json=payload,
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        print(f"SUCCESS: Payment with save_card processed - Transaction ID: {data['transaction_id']}")


class TestSolomonPayTransactions:
    """Tests for GET /api/solomonpay/transactions endpoint"""

    def test_get_transactions_as_church_admin(self, api_client, church_admin_token):
        """Test getting transactions as church admin"""
        response = api_client.get(
            f"{BASE_URL}/api/solomonpay/transactions",
            headers={"Authorization": f"Bearer {church_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert isinstance(data["transactions"], list)
        print(f"SUCCESS: Church admin retrieved {len(data['transactions'])} transactions")

    def test_get_transactions_as_platform_admin(self, api_client, platform_admin_token):
        """Test getting transactions as platform admin"""
        response = api_client.get(
            f"{BASE_URL}/api/solomonpay/transactions",
            headers={"Authorization": f"Bearer {platform_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        print(f"SUCCESS: Platform admin retrieved {len(data['transactions'])} transactions")

    def test_get_transactions_unauthorized(self, api_client, member_token):
        """Test that regular members cannot access transactions"""
        response = api_client.get(
            f"{BASE_URL}/api/solomonpay/transactions",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403 for member access, got {response.status_code}"
        print("SUCCESS: Member correctly denied access to transactions (403)")

    def test_get_transactions_no_auth(self, api_client):
        """Test that unauthenticated requests are rejected"""
        response = api_client.get(f"{BASE_URL}/api/solomonpay/transactions")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"SUCCESS: Unauthenticated request correctly rejected ({response.status_code})")


class TestLeadCapture:
    """Tests for POST /api/leads/capture endpoint"""

    def test_capture_lead_success(self, api_client):
        """Test successful lead capture with all fields"""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "church_name": f"TEST_Grace Community Church {unique_id}",
            "name": "Pastor John Smith",
            "email": f"test_pastor_{unique_id}@gracechurch.org",
            "phone": "555-123-4567",
            "current_software": "planning-center",
            "church_size": "500-1000"
        }
        response = api_client.post(f"{BASE_URL}/api/leads/capture", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "message" in data
        print(f"SUCCESS: Lead captured - {payload['church_name']}")

    def test_capture_lead_required_fields_only(self, api_client):
        """Test lead capture with only required fields"""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "church_name": f"TEST_Minimal Church {unique_id}",
            "name": "Jane Doe",
            "email": f"test_jane_{unique_id}@minimalchurch.org"
        }
        response = api_client.post(f"{BASE_URL}/api/leads/capture", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        print(f"SUCCESS: Lead captured with minimal fields - {payload['church_name']}")

    def test_capture_lead_missing_church_name(self, api_client):
        """Test that church_name is required"""
        payload = {
            "name": "Test User",
            "email": "test@example.com"
        }
        response = api_client.post(f"{BASE_URL}/api/leads/capture", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing church_name, got {response.status_code}"
        print("SUCCESS: Missing church_name correctly rejected (422)")

    def test_capture_lead_missing_name(self, api_client):
        """Test that name is required"""
        payload = {
            "church_name": "Test Church",
            "email": "test@example.com"
        }
        response = api_client.post(f"{BASE_URL}/api/leads/capture", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing name, got {response.status_code}"
        print("SUCCESS: Missing name correctly rejected (422)")

    def test_capture_lead_missing_email(self, api_client):
        """Test that email is required"""
        payload = {
            "church_name": "Test Church",
            "name": "Test User"
        }
        response = api_client.post(f"{BASE_URL}/api/leads/capture", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing email, got {response.status_code}"
        print("SUCCESS: Missing email correctly rejected (422)")

    def test_capture_lead_all_software_options(self, api_client):
        """Test lead capture with different software options"""
        software_options = ["planning-center", "ccb", "breeze", "fellowshipone", "pushpay", "other", "none"]
        
        for software in software_options:
            unique_id = uuid.uuid4().hex[:8]
            payload = {
                "church_name": f"TEST_Church Using {software} {unique_id}",
                "name": "Test Pastor",
                "email": f"test_{software}_{unique_id}@church.org",
                "current_software": software
            }
            response = api_client.post(f"{BASE_URL}/api/leads/capture", json=payload)
            assert response.status_code == 200, f"Failed for software: {software}"
        
        print(f"SUCCESS: All {len(software_options)} software options accepted")

    def test_capture_lead_all_size_options(self, api_client):
        """Test lead capture with different church size options"""
        size_options = ["<100", "100-500", "500-1000", "1000-5000", "5000+"]
        
        for size in size_options:
            unique_id = uuid.uuid4().hex[:8]
            payload = {
                "church_name": f"TEST_Church Size {size} {unique_id}",
                "name": "Test Pastor",
                "email": f"test_size_{unique_id}@church.org",
                "church_size": size
            }
            response = api_client.post(f"{BASE_URL}/api/leads/capture", json=payload)
            assert response.status_code == 200, f"Failed for size: {size}"
        
        print(f"SUCCESS: All {len(size_options)} church size options accepted")


class TestAdminLeads:
    """Tests for GET /api/admin/leads endpoint"""

    def test_get_leads_as_platform_admin(self, api_client, platform_admin_token):
        """Test getting leads as platform admin"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/leads",
            headers={"Authorization": f"Bearer {platform_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert isinstance(data["leads"], list)
        assert "total" in data
        print(f"SUCCESS: Platform admin retrieved {data['total']} leads")

    def test_get_leads_as_church_admin_denied(self, api_client, church_admin_token):
        """Test that church admin cannot access leads (platform admin only)"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/leads",
            headers={"Authorization": f"Bearer {church_admin_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403 for church admin, got {response.status_code}"
        print("SUCCESS: Church admin correctly denied access to leads (403)")

    def test_get_leads_as_member_denied(self, api_client, member_token):
        """Test that member cannot access leads"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/leads",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403 for member, got {response.status_code}"
        print("SUCCESS: Member correctly denied access to leads (403)")

    def test_get_leads_no_auth_denied(self, api_client):
        """Test that unauthenticated requests are rejected"""
        response = api_client.get(f"{BASE_URL}/api/admin/leads")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"SUCCESS: Unauthenticated request correctly rejected ({response.status_code})")

    def test_leads_contain_captured_data(self, api_client, platform_admin_token):
        """Test that leads contain the captured data fields"""
        # First capture a lead
        unique_id = uuid.uuid4().hex[:8]
        lead_payload = {
            "church_name": f"TEST_Verify Fields Church {unique_id}",
            "name": "Verify Pastor",
            "email": f"test_verify_{unique_id}@church.org",
            "phone": "555-999-8888",
            "current_software": "breeze",
            "church_size": "1000-5000"
        }
        capture_response = api_client.post(f"{BASE_URL}/api/leads/capture", json=lead_payload)
        assert capture_response.status_code == 200
        
        # Then verify it appears in leads list
        response = api_client.get(
            f"{BASE_URL}/api/admin/leads",
            headers={"Authorization": f"Bearer {platform_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Find our test lead
        test_lead = None
        for lead in data["leads"]:
            if lead.get("email") == lead_payload["email"]:
                test_lead = lead
                break
        
        assert test_lead is not None, "Test lead not found in leads list"
        assert test_lead.get("church_name") == lead_payload["church_name"]
        assert test_lead.get("name") == lead_payload["name"]
        assert test_lead.get("phone") == lead_payload["phone"]
        assert test_lead.get("current_software") == lead_payload["current_software"]
        assert test_lead.get("church_size") == lead_payload["church_size"]
        assert test_lead.get("status") == "new"
        assert "created_at" in test_lead
        print(f"SUCCESS: Lead data verified - {test_lead['church_name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
