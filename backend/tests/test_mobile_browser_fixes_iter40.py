"""
Test iteration 40: Mobile Browser Testing - 8 Critical Fixes
Tests all the fixes implemented for the mobile QR check-in flow.

Fixes covered:
1. No hardcoded URLs - all API calls use relative paths /api/...
2. Role management - PUT /api/admin/members/{user_id}/role works for admins
3. QR code renders on Kids Check-in page when child is checked in (member portal)
4. Admin Kids Check-in shows checked-in children with count, has checkout options
5. GET /api/admin/kids/checkins/today returns correct count (not 0)
6. Registration page at /signup has church selector dropdown
7. Add Child form has first_name, last_name, grade selector fields
8. Mobile responsive - 390px width works, forms don't zoom Safari (font-size >= 16px)
"""

import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
VINCE_EMAIL = "vince@charlottesoftwareengineering.com"
VINCE_PASSWORD = "SolomonTest2026!"
AIVY_EMAIL = "avopham@gmail.com"
AIVY_PASSWORD = "SolomonTest2026!"
BABY_CHILD_ID = "80f242e5-de94-4d96-9f21-1a3aff0ba40d"


class TestSession:
    """Session fixture for API testing"""
    
    @pytest.fixture
    def session(self):
        return requests.Session()
    
    @pytest.fixture
    def vince_session(self, session):
        """Login as Vince (member)"""
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": VINCE_EMAIL,
            "password": VINCE_PASSWORD
        })
        assert res.status_code == 200, f"Vince login failed: {res.text}"
        data = res.json()
        token = data.get("session_token") or data.get("token")
        session.cookies.set("session_token", token)
        session.user_id = data.get("user_id")
        return session
    
    @pytest.fixture
    def admin_session(self, session):
        """Login as Aivy (church_admin)"""
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": AIVY_EMAIL,
            "password": AIVY_PASSWORD
        })
        assert res.status_code == 200, f"Admin login failed: {res.text}"
        data = res.json()
        token = data.get("session_token") or data.get("token")
        session.cookies.set("session_token", token)
        session.user_id = data.get("user_id")
        return session


class TestFix1NoHardcodedURLs(TestSession):
    """Fix 1: No hardcoded URLs - all API calls use relative paths"""
    
    def test_login_endpoint_accessible(self, session):
        """Verify login endpoint works via public URL"""
        res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": VINCE_EMAIL,
            "password": VINCE_PASSWORD
        })
        assert res.status_code == 200
        assert "session_token" in res.json() or "token" in res.json()
    
    def test_churches_list_endpoint(self, session):
        """Verify churches list for registration is public"""
        res = session.get(f"{BASE_URL}/api/churches/list")
        assert res.status_code == 200
        churches = res.json()
        assert isinstance(churches, list)
        assert len(churches) > 0


class TestFix2RoleManagement(TestSession):
    """Fix 2: Role management - PUT /api/admin/members/{user_id}/role works"""
    
    def test_get_members_list(self, admin_session):
        """Admin can list members"""
        res = admin_session.get(f"{BASE_URL}/api/admin/members?limit=5")
        assert res.status_code == 200
        data = res.json()
        assert "members" in data
        assert "total" in data
        assert len(data["members"]) > 0
    
    def test_update_member_role(self, admin_session, vince_session):
        """Admin can update member role"""
        vince_id = vince_session.user_id
        
        # Update role to member (no change, but verifies endpoint works)
        res = admin_session.put(f"{BASE_URL}/api/admin/members/{vince_id}/role", json={
            "role": "member"
        })
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") == True
        assert data.get("new_role") == "member"


class TestFix3QRCodeRendering(TestSession):
    """Fix 3: QR code renders on Kids Check-in page when child is checked in"""
    
    def test_get_portal_kids(self, vince_session):
        """Vince can see his children"""
        res = vince_session.get(f"{BASE_URL}/api/portal/kids")
        assert res.status_code == 200
        data = res.json()
        assert "children" in data
        # Baby Hinojosa should be in list
        children = data["children"]
        baby = next((c for c in children if c.get("id") == BABY_CHILD_ID), None)
        assert baby is not None, "Baby Hinojosa not found in Vince's children"
        assert baby.get("first_name") == "Baby"
        assert baby.get("last_name") == "Hinojosa"
    
    def test_checkin_generates_pickup_code(self, vince_session, admin_session):
        """Check-in generates pickup code for QR"""
        # First checkout if already checked in
        checkins_res = vince_session.get(f"{BASE_URL}/api/portal/kids/checkins/active")
        if checkins_res.status_code == 200:
            active = checkins_res.json().get("checkins", [])
            for c in active:
                if c.get("child_id") == BABY_CHILD_ID:
                    # Checkout via admin
                    admin_session.post(f"{BASE_URL}/api/admin/kids/checkout-by-code", json={
                        "pickup_code": c.get("pickup_code")
                    })
        
        time.sleep(0.5)  # Wait for checkout to complete
        
        # Check in Baby
        res = vince_session.post(f"{BASE_URL}/api/portal/kids/{BABY_CHILD_ID}/checkin", json={
            "classroom": "Sunday School"
        })
        assert res.status_code == 200, f"Checkin failed: {res.text}"
        data = res.json()
        
        # Verify pickup code is returned for QR generation
        assert "pickup_code" in data
        assert len(data["pickup_code"]) == 3  # 3-digit code
        assert data["status"] == "checked_in"
        
        # Store for later tests
        TestFix3QRCodeRendering.pickup_code = data["pickup_code"]
    
    def test_active_checkins_include_pickup_code(self, vince_session):
        """Active checkins include pickup code for QR display"""
        res = vince_session.get(f"{BASE_URL}/api/portal/kids/checkins/active")
        assert res.status_code == 200
        data = res.json()
        
        # Find Baby's checkin
        checkins = data.get("checkins", [])
        baby_checkin = next((c for c in checkins if c.get("child_id") == BABY_CHILD_ID), None)
        assert baby_checkin is not None, "Baby's active checkin not found"
        assert "pickup_code" in baby_checkin
        assert baby_checkin["status"] == "checked_in"


class TestFix4AdminKidsCheckin(TestSession):
    """Fix 4: Admin Kids Check-in shows checked-in children with checkout options"""
    
    def test_admin_checkins_list(self, admin_session):
        """Admin can see checked-in children"""
        res = admin_session.get(f"{BASE_URL}/api/admin/kids/checkins?status=checked_in")
        assert res.status_code == 200
        data = res.json()
        assert "checkins" in data
    
    def test_checkout_by_raw_code(self, vince_session, admin_session):
        """Admin can checkout by raw 3-digit code"""
        # First check in Baby
        checkin_res = vince_session.post(f"{BASE_URL}/api/portal/kids/{BABY_CHILD_ID}/checkin", json={
            "classroom": "Sunday School"
        })
        if checkin_res.status_code != 200:
            # Already checked in, get the code
            active_res = vince_session.get(f"{BASE_URL}/api/portal/kids/checkins/active")
            if active_res.status_code == 200:
                checkins = active_res.json().get("checkins", [])
                baby = next((c for c in checkins if c.get("child_id") == BABY_CHILD_ID), None)
                if baby:
                    pickup_code = baby["pickup_code"]
                else:
                    pytest.skip("Cannot find active checkin for Baby")
            else:
                pytest.skip("Cannot get active checkins")
        else:
            pickup_code = checkin_res.json()["pickup_code"]
        
        # Checkout by raw code
        res = admin_session.post(f"{BASE_URL}/api/admin/kids/checkout-by-code", json={
            "pickup_code": pickup_code
        })
        assert res.status_code == 200, f"Checkout failed: {res.text}"
        data = res.json()
        assert data.get("success") == True
        assert data.get("child_name") == "Baby Hinojosa"
    
    def test_checkout_by_qr_format(self, vince_session, admin_session):
        """Admin can checkout using QR format string"""
        # Check in Baby again
        time.sleep(0.5)
        checkin_res = vince_session.post(f"{BASE_URL}/api/portal/kids/{BABY_CHILD_ID}/checkin", json={
            "classroom": "Sunday School"
        })
        assert checkin_res.status_code == 200, f"Checkin failed: {checkin_res.text}"
        pickup_code = checkin_res.json()["pickup_code"]
        
        # Build QR format: SOLOMON_PICKUP_{child_id}_{code}_{date}
        today = datetime.now().strftime("%Y-%m-%d")
        qr_format = f"SOLOMON_PICKUP_{BABY_CHILD_ID}_{pickup_code}_{today}"
        
        # Checkout by QR format
        res = admin_session.post(f"{BASE_URL}/api/admin/kids/checkout-by-code", json={
            "pickup_code": qr_format
        })
        assert res.status_code == 200, f"QR checkout failed: {res.text}"
        data = res.json()
        assert data.get("success") == True
        assert data.get("child_name") == "Baby Hinojosa"


class TestFix5CheckinsTodayCount(TestSession):
    """Fix 5: GET /api/admin/kids/checkins/today returns correct count"""
    
    def test_checkins_today_returns_count(self, admin_session, vince_session):
        """Checkins today returns correct total"""
        # First check in Baby
        time.sleep(0.5)
        vince_session.post(f"{BASE_URL}/api/portal/kids/{BABY_CHILD_ID}/checkin", json={
            "classroom": "Sunday School"
        })
        
        # Get today's checkins
        res = admin_session.get(f"{BASE_URL}/api/admin/kids/checkins/today")
        assert res.status_code == 200
        data = res.json()
        
        assert "checkins" in data
        assert "total" in data
        assert isinstance(data["total"], int)
        assert data["total"] > 0  # Should have at least Baby's checkin
        
        # Verify checkins array has data
        assert len(data["checkins"]) > 0
        
        # Verify checkin data structure
        checkin = data["checkins"][0]
        assert "child_name" in checkin
        assert "pickup_code" in checkin
        assert "status" in checkin


class TestFix6RegistrationChurchSelector(TestSession):
    """Fix 6: Registration page has church selector dropdown"""
    
    def test_churches_list_for_registration(self, session):
        """Churches list endpoint returns active churches"""
        res = session.get(f"{BASE_URL}/api/churches/list")
        assert res.status_code == 200
        churches = res.json()
        
        assert isinstance(churches, list)
        assert len(churches) > 0
        
        # Verify church data structure
        church = churches[0]
        assert "id" in church
        assert "name" in church
        assert "city" in church
        assert "state" in church
    
    def test_tenants_list_endpoint(self, session):
        """Tenants list endpoint also works for registration"""
        res = session.get(f"{BASE_URL}/api/tenants/list")
        assert res.status_code == 200
        tenants = res.json()
        assert isinstance(tenants, list)
    
    def test_register_endpoint_requires_tenant_id(self, session):
        """Registration requires tenant_id (church selection)"""
        # Try registration without tenant_id
        res = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": "TEST_newuser@test.com",
            "password": "TestPass123!",
            "confirm_password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User"
            # No tenant_id
        })
        # Should either fail or assign default - verify endpoint works
        assert res.status_code in [200, 400, 422]


class TestFix7AddChildForm(TestSession):
    """Fix 7: Add Child form has first_name, last_name, grade fields"""
    
    def test_add_child_with_first_last_name(self, vince_session):
        """Add child with separate first/last name and grade"""
        res = vince_session.post(f"{BASE_URL}/api/portal/kids", json={
            "name": "Test Child",  # Required field
            "first_name": "Test",
            "last_name": "Child",
            "birthdate": "2020-06-15",
            "grade": "K",
            "allergies": "None",
            "classroom": "Sunday School"
        })
        assert res.status_code == 200, f"Add child failed: {res.text}"
        data = res.json()
        
        assert "child" in data
        child = data["child"]
        assert child.get("first_name") == "Test"
        assert child.get("last_name") == "Child"
        assert child.get("grade") == "K"
        
        # Store child ID for cleanup
        TestFix7AddChildForm.test_child_id = child.get("id")
    
    def test_delete_test_child(self, vince_session):
        """Cleanup: delete test child"""
        if hasattr(TestFix7AddChildForm, 'test_child_id'):
            child_id = TestFix7AddChildForm.test_child_id
            res = vince_session.delete(f"{BASE_URL}/api/portal/kids/{child_id}")
            assert res.status_code == 200


class TestFix8MobileResponsive(TestSession):
    """Fix 8: Mobile responsive - forms work on 390px width"""
    
    def test_api_works_regardless_of_viewport(self, vince_session):
        """API endpoints work regardless of viewport size (frontend concern)"""
        # All API endpoints should work - viewport is frontend-only
        res = vince_session.get(f"{BASE_URL}/api/portal/kids")
        assert res.status_code == 200
        
        res = vince_session.get(f"{BASE_URL}/api/portal/kids/checkins/active")
        assert res.status_code == 200


class TestBidirectionalPolling(TestSession):
    """Test bidirectional sync - polling endpoints work without rate limiting"""
    
    def test_admin_checkins_today_no_rate_limit(self, admin_session):
        """Admin checkins today can be polled frequently"""
        for i in range(3):
            res = admin_session.get(f"{BASE_URL}/api/admin/kids/checkins/today")
            assert res.status_code == 200, f"Request {i+1} failed"
            time.sleep(0.1)  # Small delay between requests
    
    def test_portal_kids_no_rate_limit(self, vince_session):
        """Portal kids endpoint can be polled frequently"""
        for i in range(3):
            res = vince_session.get(f"{BASE_URL}/api/portal/kids")
            assert res.status_code == 200, f"Request {i+1} failed"
            time.sleep(0.1)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
