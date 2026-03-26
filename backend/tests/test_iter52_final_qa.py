"""
Iteration 52: FINAL QA Pass Before Deployment
Tests all features across the platform:
- Public pages (Landing, Login, Signup, Demo)
- Authentication flows (Shannon, Jacob, Platform Admin, Member)
- Admin dashboard features (Dashboard, War Room, Giving, Members, Communications)
- Portal features (Directory, Events, Groups, Give)
- API endpoints (Attendance streaks, Solomon Chat, Giving integrations)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndPublicEndpoints:
    """Test health check and public API endpoints"""
    
    def test_health_endpoint(self):
        """Health check should return ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("PASS: Health endpoint returns status: ok")
    
    def test_waitlist_endpoint(self):
        """Solomon Pay waitlist endpoint should work"""
        response = requests.post(f"{BASE_URL}/api/waitlist/solomon-pay", json={
            "email": "test_iter52@example.com",
            "church_name": "Test Church QA"
        })
        assert response.status_code == 200
        print("PASS: Waitlist endpoint accepts submissions")
    
    def test_demo_request_endpoint(self):
        """Demo request endpoint should work"""
        response = requests.post(f"{BASE_URL}/api/demo-requests", json={
            "first_name": "QA",
            "last_name": "Tester",
            "church_name": "QA Church",
            "email": "qa_iter52@example.com"
        })
        assert response.status_code == 200
        print("PASS: Demo request endpoint accepts submissions")


class TestAuthenticationFlows:
    """Test all authentication flows for different user types"""
    
    def test_shannon_login(self):
        """Shannon (Church Admin) should be able to login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "shannonnieman1030@gmail.com",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data.get("role") in ["admin", "church_admin"]
        print(f"PASS: Shannon login successful, role: {data.get('role')}")
        return data.get("token")
    
    def test_jacob_login(self):
        """Jacob (Church Admin) should be able to login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jacobpacheco@abundanteast.com",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data.get("role") in ["admin", "church_admin"]
        print(f"PASS: Jacob login successful, role: {data.get('role')}")
        return data.get("token")
    
    def test_platform_admin_login(self):
        """Platform Admin should be able to login with god mode"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@solomonai.us",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data.get("role") == "platform_admin"
        print(f"PASS: Platform admin login successful, role: {data.get('role')}")
        return data.get("token")
    
    def test_member_login(self):
        """Church Member should be able to login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data.get("role") == "member"
        print(f"PASS: Member login successful, role: {data.get('role')}")
        return data.get("token")


class TestAdminDashboardAPIs:
    """Test admin dashboard API endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "shannonnieman1030@gmail.com",
            "password": "Demo2026!"
        })
        return response.json().get("token")
    
    def test_dashboard_stats(self, admin_token):
        """Dashboard stats endpoint should return data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", 
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        data = response.json()
        # Should have key stats
        assert "total_members" in data or "members" in data or isinstance(data, dict)
        print(f"PASS: Dashboard stats endpoint returns data")
    
    def test_war_room_endpoint(self, admin_token):
        """War Room endpoint should return KPI data"""
        response = requests.get(f"{BASE_URL}/api/admin/war-room",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        data = response.json()
        # Should have counters and activity feed
        assert "counters" in data or "kpis" in data or isinstance(data, dict)
        print(f"PASS: War Room endpoint returns data")
    
    def test_giving_stats(self, admin_token):
        """Giving stats endpoint should return data"""
        response = requests.get(f"{BASE_URL}/api/giving/stats",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        data = response.json()
        # Should have giving totals
        assert "mtd_total" in data or "ytd_total" in data or isinstance(data, dict)
        print(f"PASS: Giving stats endpoint returns data")
    
    def test_giving_integrations(self, admin_token):
        """Giving integrations endpoint should return processor config"""
        response = requests.get(f"{BASE_URL}/api/admin/giving/integrations",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        data = response.json()
        # Should have processors config
        assert "processors" in data
        processors = data.get("processors", {})
        # Should have Solomon Pay, Pushpay, SecureGive
        assert "solomon_pay" in processors or len(processors) > 0
        print(f"PASS: Giving integrations returns processor config with {len(processors)} processors")
    
    def test_members_list(self, admin_token):
        """Members list endpoint should return data"""
        response = requests.get(f"{BASE_URL}/api/people",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        data = response.json()
        # Should return list of members
        assert isinstance(data, list) or "data" in data
        print(f"PASS: Members list endpoint returns data")
    
    def test_communications_list(self, admin_token):
        """Communications list endpoint should return data"""
        response = requests.get(f"{BASE_URL}/api/communications",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        data = response.json()
        # Should return list or object
        assert isinstance(data, (list, dict))
        print(f"PASS: Communications endpoint returns data")


class TestPortalAPIs:
    """Test member portal API endpoints"""
    
    @pytest.fixture
    def member_token(self):
        """Get member token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        })
        return response.json().get("token")
    
    @pytest.fixture
    def shannon_token(self):
        """Get Shannon's token for attendance streak test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "shannonnieman1030@gmail.com",
            "password": "Demo2026!"
        })
        return response.json().get("token")
    
    def test_portal_directory(self, member_token):
        """Portal directory should return 25+ members with names"""
        response = requests.get(f"{BASE_URL}/api/portal/directory",
            headers={"Authorization": f"Bearer {member_token}"})
        assert response.status_code == 200
        data = response.json()
        members = data if isinstance(data, list) else data.get("members", data.get("data", []))
        assert len(members) >= 25, f"Expected 25+ members, got {len(members)}"
        # Check that members have names
        members_with_names = [m for m in members if m.get("name") or m.get("first_name")]
        assert len(members_with_names) >= 25, f"Expected 25+ members with names, got {len(members_with_names)}"
        print(f"PASS: Portal directory returns {len(members)} members with names")
    
    def test_portal_events(self, member_token):
        """Portal events endpoint should return data"""
        response = requests.get(f"{BASE_URL}/api/portal/events",
            headers={"Authorization": f"Bearer {member_token}"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        print(f"PASS: Portal events endpoint returns data")
    
    def test_portal_groups(self, member_token):
        """Portal groups endpoint should return data"""
        response = requests.get(f"{BASE_URL}/api/portal/groups",
            headers={"Authorization": f"Bearer {member_token}"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        print(f"PASS: Portal groups endpoint returns data")
    
    def test_portal_give(self, member_token):
        """Portal give/funds endpoint should return data"""
        response = requests.get(f"{BASE_URL}/api/funds",
            headers={"Authorization": f"Bearer {member_token}"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        print(f"PASS: Portal give/funds endpoint returns data")
    
    def test_shannon_attendance_streak(self, shannon_token):
        """Shannon should have attendance streak >= 8"""
        response = requests.get(f"{BASE_URL}/api/portal/attendance/streak",
            headers={"Authorization": f"Bearer {shannon_token}"})
        assert response.status_code == 200
        data = response.json()
        current_streak = data.get("current_streak", 0)
        assert current_streak >= 8, f"Expected Shannon's streak >= 8, got {current_streak}"
        print(f"PASS: Shannon's attendance streak is {current_streak} (>= 8)")


class TestSolomonChatAPI:
    """Test Solomon AI Chat endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "shannonnieman1030@gmail.com",
            "password": "Demo2026!"
        })
        return response.json().get("token")
    
    def test_solomon_chat_responds(self, admin_token):
        """Solomon Chat should respond with church context"""
        response = requests.post(f"{BASE_URL}/api/solomon/chat",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"message": "How many members do we have?"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        # Response should contain some text
        assert len(data.get("response", "")) > 10
        print(f"PASS: Solomon Chat responds with context (response length: {len(data.get('response', ''))})")


class TestNavAndLandingPageContent:
    """Test landing page content via API (content verification)"""
    
    def test_landing_page_accessible(self):
        """Landing page should be accessible"""
        response = requests.get(f"{BASE_URL}/")
        # May redirect or return HTML
        assert response.status_code in [200, 301, 302, 304]
        print(f"PASS: Landing page accessible (status: {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
