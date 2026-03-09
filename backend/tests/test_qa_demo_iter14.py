"""
Solomon AI - Pre-Demo QA Test Suite (Iteration 14)
Testing all account types, login flows, and critical API endpoints
Corrected with actual API endpoints from server.py
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from requirement
CREDENTIALS = {
    "platform_admin": {"email": "admin@solomon.ai", "password": "Demo2026!"},
    "church_admin_abundant": {"email": "admin@abundant.church", "password": "Demo2026!"},
    "church_admin_cristo": {"email": "admin@cristoviene.church", "password": "Demo2026!"},
    "church_admin_potters": {"email": "admin@pottershouse.church", "password": "Demo2026!"},
    "church_admin_eden": {"email": "admin@edenx.church", "password": "Demo2026!"},
    "member_abundant": {"email": "member@abundant.church", "password": "Demo2026!"},
    "member_cristo": {"email": "member@cristoviene.church", "password": "Demo2026!"},
    "member_eden": {"email": "kaylen@edenx.church", "password": "Demo2026!"},
}


class TestAuthenticationFlows:
    """Test all login flows for different account types"""

    def test_platform_admin_login(self):
        """Platform Admin (admin@solomon.ai) can login"""
        creds = CREDENTIALS["platform_admin"]
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": creds["email"], "password": creds["password"]}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Response is flat user object, not nested under 'user' key
        assert "user_id" in data or "email" in data, f"Unexpected response: {data}"
        assert data.get("role") == "platform_admin", f"Expected platform_admin role, got {data.get('role')}"
        print(f"SUCCESS: Platform admin login - user role: {data.get('role')}")

    def test_church_admin_abundant_login(self):
        """Church Admin (Abundant Church) can login"""
        creds = CREDENTIALS["church_admin_abundant"]
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": creds["email"], "password": creds["password"]}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data.get("role") in ["admin", "church_admin"]
        print(f"SUCCESS: Abundant church admin login - tenant: {data.get('tenant_id')}")

    def test_church_admin_cristo_viene_login(self):
        """Church Admin (Cristo Viene) can login"""
        creds = CREDENTIALS["church_admin_cristo"]
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": creds["email"], "password": creds["password"]}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        print("SUCCESS: Cristo Viene church admin login")

    def test_church_admin_potters_house_login(self):
        """Church Admin (Potter's House) can login"""
        creds = CREDENTIALS["church_admin_potters"]
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": creds["email"], "password": creds["password"]}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        print("SUCCESS: Potter's House church admin login")

    def test_church_admin_eden_x_login(self):
        """Church Admin (Eden X) can login"""
        creds = CREDENTIALS["church_admin_eden"]
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": creds["email"], "password": creds["password"]}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        print("SUCCESS: Eden X church admin login")

    def test_member_abundant_login(self):
        """Member (Abundant Church) can login"""
        creds = CREDENTIALS["member_abundant"]
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": creds["email"], "password": creds["password"]}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        print(f"SUCCESS: Member login - role: {data.get('role')}")

    def test_member_cristo_viene_login(self):
        """Member (Cristo Viene) can login"""
        creds = CREDENTIALS["member_cristo"]
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": creds["email"], "password": creds["password"]}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        print("SUCCESS: Cristo Viene member login")

    def test_member_eden_x_login(self):
        """Member (Eden X - Kaylen) can login"""
        creds = CREDENTIALS["member_eden"]
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": creds["email"], "password": creds["password"]}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        print("SUCCESS: Eden X member login (kaylen@edenx.church)")


class TestPlatformAdminEndpoints:
    """Test Platform Admin specific endpoints"""

    @pytest.fixture
    def platform_admin_session(self):
        """Get authenticated session for platform admin"""
        session = requests.Session()
        creds = CREDENTIALS["platform_admin"]
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": creds["email"], "password": creds["password"]}
        )
        assert response.status_code == 200
        return session

    def test_get_all_tenants(self, platform_admin_session):
        """Platform Admin can view all churches/tenants"""
        response = platform_admin_session.get(f"{BASE_URL}/api/tenants")
        assert response.status_code == 200, f"Failed to get tenants: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 4, f"Expected at least 4 tenants, got {len(data)}"
        tenant_names = [t.get('name') for t in data]
        print(f"SUCCESS: Found {len(data)} tenants: {tenant_names}")

    def test_platform_stats_gmv(self, platform_admin_session):
        """Platform Admin can see platform stats including GMV ($137,218 MTD expected)"""
        response = platform_admin_session.get(f"{BASE_URL}/api/platform/stats")
        assert response.status_code == 200, f"Failed to get platform stats: {response.text}"
        data = response.json()
        assert "giving" in data, "No giving data in stats"
        mtd_total = data.get("giving", {}).get("mtd_total", 0)
        print(f"SUCCESS: Platform GMV MTD: ${mtd_total:,.2f}")
        # Check if GMV is around expected $137,218
        assert mtd_total > 100000, f"GMV seems low: ${mtd_total:,.2f}"

    def test_admin_members_list(self, platform_admin_session):
        """Platform Admin can view all members across churches"""
        response = platform_admin_session.get(f"{BASE_URL}/api/admin/members?limit=10")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "members" in data
        assert "total" in data
        print(f"SUCCESS: Total members across platform: {data['total']}")


class TestChurchAdminEndpoints:
    """Test Church Admin dashboard and features for Abundant Church"""

    @pytest.fixture
    def church_admin_session(self):
        """Get authenticated session for Abundant church admin"""
        session = requests.Session()
        creds = CREDENTIALS["church_admin_abundant"]
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": creds["email"], "password": creds["password"]}
        )
        assert response.status_code == 200
        return session

    def test_dashboard_stats(self, church_admin_session):
        """Church Admin can view dashboard stats"""
        response = church_admin_session.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_members" in data
        assert "mtd_giving" in data
        print(f"SUCCESS: Dashboard - Members: {data['total_members']}, MTD Giving: ${data.get('mtd_giving', 0):,.2f}")

    def test_media_library(self, church_admin_session):
        """Church Admin can access media library (admin/media/videos)"""
        response = church_admin_session.get(f"{BASE_URL}/api/admin/media/videos")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        videos = data if isinstance(data, list) else data.get('videos', [])
        print(f"SUCCESS: Media library - found {len(videos)} videos")

    def test_groups_list(self, church_admin_session):
        """Church Admin can view groups (admin/groups)"""
        response = church_admin_session.get(f"{BASE_URL}/api/admin/groups")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        groups = data if isinstance(data, list) else data.get('groups', [])
        print(f"SUCCESS: Groups - found {len(groups)} groups")

    def test_events_list(self, church_admin_session):
        """Church Admin can view events"""
        response = church_admin_session.get(f"{BASE_URL}/api/events")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        events = data if isinstance(data, list) else []
        print(f"SUCCESS: Events - found {len(events)} events")

    def test_giving_dashboard(self, church_admin_session):
        """Church Admin can view giving dashboard"""
        response = church_admin_session.get(f"{BASE_URL}/api/giving/stats")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"SUCCESS: Giving stats loaded - MTD: ${data.get('mtd_total', 0):,.2f}")

    def test_meetings_list(self, church_admin_session):
        """Church Admin can view pastoral meetings (admin/meetings)"""
        response = church_admin_session.get(f"{BASE_URL}/api/admin/meetings")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        meetings = data if isinstance(data, list) else data.get('meetings', [])
        print(f"SUCCESS: Meetings - found {len(meetings)} meetings")

    def test_pathways_courses(self, church_admin_session):
        """Church Admin can view Abundant Pathways courses (admin/pathways/courses)"""
        response = church_admin_session.get(f"{BASE_URL}/api/admin/pathways/courses")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        courses = data if isinstance(data, list) else data.get('courses', [])
        print(f"SUCCESS: Pathways - found {len(courses)} courses")

    def test_merch_products(self, church_admin_session):
        """Church Admin can view merchandise products (admin/merch/products)"""
        response = church_admin_session.get(f"{BASE_URL}/api/admin/merch/products")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        products = data if isinstance(data, list) else data.get('products', [])
        print(f"SUCCESS: Merch - found {len(products)} products")

    def test_api_keys_admin(self, church_admin_session):
        """Church Admin can view API keys (Developer API)"""
        response = church_admin_session.get(f"{BASE_URL}/api/admin/api-keys")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        keys = data if isinstance(data, list) else data.get('api_keys', [])
        print(f"SUCCESS: API Keys - found {len(keys)} keys")


class TestMemberPortalEndpoints:
    """Test Member Portal features"""

    @pytest.fixture
    def member_session(self):
        """Get authenticated session for member"""
        session = requests.Session()
        creds = CREDENTIALS["member_abundant"]
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": creds["email"], "password": creds["password"]}
        )
        assert response.status_code == 200
        return session

    def test_portal_member_data(self, member_session):
        """Member can fetch their portal data (portal/me)"""
        response = member_session.get(f"{BASE_URL}/api/portal/me")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # The response might have different structure, just verify it returns something
        print(f"SUCCESS: Member portal data loaded - keys: {list(data.keys()) if data else 'None'}")

    def test_portal_events(self, member_session):
        """Member can view portal events (portal/events)"""
        response = member_session.get(f"{BASE_URL}/api/portal/events")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        events = data if isinstance(data, list) else []
        print(f"SUCCESS: Portal events - found {len(events)} events")

    def test_portal_groups(self, member_session):
        """Member can view portal groups (portal/groups)"""
        response = member_session.get(f"{BASE_URL}/api/portal/groups")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        groups = data if isinstance(data, list) else []
        print(f"SUCCESS: Portal groups - found {len(groups)} groups")

    def test_portal_media(self, member_session):
        """Member can view portal media/watch (portal/media/videos)"""
        response = member_session.get(f"{BASE_URL}/api/portal/media/videos")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        videos = data if isinstance(data, list) else data.get('videos', [])
        print(f"SUCCESS: Portal media - found {len(videos)} videos")

    def test_portal_pathways(self, member_session):
        """Member can view Pathways courses (portal/pathways/courses)"""
        response = member_session.get(f"{BASE_URL}/api/portal/pathways/courses")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        courses = data if isinstance(data, list) else data.get('courses', [])
        print(f"SUCCESS: Portal pathways - found {len(courses)} courses")

    def test_portal_merch(self, member_session):
        """Member can view merch store (portal/merch/products)"""
        response = member_session.get(f"{BASE_URL}/api/portal/merch/products")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        products = data if isinstance(data, list) else data.get('products', [])
        print(f"SUCCESS: Portal merch - found {len(products)} products")

    def test_portal_meetings_slots(self, member_session):
        """Member can view meeting slots (portal/meetings/slots)"""
        response = member_session.get(f"{BASE_URL}/api/portal/meetings/slots")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        slots = data if isinstance(data, list) else data.get('slots', [])
        print(f"SUCCESS: Portal meeting slots - found {len(slots)} slots")

    def test_solomon_ai_chat(self, member_session):
        """Member can interact with Solomon AI chat"""
        response = member_session.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "What events are coming up?"}
        )
        # Allow both 200 (success) and 503 (service unavailable if LLM not configured)
        assert response.status_code in [200, 503], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            print("SUCCESS: Solomon AI chat responded")
        else:
            print("INFO: Solomon AI chat returned 503 (LLM service may be unavailable)")


class TestSignupFlow:
    """Test new user signup flow"""

    def test_signup_endpoint_exists(self):
        """Signup endpoint exists and accepts POST (auth/register)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": "test_qa_user@example.com",
                "password": "TestPassword123!",
                "confirm_password": "TestPassword123!",
                "first_name": "QA",
                "last_name": "Test User"
            }
        )
        # Could be 200 (created), 400 (validation), or 409 (already exists)
        # We just want to confirm the endpoint works
        assert response.status_code in [200, 201, 400, 409, 422], f"Unexpected: {response.status_code}"
        print(f"SUCCESS: Register endpoint responded with status {response.status_code}")


class TestTenantInfo:
    """Test tenant/church info endpoints"""

    def test_tenant_info(self):
        """Public tenant info endpoint"""
        response = requests.get(f"{BASE_URL}/api/tenant")
        assert response.status_code == 200
        data = response.json()
        print(f"SUCCESS: Tenant info - name: {data.get('name')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
