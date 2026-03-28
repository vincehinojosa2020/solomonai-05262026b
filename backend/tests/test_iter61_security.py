"""
Iteration 61: Security Testing - Cross-Tenant Isolation & Rate Limiting
Tests for:
1. Cross-Tenant Data Isolation (groups, locations, stations)
2. Cross-Resource Access Prevention (PUT/DELETE with wrong tenant token)
3. Platform Admin Isolation (no tenant_id returns empty data)
4. IP Rate Limiting (5 requests per 60 seconds)
5. Email Rate Limiting (10 requests per hour)
"""

import pytest
import requests
import time
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CHURCH_ADMIN_1 = {
    "email": "shannonnieman1030@gmail.com",
    "password": "Demo2026!",
    "tenant_id": "abundant-east-001"
}

CHURCH_ADMIN_2 = {
    "email": "admin@cristoviene.church",
    "password": "Demo2026!",
    "tenant_id": "cristoviene-church-001"
}

CHURCH_ADMIN_3 = {
    "email": "admin@pottershouse.church",
    "password": "Demo2026!",
    "tenant_id": "pottershouse-church-001"
}

PLATFORM_ADMIN = {
    "email": "admin@solomonai.us",
    "password": "Demo2026!",
    "tenant_id": None  # Platform admin has no tenant_id
}


class TestCrossTenantIsolation:
    """Test that different tenants cannot see each other's data"""
    
    @pytest.fixture(scope="class")
    def session1(self):
        """Login as Church Admin 1 (Shannon - abundant-east-001)"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_1["email"],
            "password": CHURCH_ADMIN_1["password"]
        })
        assert response.status_code == 200, f"Login failed for admin 1: {response.text}"
        return session
    
    @pytest.fixture(scope="class")
    def session2(self):
        """Login as Church Admin 2 (CristoViene - cristoviene-church-001)"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_2["email"],
            "password": CHURCH_ADMIN_2["password"]
        })
        assert response.status_code == 200, f"Login failed for admin 2: {response.text}"
        return session
    
    @pytest.fixture(scope="class")
    def platform_session(self):
        """Login as Platform Admin (no tenant_id)"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN["email"],
            "password": PLATFORM_ADMIN["password"]
        })
        assert response.status_code == 200, f"Login failed for platform admin: {response.text}"
        return session
    
    def test_api_health(self):
        """Verify API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("API health check passed")
    
    def test_tenant1_gets_own_groups(self, session1):
        """Shannon (abundant-east-001) should get her tenant's groups"""
        response = session1.get(f"{BASE_URL}/api/admin/groups")
        assert response.status_code == 200
        data = response.json()
        groups = data.get("groups", [])
        print(f"Tenant 1 (abundant-east-001) has {len(groups)} groups")
        
        # All groups should belong to tenant 1
        for group in groups:
            assert group.get("tenant_id") == CHURCH_ADMIN_1["tenant_id"], \
                f"Group {group.get('name')} has wrong tenant_id: {group.get('tenant_id')}"
        
        return groups
    
    def test_tenant2_gets_own_groups(self, session2):
        """CristoViene (cristoviene-church-001) should get their tenant's groups"""
        response = session2.get(f"{BASE_URL}/api/admin/groups")
        assert response.status_code == 200
        data = response.json()
        groups = data.get("groups", [])
        print(f"Tenant 2 (cristoviene-church-001) has {len(groups)} groups")
        
        # All groups should belong to tenant 2
        for group in groups:
            assert group.get("tenant_id") == CHURCH_ADMIN_2["tenant_id"], \
                f"Group {group.get('name')} has wrong tenant_id: {group.get('tenant_id')}"
        
        return groups
    
    def test_tenants_have_different_groups(self, session1, session2):
        """Verify tenant 1 and tenant 2 get different group data"""
        response1 = session1.get(f"{BASE_URL}/api/admin/groups")
        response2 = session2.get(f"{BASE_URL}/api/admin/groups")
        
        groups1 = response1.json().get("groups", [])
        groups2 = response2.json().get("groups", [])
        
        group_ids_1 = set(g.get("id") for g in groups1)
        group_ids_2 = set(g.get("id") for g in groups2)
        
        # No overlap in group IDs
        overlap = group_ids_1.intersection(group_ids_2)
        assert len(overlap) == 0, f"SECURITY ISSUE: Tenants share group IDs: {overlap}"
        print(f"PASS: No overlap in group IDs between tenants")
    
    def test_tenant1_gets_own_locations(self, session1):
        """Shannon should get her tenant's check-in locations"""
        response = session1.get(f"{BASE_URL}/api/admin/checkin/locations")
        assert response.status_code == 200
        data = response.json()
        locations = data.get("locations", [])
        print(f"Tenant 1 has {len(locations)} check-in locations")
        
        for loc in locations:
            assert loc.get("tenant_id") == CHURCH_ADMIN_1["tenant_id"], \
                f"Location {loc.get('name')} has wrong tenant_id"
        
        return locations
    
    def test_tenant2_gets_own_locations(self, session2):
        """CristoViene should get their tenant's check-in locations"""
        response = session2.get(f"{BASE_URL}/api/admin/checkin/locations")
        assert response.status_code == 200
        data = response.json()
        locations = data.get("locations", [])
        print(f"Tenant 2 has {len(locations)} check-in locations")
        
        for loc in locations:
            assert loc.get("tenant_id") == CHURCH_ADMIN_2["tenant_id"], \
                f"Location {loc.get('name')} has wrong tenant_id"
        
        return locations
    
    def test_tenant1_gets_own_stations(self, session1):
        """Shannon should get her tenant's check-in stations"""
        response = session1.get(f"{BASE_URL}/api/admin/checkin/stations")
        assert response.status_code == 200
        data = response.json()
        stations = data.get("stations", [])
        print(f"Tenant 1 has {len(stations)} check-in stations")
        
        for st in stations:
            assert st.get("tenant_id") == CHURCH_ADMIN_1["tenant_id"], \
                f"Station {st.get('name')} has wrong tenant_id"
        
        return stations
    
    def test_tenant2_gets_own_stations(self, session2):
        """CristoViene should get their tenant's check-in stations"""
        response = session2.get(f"{BASE_URL}/api/admin/checkin/stations")
        assert response.status_code == 200
        data = response.json()
        stations = data.get("stations", [])
        print(f"Tenant 2 has {len(stations)} check-in stations")
        
        for st in stations:
            assert st.get("tenant_id") == CHURCH_ADMIN_2["tenant_id"], \
                f"Station {st.get('name')} has wrong tenant_id"
        
        return stations


class TestCrossResourceAccess:
    """Test that one tenant cannot modify another tenant's resources"""
    
    @pytest.fixture(scope="class")
    def session1(self):
        """Login as Church Admin 1"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_1["email"],
            "password": CHURCH_ADMIN_1["password"]
        })
        assert response.status_code == 200
        return session
    
    @pytest.fixture(scope="class")
    def session2(self):
        """Login as Church Admin 2"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_2["email"],
            "password": CHURCH_ADMIN_2["password"]
        })
        assert response.status_code == 200
        return session
    
    def test_cannot_update_other_tenant_group(self, session1, session2):
        """Tenant 2 should NOT be able to update Tenant 1's group"""
        # First, get a group from tenant 1
        response1 = session1.get(f"{BASE_URL}/api/admin/groups")
        groups1 = response1.json().get("groups", [])
        
        if not groups1:
            pytest.skip("Tenant 1 has no groups to test")
        
        target_group_id = groups1[0].get("id")
        print(f"Attempting to update tenant 1's group {target_group_id} with tenant 2's token")
        
        # Try to update with tenant 2's session
        response = session2.put(f"{BASE_URL}/api/admin/groups/{target_group_id}", json={
            "name": "HACKED BY TENANT 2"
        })
        
        # Should return 404 (not found) because tenant isolation prevents access
        assert response.status_code in [404, 403], \
            f"SECURITY ISSUE: Cross-tenant update returned {response.status_code}: {response.text}"
        print(f"PASS: Cross-tenant group update blocked with status {response.status_code}")
    
    def test_cannot_delete_other_tenant_group(self, session1, session2):
        """Tenant 2 should NOT be able to delete Tenant 1's group"""
        # Get a group from tenant 1
        response1 = session1.get(f"{BASE_URL}/api/admin/groups")
        groups1 = response1.json().get("groups", [])
        
        if not groups1:
            pytest.skip("Tenant 1 has no groups to test")
        
        target_group_id = groups1[0].get("id")
        print(f"Attempting to delete tenant 1's group {target_group_id} with tenant 2's token")
        
        # Try to delete with tenant 2's session
        response = session2.delete(f"{BASE_URL}/api/admin/groups/{target_group_id}")
        
        # Should return 404 (not found) because tenant isolation prevents access
        assert response.status_code in [404, 403], \
            f"SECURITY ISSUE: Cross-tenant delete returned {response.status_code}: {response.text}"
        print(f"PASS: Cross-tenant group delete blocked with status {response.status_code}")
        
        # Verify the group still exists for tenant 1
        response_verify = session1.get(f"{BASE_URL}/api/admin/groups")
        groups_after = response_verify.json().get("groups", [])
        group_ids_after = [g.get("id") for g in groups_after]
        assert target_group_id in group_ids_after, "Group was deleted despite tenant isolation!"
        print("PASS: Group still exists for original tenant")
    
    def test_cannot_update_other_tenant_location(self, session1, session2):
        """Tenant 2 should NOT be able to update Tenant 1's check-in location"""
        # Get a location from tenant 1
        response1 = session1.get(f"{BASE_URL}/api/admin/checkin/locations")
        locations1 = response1.json().get("locations", [])
        
        if not locations1:
            pytest.skip("Tenant 1 has no locations to test")
        
        target_location_id = locations1[0].get("id")
        print(f"Attempting to update tenant 1's location {target_location_id} with tenant 2's token")
        
        # Try to update with tenant 2's session
        response = session2.put(f"{BASE_URL}/api/admin/checkin/locations/{target_location_id}", json={
            "name": "HACKED LOCATION"
        })
        
        # The update should not affect tenant 1's data
        # Check if the location name changed
        response_verify = session1.get(f"{BASE_URL}/api/admin/checkin/locations")
        locations_after = response_verify.json().get("locations", [])
        target_loc = next((l for l in locations_after if l.get("id") == target_location_id), None)
        
        assert target_loc is not None, "Location disappeared!"
        assert target_loc.get("name") != "HACKED LOCATION", \
            f"SECURITY ISSUE: Cross-tenant location update succeeded!"
        print(f"PASS: Cross-tenant location update blocked")


class TestPlatformAdminIsolation:
    """Test that platform admin (no tenant_id) gets empty data for tenant-specific resources"""
    
    @pytest.fixture(scope="class")
    def platform_session(self):
        """Login as Platform Admin"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN["email"],
            "password": PLATFORM_ADMIN["password"]
        })
        assert response.status_code == 200, f"Platform admin login failed: {response.text}"
        return session
    
    def test_platform_admin_gets_zero_groups(self, platform_session):
        """Platform admin should get 0 groups (no tenant_id)"""
        response = platform_session.get(f"{BASE_URL}/api/admin/groups")
        assert response.status_code == 200
        data = response.json()
        groups = data.get("groups", [])
        
        # Platform admin has no tenant_id, so query for tenant_id=None returns 0
        print(f"Platform admin groups count: {len(groups)}")
        assert len(groups) == 0, f"Platform admin should get 0 groups, got {len(groups)}"
        print("PASS: Platform admin gets 0 groups (correct isolation)")
    
    def test_platform_admin_gets_zero_locations(self, platform_session):
        """Platform admin should get 0 check-in locations (no tenant_id)"""
        response = platform_session.get(f"{BASE_URL}/api/admin/checkin/locations")
        assert response.status_code == 200
        data = response.json()
        locations = data.get("locations", [])
        
        print(f"Platform admin locations count: {len(locations)}")
        assert len(locations) == 0, f"Platform admin should get 0 locations, got {len(locations)}"
        print("PASS: Platform admin gets 0 locations (correct isolation)")
    
    def test_platform_admin_gets_zero_stations(self, platform_session):
        """Platform admin should get 0 check-in stations (no tenant_id)"""
        response = platform_session.get(f"{BASE_URL}/api/admin/checkin/stations")
        assert response.status_code == 200
        data = response.json()
        stations = data.get("stations", [])
        
        print(f"Platform admin stations count: {len(stations)}")
        assert len(stations) == 0, f"Platform admin should get 0 stations, got {len(stations)}"
        print("PASS: Platform admin gets 0 stations (correct isolation)")


class TestIPRateLimiting:
    """Test IP-based rate limiting: 5 requests per 60 seconds"""
    
    def test_rate_limit_blocks_after_5_attempts(self):
        """After 5 failed login attempts, 6th should return 429"""
        print("\n=== IP Rate Limit Test ===")
        print("Waiting 62 seconds for rate limit window to reset...")
        time.sleep(62)  # Wait for window reset
        
        results = []
        for i in range(8):
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "ratelimit_test@example.com",
                "password": "wrongpassword"
            })
            results.append({
                "attempt": i + 1,
                "status": response.status_code,
                "detail": response.json().get("detail", "")
            })
            print(f"Attempt {i+1}: Status {response.status_code}")
            time.sleep(0.1)  # Small delay between requests
        
        # Attempts 1-5 should return 401 (invalid credentials)
        for i in range(5):
            assert results[i]["status"] == 401, \
                f"Attempt {i+1} should be 401, got {results[i]['status']}"
        
        # Attempts 6+ should return 429 (rate limited)
        for i in range(5, 8):
            assert results[i]["status"] == 429, \
                f"Attempt {i+1} should be 429 (rate limited), got {results[i]['status']}"
        
        print("PASS: IP rate limiting working correctly (5 per 60s)")


class TestEmailRateLimiting:
    """Test email-based rate limiting: 10 requests per hour"""
    
    def test_email_rate_limit_info(self):
        """Document email rate limit behavior (10 per hour per email)"""
        print("\n=== Email Rate Limit Info ===")
        print("Email rate limit: 10 attempts per email per hour")
        print("To fully test, would need 11+ attempts on same email across multiple IP windows")
        print("This test documents the expected behavior")
        
        # The email rate limit is harder to test because:
        # 1. IP rate limit kicks in first (5 per 60s)
        # 2. Need to wait 62s between batches
        # 3. Need 11+ total attempts to trigger email limit
        
        # For now, verify the rate limit response message format
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "email_limit_test@example.com",
            "password": "wrongpassword"
        })
        
        # Should be 401 (invalid credentials) or 429 (rate limited)
        assert response.status_code in [401, 429], f"Unexpected status: {response.status_code}"
        print(f"Response status: {response.status_code}")
        print(f"Response detail: {response.json().get('detail', '')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
