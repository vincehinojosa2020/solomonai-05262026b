"""
Push Notifications & Kids Check-in API Tests - Iteration 24
Tests for:
1. Push notification VAPID key endpoint
2. Push subscription endpoints (requires auth)
3. Kids check-in related endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = "Demo2026!"

class TestPushNotificationEndpoints:
    """Push notification API tests"""
    
    def test_vapid_public_key_endpoint(self):
        """Test GET /api/push/vapid-public-key returns a valid public key"""
        response = requests.get(f"{BASE_URL}/api/push/vapid-public-key")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "public_key" in data, "Response should contain 'public_key'"
        assert isinstance(data["public_key"], str), "public_key should be a string"
        assert len(data["public_key"]) > 0, "public_key should not be empty"
        print(f"✓ VAPID public key returned: {data['public_key'][:30]}...")
    
    def test_push_subscribe_requires_auth(self):
        """Test POST /api/push/subscribe requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/push/subscribe",
            json={"subscription": {"endpoint": "https://test.endpoint", "keys": {}}}
        )
        assert response.status_code == 401, f"Expected 401 for unauthenticated request, got {response.status_code}"
        print("✓ Push subscribe correctly requires authentication")
    
    def test_push_unsubscribe_requires_auth(self):
        """Test DELETE /api/push/subscribe requires authentication"""
        response = requests.delete(
            f"{BASE_URL}/api/push/subscribe",
            json={"endpoint": "https://test.endpoint"}
        )
        assert response.status_code == 401, f"Expected 401 for unauthenticated request, got {response.status_code}"
        print("✓ Push unsubscribe correctly requires authentication")
    
    def test_push_subscribe_with_auth(self, authenticated_session):
        """Test POST /api/push/subscribe works with authentication"""
        test_subscription = {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-12345",
                "keys": {
                    "p256dh": "test-p256dh-key",
                    "auth": "test-auth-key"
                }
            }
        }
        
        response = authenticated_session.post(
            f"{BASE_URL}/api/push/subscribe",
            json=test_subscription
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "subscribed", f"Expected status 'subscribed', got {data}"
        print("✓ Push subscription created successfully")
    
    def test_push_unsubscribe_with_auth(self, authenticated_session):
        """Test DELETE /api/push/subscribe works with authentication"""
        response = authenticated_session.delete(
            f"{BASE_URL}/api/push/subscribe",
            json={"endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-12345"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "unsubscribed", f"Expected status 'unsubscribed', got {data}"
        print("✓ Push subscription removed successfully")


class TestKidsCheckinEndpoints:
    """Kids check-in API tests"""
    
    def test_get_kids_list(self, authenticated_session):
        """Test GET /api/portal/kids returns children list"""
        response = authenticated_session.get(f"{BASE_URL}/api/portal/kids")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "children" in data, "Response should contain 'children'"
        assert isinstance(data["children"], list), "children should be a list"
        print(f"✓ Kids list returned: {len(data['children'])} children")
        return data["children"]
    
    def test_get_active_checkins(self, authenticated_session):
        """Test GET /api/portal/kids/checkins/active returns active check-ins"""
        response = authenticated_session.get(f"{BASE_URL}/api/portal/kids/checkins/active")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "checkins" in data, "Response should contain 'checkins'"
        assert isinstance(data["checkins"], list), "checkins should be a list"
        print(f"✓ Active check-ins returned: {len(data['checkins'])} check-ins")
        return data["checkins"]
    
    def test_add_child(self, authenticated_session):
        """Test POST /api/portal/kids adds a new child"""
        test_child = {
            "name": "TEST_Tommy Test",
            "birthdate": "2020-05-15",
            "allergies": "Peanuts",
            "special_needs": "None",
            "emergency_contact": "Test Parent",
            "emergency_phone": "555-123-4567"
        }
        
        response = authenticated_session.post(
            f"{BASE_URL}/api/portal/kids",
            json=test_child
        )
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        
        data = response.json()
        assert "id" in data or "child" in data, "Response should contain child data with id"
        print("✓ Child added successfully")
        return data
    
    def test_checkin_child(self, authenticated_session):
        """Test POST /api/portal/kids/{child_id}/checkin checks in a child"""
        # First get the list of children
        kids_response = authenticated_session.get(f"{BASE_URL}/api/portal/kids")
        kids_data = kids_response.json()
        children = kids_data.get("children", [])
        
        if not children:
            pytest.skip("No children available to check in")
        
        # Find an unchecked child (prefer TEST_ prefixed)
        checkins_response = authenticated_session.get(f"{BASE_URL}/api/portal/kids/checkins/active")
        checkins_data = checkins_response.json()
        checked_in_ids = [c.get("child_id") for c in checkins_data.get("checkins", [])]
        
        unchecked_child = None
        for child in children:
            if child.get("id") not in checked_in_ids:
                unchecked_child = child
                break
        
        if not unchecked_child:
            pytest.skip("All children are already checked in")
        
        # Check in the child
        response = authenticated_session.post(
            f"{BASE_URL}/api/portal/kids/{unchecked_child['id']}/checkin",
            json={"classroom": "Sunday School"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "pickup_code" in data, "Response should contain pickup_code"
        assert isinstance(data["pickup_code"], str), "pickup_code should be a string"
        print(f"✓ Child checked in. Pickup code: {data['pickup_code']}")
        return data


# Fixtures
@pytest.fixture
def api_session():
    """Create a requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def authenticated_session(api_session):
    """Create an authenticated session with member credentials"""
    # Login
    login_response = api_session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
    )
    
    if login_response.status_code != 200:
        pytest.skip(f"Login failed with status {login_response.status_code}")
    
    return api_session


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed data after tests"""
    yield
    # Cleanup would go here if needed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
