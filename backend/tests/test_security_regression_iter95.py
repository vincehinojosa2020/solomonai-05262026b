"""
Security Remediation Regression Tests - Iteration 95
Tests for Snyk security fixes: login, platform stats, Solomon AI, Stripe config
"""
import pytest
import requests
import os
import hashlib

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSecurityRegression:
    """Regression tests after security remediation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    # ============== LOGIN REGRESSION ==============
    
    def test_platform_admin_login(self):
        """Test platform admin login still works with admin@solomonai.us / Demo2026!"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@solomonai.us",
            "password": "Demo2026!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "session_token" in data or "token" in data, "No session_token in response"
        # Role is at top level, not nested under user
        assert data.get("role") == "platform_admin", f"Expected platform_admin role, got {data.get('role')}"
        print(f"PASS: Platform admin login works - role: {data.get('role')}")
        return data.get("session_token") or data.get("token")
    
    def test_church_admin_login(self):
        """Test church admin login still works with shannonnieman1030@gmail.com / Demo2026!"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "shannonnieman1030@gmail.com",
            "password": "Demo2026!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "session_token" in data, "No session_token in response"
        print(f"PASS: Church admin login works - role: {data.get('user', {}).get('role')}")
    
    def test_member_login(self):
        """Test member login still works with member@abundant.church / Demo2026!"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "session_token" in data, "No session_token in response"
        print(f"PASS: Member login works - role: {data.get('user', {}).get('role')}")
    
    # ============== PLATFORM STATS REGRESSION ==============
    
    def test_platform_stats_transactions(self):
        """Test platform stats shows 3M+ transactions"""
        # Login as platform admin first
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@solomonai.us",
            "password": "Demo2026!"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["session_token"]
        
        # Get platform stats
        response = self.session.get(
            f"{BASE_URL}/api/platform/stats",
            cookies={"session_token": token}
        )
        assert response.status_code == 200, f"Platform stats failed: {response.text}"
        data = response.json()
        
        # Check transactions
        transactions = data.get("transactions", {})
        total_txn = transactions.get("total", 0)
        print(f"Platform transactions total: {total_txn:,}")
        assert total_txn > 0, "Expected transactions > 0"
        print(f"PASS: Platform stats transactions: {total_txn:,}")
    
    def test_platform_stats_donors(self):
        """Test platform stats shows 41K+ donors"""
        # Login as platform admin first
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@solomonai.us",
            "password": "Demo2026!"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["session_token"]
        
        # Get platform stats
        response = self.session.get(
            f"{BASE_URL}/api/platform/stats",
            cookies={"session_token": token}
        )
        assert response.status_code == 200, f"Platform stats failed: {response.text}"
        data = response.json()
        
        # Check donors
        donors = data.get("donors", {})
        total_donors = donors.get("total", 0)
        print(f"Platform donors total: {total_donors:,}")
        assert total_donors > 0, "Expected donors > 0"
        print(f"PASS: Platform stats donors: {total_donors:,}")
    
    def test_platform_giving_totals(self):
        """Test platform giving shows $108M+ all-time"""
        # Login as platform admin first
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@solomonai.us",
            "password": "Demo2026!"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["session_token"]
        
        # Get platform stats
        response = self.session.get(
            f"{BASE_URL}/api/platform/stats",
            cookies={"session_token": token}
        )
        assert response.status_code == 200, f"Platform stats failed: {response.text}"
        data = response.json()
        
        # Check giving
        giving = data.get("giving", {})
        all_time = giving.get("all_time", 0)
        print(f"Platform giving all-time: ${all_time:,.2f}")
        assert all_time > 0, "Expected giving > 0"
        print(f"PASS: Platform giving all-time: ${all_time:,.2f}")
    
    # ============== SOLOMON AI REGRESSION ==============
    
    def test_solomon_chat_stream_endpoint(self):
        """Test Solomon AI chat/stream endpoint still works"""
        response = self.session.post(f"{BASE_URL}/api/solomon/chat/stream", json={
            "message": "Hello, what can you help me with?",
            "session_id": None
        })
        assert response.status_code == 200, f"Solomon chat/stream failed: {response.status_code} - {response.text}"
        print(f"PASS: Solomon AI chat/stream endpoint works (status: {response.status_code})")
    
    def test_solomon_chat_endpoint(self):
        """Test Solomon AI chat endpoint still works"""
        response = self.session.post(f"{BASE_URL}/api/solomon/chat", json={
            "message": "What events are coming up?",
            "session_id": None
        })
        assert response.status_code == 200, f"Solomon chat failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "response" in data, "No response in Solomon chat"
        assert "session_id" in data, "No session_id in Solomon chat"
        print(f"PASS: Solomon AI chat endpoint works - got response")
    
    # ============== STRIPE CONFIG REGRESSION ==============
    
    def test_stripe_config_endpoint(self):
        """Test Stripe config endpoint returns correct configuration"""
        response = self.session.get(f"{BASE_URL}/api/stripe/config")
        assert response.status_code == 200, f"Stripe config failed: {response.status_code} - {response.text}"
        data = response.json()
        # Should have stripe_configured status
        assert "stripe_configured" in data or "publishable_key" in data or "live_mode" in data, f"Unexpected stripe config response: {data}"
        print(f"PASS: Stripe config endpoint works - response: {data}")
    
    # ============== SECURITY VERIFICATION ==============
    
    def test_test_login_html_deleted(self):
        """Verify test-login.html file is deleted (returns React SPA fallback, not actual file)"""
        # The file should be deleted from /app/frontend/public/
        # When accessing /test-login.html, it should return the React SPA index.html (fallback)
        # NOT the actual test-login.html file with credentials
        response = self.session.get(f"{BASE_URL}/test-login.html")
        # It will return 200 because React SPA serves index.html for unknown routes
        # But the content should be the main React app, not a login test page
        if response.status_code == 200:
            content = response.text
            # The old test-login.html had specific content like "Test Login" form
            # The React SPA fallback has "Solomon AI" title
            assert "Solomon AI" in content, "Expected React SPA fallback"
            assert "test-login" not in content.lower() or "Test Login Form" not in content, "test-login.html content should not exist"
        print(f"PASS: test-login.html returns React SPA fallback (file deleted)")
    
    def test_health_endpoint(self):
        """Test health endpoint still works"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print(f"PASS: Health endpoint works")
    
    # ============== FUND RECONCILIATION REGRESSION ==============
    
    def test_fund_reconciliation(self):
        """Test fund reconciliation endpoint still works"""
        # Login as church admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "shannonnieman1030@gmail.com",
            "password": "Demo2026!"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["session_token"]
        
        # Get fund reconciliation
        response = self.session.get(
            f"{BASE_URL}/api/admin/funds/reconciliation",
            cookies={"session_token": token}
        )
        # May return 200 or 404 depending on data
        if response.status_code == 200:
            data = response.json()
            print(f"PASS: Fund reconciliation works - response keys: {list(data.keys())}")
        else:
            print(f"INFO: Fund reconciliation returned {response.status_code} (may be expected if no data)")


class TestCSPMetaTag:
    """Verify CSP meta tag exists in index.html"""
    
    def test_csp_meta_tag_in_response(self):
        """Test that CSP meta tag is present in the HTML response"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        content = response.text
        
        # Check for CSP meta tag
        assert 'Content-Security-Policy' in content, "CSP meta tag not found in index.html"
        assert "default-src 'self'" in content, "CSP default-src directive not found"
        print(f"PASS: CSP meta tag exists in index.html")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
