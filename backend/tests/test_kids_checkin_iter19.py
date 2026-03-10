"""
Kids Check-in Production Readiness Tests - Iteration 19
Tests for bidirectional real-time sync and admin register family feature

Features tested:
1. Admin Dashboard Kids Check-in endpoints
2. Register New Family modal (admin creates parent + child)
3. Member Portal Kids Check-in endpoints
4. Bidirectional sync (parent check-in reflects on admin within 2s)
5. Pickup code verification workflow
6. Checkout workflow
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAdminKidsCheckinDashboard:
    """Admin Kids Check-in Dashboard Tests - /kids-checkin"""
    
    session = None
    
    @classmethod
    def setup_class(cls):
        """Login as admin"""
        cls.session = requests.Session()
        response = cls.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@abundant.church", "password": "Demo2026!"}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        print("Admin login successful")
    
    def test_get_checked_in_children(self):
        """GET /api/admin/kids/checkins?status=checked_in - Core polling endpoint for LIVE sync"""
        response = self.session.get(f"{BASE_URL}/api/admin/kids/checkins", params={"status": "checked_in"})
        
        assert response.status_code == 200, f"Should return 200, got {response.status_code}"
        data = response.json()
        assert "checkins" in data, "Response should have 'checkins' key"
        
        checkins = data["checkins"]
        print(f"Currently {len(checkins)} children checked in")
        
        # Verify data structure for LIVE indicator display
        for checkin in checkins:
            assert "pickup_code" in checkin, "Each checkin should have pickup_code"
            assert "child_name" in checkin, "Each checkin should have child_name"
            assert "checked_in_at" in checkin, "Each checkin should have checked_in_at"
            print(f"  - {checkin.get('child_name')}: {checkin.get('pickup_code')}")
    
    def test_get_all_registered_kids(self):
        """GET /api/admin/kids/all - For Check In tab"""
        response = self.session.get(f"{BASE_URL}/api/admin/kids/all")
        
        assert response.status_code == 200, f"Should return 200, got {response.status_code}"
        data = response.json()
        assert "children" in data, "Response should have 'children' key"
        
        children = data["children"]
        print(f"Total {len(children)} registered children")
        
        # Verify enriched data with parent info
        if len(children) > 0:
            child = children[0]
            assert "id" in child, "Child should have id"
            assert "name" in child, "Child should have name"
            assert "parent_name" in child, "Child should have parent_name (enriched)"


class TestRegisterNewFamily:
    """Admin Register New Family Feature - Modal on /kids-checkin"""
    
    session = None
    test_email = f"TEST_family_{uuid.uuid4().hex[:6]}@test.com"
    test_parent_name = f"TEST_Parent_{uuid.uuid4().hex[:4]}"
    test_child_name = f"TEST_Child_{uuid.uuid4().hex[:4]}"
    
    @classmethod
    def setup_class(cls):
        """Login as admin"""
        cls.session = requests.Session()
        response = cls.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@abundant.church", "password": "Demo2026!"}
        )
        assert response.status_code == 200, "Admin login should succeed"
    
    def test_register_new_family_success(self):
        """POST /api/admin/kids/register-family - Admin registers walk-in family"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/kids/register-family",
            json={
                "parentName": self.test_parent_name,
                "parentEmail": self.test_email,
                "parentPhone": "555-123-4567",
                "childName": self.test_child_name,
                "childBirthdate": "2020-06-15",
                "childAllergies": "Peanuts",
                "childNotes": "TEST - can be deleted"
            }
        )
        
        assert response.status_code == 200, f"Register family should return 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should have message"
        assert self.test_parent_name in data.get("message", ""), "Message should include parent name"
        assert self.test_child_name in data.get("message", ""), "Message should include child name"
        
        print(f"Registered family: {self.test_parent_name} & {self.test_child_name}")
    
    def test_verify_registered_child_appears(self):
        """Verify newly registered child appears in admin list"""
        response = self.session.get(f"{BASE_URL}/api/admin/kids/all")
        
        assert response.status_code == 200
        children = response.json().get("children", [])
        
        found = any(c.get("name") == self.test_child_name for c in children)
        assert found, f"Newly registered child {self.test_child_name} should appear in admin list"
        
        print(f"Verified {self.test_child_name} appears in admin children list")
    
    def test_register_duplicate_child_rejected(self):
        """POST /api/admin/kids/register-family - Duplicate child for same parent rejected"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/kids/register-family",
            json={
                "parentName": self.test_parent_name,
                "parentEmail": self.test_email,
                "childName": self.test_child_name  # Same child name
            }
        )
        
        assert response.status_code == 400, f"Duplicate should return 400, got {response.status_code}"
        print("Duplicate family registration correctly rejected")
    
    def test_register_missing_required_fields(self):
        """POST /api/admin/kids/register-family - Missing fields return error"""
        # Missing childName
        response = self.session.post(
            f"{BASE_URL}/api/admin/kids/register-family",
            json={
                "parentName": "Test Parent",
                "parentEmail": "test@example.com"
            }
        )
        
        assert response.status_code == 422, f"Missing childName should return 422, got {response.status_code}"
        print("Missing required fields correctly rejected")


class TestMemberPortalKidsCheckin:
    """Member Portal Kids Check-in - /portal/kids"""
    
    session = None
    
    @classmethod
    def setup_class(cls):
        """Login as member"""
        cls.session = requests.Session()
        response = cls.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "member@abundant.church", "password": "Demo2026!"}
        )
        assert response.status_code == 200, "Member login should succeed"
        print("Member login successful")
    
    def test_get_my_children(self):
        """GET /api/portal/kids - Parent gets their children"""
        response = self.session.get(f"{BASE_URL}/api/portal/kids")
        
        assert response.status_code == 200, f"Should return 200, got {response.status_code}"
        data = response.json()
        assert "children" in data, "Response should have 'children' key"
        
        children = data["children"]
        print(f"Member has {len(children)} registered children")
        
        for child in children:
            print(f"  - {child.get('name')}: {child.get('birthdate', 'N/A')}")
    
    def test_get_active_checkins(self):
        """GET /api/portal/kids/checkins/active - Parent sees their checked-in children"""
        response = self.session.get(f"{BASE_URL}/api/portal/kids/checkins/active")
        
        assert response.status_code == 200, f"Should return 200, got {response.status_code}"
        data = response.json()
        assert "checkins" in data, "Response should have 'checkins' key"
        
        checkins = data["checkins"]
        print(f"Member has {len(checkins)} active check-ins")
        
        # Verify pickup codes are visible to parent
        for checkin in checkins:
            assert "pickup_code" in checkin, "Parent should see pickup_code"
            print(f"  - {checkin.get('child_name')}: Pickup Code = {checkin.get('pickup_code')}")


class TestBidirectionalSync:
    """Test bidirectional sync between parent portal and admin dashboard"""
    
    member_session = None
    admin_session = None
    test_child_id = None
    created_checkin_id = None
    
    @classmethod
    def setup_class(cls):
        """Login as both member and admin"""
        cls.member_session = requests.Session()
        cls.admin_session = requests.Session()
        
        # Member login
        member_login = cls.member_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "member@abundant.church", "password": "Demo2026!"}
        )
        assert member_login.status_code == 200, "Member login should succeed"
        
        # Admin login
        admin_login = cls.admin_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@abundant.church", "password": "Demo2026!"}
        )
        assert admin_login.status_code == 200, "Admin login should succeed"
        
        print("Both member and admin logged in successfully")
    
    def test_01_get_member_child_for_test(self):
        """Get a member's child for sync testing"""
        response = self.member_session.get(f"{BASE_URL}/api/portal/kids")
        assert response.status_code == 200
        
        children = response.json().get("children", [])
        
        # First check if any children are already checked in
        checkin_response = self.member_session.get(f"{BASE_URL}/api/portal/kids/checkins/active")
        active_checkins = checkin_response.json().get("checkins", [])
        checked_in_ids = [c.get("child_id") for c in active_checkins]
        
        # Find child not checked in
        available = [c for c in children if c.get("id") not in checked_in_ids]
        
        if len(available) == 0:
            pytest.skip("No available children to test sync (all checked in)")
        
        TestBidirectionalSync.test_child_id = available[0].get("id")
        print(f"Will test sync with child: {available[0].get('name')} (ID: {TestBidirectionalSync.test_child_id})")
    
    def test_02_admin_baseline_count(self):
        """Record admin's current checked-in count"""
        response = self.admin_session.get(f"{BASE_URL}/api/admin/kids/checkins", params={"status": "checked_in"})
        assert response.status_code == 200
        
        self.admin_baseline_count = len(response.json().get("checkins", []))
        print(f"Admin baseline: {self.admin_baseline_count} children checked in")
    
    def test_03_parent_checks_in_child(self):
        """POST /api/portal/kids/{child_id}/checkin - Parent initiates check-in"""
        if not TestBidirectionalSync.test_child_id:
            pytest.skip("No child ID available")
        
        response = self.member_session.post(
            f"{BASE_URL}/api/portal/kids/{TestBidirectionalSync.test_child_id}/checkin",
            json={"classroom": "Sunday School"}
        )
        
        assert response.status_code == 200, f"Check-in should succeed, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "pickup_code" in data, "Response should have pickup_code"
        
        pickup_code = data.get("pickup_code")
        TestBidirectionalSync.created_checkin_id = data.get("checkin", {}).get("id")
        
        print(f"Parent check-in successful! Pickup code: {pickup_code}")
    
    def test_04_admin_sees_new_checkin_immediately(self):
        """Admin dashboard should see new check-in within 2 seconds (bidirectional sync)"""
        if not TestBidirectionalSync.test_child_id:
            pytest.skip("No child ID available")
        
        # Poll like the dashboard does every 2 seconds
        time.sleep(1)  # Wait a moment for DB write
        
        response = self.admin_session.get(f"{BASE_URL}/api/admin/kids/checkins", params={"status": "checked_in"})
        assert response.status_code == 200
        
        checkins = response.json().get("checkins", [])
        found = any(c.get("child_id") == TestBidirectionalSync.test_child_id for c in checkins)
        
        assert found, f"Admin should see child {TestBidirectionalSync.test_child_id} checked in immediately"
        
        # Find the checkin for this child
        child_checkin = next(c for c in checkins if c.get("child_id") == TestBidirectionalSync.test_child_id)
        print(f"BIDIRECTIONAL SYNC VERIFIED: Admin sees {child_checkin.get('child_name')} - Pickup: {child_checkin.get('pickup_code')}")
    
    def test_05_cleanup_checkout(self):
        """Checkout the child to cleanup test data"""
        if not TestBidirectionalSync.created_checkin_id:
            pytest.skip("No checkin to cleanup")
        
        response = self.admin_session.post(
            f"{BASE_URL}/api/admin/kids/checkins/{TestBidirectionalSync.created_checkin_id}/checkout"
        )
        
        if response.status_code == 200:
            print(f"Cleanup: Checked out test checkin {TestBidirectionalSync.created_checkin_id}")
        else:
            print(f"Cleanup note: Could not checkout - {response.status_code}")


class TestPickupCodeVerification:
    """Test pickup code verification workflow for admin checkout"""
    
    session = None
    
    @classmethod
    def setup_class(cls):
        """Login as admin"""
        cls.session = requests.Session()
        response = cls.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@abundant.church", "password": "Demo2026!"}
        )
        assert response.status_code == 200
    
    def test_verify_valid_pickup_code(self):
        """POST /api/admin/kids/verify-pickup - Valid code shows child & parent info"""
        # Get a checked-in child's pickup code
        response = self.session.get(f"{BASE_URL}/api/admin/kids/checkins", params={"status": "checked_in"})
        
        if response.status_code != 200:
            pytest.skip("Could not get checkins")
        
        checkins = response.json().get("checkins", [])
        if len(checkins) == 0:
            pytest.skip("No checked-in children to test")
        
        pickup_code = checkins[0].get("pickup_code")
        
        # Verify the code
        verify_response = self.session.post(
            f"{BASE_URL}/api/admin/kids/verify-pickup",
            json={"code": pickup_code}
        )
        
        assert verify_response.status_code == 200
        result = verify_response.json()
        
        assert result.get("valid") == True, "Valid code should return valid=True"
        assert "child" in result, "Should include child info"
        assert "parent" in result, "Should include parent info"
        
        print(f"Verified code {pickup_code}:")
        print(f"  Child: {result.get('child', {}).get('name')}")
        print(f"  Parent: {result.get('parent', {}).get('name')}")
    
    def test_verify_invalid_code(self):
        """POST /api/admin/kids/verify-pickup - Invalid code returns valid=False"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/kids/verify-pickup",
            json={"code": "XXX-9999"}
        )
        
        assert response.status_code == 200
        assert response.json().get("valid") == False
        print("Invalid code correctly rejected")


class TestAdminDirectCheckin:
    """Test admin walk-in check-in from Check In tab"""
    
    session = None
    test_checkin_id = None
    
    @classmethod
    def setup_class(cls):
        """Login as admin"""
        cls.session = requests.Session()
        response = cls.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@abundant.church", "password": "Demo2026!"}
        )
        assert response.status_code == 200
    
    def test_admin_direct_checkin(self):
        """POST /api/admin/kids/{child_id}/checkin - Admin walk-in check-in"""
        # Get available kids
        kids_response = self.session.get(f"{BASE_URL}/api/admin/kids/all")
        all_kids = kids_response.json().get("children", [])
        
        # Get checked in kids
        checkin_response = self.session.get(f"{BASE_URL}/api/admin/kids/checkins", params={"status": "checked_in"})
        checked_in_ids = [c.get("child_id") for c in checkin_response.json().get("checkins", [])]
        
        # Find available kid
        available = [k for k in all_kids if k.get("id") not in checked_in_ids]
        
        if len(available) == 0:
            pytest.skip("No available kids for direct check-in test")
        
        child_id = available[0].get("id")
        child_name = available[0].get("name")
        
        # Direct check-in
        response = self.session.post(
            f"{BASE_URL}/api/admin/kids/{child_id}/checkin",
            json={"classroom": "Sunday School"}
        )
        
        assert response.status_code == 200, f"Direct check-in should succeed: {response.text}"
        
        data = response.json()
        assert "pickup_code" in data
        
        TestAdminDirectCheckin.test_checkin_id = data.get("checkin", {}).get("id")
        print(f"Admin direct check-in successful: {child_name} - Code: {data.get('pickup_code')}")
    
    def test_admin_checkout(self):
        """POST /api/admin/kids/checkins/{id}/checkout - Checkout child"""
        if not TestAdminDirectCheckin.test_checkin_id:
            pytest.skip("No checkin to checkout")
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/kids/checkins/{TestAdminDirectCheckin.test_checkin_id}/checkout"
        )
        
        assert response.status_code == 200, f"Checkout should succeed: {response.text}"
        
        result = response.json()
        assert result.get("checkin", {}).get("status") == "checked_out"
        print(f"Child checked out successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
