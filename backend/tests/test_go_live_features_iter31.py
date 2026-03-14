"""
Test Suite for Solomon AI Church Management System - Iteration 31
Go-Live Backend Preparation: 5 New Feature Sets

Features tested:
1. Geofencing Check-in (admin config + portal check-in with haversine validation)
2. Giving Nudge (contextual nudges for cafe, merch, general)
3. Admin Announcements CRUD
4. Admin Volunteer Management CRUD (opportunities + signups)
5. Media File Uploads (multipart upload, list, serve, delete)
6. Portal Payment Methods (Bearer token auth)
7. Portal routes (announcements, volunteer opportunities, volunteer signup)
8. Role-based access control (member cannot access admin endpoints -> 403)
"""

import pytest
import requests
import os
import io

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable is required")

# Test credentials
ADMIN_EMAIL = "admin@abundant.church"
ADMIN_PASSWORD = "Demo2026!"
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = "Demo2026!"
PLATFORM_ADMIN_EMAIL = "admin@solomon.ai"
PLATFORM_ADMIN_PASSWORD = "Demo2026!"


class TestAuth:
    """Helper class to get authentication tokens"""

    @staticmethod
    def get_token(email: str, password: str) -> str:
        """Login and get session token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        assert response.status_code == 200, f"Login failed for {email}: {response.text}"
        data = response.json()
        return data.get("session_token") or data.get("token")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token for tests"""
    return TestAuth.get_token(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def member_token():
    """Get member token for tests"""
    return TestAuth.get_token(MEMBER_EMAIL, MEMBER_PASSWORD)


@pytest.fixture(scope="module")
def platform_admin_token():
    """Get platform admin token for tests"""
    return TestAuth.get_token(PLATFORM_ADMIN_EMAIL, PLATFORM_ADMIN_PASSWORD)


# ============== FEATURE 1: GEOFENCING CHECK-IN ==============

class TestGeofenceConfig:
    """Test admin geofence configuration endpoints"""

    def test_get_geofence_config(self, admin_token):
        """GET /api/admin/geofence/config - returns geofence zones for admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/geofence/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "config" in data
        config = data["config"]
        assert "zones" in config
        assert isinstance(config["zones"], list)
        # Default zone should be at lat=31.7619, lng=-106.485
        if len(config["zones"]) > 0:
            zone = config["zones"][0]
            assert "latitude" in zone
            assert "longitude" in zone
            assert "radius_meters" in zone
        print(f"PASS: Geofence config retrieved with {len(config['zones'])} zones")

    def test_update_geofence_config(self, admin_token):
        """PUT /api/admin/geofence/config - updates geofence zones"""
        new_config = {
            "zones": [
                {
                    "id": "zone_test",
                    "name": "Test Campus",
                    "latitude": 31.7619,
                    "longitude": -106.4850,
                    "radius_meters": 300.0,
                    "is_enabled": True
                }
            ],
            "auto_checkin_enabled": True
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/geofence/config",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=new_config
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "config" in data
        print("PASS: Geofence config updated successfully")

    def test_member_cannot_access_geofence_config(self, member_token):
        """Member role cannot access admin geofence endpoint (403)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/geofence/config",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("PASS: Member correctly denied access to admin geofence config")


class TestGeofenceCheckin:
    """Test portal geofence check-in endpoint"""

    def test_geofence_checkin_inside_zone(self, member_token, admin_token):
        """POST /api/portal/attendance/geofence-checkin - inside zone -> success"""
        # First ensure geofence is configured
        requests.put(
            f"{BASE_URL}/api/admin/geofence/config",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "zones": [{
                    "id": "zone_main",
                    "name": "Main Campus",
                    "latitude": 31.7619,
                    "longitude": -106.4850,
                    "radius_meters": 200.0,
                    "is_enabled": True
                }],
                "auto_checkin_enabled": True
            }
        )
        
        # Check in with exact coordinates (inside zone)
        response = requests.post(
            f"{BASE_URL}/api/portal/attendance/geofence-checkin",
            headers={"Authorization": f"Bearer {member_token}"},
            json={"latitude": 31.7619, "longitude": -106.4850}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "checked_in" in data
        assert data["checked_in"] is True
        assert "zone" in data or "message" in data
        print(f"PASS: Geofence check-in inside zone - {data.get('message', 'success')}")

    def test_geofence_checkin_outside_zone(self, member_token):
        """POST /api/portal/attendance/geofence-checkin - outside zone -> failure"""
        # Check in with coordinates far outside zone (lat=0, lng=0)
        response = requests.post(
            f"{BASE_URL}/api/portal/attendance/geofence-checkin",
            headers={"Authorization": f"Bearer {member_token}"},
            json={"latitude": 0.0, "longitude": 0.0}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "checked_in" in data
        assert data["checked_in"] is False
        assert "message" in data
        print(f"PASS: Geofence check-in outside zone correctly rejected - {data['message']}")


# ============== FEATURE 2: GIVING NUDGE ==============

class TestGivingNudge:
    """Test giving nudge endpoints"""

    def test_giving_nudge_cafe(self, member_token):
        """GET /api/portal/giving/nudge?context=cafe - returns cafe giving nudge"""
        response = requests.get(
            f"{BASE_URL}/api/portal/giving/nudge?context=cafe",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "nudge" in data
        nudge = data["nudge"]
        assert "title" in nudge
        assert "message" in nudge
        assert "suggested_amounts" in nudge
        assert "cta" in nudge
        print(f"PASS: Cafe nudge - {nudge['title']}")

    def test_giving_nudge_merch(self, member_token):
        """GET /api/portal/giving/nudge?context=merch - returns merch giving nudge"""
        response = requests.get(
            f"{BASE_URL}/api/portal/giving/nudge?context=merch",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "nudge" in data
        nudge = data["nudge"]
        assert "title" in nudge
        assert "message" in nudge
        print(f"PASS: Merch nudge - {nudge['title']}")

    def test_giving_nudge_general(self, member_token):
        """GET /api/portal/giving/nudge - returns general giving nudge"""
        response = requests.get(
            f"{BASE_URL}/api/portal/giving/nudge",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "nudge" in data
        nudge = data["nudge"]
        assert "title" in nudge
        assert "ytd_giving" in nudge  # YTD giving should be included
        print(f"PASS: General nudge - {nudge['title']}, YTD: ${nudge['ytd_giving']}")


# ============== FEATURE 3: ADMIN ANNOUNCEMENTS CRUD ==============

class TestAdminAnnouncements:
    """Test admin announcements CRUD operations"""
    
    created_announcement_id = None

    def test_get_admin_announcements(self, admin_token):
        """GET /api/admin/announcements - list all announcements"""
        response = requests.get(
            f"{BASE_URL}/api/admin/announcements",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "announcements" in data
        assert isinstance(data["announcements"], list)
        print(f"PASS: Retrieved {len(data['announcements'])} announcements")

    def test_create_admin_announcement(self, admin_token):
        """POST /api/admin/announcements - create announcement"""
        payload = {
            "title": "TEST_Announcement_Iter31",
            "body": "This is a test announcement for iteration 31",
            "priority": "high",
            "expires_at": "2026-12-31T23:59:59Z"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/announcements",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "announcement" in data
        announcement = data["announcement"]
        assert announcement["title"] == payload["title"]
        assert announcement["body"] == payload["body"]
        TestAdminAnnouncements.created_announcement_id = announcement["id"]
        print(f"PASS: Created announcement with ID {announcement['id']}")

    def test_update_admin_announcement(self, admin_token):
        """PUT /api/admin/announcements/{id} - update announcement"""
        if not TestAdminAnnouncements.created_announcement_id:
            pytest.skip("No announcement created to update")
        
        payload = {
            "title": "TEST_Announcement_Updated",
            "priority": "normal"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/announcements/{TestAdminAnnouncements.created_announcement_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
        print("PASS: Announcement updated successfully")

    def test_delete_admin_announcement(self, admin_token):
        """DELETE /api/admin/announcements/{id} - delete announcement"""
        if not TestAdminAnnouncements.created_announcement_id:
            pytest.skip("No announcement created to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/announcements/{TestAdminAnnouncements.created_announcement_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
        print("PASS: Announcement deleted successfully")

    def test_member_cannot_access_admin_announcements(self, member_token):
        """Member role cannot access admin announcements endpoint (403)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/announcements",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("PASS: Member correctly denied access to admin announcements")


# ============== FEATURE 4: ADMIN VOLUNTEER MANAGEMENT ==============

class TestAdminVolunteerOpportunities:
    """Test admin volunteer opportunities CRUD"""
    
    created_opportunity_id = None

    def test_get_admin_volunteer_opportunities(self, admin_token):
        """GET /api/admin/volunteer/opportunities - list volunteer opportunities"""
        response = requests.get(
            f"{BASE_URL}/api/admin/volunteer/opportunities",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "opportunities" in data
        assert isinstance(data["opportunities"], list)
        print(f"PASS: Retrieved {len(data['opportunities'])} volunteer opportunities")

    def test_create_admin_volunteer_opportunity(self, admin_token):
        """POST /api/admin/volunteer/opportunities - create opportunity"""
        payload = {
            "title": "TEST_Volunteer_Opportunity_Iter31",
            "description": "Test volunteer opportunity for iteration 31",
            "schedule": "Sundays 9AM-12PM",
            "location": "Main Lobby",
            "spots_available": 5,
            "ministry_area": "Hospitality"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/volunteer/opportunities",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "opportunity" in data
        opportunity = data["opportunity"]
        assert opportunity["title"] == payload["title"]
        TestAdminVolunteerOpportunities.created_opportunity_id = opportunity["id"]
        print(f"PASS: Created volunteer opportunity with ID {opportunity['id']}")

    def test_update_admin_volunteer_opportunity(self, admin_token):
        """PUT /api/admin/volunteer/opportunities/{id} - update opportunity"""
        if not TestAdminVolunteerOpportunities.created_opportunity_id:
            pytest.skip("No opportunity created to update")
        
        payload = {
            "title": "TEST_Volunteer_Updated",
            "spots_available": 10
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/volunteer/opportunities/{TestAdminVolunteerOpportunities.created_opportunity_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print("PASS: Volunteer opportunity updated successfully")

    def test_delete_admin_volunteer_opportunity(self, admin_token):
        """DELETE /api/admin/volunteer/opportunities/{id} - delete opportunity"""
        if not TestAdminVolunteerOpportunities.created_opportunity_id:
            pytest.skip("No opportunity created to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/volunteer/opportunities/{TestAdminVolunteerOpportunities.created_opportunity_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print("PASS: Volunteer opportunity deleted successfully")

    def test_member_cannot_access_admin_volunteer_opportunities(self, member_token):
        """Member role cannot access admin volunteer endpoint (403)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/volunteer/opportunities",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("PASS: Member correctly denied access to admin volunteer opportunities")


class TestAdminVolunteerSignups:
    """Test admin volunteer signups management"""

    def test_get_admin_volunteer_signups(self, admin_token):
        """GET /api/admin/volunteer/signups - list signups"""
        response = requests.get(
            f"{BASE_URL}/api/admin/volunteer/signups",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "signups" in data
        assert isinstance(data["signups"], list)
        print(f"PASS: Retrieved {len(data['signups'])} volunteer signups")

    def test_update_admin_volunteer_signup(self, admin_token, member_token):
        """PUT /api/admin/volunteer/signups/{id} - update signup status"""
        # First create an opportunity and have member sign up
        opp_response = requests.post(
            f"{BASE_URL}/api/admin/volunteer/opportunities",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "TEST_Signup_Test_Opportunity",
                "description": "Test opportunity for signup",
                "schedule": "Sundays",
                "location": "Lobby",
                "spots_available": 5,
                "ministry_area": "Test"
            }
        )
        if opp_response.status_code != 200:
            pytest.skip("Could not create opportunity for signup test")
        
        opportunity_id = opp_response.json()["opportunity"]["id"]
        
        # Member signs up
        signup_response = requests.post(
            f"{BASE_URL}/api/portal/volunteer/signup",
            headers={"Authorization": f"Bearer {member_token}"},
            json={"opportunity_id": opportunity_id}
        )
        if signup_response.status_code != 200:
            # Clean up
            requests.delete(
                f"{BASE_URL}/api/admin/volunteer/opportunities/{opportunity_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            pytest.skip("Could not create signup for test")
        
        signup_id = signup_response.json()["signup"]["id"]
        
        # Admin updates signup status
        update_response = requests.put(
            f"{BASE_URL}/api/admin/volunteer/signups/{signup_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "approved", "admin_notes": "Test approved"}
        )
        assert update_response.status_code == 200, f"Failed: {update_response.text}"
        print("PASS: Volunteer signup status updated successfully")
        
        # Clean up
        requests.delete(
            f"{BASE_URL}/api/admin/volunteer/opportunities/{opportunity_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )


# ============== FEATURE 5: MEDIA FILE UPLOADS ==============

class TestMediaUploads:
    """Test admin media file upload endpoints"""
    
    uploaded_file_id = None

    def test_upload_media_file(self, admin_token):
        """POST /api/admin/media/upload - upload a file"""
        # Create a test file
        test_content = b"Test file content for iteration 31"
        files = {
            "file": ("test_file.txt", io.BytesIO(test_content), "application/pdf")
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/media/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "upload" in data
        upload = data["upload"]
        assert "id" in upload
        assert "filename" in upload
        assert "url" in upload
        TestMediaUploads.uploaded_file_id = upload["id"]
        print(f"PASS: File uploaded with ID {upload['id']}")

    def test_list_media_uploads(self, admin_token):
        """GET /api/admin/media/uploads - list uploaded files"""
        response = requests.get(
            f"{BASE_URL}/api/admin/media/uploads",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "uploads" in data
        assert isinstance(data["uploads"], list)
        print(f"PASS: Retrieved {len(data['uploads'])} uploaded files")

    def test_serve_uploaded_file(self, admin_token):
        """GET /api/admin/media/uploads/{id}/file - serve uploaded file"""
        if not TestMediaUploads.uploaded_file_id:
            pytest.skip("No file uploaded to serve")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/media/uploads/{TestMediaUploads.uploaded_file_id}/file",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.status_code}"
        assert len(response.content) > 0
        print("PASS: Uploaded file served successfully")

    def test_delete_media_upload(self, admin_token):
        """DELETE /api/admin/media/uploads/{id} - delete uploaded file"""
        if not TestMediaUploads.uploaded_file_id:
            pytest.skip("No file uploaded to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/media/uploads/{TestMediaUploads.uploaded_file_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print("PASS: Uploaded file deleted successfully")

    def test_member_cannot_access_media_upload(self, member_token):
        """Member role cannot access admin media endpoint (403)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/media/uploads",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("PASS: Member correctly denied access to admin media uploads")


# ============== FEATURE 6: PORTAL PAYMENT METHODS ==============

class TestPortalPaymentMethods:
    """Test portal payment methods endpoints (Bearer token auth)"""
    
    created_method_id = None

    def test_get_portal_payment_methods(self, member_token):
        """GET /api/portal/payment-methods - get saved payment methods"""
        response = requests.get(
            f"{BASE_URL}/api/portal/payment-methods",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "payment_methods" in data
        assert isinstance(data["payment_methods"], list)
        print(f"PASS: Retrieved {len(data['payment_methods'])} payment methods")

    def test_save_portal_payment_method(self, member_token):
        """POST /api/portal/payment-methods - save new payment method"""
        payload = {
            "card_last_four": "4242",
            "card_brand": "visa",
            "card_exp_month": 12,
            "card_exp_year": 2028,
            "stripe_payment_method_id": "pm_test_iter31",
            "is_default": True
        }
        response = requests.post(
            f"{BASE_URL}/api/portal/payment-methods",
            headers={"Authorization": f"Bearer {member_token}"},
            json=payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "payment_method" in data
        pm = data["payment_method"]
        assert pm["card_last_four"] == "4242"
        TestPortalPaymentMethods.created_method_id = pm["id"]
        print(f"PASS: Payment method saved with ID {pm['id']}")

    def test_set_portal_default_payment_method(self, member_token):
        """PUT /api/portal/payment-methods/{id}/default - set default payment method"""
        if not TestPortalPaymentMethods.created_method_id:
            pytest.skip("No payment method created to set as default")
        
        response = requests.put(
            f"{BASE_URL}/api/portal/payment-methods/{TestPortalPaymentMethods.created_method_id}/default",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print("PASS: Default payment method set successfully")

    def test_delete_portal_payment_method(self, member_token):
        """DELETE /api/portal/payment-methods/{id} - delete payment method"""
        if not TestPortalPaymentMethods.created_method_id:
            pytest.skip("No payment method created to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/portal/payment-methods/{TestPortalPaymentMethods.created_method_id}",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print("PASS: Payment method deleted successfully")


# ============== PORTAL ROUTES (MEMBER ACCESS) ==============

class TestPortalRoutes:
    """Test portal routes accessible by members"""

    def test_get_portal_announcements(self, member_token):
        """GET /api/portal/announcements - member sees active announcements"""
        response = requests.get(
            f"{BASE_URL}/api/portal/announcements",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "announcements" in data
        assert isinstance(data["announcements"], list)
        print(f"PASS: Portal announcements - {len(data['announcements'])} active announcements")

    def test_get_portal_volunteer_opportunities(self, member_token):
        """GET /api/portal/volunteer/opportunities - member sees active opportunities"""
        response = requests.get(
            f"{BASE_URL}/api/portal/volunteer/opportunities",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "opportunities" in data
        assert isinstance(data["opportunities"], list)
        print(f"PASS: Portal volunteer opportunities - {len(data['opportunities'])} active")

    def test_portal_volunteer_signup(self, member_token, admin_token):
        """POST /api/portal/volunteer/signup - member signs up for opportunity"""
        # First create an opportunity
        opp_response = requests.post(
            f"{BASE_URL}/api/admin/volunteer/opportunities",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "TEST_Member_Signup_Opportunity",
                "description": "Test opportunity for member signup",
                "schedule": "Sundays 10AM",
                "location": "Lobby",
                "spots_available": 10,
                "ministry_area": "Welcome"
            }
        )
        if opp_response.status_code != 200:
            pytest.skip("Could not create opportunity for signup test")
        
        opportunity_id = opp_response.json()["opportunity"]["id"]
        
        # Member signs up
        response = requests.post(
            f"{BASE_URL}/api/portal/volunteer/signup",
            headers={"Authorization": f"Bearer {member_token}"},
            json={"opportunity_id": opportunity_id}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "signup" in data or "message" in data
        print("PASS: Member volunteer signup successful")
        
        # Clean up
        requests.delete(
            f"{BASE_URL}/api/admin/volunteer/opportunities/{opportunity_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )


# ============== UNAUTHORIZED ACCESS TESTS ==============

class TestUnauthorizedAccess:
    """Test that unauthorized requests are rejected"""

    def test_no_token_returns_401(self):
        """Requests without token should return 401"""
        endpoints = [
            "/api/admin/geofence/config",
            "/api/admin/announcements",
            "/api/admin/volunteer/opportunities",
            "/api/admin/media/uploads",
            "/api/portal/payment-methods",
            "/api/portal/giving/nudge"
        ]
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 401, f"{endpoint} should return 401, got {response.status_code}"
        print("PASS: All endpoints correctly return 401 for unauthenticated requests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
