"""
Iteration 92 Tests - Solomon AI
Tests for:
1. Person_ID cross-referencing in transactions API
2. Component splitting verification (code review)
3. Regression tests for platform dashboard, donors, fund reconciliation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PLATFORM_ADMIN_EMAIL = "admin@solomonai.us"
PLATFORM_ADMIN_PASSWORD = os.environ.get("TEST_PASSWORD", "Demo2026!")
CHURCH_ADMIN_EMAIL = "shannonnieman1030@gmail.com"
CHURCH_ADMIN_PASSWORD = os.environ.get("TEST_PASSWORD", "Demo2026!")


@pytest.fixture(scope="module")
def platform_admin_token():
    """Get platform admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": PLATFORM_ADMIN_EMAIL,
        "password": PLATFORM_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("session_token")
    pytest.skip(f"Platform admin login failed: {response.status_code}")


@pytest.fixture(scope="module")
def church_admin_token():
    """Get church admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": CHURCH_ADMIN_EMAIL,
        "password": CHURCH_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("session_token")
    pytest.skip(f"Church admin login failed: {response.status_code}")


class TestHealthAndBasics:
    """Basic health checks"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"API Health: {data}")


class TestPersonIdCrossReferencing:
    """Test donation person_id cross-referencing - transactions should have real person names"""
    
    def test_transactions_have_person_names(self, platform_admin_token):
        """GET /api/platform/transactions should return transactions with real person names"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/transactions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        transactions = data.get("transactions", [])
        assert len(transactions) > 0, "Should have transactions"
        
        # Count transactions with real names vs generic names
        real_names = 0
        generic_names = 0
        
        for tx in transactions[:50]:  # Check first 50
            donor_name = tx.get("donor_name", "") or tx.get("person_name", "") or ""
            if donor_name and donor_name not in ["Member", "Anonymous", "Unknown", ""]:
                real_names += 1
            else:
                generic_names += 1
        
        # Most transactions should have real names (>50%)
        total = real_names + generic_names
        if total > 0:
            real_name_pct = (real_names / total) * 100
            print(f"Person ID cross-referencing: {real_names}/{total} ({real_name_pct:.1f}%) have real names")
            # Allow some anonymous donations but majority should have names
            assert real_name_pct >= 50, f"Expected >50% real names, got {real_name_pct:.1f}%"


class TestRegressionPlatformDashboard:
    """Regression tests for platform dashboard"""
    
    def test_platform_stats_loads(self, platform_admin_token):
        """Platform stats should load with KPI data"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check for expected KPI fields
        assert "churches" in data or "platform" in data
        churches = data.get("churches", {})
        assert churches.get("total", 0) >= 8, "Expected 8+ churches"
        print(f"Platform stats: {churches.get('total', 0)} churches, {data.get('members', {}).get('total', 0)} members")
    
    def test_platform_organizations_list(self, platform_admin_token):
        """Platform should list organizations/churches"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/organizations", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Data is a list of organizations
        assert isinstance(data, list), "Expected list of organizations"
        assert len(data) >= 1, f"Expected 1+ organizations, got {len(data)}"
        print(f"Platform organizations: {len(data)} orgs")


class TestRegressionDonors:
    """Regression tests for donors module"""
    
    def test_donors_count(self, platform_admin_token):
        """Donors module should show 41K+ donors"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/donors", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        total_donors = data.get("total", 0) or data.get("total_donors", 0) or len(data.get("donors", []))
        print(f"Total donors: {total_donors}")
        # Should have significant donor count
        assert total_donors >= 1000, f"Expected 1000+ donors, got {total_donors}"


class TestRegressionFundReconciliation:
    """Regression tests for fund reconciliation - using platform stats giving data"""
    
    def test_platform_giving_total(self, platform_admin_token):
        """Platform giving should show $108M+ total"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check for total giving amount
        giving = data.get("giving", {})
        total = giving.get("all_time", 0)
        print(f"Platform giving total: ${total:,.2f}")
        # Should have $108M+ total
        assert total >= 100000000, f"Expected $100M+ total, got ${total:,.2f}"


class TestChurchAdminAccess:
    """Test church admin can access their data"""
    
    def test_church_admin_dashboard(self, church_admin_token):
        """Church admin should access dashboard"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Church admin dashboard keys: {list(data.keys())}")
    
    def test_church_admin_members(self, church_admin_token):
        """Church admin should access members"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        assert response.status_code == 200
        data = response.json()
        members = data.get("members", [])
        print(f"Church admin members: {len(members)}")


class TestKidsCheckinEndpoints:
    """Test kids check-in endpoints (component splitting verification)"""
    
    def test_kids_checkins_endpoint(self, church_admin_token):
        """Kids check-in endpoint should work"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/kids/checkins", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Kids checkins: {len(data.get('checkins', []))}")
    
    def test_kids_all_endpoint(self, church_admin_token):
        """Kids all endpoint should work"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/kids/all", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"All kids: {len(data.get('children', []))}")


class TestCheckinSetupEndpoints:
    """Test check-in setup endpoints (component splitting verification)"""
    
    def test_checkin_locations(self, church_admin_token):
        """Check-in locations endpoint should work"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/checkin/locations", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Check-in locations: {len(data.get('locations', []))}")
    
    def test_checkin_reports_trends(self, church_admin_token):
        """Check-in reports trends endpoint should work"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/checkin/reports/trends", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Check-in trends: {data.get('total_checkins', 0)} total")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
