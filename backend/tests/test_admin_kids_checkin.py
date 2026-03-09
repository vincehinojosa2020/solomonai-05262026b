"""
Admin Kids Check-in API Tests
Tests for the admin-facing kids check-in functionality including:
- Get all check-ins
- Get all kids (admin view)
- Direct check-in by admin
- Verify pickup code
- Check out child
"""

import pytest
import requests
import os
import re

# Use the public URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAdminKidsCheckinAPI:
    """Test admin kids check-in endpoints"""
    
    session = None
    session_token = None
    
    @classmethod
    def setup_class(cls):
        """Login as admin and store session"""
        cls.session = requests.Session()
        
        # Login as admin
        login_response = cls.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@abundant.church", "password": "Demo2026!"}
        )
        
        if login_response.status_code == 200:
            # Extract session token from cookies
            cls.session_token = cls.session.cookies.get("session_token")
            print(f"Admin login successful, session token: {cls.session_token[:20]}...")
        else:
            print(f"Admin login failed: {login_response.status_code} - {login_response.text}")
    
    def test_admin_login(self):
        """Verify admin login worked"""
        assert self.session_token is not None, "Admin login should succeed"
        print("Admin login verified successfully")
    
    def test_get_all_kids_admin(self):
        """GET /api/admin/kids/all - Get all registered children"""
        response = self.session.get(f"{BASE_URL}/api/admin/kids/all")
        
        assert response.status_code == 200, f"Should return 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "children" in data, "Response should have 'children' key"
        
        children = data["children"]
        print(f"Found {len(children)} registered children")
        
        # Verify structure of child data
        if len(children) > 0:
            child = children[0]
            expected_fields = ["id", "name", "tenant_id"]
            for field in expected_fields:
                assert field in child, f"Child should have '{field}' field"
            print(f"Sample child: {child.get('name')} - Parent: {child.get('parent_name', 'N/A')}")
    
    def test_get_all_checkins_default(self):
        """GET /api/admin/kids/checkins - Get all check-ins without filter"""
        response = self.session.get(f"{BASE_URL}/api/admin/kids/checkins")
        
        assert response.status_code == 200, f"Should return 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "checkins" in data, "Response should have 'checkins' key"
        
        checkins = data["checkins"]
        print(f"Found {len(checkins)} total check-ins")
        
        # Verify checkin structure if we have data
        if len(checkins) > 0:
            checkin = checkins[0]
            expected_fields = ["id", "child_id", "pickup_code", "status", "tenant_id"]
            for field in expected_fields:
                assert field in checkin, f"Checkin should have '{field}' field"
            print(f"Sample checkin: {checkin.get('child_name', 'N/A')} - Code: {checkin.get('pickup_code')} - Status: {checkin.get('status')}")
    
    def test_get_checked_in_kids(self):
        """GET /api/admin/kids/checkins?status=checked_in - Filter by status"""
        response = self.session.get(f"{BASE_URL}/api/admin/kids/checkins", params={"status": "checked_in"})
        
        assert response.status_code == 200, f"Should return 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        checkins = data.get("checkins", [])
        
        # All returned should have status checked_in
        for checkin in checkins:
            assert checkin.get("status") == "checked_in", f"All checkins should be 'checked_in', got '{checkin.get('status')}'"
        
        print(f"Found {len(checkins)} currently checked-in children")
    
    def test_verify_valid_pickup_code(self):
        """POST /api/admin/kids/verify-pickup - Verify a valid pickup code"""
        # First, get a valid pickup code from checked-in kids
        response = self.session.get(f"{BASE_URL}/api/admin/kids/checkins", params={"status": "checked_in"})
        
        if response.status_code != 200:
            pytest.skip("Could not get checked-in kids")
        
        data = response.json()
        checkins = data.get("checkins", [])
        
        if len(checkins) == 0:
            pytest.skip("No checked-in kids to verify")
        
        valid_code = checkins[0].get("pickup_code")
        print(f"Testing with valid pickup code: {valid_code}")
        
        # Verify the code
        verify_response = self.session.post(
            f"{BASE_URL}/api/admin/kids/verify-pickup",
            json={"code": valid_code}
        )
        
        assert verify_response.status_code == 200, f"Should return 200, got {verify_response.status_code}: {verify_response.text}"
        
        result = verify_response.json()
        assert result.get("valid") == True, "Valid code should return valid=True"
        assert "checkin" in result, "Response should include checkin details"
        assert "child" in result, "Response should include child details"
        assert "parent" in result, "Response should include parent details"
        
        print(f"Verified code {valid_code}: Child = {result.get('child', {}).get('name', 'N/A')}")
    
    def test_verify_invalid_pickup_code(self):
        """POST /api/admin/kids/verify-pickup - Invalid pickup code returns valid=False"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/kids/verify-pickup",
            json={"code": "INVALID-9999"}
        )
        
        assert response.status_code == 200, f"Should return 200 even for invalid code, got {response.status_code}"
        
        result = response.json()
        assert result.get("valid") == False, "Invalid code should return valid=False"
        print("Invalid code correctly rejected")
    
    def test_verify_empty_pickup_code(self):
        """POST /api/admin/kids/verify-pickup - Empty code returns error"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/kids/verify-pickup",
            json={"code": ""}
        )
        
        assert response.status_code == 400, f"Empty code should return 400, got {response.status_code}"
        print("Empty code correctly rejected with 400")
    
    def test_checkout_child_workflow(self):
        """POST /api/admin/kids/checkins/{id}/checkout - Check out a child"""
        # Get a checked-in kid
        response = self.session.get(f"{BASE_URL}/api/admin/kids/checkins", params={"status": "checked_in"})
        
        if response.status_code != 200:
            pytest.skip("Could not get checked-in kids")
        
        data = response.json()
        checkins = data.get("checkins", [])
        
        if len(checkins) == 0:
            pytest.skip("No checked-in kids to checkout")
        
        checkin_to_checkout = checkins[0]
        checkin_id = checkin_to_checkout.get("id")
        child_name = checkin_to_checkout.get("child_name", "Unknown")
        
        print(f"Testing checkout for checkin ID: {checkin_id} - Child: {child_name}")
        
        # Checkout
        checkout_response = self.session.post(f"{BASE_URL}/api/admin/kids/checkins/{checkin_id}/checkout")
        
        assert checkout_response.status_code == 200, f"Checkout should return 200, got {checkout_response.status_code}: {checkout_response.text}"
        
        result = checkout_response.json()
        assert "message" in result, "Response should have message"
        assert result.get("checkin", {}).get("status") == "checked_out", "Checkin status should be 'checked_out'"
        
        print(f"Child checked out successfully: {result.get('message')}")
    
    def test_checkout_already_checked_out_child(self):
        """POST /api/admin/kids/checkins/{id}/checkout - Cannot checkout twice"""
        # Get a checked-out kid (from previous test or existing data)
        response = self.session.get(f"{BASE_URL}/api/admin/kids/checkins")
        
        if response.status_code != 200:
            pytest.skip("Could not get checkins")
        
        data = response.json()
        checkins = data.get("checkins", [])
        
        checked_out = [c for c in checkins if c.get("status") == "checked_out"]
        if len(checked_out) == 0:
            pytest.skip("No checked-out kids to test")
        
        checkin_id = checked_out[0].get("id")
        
        # Try to checkout again
        checkout_response = self.session.post(f"{BASE_URL}/api/admin/kids/checkins/{checkin_id}/checkout")
        
        assert checkout_response.status_code == 400, f"Should return 400 for already checked out, got {checkout_response.status_code}"
        print("Correctly rejected double checkout with 400")
    
    def test_checkout_invalid_checkin_id(self):
        """POST /api/admin/kids/checkins/{id}/checkout - Invalid ID returns 404"""
        response = self.session.post(f"{BASE_URL}/api/admin/kids/checkins/invalid-id-999/checkout")
        
        assert response.status_code == 404, f"Invalid ID should return 404, got {response.status_code}"
        print("Invalid checkin ID correctly rejected with 404")
    
    def test_direct_admin_checkin(self):
        """POST /api/admin/kids/{child_id}/checkin - Admin checks in a child directly"""
        # Get all kids to find one NOT checked in
        kids_response = self.session.get(f"{BASE_URL}/api/admin/kids/all")
        
        if kids_response.status_code != 200:
            pytest.skip("Could not get kids list")
        
        all_kids = kids_response.json().get("children", [])
        
        # Get currently checked in kids
        checkin_response = self.session.get(f"{BASE_URL}/api/admin/kids/checkins", params={"status": "checked_in"})
        checked_in_ids = [c.get("child_id") for c in checkin_response.json().get("checkins", [])]
        
        # Find a kid not currently checked in
        available_kids = [k for k in all_kids if k.get("id") not in checked_in_ids]
        
        if len(available_kids) == 0:
            pytest.skip("All kids are already checked in")
        
        kid_to_checkin = available_kids[0]
        child_id = kid_to_checkin.get("id")
        child_name = kid_to_checkin.get("name")
        
        print(f"Testing direct admin check-in for: {child_name} (ID: {child_id})")
        
        # Direct check-in
        checkin_response = self.session.post(
            f"{BASE_URL}/api/admin/kids/{child_id}/checkin",
            json={"classroom": "Sunday School"}
        )
        
        assert checkin_response.status_code == 200, f"Admin checkin should return 200, got {checkin_response.status_code}: {checkin_response.text}"
        
        result = checkin_response.json()
        assert "pickup_code" in result, "Response should include pickup_code"
        assert "checkin" in result, "Response should include checkin details"
        
        pickup_code = result.get("pickup_code")
        # Verify code format (e.g., ABC-1234)
        assert re.match(r'^[A-Z]{3}-\d{4}$', pickup_code), f"Pickup code should match pattern ABC-1234, got {pickup_code}"
        
        print(f"Admin check-in successful! Pickup code: {pickup_code}")
    
    def test_direct_checkin_already_checked_in(self):
        """POST /api/admin/kids/{child_id}/checkin - Cannot check in twice"""
        # Get a currently checked in kid
        response = self.session.get(f"{BASE_URL}/api/admin/kids/checkins", params={"status": "checked_in"})
        
        if response.status_code != 200:
            pytest.skip("Could not get checkins")
        
        checkins = response.json().get("checkins", [])
        if len(checkins) == 0:
            pytest.skip("No checked-in kids to test")
        
        child_id = checkins[0].get("child_id")
        
        # Try to check in again
        checkin_response = self.session.post(
            f"{BASE_URL}/api/admin/kids/{child_id}/checkin",
            json={"classroom": "Sunday School"}
        )
        
        assert checkin_response.status_code == 400, f"Double checkin should return 400, got {checkin_response.status_code}"
        print("Correctly rejected double check-in with 400")
    
    def test_direct_checkin_invalid_child_id(self):
        """POST /api/admin/kids/{child_id}/checkin - Invalid child ID returns 404"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/kids/invalid-child-999/checkin",
            json={"classroom": "Sunday School"}
        )
        
        assert response.status_code == 404, f"Invalid child ID should return 404, got {response.status_code}"
        print("Invalid child ID correctly rejected with 404")
    
    def test_get_checkin_history(self):
        """GET /api/admin/kids/checkins/history - Get historical check-ins"""
        response = self.session.get(f"{BASE_URL}/api/admin/kids/checkins/history", params={"days": 7})
        
        assert response.status_code == 200, f"Should return 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "checkins" in data, "Response should have 'checkins' key"
        assert "days" in data, "Response should have 'days' key"
        
        print(f"Found {len(data.get('checkins', []))} check-ins in the last {data.get('days')} days")


class TestAdminKidsCheckinAuthRequired:
    """Test that admin endpoints require authentication"""
    
    def test_get_all_kids_requires_auth(self):
        """Unauthenticated request to admin endpoint should fail"""
        response = requests.get(f"{BASE_URL}/api/admin/kids/all")
        assert response.status_code == 401, f"Should return 401 without auth, got {response.status_code}"
        print("Admin endpoint correctly requires authentication")
    
    def test_checkout_requires_auth(self):
        """Unauthenticated checkout request should fail"""
        response = requests.post(f"{BASE_URL}/api/admin/kids/checkins/test-id/checkout")
        assert response.status_code == 401, f"Should return 401 without auth, got {response.status_code}"
        print("Checkout endpoint correctly requires authentication")
    
    def test_verify_pickup_requires_auth(self):
        """Unauthenticated verify request should fail"""
        response = requests.post(f"{BASE_URL}/api/admin/kids/verify-pickup", json={"code": "ABC-1234"})
        assert response.status_code == 401, f"Should return 401 without auth, got {response.status_code}"
        print("Verify pickup endpoint correctly requires authentication")


class TestMemberCannotAccessAdminEndpoints:
    """Test that member role cannot access admin endpoints"""
    
    session = None
    
    @classmethod
    def setup_class(cls):
        """Login as member"""
        cls.session = requests.Session()
        
        login_response = cls.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "member@abundant.church", "password": "Demo2026!"}
        )
        
        if login_response.status_code == 200:
            print("Member login successful")
        else:
            print(f"Member login failed: {login_response.status_code}")
    
    def test_member_cannot_access_admin_kids_all(self):
        """Member should get 403 on admin endpoint"""
        response = self.session.get(f"{BASE_URL}/api/admin/kids/all")
        assert response.status_code == 403, f"Member should get 403, got {response.status_code}"
        print("Member correctly denied access to admin endpoint")
    
    def test_member_cannot_checkout_kids(self):
        """Member should get 403 on checkout endpoint"""
        response = self.session.post(f"{BASE_URL}/api/admin/kids/checkins/test-id/checkout")
        assert response.status_code == 403, f"Member should get 403, got {response.status_code}"
        print("Member correctly denied checkout access")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
