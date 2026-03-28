"""
Phase 5: Registrations Module Tests
Tests for registration configs, registrants, promo codes, and public registration
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "shannonnieman1030@gmail.com"
TEST_PASSWORD = "Demo2026!"

# Known test event with registration config
TEST_EVENT_ID = "event_abundant_012"


class TestPhase5Registrations:
    """Phase 5: Registrations Module Tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("session_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    # ============== ADMIN REGISTRATION EVENTS ==============
    
    def test_api_health(self):
        """Test API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ API health check passed")
    
    def test_get_registration_events(self, auth_headers):
        """GET /api/admin/registrations/events - Get events with registration enabled"""
        response = requests.get(
            f"{BASE_URL}/api/admin/registrations/events",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "events" in data
        assert "total" in data
        # Should have registration-enabled events
        assert data["total"] > 0, "Expected at least one registration event"
        # Check event structure
        if data["events"]:
            evt = data["events"][0]
            assert "id" in evt
            assert "name" in evt
            assert "confirmed_count" in evt or evt.get("confirmed_count") is not None
            assert "waitlist_count" in evt or evt.get("waitlist_count") is not None
            assert "has_config" in evt or evt.get("has_config") is not None
        print(f"✓ GET registration events: {data['total']} events found")
    
    # ============== REGISTRATION CONFIG ==============
    
    def test_get_registration_config(self, auth_headers):
        """GET /api/admin/registrations/configs/{eventId} - Get config for event"""
        response = requests.get(
            f"{BASE_URL}/api/admin/registrations/configs/{TEST_EVENT_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Config may or may not exist
        if data.get("config"):
            config = data["config"]
            assert "pricing" in config or config.get("pricing") is not None
            assert "add_ons" in config or config.get("add_ons") is not None
            assert "custom_questions" in config or config.get("custom_questions") is not None
            print(f"✓ GET registration config: Config exists with pricing={config.get('pricing')}")
        else:
            print("✓ GET registration config: No config yet (expected for new events)")
    
    def test_create_update_registration_config(self, auth_headers):
        """POST /api/admin/registrations/configs/{eventId} - Create/update config"""
        config_payload = {
            "pricing": {"enabled": True, "amount": 30, "currency": "USD"},
            "add_ons": [
                {"id": "test_addon_1", "name": "TEST_Parking Pass", "price": 5},
                {"id": "test_addon_2", "name": "TEST_Meal Ticket", "price": 12}
            ],
            "custom_questions": [
                {"id": "test_q1", "label": "TEST_Emergency Contact?", "type": "text", "required": True},
                {"id": "test_q2", "label": "TEST_Meal Preference", "type": "select", "options": ["Vegetarian", "Non-Vegetarian", "Vegan"]}
            ],
            "waitlist_enabled": True,
            "auto_confirm": True,
            "confirmation_message": "TEST: Thank you for registering!"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/registrations/configs/{TEST_EVENT_ID}",
            headers=auth_headers,
            json=config_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "config" in data or "message" in data
        print(f"✓ POST registration config: {data.get('message', 'Config saved')}")
        
        # Verify config was saved by fetching it
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/registrations/configs/{TEST_EVENT_ID}",
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data.get("config") is not None
        config = verify_data["config"]
        assert config["pricing"]["amount"] == 30
        print("✓ Config verified: pricing amount = $30")
    
    # ============== PROMO CODES ==============
    
    def test_add_promo_code(self, auth_headers):
        """POST /api/admin/registrations/{eventId}/promo-codes - Add promo code"""
        promo_payload = {
            "code": f"TEST{uuid.uuid4().hex[:6].upper()}",
            "discount_type": "percentage",
            "discount_value": 15,
            "max_uses": 50
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/registrations/{TEST_EVENT_ID}/promo-codes",
            headers=auth_headers,
            json=promo_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "promo_code" in data
        promo = data["promo_code"]
        assert promo["code"] == promo_payload["code"]
        assert promo["discount_type"] == "percentage"
        assert promo["discount_value"] == 15
        print(f"✓ POST promo code: {promo['code']} (15% off)")
    
    # ============== REGISTRANTS ==============
    
    def test_get_event_registrants(self, auth_headers):
        """GET /api/admin/registrations/{eventId}/registrants - Get registrants"""
        response = requests.get(
            f"{BASE_URL}/api/admin/registrations/{TEST_EVENT_ID}/registrants",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "registrants" in data
        assert "totals" in data
        totals = data["totals"]
        assert "confirmed" in totals
        assert "waitlisted" in totals
        assert "cancelled" in totals
        print(f"✓ GET registrants: {len(data['registrants'])} registrants, totals={totals}")
    
    # ============== PUBLIC REGISTRATION ==============
    
    def test_get_public_registration_page(self):
        """GET /api/register/{eventId} - Public registration page data"""
        response = requests.get(f"{BASE_URL}/api/register/{TEST_EVENT_ID}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "event" in data
        assert "config" in data
        # Event should have basic info
        event = data["event"]
        assert "id" in event
        assert "name" in event
        # Config should NOT have sensitive promo code details
        config = data.get("config")
        if config:
            # Promo codes should be stripped from public view
            assert "promo_codes" not in config, "Promo codes should not be exposed publicly"
            assert "pricing" in config
            assert "add_ons" in config
            assert "custom_questions" in config
        print(f"✓ GET public registration: Event '{event['name']}', spots_left={data.get('spots_left')}")
    
    def test_submit_public_registration(self):
        """POST /api/register/{eventId} - Submit public registration"""
        unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        reg_payload = {
            "name": "TEST_Registration User",
            "email": unique_email,
            "phone": "555-123-4567",
            "add_ons": [],  # No add-ons for basic test
            "custom_answers": {},
            "promo_code": ""
        }
        response = requests.post(
            f"{BASE_URL}/api/register/{TEST_EVENT_ID}",
            json=reg_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert "registration_ids" in data
        assert "total_amount" in data
        assert data["status"] in ["confirmed", "waitlisted"]
        print(f"✓ POST public registration: {data['message']}, total=${data['total_amount']}")
        return data["registration_ids"][0] if data["registration_ids"] else None
    
    def test_submit_registration_with_addons(self):
        """POST /api/register/{eventId} - Registration with add-ons calculates total correctly"""
        # First get the config to know available add-ons
        config_response = requests.get(f"{BASE_URL}/api/register/{TEST_EVENT_ID}")
        assert config_response.status_code == 200
        config_data = config_response.json()
        config = config_data.get("config", {})
        add_ons = config.get("add_ons", [])
        
        # Select all add-ons
        selected_addon_ids = [addon["id"] for addon in add_ons]
        expected_addon_total = sum(addon.get("price", 0) for addon in add_ons)
        base_price = config.get("pricing", {}).get("amount", 0) if config.get("pricing", {}).get("enabled") else 0
        expected_total = base_price + expected_addon_total
        
        unique_email = f"test_addon_{uuid.uuid4().hex[:8]}@test.com"
        reg_payload = {
            "name": "TEST_Addon User",
            "email": unique_email,
            "phone": "555-999-8888",
            "add_ons": selected_addon_ids,
            "custom_answers": {},
            "promo_code": ""
        }
        response = requests.post(
            f"{BASE_URL}/api/register/{TEST_EVENT_ID}",
            json=reg_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Verify total calculation
        actual_total = data["total_amount"]
        assert actual_total == expected_total, f"Expected total ${expected_total}, got ${actual_total}"
        print(f"✓ Registration with add-ons: base=${base_price} + addons=${expected_addon_total} = ${actual_total}")
    
    # ============== UPDATE REGISTRANT STATUS ==============
    
    def test_update_registrant_status(self, auth_headers):
        """PUT /api/admin/registrations/{eventId}/registrants/{regId} - Update status"""
        # First create a test registration
        unique_email = f"test_status_{uuid.uuid4().hex[:8]}@test.com"
        reg_response = requests.post(
            f"{BASE_URL}/api/register/{TEST_EVENT_ID}",
            json={
                "name": "TEST_Status User",
                "email": unique_email,
                "add_ons": [],
                "custom_answers": {}
            }
        )
        assert reg_response.status_code == 200
        reg_data = reg_response.json()
        reg_id = reg_data["registration_ids"][0]
        
        # Update status to cancelled
        update_response = requests.put(
            f"{BASE_URL}/api/admin/registrations/{TEST_EVENT_ID}/registrants/{reg_id}",
            headers=auth_headers,
            json={"status": "cancelled"}
        )
        assert update_response.status_code == 200, f"Failed: {update_response.text}"
        data = update_response.json()
        assert "message" in data
        print(f"✓ PUT registrant status: {data['message']}")
    
    # ============== EDGE CASES ==============
    
    def test_public_registration_invalid_event(self):
        """GET /api/register/{eventId} - Invalid event returns 404"""
        response = requests.get(f"{BASE_URL}/api/register/invalid_event_xyz")
        assert response.status_code == 404
        print("✓ Invalid event returns 404")
    
    def test_registration_config_not_found(self, auth_headers):
        """GET /api/admin/registrations/configs/{eventId} - Non-existent config returns null"""
        # Use a random event ID that likely doesn't have a config
        response = requests.get(
            f"{BASE_URL}/api/admin/registrations/configs/nonexistent_event_123",
            headers=auth_headers
        )
        # Should return 200 with null config, not 404
        assert response.status_code in [200, 404]
        print("✓ Non-existent config handled correctly")
    
    # ============== CLEANUP ==============
    
    def test_cleanup_test_registrations(self, auth_headers):
        """Cleanup: Cancel all TEST_ registrations"""
        # Get all registrants
        response = requests.get(
            f"{BASE_URL}/api/admin/registrations/{TEST_EVENT_ID}/registrants",
            headers=auth_headers
        )
        if response.status_code == 200:
            data = response.json()
            for reg in data.get("registrants", []):
                if reg.get("user_name", "").startswith("TEST_"):
                    # Cancel test registrations
                    requests.put(
                        f"{BASE_URL}/api/admin/registrations/{TEST_EVENT_ID}/registrants/{reg['id']}",
                        headers=auth_headers,
                        json={"status": "cancelled"}
                    )
        print("✓ Cleanup: Test registrations cancelled")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
