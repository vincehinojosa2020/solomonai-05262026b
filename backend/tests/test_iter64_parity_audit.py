"""
Solomon AI — Iteration 64: Post-Parity-Audit Testing
=====================================================
Tests all 12 P0 bug fixes from the parity audit.
Uses class-scoped sessions to minimize login attempts (rate limit: 5/min/IP)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://parity-audit-1.preview.emergentagent.com").rstrip("/")

# Test credentials
PLATFORM_ADMIN = {"email": "admin@solomonai.us", "password": "Demo2026!"}
CHURCH_ADMIN = {"email": "shannonnieman1030@gmail.com", "password": "Demo2026!"}
PORTAL_MEMBER = {"email": "member@abundant.church", "password": "Demo2026!"}

# Global sessions to minimize login attempts
_sessions = {}


def get_session(user_type):
    """Get or create a session for the given user type"""
    if user_type not in _sessions:
        session = requests.Session()
        creds = {
            "platform_admin": PLATFORM_ADMIN,
            "church_admin": CHURCH_ADMIN,
            "member": PORTAL_MEMBER
        }[user_type]
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=creds)
        if response.status_code == 429:
            pytest.skip("Rate limited - wait 65 seconds and retry")
        assert response.status_code == 200, f"Login failed: {response.text}"
        _sessions[user_type] = session
    return _sessions[user_type]


class TestHealthEndpoints:
    """Basic health check tests"""
    
    def test_health_check(self):
        """Test basic health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print(f"✓ Health check passed: {data}")
    
    def test_health_detailed(self):
        """Test detailed health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        print(f"✓ Detailed health check passed: {data}")


class TestAuthenticationFlows:
    """Test authentication for all three user types"""
    
    def test_platform_admin_login(self):
        """Test platform admin login"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
        if response.status_code == 429:
            pytest.skip("Rate limited")
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Response has user data at top level (not nested under "user")
        assert data.get("role") == "platform_admin" or data.get("user", {}).get("role") == "platform_admin"
        print(f"✓ Platform admin login: {data.get('email')} - role: {data.get('role')}")
        _sessions["platform_admin"] = session
    
    def test_church_admin_login(self):
        """Test church admin login"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        if response.status_code == 429:
            pytest.skip("Rate limited")
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data.get("role") == "church_admin" or data.get("user", {}).get("role") == "church_admin"
        print(f"✓ Church admin login: {data.get('email')} - role: {data.get('role')}")
        _sessions["church_admin"] = session
    
    def test_portal_member_login(self):
        """Test portal member login"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=PORTAL_MEMBER)
        if response.status_code == 429:
            pytest.skip("Rate limited")
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data.get("role") == "member" or data.get("user", {}).get("role") == "member"
        print(f"✓ Portal member login: {data.get('email')} - role: {data.get('role')}")
        _sessions["member"] = session


class TestAdminEndpoints:
    """Test admin endpoints with church admin session"""
    
    def test_admin_members(self):
        """GET /api/admin/members - returns members list"""
        session = get_session("church_admin")
        response = session.get(f"{BASE_URL}/api/admin/members")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        count = len(data.get("members", data))
        print(f"✓ Admin members: {count} members returned")
    
    def test_admin_giving_summary(self):
        """GET /api/admin/giving/summary - returns giving metrics (P0 fix: import)"""
        session = get_session("church_admin")
        response = session.get(f"{BASE_URL}/api/admin/giving/summary")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"✓ Admin giving summary: YTD=${data.get('ytd_total', 0):,.2f}")
    
    def test_admin_giving_export(self):
        """GET /api/admin/giving/export - returns CSV (P0 fix: StreamingResponse)"""
        session = get_session("church_admin")
        response = session.get(f"{BASE_URL}/api/admin/giving/export")
        assert response.status_code == 200, f"Failed: {response.text}"
        assert "text/csv" in response.headers.get("content-type", "")
        print(f"✓ Admin giving export: CSV returned ({len(response.content)} bytes)")
    
    def test_admin_giving_settings(self):
        """GET /api/admin/giving/settings - returns settings (P0 fix: RBAC)"""
        session = get_session("church_admin")
        response = session.get(f"{BASE_URL}/api/admin/giving/settings")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"✓ Admin giving settings: active_processor={data.get('active_processor')}")
    
    def test_admin_checkin_stations(self):
        """GET /api/admin/checkin/stations - returns stations"""
        session = get_session("church_admin")
        response = session.get(f"{BASE_URL}/api/admin/checkin/stations")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        count = len(data.get("stations", data))
        print(f"✓ Admin checkin stations: {count} stations")
    
    def test_admin_groups(self):
        """GET /api/admin/groups - returns groups"""
        session = get_session("church_admin")
        response = session.get(f"{BASE_URL}/api/admin/groups")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        count = len(data.get("groups", data))
        print(f"✓ Admin groups: {count} groups returned")
    
    def test_admin_events(self):
        """GET /api/admin/events - returns events"""
        session = get_session("church_admin")
        response = session.get(f"{BASE_URL}/api/admin/events")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        count = len(data.get("events", data))
        print(f"✓ Admin events: {count} events returned")
    
    def test_admin_prayer_dashboard(self):
        """GET /api/admin/prayer/dashboard - returns prayer data (P0 fix: PRAYER_CATEGORIES)"""
        session = get_session("church_admin")
        response = session.get(f"{BASE_URL}/api/admin/prayer/dashboard")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "categories" in data, "Missing categories in response"
        print(f"✓ Admin prayer dashboard: {len(data.get('categories', []))} categories")


class TestSolomonPayEndpoints:
    """Test SolomonPay endpoints (P0 fix: get_current_portal_user import)"""
    
    def test_solomonpay_transactions(self):
        """GET /api/solomonpay/transactions - returns transactions (P0 fix)"""
        session = get_session("church_admin")
        response = session.get(f"{BASE_URL}/api/solomonpay/transactions")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "transactions" in data
        print(f"✓ SolomonPay transactions: {len(data['transactions'])} transactions")


class TestPaymentMethodsEndpoints:
    """Test payment methods endpoints (P0 fix: get_session_token_from_request)"""
    
    def test_payments_methods(self):
        """GET /api/payments/methods - returns methods (P0 fix)"""
        session = get_session("member")
        response = session.get(f"{BASE_URL}/api/payments/methods")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "payment_methods" in data
        print(f"✓ Payment methods: {len(data['payment_methods'])} methods")


class TestPortalEndpoints:
    """Test portal endpoints (P0 fix: get_session_token_from_request)"""
    
    def test_portal_profile(self):
        """GET /api/portal/profile - returns member profile"""
        session = get_session("member")
        response = session.get(f"{BASE_URL}/api/portal/profile")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "user" in data
        print(f"✓ Portal profile: {data['user'].get('name', data['user'].get('email'))}")
    
    def test_portal_media_featured(self):
        """GET /api/portal/media/featured - returns featured media (P0 fix)"""
        session = get_session("member")
        response = session.get(f"{BASE_URL}/api/portal/media/featured")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"✓ Portal media featured: video={data.get('video', {}).get('title', 'None')}")
    
    def test_portal_volunteer_schedule(self):
        """GET /api/portal/volunteer/schedule - returns schedule (P0 fix)"""
        session = get_session("member")
        response = session.get(f"{BASE_URL}/api/portal/volunteer/schedule")
        # May return 200 or 404 if no schedule exists
        assert response.status_code in [200, 404], f"Failed: {response.text}"
        print(f"✓ Portal volunteer schedule: status {response.status_code}")


class TestTenantEndpoints:
    """Test tenant endpoints (P0 fix: get_session_token_from_request)"""
    
    def test_tenant_info(self):
        """GET /api/tenant - returns tenant info (P0 fix)"""
        response = requests.get(f"{BASE_URL}/api/tenant")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data or "name" in data
        print(f"✓ Tenant info: {data.get('name', data.get('id'))}")


class TestPlatformAdminEndpoints:
    """Test platform admin only endpoints"""
    
    def test_admin_leads(self):
        """GET /api/admin/leads - returns leads (platform admin only)"""
        session = get_session("platform_admin")
        response = session.get(f"{BASE_URL}/api/admin/leads")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "leads" in data
        print(f"✓ Admin leads: {len(data['leads'])} leads")


class TestSolomonChatEndpoint:
    """Test Solomon AI chat endpoint"""
    
    def test_solomon_chat(self):
        """POST /api/solomon/chat - AI responds with church context"""
        session = get_session("church_admin")
        response = session.post(
            f"{BASE_URL}/api/solomon/chat",
            json={
                "message": "What is the church attendance trend?",
                "conversation_id": "test-iter64"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "response" in data or "message" in data
        print(f"✓ Solomon chat: AI responded")


class TestRBACPermissions:
    """Test RBAC permission fixes"""
    
    def test_giving_settings_requires_auth(self):
        """Verify giving settings requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/giving/settings")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Giving settings requires auth")
    
    def test_giving_export_requires_auth(self):
        """Verify giving export requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/giving/export")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Giving export requires auth")
    
    def test_leads_requires_platform_admin(self):
        """Verify leads endpoint requires platform admin"""
        # Use church admin session (not platform admin)
        session = get_session("church_admin")
        response = session.get(f"{BASE_URL}/api/admin/leads")
        # Should be 403 Forbidden for non-platform admin
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Leads requires platform admin")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
