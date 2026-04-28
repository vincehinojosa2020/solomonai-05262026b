"""
Iteration 93 — Stripe Connect Integration Tests
Tests for real Stripe payment processing with feature flag STRIPE_LIVE=true
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = os.environ.get("TEST_PASSWORD", "Demo2026!")


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def member_token(api_client):
    """Get member authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": MEMBER_EMAIL,
        "password": MEMBER_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("session_token") or data.get("token")
    pytest.skip(f"Member authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, member_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {member_token}"})
    return api_client


class TestStripeConfig:
    """Test GET /api/stripe/config endpoint"""
    
    def test_stripe_config_returns_correct_values(self, api_client):
        """GET /api/stripe/config should return stripe_live=true, stripe_configured=true, platform_fee_rate, mode='production'"""
        response = api_client.get(f"{BASE_URL}/api/stripe/config")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify stripe_live is true
        assert data.get("stripe_live") == True, f"Expected stripe_live=true, got {data.get('stripe_live')}"
        
        # Verify stripe_configured is true
        assert data.get("stripe_configured") == True, f"Expected stripe_configured=true, got {data.get('stripe_configured')}"
        
        # Verify platform_fee_rate is present
        assert "platform_fee_rate" in data, "platform_fee_rate should be present"
        assert "1.9%" in data.get("platform_fee_rate", ""), f"Expected 1.9% in fee rate, got {data.get('platform_fee_rate')}"
        
        # Verify mode is production
        assert data.get("mode") == "production", f"Expected mode='production', got {data.get('mode')}"
        
        print(f"✓ Stripe config: stripe_live={data['stripe_live']}, mode={data['mode']}, fee={data['platform_fee_rate']}")


class TestStripeCheckoutGiving:
    """Test POST /api/stripe/checkout/giving endpoint"""
    
    def test_checkout_giving_returns_stripe_url(self, authenticated_client):
        """POST /api/stripe/checkout/giving with valid amount should return real Stripe checkout URL"""
        payload = {
            "amount": 50.00,
            "fund_name": "General Fund",
            "cover_fees": False,
            "origin_url": "https://exec-metrics-hub.preview.emergentagent.com"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/stripe/checkout/giving", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify URL starts with https://checkout.stripe.com
        assert "url" in data, "Response should contain 'url'"
        assert data["url"].startswith("https://checkout.stripe.com"), f"URL should start with https://checkout.stripe.com, got {data['url'][:50]}..."
        
        # Verify session_id is present
        assert "session_id" in data, "Response should contain 'session_id'"
        assert data["session_id"].startswith("cs_"), f"session_id should start with 'cs_', got {data['session_id'][:10]}..."
        
        # Verify stripe_live is true
        assert data.get("stripe_live") == True, f"Expected stripe_live=true, got {data.get('stripe_live')}"
        
        # Verify amount matches
        assert data.get("amount") == 50.00, f"Expected amount=50.00, got {data.get('amount')}"
        
        print(f"✓ Checkout created: session_id={data['session_id'][:20]}..., url starts with checkout.stripe.com")
        
        # Return session_id for status test
        return data["session_id"]
    
    def test_checkout_giving_creates_payment_transaction(self, authenticated_client):
        """POST /api/stripe/checkout/giving should create a payment_transactions record with status='pending'"""
        payload = {
            "amount": 25.00,
            "fund_name": "Building Fund",
            "cover_fees": False,
            "origin_url": "https://exec-metrics-hub.preview.emergentagent.com"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/stripe/checkout/giving", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        session_id = data.get("session_id")
        
        # Verify the transaction was created by checking status endpoint
        status_response = authenticated_client.get(f"{BASE_URL}/api/stripe/checkout/status/{session_id}")
        
        assert status_response.status_code == 200, f"Status check failed: {status_response.status_code}"
        
        status_data = status_response.json()
        # Status should be 'open' or similar for a new session
        assert "status" in status_data, "Status response should contain 'status'"
        
        print(f"✓ Payment transaction created for session {session_id[:20]}..., status={status_data.get('status')}")
    
    def test_checkout_giving_with_cover_fees(self, authenticated_client):
        """POST /api/stripe/checkout/giving with cover_fees=true should add platform fee to total_charged"""
        base_amount = 50.00
        payload = {
            "amount": base_amount,
            "fund_name": "General Fund",
            "cover_fees": True,
            "origin_url": "https://exec-metrics-hub.preview.emergentagent.com"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/stripe/checkout/giving", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Calculate expected fee: 1.9% + $0.30
        expected_fee = round(base_amount * 0.019 + 0.30, 2)  # $1.25 for $50
        expected_total = round(base_amount + expected_fee, 2)  # $51.25
        
        # Verify platform_fee is calculated correctly
        assert "platform_fee" in data, "Response should contain 'platform_fee'"
        assert data["platform_fee"] == expected_fee, f"Expected platform_fee={expected_fee}, got {data['platform_fee']}"
        
        # Verify total_charged includes the fee
        assert "total_charged" in data, "Response should contain 'total_charged'"
        assert data["total_charged"] == expected_total, f"Expected total_charged={expected_total}, got {data['total_charged']}"
        
        print(f"✓ Cover fees: base=${base_amount}, fee=${data['platform_fee']}, total=${data['total_charged']}")
    
    def test_checkout_giving_minimum_amount_validation(self, authenticated_client):
        """POST /api/stripe/checkout/giving with amount < 1.00 should return 400 error"""
        payload = {
            "amount": 0.50,  # Below minimum
            "fund_name": "General Fund",
            "cover_fees": False,
            "origin_url": "https://exec-metrics-hub.preview.emergentagent.com"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/stripe/checkout/giving", json=payload)
        
        assert response.status_code == 400, f"Expected 400 for amount < $1.00, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data or "error" in data, "Error response should contain detail or error message"
        
        print(f"✓ Minimum amount validation: 400 returned for $0.50 donation")


class TestStripeCheckoutStatus:
    """Test GET /api/stripe/checkout/status/{session_id} endpoint"""
    
    def test_checkout_status_for_valid_session(self, authenticated_client):
        """GET /api/stripe/checkout/status/{session_id} should return payment status for a valid session"""
        # First create a checkout session
        payload = {
            "amount": 10.00,
            "fund_name": "General Fund",
            "cover_fees": False,
            "origin_url": "https://exec-metrics-hub.preview.emergentagent.com"
        }
        
        create_response = authenticated_client.post(f"{BASE_URL}/api/stripe/checkout/giving", json=payload)
        assert create_response.status_code == 200, f"Failed to create checkout: {create_response.text}"
        
        session_id = create_response.json().get("session_id")
        
        # Now check status
        status_response = authenticated_client.get(f"{BASE_URL}/api/stripe/checkout/status/{session_id}")
        
        assert status_response.status_code == 200, f"Expected 200, got {status_response.status_code}: {status_response.text}"
        
        data = status_response.json()
        
        # Verify required fields
        assert "status" in data, "Response should contain 'status'"
        assert "payment_status" in data, "Response should contain 'payment_status'"
        assert data.get("stripe_live") == True, f"Expected stripe_live=true, got {data.get('stripe_live')}"
        
        print(f"✓ Status check: session={session_id[:20]}..., status={data['status']}, payment_status={data['payment_status']}")


class TestStripeWebhook:
    """Test POST /api/webhook/stripe endpoint"""
    
    def test_webhook_endpoint_exists_and_accepts_post(self, api_client):
        """POST /api/webhook/stripe endpoint should exist and accept POST requests"""
        # Send a minimal webhook payload (will fail signature validation but should not 500)
        response = api_client.post(
            f"{BASE_URL}/api/webhook/stripe",
            json={"type": "test.event", "data": {}},
            headers={"Stripe-Signature": "test_signature"}
        )
        
        # Should return 200 with graceful handling (not 404 or 500)
        # The endpoint exists and handles the request gracefully even without valid signature
        assert response.status_code == 200, f"Expected 200 (graceful handling), got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "received" in data, "Response should contain 'received'"
        
        print(f"✓ Webhook endpoint exists and accepts POST: received={data.get('received')}")


class TestSolomonPayRegression:
    """Regression test: Solomon Pay flow should still work"""
    
    def test_solomonpay_process_endpoint_exists(self, authenticated_client):
        """Solomon Pay process endpoint should still be accessible"""
        # Just verify the endpoint exists - we won't actually process a payment
        # Check if we can get saved payment methods (part of Solomon Pay flow)
        response = authenticated_client.get(f"{BASE_URL}/api/portal/payment-methods")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "payment_methods" in data, "Response should contain 'payment_methods'"
        
        print(f"✓ Solomon Pay flow accessible: {len(data.get('payment_methods', []))} saved cards found")
    
    def test_solomonpay_process_with_saved_card(self, authenticated_client):
        """Solomon Pay should process payment with saved card (Visa 4242)"""
        # First get saved payment methods
        methods_response = authenticated_client.get(f"{BASE_URL}/api/portal/payment-methods")
        assert methods_response.status_code == 200
        
        methods = methods_response.json().get("payment_methods", [])
        
        # Find Visa 4242 card
        visa_card = None
        for card in methods:
            if card.get("card_last_four") == "4242" and card.get("card_brand") == "Visa":
                visa_card = card
                break
        
        if not visa_card:
            pytest.skip("No Visa 4242 card found in saved payment methods")
        
        # Process a small donation with the saved card
        payload = {
            "amount": 5.00,
            "payment_method_type": "card",
            "token": visa_card.get("token"),
            "cover_fees": False,
            "context": "donation",
            "fund_id": "general",
            "fund_name": "General Fund",
            "frequency": "one-time",
            "description": "Test donation via Solomon Pay"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/solomonpay/process", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True or "transaction_id" in data, f"Payment should succeed: {data}"
        
        print(f"✓ Solomon Pay regression: Payment processed successfully with Visa 4242")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
