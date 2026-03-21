"""
Test Suite for Iteration 6: Email/Password Auth + Member Portal + Mega-Church Stats
- Email/password login with demo accounts (admin@abundant.org, member@abundant.org)
- Role-based routing (admin -> /dashboard, member -> /portal)
- Member Portal endpoints (groups, events, profile)
- Mega-church scale stats (50,000+ members)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://solomon-phase-a.preview.emergentagent.com').rstrip('/')

class TestEmailPasswordAuth:
    """Test email/password authentication for demo accounts"""
    
    def test_admin_login_success(self):
        """Admin login should return role: admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@abundant.org",
            "password": "Demo2026!"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "user_id" in data
        assert data["email"] == "admin@abundant.org"
        assert data["role"] == "admin", f"Expected role='admin', got {data.get('role')}"
        assert "name" in data
        print(f"✓ Admin login successful: {data['name']} (role: {data['role']})")
    
    def test_member_login_success(self):
        """Member login should return role: member"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.org",
            "password": "Demo2026!"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "user_id" in data
        assert data["email"] == "member@abundant.org"
        assert data["role"] == "member", f"Expected role='member', got {data.get('role')}"
        assert "name" in data
        print(f"✓ Member login successful: {data['name']} (role: {data['role']})")
    
    def test_login_wrong_password(self):
        """Login with wrong password should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@abundant.org",
            "password": "WrongPassword123"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Wrong password correctly rejected with 401")
    
    def test_login_nonexistent_email(self):
        """Login with non-existent email should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@email.com",
            "password": "Demo2026!"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Non-existent email correctly rejected with 401")


class TestMegaChurchStats:
    """Test dashboard stats return mega-church scale numbers"""
    
    def test_dashboard_stats_scale(self):
        """Dashboard stats should return mega-church numbers (50,000+ members)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify mega-church scale stats
        assert "total_members" in data
        assert data["total_members"] >= 50000, f"Expected 50,000+ members, got {data['total_members']}"
        
        assert "mtd_giving" in data
        assert data["mtd_giving"] >= 800000, f"Expected $800,000+ MTD giving, got {data['mtd_giving']}"
        
        assert "ytd_giving" in data
        assert data["ytd_giving"] >= 2800000, f"Expected $2,800,000+ YTD giving, got {data['ytd_giving']}"
        
        assert "active_groups" in data
        assert data["active_groups"] >= 280, f"Expected 280+ groups, got {data['active_groups']}"
        
        assert "last_attendance" in data
        assert data["last_attendance"] >= 8000, f"Expected 8,000+ attendance, got {data['last_attendance']}"
        
        print(f"✓ Mega-church stats verified:")
        print(f"  - Total Members: {data['total_members']:,}")
        print(f"  - MTD Giving: ${data['mtd_giving']:,}")
        print(f"  - YTD Giving: ${data['ytd_giving']:,}")
        print(f"  - Active Groups: {data['active_groups']}")
        print(f"  - Last Attendance: {data['last_attendance']:,}")


class TestPortalEndpoints:
    """Test member portal API endpoints"""
    
    def test_portal_groups_endpoint(self):
        """Portal groups endpoint should return available groups"""
        response = requests.get(f"{BASE_URL}/api/portal/groups")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of groups"
        assert len(data) > 0, "Expected at least one group"
        
        # Verify group structure
        first_group = data[0]
        assert "id" in first_group
        assert "name" in first_group
        assert "is_active" in first_group
        
        print(f"✓ Portal groups returned {len(data)} groups")
    
    def test_portal_events_endpoint(self):
        """Portal events endpoint should return upcoming events"""
        response = requests.get(f"{BASE_URL}/api/portal/events")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of events"
        
        if len(data) > 0:
            first_event = data[0]
            assert "id" in first_event
            assert "name" in first_event
            assert "start_datetime" in first_event
        
        print(f"✓ Portal events returned {len(data)} events")
    
    def test_funds_endpoint(self):
        """Funds endpoint should return available giving funds"""
        response = requests.get(f"{BASE_URL}/api/funds")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of funds"
        assert len(data) > 0, "Expected at least one fund"
        
        # Verify fund structure
        first_fund = data[0]
        assert "id" in first_fund
        assert "name" in first_fund
        assert "is_active" in first_fund
        
        # Check for expected funds
        fund_names = [f["name"] for f in data]
        assert "General Fund" in fund_names, "Expected 'General Fund' in funds"
        
        print(f"✓ Funds endpoint returned {len(data)} funds: {fund_names[:5]}")


class TestAuthMe:
    """Test /auth/me endpoint with session cookie"""
    
    @pytest.fixture
    def admin_session(self):
        """Login as admin and get session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@abundant.org",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        return response.cookies
    
    @pytest.fixture
    def member_session(self):
        """Login as member and get session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.org",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        return response.cookies
    
    def test_auth_me_admin(self, admin_session):
        """Admin /auth/me should return admin role"""
        response = requests.get(f"{BASE_URL}/api/auth/me", cookies=admin_session)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["email"] == "admin@abundant.org"
        assert data["role"] == "admin"
        print(f"✓ Admin /auth/me returns correct user with role: {data['role']}")
    
    def test_auth_me_member(self, member_session):
        """Member /auth/me should return member role"""
        response = requests.get(f"{BASE_URL}/api/auth/me", cookies=member_session)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["email"] == "member@abundant.org"
        assert data["role"] == "member"
        print(f"✓ Member /auth/me returns correct user with role: {data['role']}")
    
    def test_auth_me_no_session(self):
        """No session should return 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ No session correctly returns 401")


class TestPortalMe:
    """Test /portal/me endpoint (requires member session)"""
    
    @pytest.fixture
    def member_session(self):
        """Login as member and get session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.org",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        return response.cookies
    
    def test_portal_me_authenticated(self, member_session):
        """Portal /me should return member profile"""
        response = requests.get(f"{BASE_URL}/api/portal/me", cookies=member_session)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "user" in data, "Expected 'user' in response"
        assert data["user"]["email"] == "member@abundant.org"
        print(f"✓ Portal /me returns member profile for: {data['user']['email']}")
    
    def test_portal_me_no_session(self):
        """Portal /me without session should return 401"""
        response = requests.get(f"{BASE_URL}/api/portal/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Portal /me correctly returns 401 without session")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
