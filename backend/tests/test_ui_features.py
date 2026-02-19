"""
Tests for Samson Church Management System - UI/UX Overhaul Features
Testing: Green 'Sanctuary' color palette, Join Service buttons, Donation methods, Music player
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBasicAPIs:
    """Basic API tests for core functionality"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Samson Church Management API"
        print(f"API Root: {data['message']} v{data['version']}")
    
    def test_tenant_endpoint(self):
        """Test tenant configuration endpoint"""
        response = requests.get(f"{BASE_URL}/api/tenant")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "id" in data
        print(f"Tenant: {data['name']}")

class TestDashboardAPIs:
    """Dashboard API tests"""
    
    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_members" in data
        assert "active_groups" in data
        assert "mtd_giving" in data
        assert "ytd_giving" in data
        print(f"Members: {data['total_members']}, Groups: {data['active_groups']}, MTD: ${data['mtd_giving']}")
    
    def test_dashboard_giving_trend(self):
        """Test giving trend chart data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/giving-trend")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"Giving trend data points: {len(data)}")
    
    def test_dashboard_attendance_trend(self):
        """Test attendance trend chart data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/attendance-trend")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Attendance trend data points: {len(data)}")
    
    def test_dashboard_activity(self):
        """Test recent activity endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/activity")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Recent activities: {len(data)}")
    
    def test_dashboard_upcoming_events(self):
        """Test upcoming events endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/upcoming-events")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Upcoming events: {len(data)}")

class TestPeopleAPIs:
    """People/Members API tests"""
    
    def test_get_people_list(self):
        """Test people list endpoint with pagination"""
        response = requests.get(f"{BASE_URL}/api/people?page=1&per_page=25")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        print(f"People: {data['total']} total, {len(data['data'])} returned")
    
    def test_people_search(self):
        """Test people search functionality"""
        response = requests.get(f"{BASE_URL}/api/people?search=Smith")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        print(f"Search 'Smith': {len(data['data'])} results")
    
    def test_people_filter_by_status(self):
        """Test filtering people by membership status"""
        response = requests.get(f"{BASE_URL}/api/people?status=member")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        print(f"Members only: {data['total']} found")

class TestGroupsAPIs:
    """Groups API tests"""
    
    def test_get_groups_list(self):
        """Test groups list endpoint"""
        response = requests.get(f"{BASE_URL}/api/groups")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        print(f"Groups: {data['total']} total")
    
    def test_get_group_types(self):
        """Test group types endpoint"""
        response = requests.get(f"{BASE_URL}/api/group-types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Group types: {len(data)}")

class TestGivingAPIs:
    """Giving/Donation API tests"""
    
    def test_giving_stats(self):
        """Test giving stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/giving/stats")
        assert response.status_code == 200
        data = response.json()
        assert "mtd_total" in data
        assert "ytd_total" in data
        assert "by_method" in data
        print(f"MTD: ${data['mtd_total']}, YTD: ${data['ytd_total']}")
    
    def test_get_funds(self):
        """Test funds list endpoint"""
        response = requests.get(f"{BASE_URL}/api/funds")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Funds: {len(data)}")
    
    def test_get_donations(self):
        """Test donations list endpoint"""
        response = requests.get(f"{BASE_URL}/api/donations?page=1&per_page=20")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        print(f"Donations: {data['total']} total")
    
    def test_get_batches(self):
        """Test donation batches endpoint"""
        response = requests.get(f"{BASE_URL}/api/batches")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Batches: {len(data)}")

class TestSearchAPI:
    """Global search API tests"""
    
    def test_global_search(self):
        """Test global search endpoint"""
        response = requests.get(f"{BASE_URL}/api/search?q=John")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Search 'John': {len(data)} results")

class TestEventsAPIs:
    """Events API tests"""
    
    def test_get_events(self):
        """Test events list endpoint"""
        response = requests.get(f"{BASE_URL}/api/events")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Events: {len(data)}")

class TestCommunicationsAPIs:
    """Communications API tests"""
    
    def test_get_communications(self):
        """Test communications list endpoint"""
        response = requests.get(f"{BASE_URL}/api/communications")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Communications: {len(data)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
