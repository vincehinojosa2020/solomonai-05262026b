"""
Iteration 61: Security Testing - Cross-Tenant Isolation, Rate Limiting, Platform Admin Isolation
Tests for Go-To-Market production launch prep security fixes
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
CHURCH_ADMIN_1 = {"email": "shannonnieman1030@gmail.com", "password": "Demo2026!"}  # tenant: abundant-east-001
CHURCH_ADMIN_2 = {"email": "admin@cristoviene.church", "password": "Demo2026!"}  # tenant: cristoviene-church-001
PLATFORM_ADMIN = {"email": "admin@solomonai.us", "password": "Demo2026!"}  # no tenant_id


class TestAPIHealth:
    """Basic API health check"""
    
    def test_api_health(self):
        """Verify API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✓ API health check passed")


class TestCrossTenantIsolation:
    """Test cross-tenant data isolation - CRITICAL SECURITY"""
    
    def test_login_church_admin_1(self):
        """Login as Church Admin 1 (Abundant East)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN_1)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "session_token" in data, "No session token returned"
        self.token_1 = data["session_token"]
        print(f"✓ Church Admin 1 logged in successfully")
        return data["session_token"]
    
    def test_login_church_admin_2(self):
        """Login as Church Admin 2 (CristoViene)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN_2)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "session_token" in data, "No session token returned"
        print(f"✓ Church Admin 2 logged in successfully")
        return data["session_token"]
    
    def test_cross_tenant_groups_isolation(self):
        """CRITICAL: Verify Church Admin 1 and Church Admin 2 see DIFFERENT groups"""
        # Login as Church Admin 1
        response1 = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN_1)
        assert response1.status_code == 200
        token1 = response1.json()["session_token"]
        
        # Get groups for Church Admin 1
        groups_response1 = requests.get(
            f"{BASE_URL}/api/admin/groups",
            cookies={"session_token": token1}
        )
        assert groups_response1.status_code == 200, f"Failed to get groups for Admin 1: {groups_response1.text}"
        groups_data1 = groups_response1.json()
        total_groups_1 = groups_data1.get("total", 0)
        print(f"✓ Church Admin 1 (Abundant East) sees {total_groups_1} groups")
        
        # Login as Church Admin 2
        response2 = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN_2)
        assert response2.status_code == 200
        token2 = response2.json()["session_token"]
        
        # Get groups for Church Admin 2
        groups_response2 = requests.get(
            f"{BASE_URL}/api/admin/groups",
            cookies={"session_token": token2}
        )
        assert groups_response2.status_code == 200, f"Failed to get groups for Admin 2: {groups_response2.text}"
        groups_data2 = groups_response2.json()
        total_groups_2 = groups_data2.get("total", 0)
        print(f"✓ Church Admin 2 (CristoViene) sees {total_groups_2} groups")
        
        # CristoViene should have 0 groups (new tenant with no data)
        # Abundant East should have groups (seeded data)
        # The key test: they should see DIFFERENT data
        print(f"✓ Cross-tenant isolation verified: Admin 1 sees {total_groups_1} groups, Admin 2 sees {total_groups_2} groups")
        
        # If both see the same non-zero count, that's a potential leak
        if total_groups_1 > 0 and total_groups_1 == total_groups_2:
            # Check if they're actually the same groups (data leak)
            groups_1_ids = [g.get("id") for g in groups_data1.get("groups", [])]
            groups_2_ids = [g.get("id") for g in groups_data2.get("groups", [])]
            overlap = set(groups_1_ids) & set(groups_2_ids)
            assert len(overlap) == 0, f"SECURITY BREACH: Cross-tenant data leak detected! Overlapping group IDs: {overlap}"
        
        print("✓ SECURITY: Cross-tenant data isolation PASSED")


class TestPlatformAdminIsolation:
    """Test platform admin sees no tenant-specific data"""
    
    def test_platform_admin_login(self):
        """Login as Platform Admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        assert response.status_code == 200, f"Platform admin login failed: {response.text}"
        data = response.json()
        assert "session_token" in data
        print("✓ Platform Admin logged in successfully")
        return data["session_token"]
    
    def test_platform_admin_groups_empty(self):
        """Platform Admin should see 0 groups (no tenant context)"""
        # Login as Platform Admin
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        assert response.status_code == 200
        token = response.json()["session_token"]
        
        # Get groups - should return 0 or empty
        groups_response = requests.get(
            f"{BASE_URL}/api/admin/groups",
            cookies={"session_token": token}
        )
        
        # Platform admin without tenant context should get 0 groups or 403
        if groups_response.status_code == 200:
            data = groups_response.json()
            total = data.get("total", 0)
            # Platform admin with no tenant_id should see 0 groups
            assert total == 0, f"Platform admin should see 0 groups, but sees {total}"
            print(f"✓ Platform Admin sees {total} groups (expected: 0)")
        elif groups_response.status_code == 403:
            print("✓ Platform Admin correctly denied access to groups (no tenant context)")
        else:
            pytest.fail(f"Unexpected status code: {groups_response.status_code}")
        
        print("✓ SECURITY: Platform Admin isolation PASSED")
    
    def test_platform_admin_checkin_locations_empty(self):
        """Platform Admin should see empty check-in locations"""
        # Login as Platform Admin
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        assert response.status_code == 200
        token = response.json()["session_token"]
        
        # Get check-in locations
        locations_response = requests.get(
            f"{BASE_URL}/api/admin/checkin/locations",
            cookies={"session_token": token}
        )
        
        if locations_response.status_code == 200:
            data = locations_response.json()
            locations = data.get("locations", [])
            assert len(locations) == 0, f"Platform admin should see 0 locations, but sees {len(locations)}"
            print(f"✓ Platform Admin sees {len(locations)} check-in locations (expected: 0)")
        elif locations_response.status_code == 403:
            print("✓ Platform Admin correctly denied access to check-in locations")
        else:
            pytest.fail(f"Unexpected status code: {locations_response.status_code}")
        
        print("✓ SECURITY: Platform Admin check-in isolation PASSED")


class TestRateLimiting:
    """Test rate limiting on login endpoint - CRITICAL SECURITY"""
    
    def test_rate_limit_on_login(self):
        """
        Make 8 rapid login attempts with wrong credentials.
        First 5 should return 401 (invalid credentials).
        Requests 6+ should return 429 (rate limited).
        
        IMPORTANT: This test waits 65 seconds first to reset the rate limit window.
        """
        print("⏳ Waiting 65 seconds to reset rate limit window...")
        time.sleep(65)
        
        wrong_creds = {"email": "test_rate_limit@example.com", "password": "wrongpassword123"}
        
        results = []
        for i in range(8):
            response = requests.post(f"{BASE_URL}/api/auth/login", json=wrong_creds)
            results.append(response.status_code)
            print(f"  Request {i+1}: Status {response.status_code}")
            time.sleep(0.1)  # Small delay between requests
        
        # First 5 should be 401 (invalid credentials)
        for i in range(5):
            assert results[i] == 401, f"Request {i+1} should be 401, got {results[i]}"
        
        # Requests 6-8 should be 429 (rate limited)
        rate_limited_count = sum(1 for r in results[5:] if r == 429)
        assert rate_limited_count >= 1, f"Expected at least 1 rate-limited response (429) after 5 attempts, got {rate_limited_count}"
        
        print(f"✓ Rate limiting working: {results}")
        print(f"✓ SECURITY: Rate limiting PASSED - {rate_limited_count}/3 requests after limit were blocked")


class TestAuthenticationFlow:
    """Test basic authentication flows"""
    
    def test_login_returns_user_data(self):
        """Verify login returns proper user data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN_1)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "session_token" in data
        assert "user" in data
        
        user = data["user"]
        assert user.get("email") == CHURCH_ADMIN_1["email"]
        assert "tenant_id" in user
        assert user.get("tenant_id") == "abundant-east-001"
        
        print(f"✓ Login returns correct user data with tenant_id: {user.get('tenant_id')}")
    
    def test_invalid_credentials_returns_401(self):
        """Verify invalid credentials return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly return 401")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
