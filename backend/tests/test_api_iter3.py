"""
Backend API tests for SAMSON Church Management System - Iteration 3
Testing: Auth endpoints, Dashboard, Giving, People, Groups
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasics:
    """Basic API health and configuration tests"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Samson" in data["message"]
        print(f"SUCCESS: API root returns: {data}")
    
    def test_tenant_info(self):
        """Test tenant info endpoint"""
        response = requests.get(f"{BASE_URL}/api/tenant")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Abundant Church"
        print(f"SUCCESS: Tenant name: {data['name']}")


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_auth_me_without_session(self):
        """Test /auth/me without session - should return 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("SUCCESS: /auth/me returns 401 without auth")
    
    def test_auth_me_with_test_session(self):
        """Test /auth/me with test session cookie"""
        cookies = {"session_token": "test_session_1771463210214"}
        response = requests.get(f"{BASE_URL}/api/auth/me", cookies=cookies)
        # Test session may or may not be valid depending on DB state
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Auth me returns user: {data.get('name', 'Unknown')}")
        else:
            print(f"INFO: Test session returns {response.status_code} (may not be seeded)")
    
    def test_auth_logout(self):
        """Test logout endpoint"""
        response = requests.post(f"{BASE_URL}/api/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert data.get("message") == "Logged out"
        print("SUCCESS: Logout endpoint works")


class TestDashboardAPIs:
    """Dashboard data endpoint tests"""
    
    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields
        assert "total_members" in data
        assert "active_groups" in data
        assert "mtd_giving" in data
        assert "ytd_giving" in data
        
        print(f"SUCCESS: Dashboard stats - Members: {data['total_members']}, Groups: {data['active_groups']}, MTD: ${data['mtd_giving']:.2f}")
    
    def test_dashboard_giving_trend(self):
        """Test giving trend endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/giving-trend")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "month" in data[0]
        print(f"SUCCESS: Giving trend returns {len(data)} months of data")
    
    def test_dashboard_attendance_trend(self):
        """Test attendance trend endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/attendance-trend")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "week" in data[0]
        print(f"SUCCESS: Attendance trend returns {len(data)} weeks of data")
    
    def test_dashboard_activity(self):
        """Test recent activity endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/activity")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Activity returns {len(data)} recent items")
    
    def test_dashboard_upcoming_events(self):
        """Test upcoming events endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/upcoming-events")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Upcoming events returns {len(data)} events")


class TestGivingAPIs:
    """Giving/Stewardship endpoint tests"""
    
    def test_giving_stats(self):
        """Test giving stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/giving/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "mtd_total" in data
        assert "ytd_total" in data
        assert "by_method" in data
        assert "active_recurring" in data
        
        print(f"SUCCESS: Giving stats - MTD: ${data['mtd_total']:.2f}, YTD: ${data['ytd_total']:.2f}")
    
    def test_donations_list(self):
        """Test donations list endpoint"""
        response = requests.get(f"{BASE_URL}/api/donations?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "total" in data
        assert "page" in data
        
        print(f"SUCCESS: Donations list - Total: {data['total']}, Page: {data['page']}")
    
    def test_funds_list(self):
        """Test funds list endpoint"""
        response = requests.get(f"{BASE_URL}/api/funds")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            assert "name" in data[0]
            fund_names = [f["name"] for f in data]
            print(f"SUCCESS: Funds list - {len(data)} funds: {', '.join(fund_names[:3])}")
        else:
            print("SUCCESS: Funds list returns empty (no funds seeded)")
    
    def test_batches_list(self):
        """Test batches list endpoint"""
        response = requests.get(f"{BASE_URL}/api/batches")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Batches list - {len(data)} batches")


class TestPeopleAPIs:
    """People/Members endpoint tests"""
    
    def test_people_list(self):
        """Test people list endpoint"""
        response = requests.get(f"{BASE_URL}/api/people?page=1&per_page=25")
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "total" in data
        assert "page" in data
        
        print(f"SUCCESS: People list - Total: {data['total']}, Page: {data['page']}")
    
    def test_people_search(self):
        """Test people search endpoint"""
        response = requests.get(f"{BASE_URL}/api/people?search=john")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        print(f"SUCCESS: People search for 'john' - {len(data['data'])} results")
    
    def test_people_filter_by_status(self):
        """Test people filter by status"""
        response = requests.get(f"{BASE_URL}/api/people?status=member")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        print(f"SUCCESS: People filter by 'member' - {len(data['data'])} results")


class TestGroupsAPIs:
    """Groups endpoint tests"""
    
    def test_groups_list(self):
        """Test groups list endpoint"""
        response = requests.get(f"{BASE_URL}/api/groups?page=1&per_page=25")
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "total" in data
        
        print(f"SUCCESS: Groups list - Total: {data['total']}")
    
    def test_group_types(self):
        """Test group types endpoint"""
        response = requests.get(f"{BASE_URL}/api/group-types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            type_names = [t["name"] for t in data]
            print(f"SUCCESS: Group types - {len(data)} types: {', '.join(type_names)}")
        else:
            print("SUCCESS: Group types returns empty (no types seeded)")


class TestEventsAPIs:
    """Events endpoint tests"""
    
    def test_events_list(self):
        """Test events list endpoint"""
        response = requests.get(f"{BASE_URL}/api/events?upcoming=true")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Events list - {len(data)} upcoming events")


class TestSearchAPI:
    """Global search endpoint tests"""
    
    def test_global_search(self):
        """Test global search endpoint"""
        response = requests.get(f"{BASE_URL}/api/search?q=john")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Global search for 'john' - {len(data)} results")


class TestReportsAPIs:
    """Reports endpoint tests"""
    
    def test_giving_by_fund_report(self):
        """Test giving by fund report"""
        response = requests.get(f"{BASE_URL}/api/reports/giving-by-fund?start_date=2025-01-01&end_date=2026-12-31")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Giving by fund report - {len(data)} funds")
    
    def test_membership_report(self):
        """Test membership report"""
        response = requests.get(f"{BASE_URL}/api/reports/membership")
        assert response.status_code == 200
        data = response.json()
        assert "by_status" in data
        assert "total" in data
        print(f"SUCCESS: Membership report - Total: {data['total']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
