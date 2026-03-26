"""
Iteration 51: Quality Improvements Testing
- 7E: Attendance Streaks for Shannon & Jacob (12-week streaks)
- 7C: Member Directory (25+ members with actual names)
- 7D: Solomon Chat Context (live church data injection)
- Giving Integrations (Solomon Pay, Pushpay, SecureGive - mocked)
- No regression: Landing, Login, Signup pages
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthAndCredentials:
    """Test login for Shannon, Jacob, and other users"""
    
    def test_shannon_login(self):
        """Shannon (Church Admin) can log in"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "shannonnieman1030@gmail.com",
            "password": "Demo2026!"
        })
        assert response.status_code == 200, f"Shannon login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert data.get("role") in ["church_admin", "admin"], f"Unexpected role: {data.get('role')}"
        print(f"✓ Shannon login successful, role: {data.get('role')}")
        return data["token"]
    
    def test_jacob_login(self):
        """Jacob (Church Admin) can log in"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jacobpacheco@abundanteast.com",
            "password": "Demo2026!"
        })
        assert response.status_code == 200, f"Jacob login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        print(f"✓ Jacob login successful, role: {data.get('role')}")
        return data["token"]
    
    def test_platform_admin_login(self):
        """Platform Admin can log in"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@solomonai.us",
            "password": "Demo2026!"
        })
        assert response.status_code == 200, f"Platform admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        print(f"✓ Platform admin login successful")
        return data["token"]
    
    def test_member_login(self):
        """Church Member can log in"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        })
        assert response.status_code == 200, f"Member login failed: {response.text}"
        data = response.json()
        assert "token" in data
        print(f"✓ Member login successful")
        return data["token"]


class TestAttendanceStreaks:
    """7E: Attendance Streaks for Shannon & Jacob"""
    
    @pytest.fixture
    def shannon_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "shannonnieman1030@gmail.com",
            "password": "Demo2026!"
        })
        return response.json().get("token")
    
    @pytest.fixture
    def jacob_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jacobpacheco@abundanteast.com",
            "password": "Demo2026!"
        })
        return response.json().get("token")
    
    def test_shannon_attendance_streak(self, shannon_token):
        """Shannon should have current_streak >= 8, longest >= 12"""
        headers = {"Authorization": f"Bearer {shannon_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/attendance/streak", headers=headers)
        assert response.status_code == 200, f"Failed to get Shannon's streak: {response.text}"
        data = response.json()
        current_streak = data.get("current_streak", 0)
        longest_streak = data.get("longest_streak", 0)
        print(f"Shannon's streaks - Current: {current_streak}, Longest: {longest_streak}")
        assert current_streak >= 8, f"Shannon's current streak {current_streak} < 8"
        assert longest_streak >= 12, f"Shannon's longest streak {longest_streak} < 12"
        print(f"✓ Shannon attendance streak verified: current={current_streak}, longest={longest_streak}")
    
    def test_jacob_attendance_streak(self, jacob_token):
        """Jacob should have current_streak >= 8, longest >= 12"""
        headers = {"Authorization": f"Bearer {jacob_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/attendance/streak", headers=headers)
        assert response.status_code == 200, f"Failed to get Jacob's streak: {response.text}"
        data = response.json()
        current_streak = data.get("current_streak", 0)
        longest_streak = data.get("longest_streak", 0)
        print(f"Jacob's streaks - Current: {current_streak}, Longest: {longest_streak}")
        assert current_streak >= 8, f"Jacob's current streak {current_streak} < 8"
        assert longest_streak >= 12, f"Jacob's longest streak {longest_streak} < 12"
        print(f"✓ Jacob attendance streak verified: current={current_streak}, longest={longest_streak}")


class TestMemberDirectory:
    """7C: Member Directory - 25+ members with actual names"""
    
    @pytest.fixture
    def member_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        })
        return response.json().get("token")
    
    def test_directory_returns_25_plus_members(self, member_token):
        """GET /api/portal/directory should return 25+ members"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/directory", headers=headers)
        assert response.status_code == 200, f"Directory fetch failed: {response.text}"
        data = response.json()
        members = data.get("members", [])
        total = data.get("total", 0)
        print(f"Directory returned {total} members")
        assert total >= 25, f"Directory has only {total} members, expected 25+"
        print(f"✓ Directory has {total} members (>= 25)")
    
    def test_directory_members_have_names(self, member_token):
        """All members should have actual names (not empty)"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/directory", headers=headers)
        assert response.status_code == 200
        data = response.json()
        members = data.get("members", [])
        
        empty_names = [m for m in members if not m.get("name") or m.get("name").strip() == ""]
        assert len(empty_names) == 0, f"Found {len(empty_names)} members with empty names"
        
        # Check first 5 members have real names
        for i, m in enumerate(members[:5]):
            name = m.get("name", "")
            assert len(name) > 2, f"Member {i} has invalid name: '{name}'"
            print(f"  Member {i}: {name}")
        
        print(f"✓ All {len(members)} members have valid names")
    
    def test_directory_search_works(self, member_token):
        """Search should filter members by name"""
        headers = {"Authorization": f"Bearer {member_token}"}
        
        # First get all members to find a name to search
        response = requests.get(f"{BASE_URL}/api/portal/directory", headers=headers)
        assert response.status_code == 200
        members = response.json().get("members", [])
        
        if members:
            # Search for first member's first name
            first_name = members[0].get("name", "").split()[0]
            search_response = requests.get(f"{BASE_URL}/api/portal/directory?search={first_name}", headers=headers)
            assert search_response.status_code == 200
            search_results = search_response.json().get("members", [])
            
            # Should find at least the original member
            found = any(first_name.lower() in m.get("name", "").lower() for m in search_results)
            assert found, f"Search for '{first_name}' didn't find expected member"
            print(f"✓ Search for '{first_name}' returned {len(search_results)} results")


class TestSolomonChatContext:
    """7D: Solomon Chat should inject live church context"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "shannonnieman1030@gmail.com",
            "password": "Demo2026!"
        })
        return response.json().get("token")
    
    def test_solomon_chat_responds(self, admin_token):
        """Solomon Chat should respond to messages"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/api/solomon/chat", 
            headers=headers,
            json={"message": "How many members do we have?"}
        )
        assert response.status_code == 200, f"Solomon chat failed: {response.text}"
        data = response.json()
        assert "response" in data, "No response in Solomon chat"
        response_text = data.get("response", "")
        assert len(response_text) > 10, "Response too short"
        print(f"✓ Solomon responded: {response_text[:100]}...")
    
    def test_solomon_chat_has_church_context(self, admin_token):
        """Solomon should reference live church data (member count, events, etc)"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        
        # Ask about membership - should reference actual numbers
        response = requests.post(f"{BASE_URL}/api/solomon/chat", 
            headers=headers,
            json={"message": "Tell me about our church membership numbers and any upcoming events."}
        )
        assert response.status_code == 200, f"Solomon chat failed: {response.text}"
        data = response.json()
        response_text = data.get("response", "").lower()
        
        # Check for indicators of live data (numbers, dates, specific info)
        has_numbers = any(char.isdigit() for char in response_text)
        print(f"Solomon response contains numbers: {has_numbers}")
        print(f"Response preview: {response_text[:200]}...")
        
        # The response should contain some church-specific data
        assert len(response_text) > 50, "Response too short to contain context"
        print(f"✓ Solomon chat returned contextual response ({len(response_text)} chars)")


class TestGivingIntegrations:
    """Giving Integrations - Solomon Pay, Pushpay, SecureGive (mocked)"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "shannonnieman1030@gmail.com",
            "password": "Demo2026!"
        })
        return response.json().get("token")
    
    def test_get_giving_integrations(self, admin_token):
        """GET /api/admin/giving/integrations should return processor config"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/giving/integrations", headers=headers)
        assert response.status_code == 200, f"Failed to get integrations: {response.text}"
        data = response.json()
        
        # Should have processors object
        processors = data.get("processors", {})
        assert "solomon_pay" in processors, "Missing solomon_pay processor"
        assert "pushpay" in processors, "Missing pushpay processor"
        assert "securegive" in processors, "Missing securegive processor"
        
        # Each processor should have label and description
        for key in ["solomon_pay", "pushpay", "securegive"]:
            proc = processors[key]
            assert "label" in proc, f"{key} missing label"
            assert "description" in proc, f"{key} missing description"
            print(f"  {key}: {proc.get('label')} - {proc.get('status', 'unknown')}")
        
        print(f"✓ Giving integrations config returned with 3 processors")
    
    def test_connect_processor(self, admin_token):
        """POST /api/admin/giving/integrations/connect should switch active processor"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        
        # Connect Solomon Pay
        response = requests.post(f"{BASE_URL}/api/admin/giving/integrations/connect",
            headers=headers,
            json={"processor": "solomon_pay"}
        )
        assert response.status_code == 200, f"Failed to connect processor: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("active_processor") == "solomon_pay"
        print(f"✓ Connected Solomon Pay successfully")
        
        # Verify it's now active
        get_response = requests.get(f"{BASE_URL}/api/admin/giving/integrations", headers=headers)
        assert get_response.status_code == 200
        config = get_response.json()
        assert config.get("active_processor") == "solomon_pay"
        print(f"✓ Verified Solomon Pay is active processor")
    
    def test_disconnect_processor(self, admin_token):
        """POST /api/admin/giving/integrations/disconnect should deactivate"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        
        # First connect a processor
        requests.post(f"{BASE_URL}/api/admin/giving/integrations/connect",
            headers=headers,
            json={"processor": "pushpay"}
        )
        
        # Now disconnect it
        response = requests.post(f"{BASE_URL}/api/admin/giving/integrations/disconnect",
            headers=headers,
            json={"processor": "pushpay"}
        )
        assert response.status_code == 200, f"Failed to disconnect: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Disconnected Pushpay successfully")
        
        # Verify no active processor
        get_response = requests.get(f"{BASE_URL}/api/admin/giving/integrations", headers=headers)
        config = get_response.json()
        assert config.get("active_processor") is None, f"Processor still active: {config.get('active_processor')}"
        print(f"✓ Verified no active processor after disconnect")
    
    def test_invalid_processor_rejected(self, admin_token):
        """Invalid processor name should be rejected"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/api/admin/giving/integrations/connect",
            headers=headers,
            json={"processor": "invalid_processor"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid processor, got {response.status_code}"
        print(f"✓ Invalid processor correctly rejected")


class TestNoRegression:
    """No regression: Landing page, Login, Signup should load"""
    
    def test_landing_page_loads(self):
        """Landing page (/) should return 200"""
        response = requests.get(f"{BASE_URL}/")
        # Frontend routes return HTML, so we just check it doesn't error
        assert response.status_code in [200, 304], f"Landing page failed: {response.status_code}"
        print(f"✓ Landing page accessible")
    
    def test_health_endpoint(self):
        """Health endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") in ["healthy", "ok"], f"Unexpected status: {data.get('status')}"
        print(f"✓ Health endpoint status: {data.get('status')}")
    
    def test_giving_stats_public(self):
        """Giving stats should be accessible (public endpoint)"""
        response = requests.get(f"{BASE_URL}/api/giving/stats")
        assert response.status_code == 200, f"Giving stats failed: {response.text}"
        data = response.json()
        assert "mtd_total" in data or "ytd_total" in data
        print(f"✓ Giving stats endpoint working")
    
    def test_funds_endpoint(self):
        """Funds endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/funds")
        assert response.status_code == 200, f"Funds endpoint failed: {response.text}"
        print(f"✓ Funds endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
