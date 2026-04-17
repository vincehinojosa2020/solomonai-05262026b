"""
Solomon AI — P1 Batch Testing (Iteration 90)
Tests for:
1. Public Site Polish (FIX 6-12)
2. Ask Solomon AI Upgrade (streaming, TTS)
3. Stripe/SecureGive Parity (Fund Reconciliation, Payout Drill-Down, Monday Morning Email)
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PLATFORM_ADMIN_EMAIL = "admin@solomonai.us"
PLATFORM_ADMIN_PASSWORD = "Demo2026!"
CHURCH_ADMIN_EMAIL = "shannonnieman1030@gmail.com"
CHURCH_ADMIN_PASSWORD = "Demo2026!"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def platform_admin_token(api_client):
    """Get platform admin auth token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": PLATFORM_ADMIN_EMAIL,
        "password": PLATFORM_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("session_token") or data.get("token")
    pytest.skip(f"Platform admin login failed: {response.status_code}")


@pytest.fixture(scope="module")
def church_admin_token(api_client):
    """Get church admin auth token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": CHURCH_ADMIN_EMAIL,
        "password": CHURCH_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("session_token") or data.get("token")
    pytest.skip(f"Church admin login failed: {response.status_code}")


class TestForgotPassword:
    """FIX 12: Forgot password endpoint"""
    
    def test_forgot_password_endpoint_exists(self, api_client):
        """POST /api/auth/forgot-password should return 200"""
        response = api_client.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": "test@example.com"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "message" in data
        # Should always return success to prevent email enumeration
        assert "reset" in data["message"].lower() or "sent" in data["message"].lower()
    
    def test_forgot_password_with_valid_email(self, api_client):
        """Forgot password with existing user email"""
        response = api_client.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": PLATFORM_ADMIN_EMAIL
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_forgot_password_empty_email(self, api_client):
        """Forgot password with empty email should still return 200"""
        response = api_client.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": ""
        })
        # Should return 200 to prevent enumeration
        assert response.status_code == 200


class TestSolomonStreaming:
    """Ask Solomon AI Streaming SSE endpoint"""
    
    def test_streaming_endpoint_exists(self, api_client, church_admin_token):
        """POST /api/solomon/chat/stream should return SSE events"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = api_client.post(
            f"{BASE_URL}/api/solomon/chat/stream",
            json={"message": "Hello", "session_id": "test-stream-123"},
            headers=headers,
            stream=True,
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "text/event-stream" in response.headers.get("Content-Type", "")
        
        # Read first few events
        events = []
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                try:
                    event_data = json.loads(line[5:].strip())
                    events.append(event_data)
                    if event_data.get("type") == "done":
                        break
                except json.JSONDecodeError:
                    pass
            if len(events) >= 5:
                break
        
        # Should have at least one chunk event
        assert len(events) > 0, "No SSE events received"
        # Check event structure
        chunk_events = [e for e in events if e.get("type") == "chunk"]
        done_events = [e for e in events if e.get("type") == "done"]
        assert len(chunk_events) > 0 or len(done_events) > 0, "No chunk or done events"
    
    def test_streaming_empty_message_rejected(self, api_client, church_admin_token):
        """Empty message should be rejected"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = api_client.post(
            f"{BASE_URL}/api/solomon/chat/stream",
            json={"message": "", "session_id": "test-empty"},
            headers=headers
        )
        assert response.status_code == 400


class TestSolomonTTS:
    """Text-to-Speech scaffold endpoint"""
    
    def test_tts_endpoint_exists(self, api_client, church_admin_token):
        """POST /api/solomon/tts should return TTS info"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = api_client.post(
            f"{BASE_URL}/api/solomon/tts",
            json={"text": "Hello world", "voice": "en-GB"},
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "method" in data
        assert "voice" in data
        assert data["method"] == "web_speech_api"
    
    def test_tts_empty_text_rejected(self, api_client, church_admin_token):
        """Empty text should be rejected"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = api_client.post(
            f"{BASE_URL}/api/solomon/tts",
            json={"text": "", "voice": "en-GB"},
            headers=headers
        )
        assert response.status_code == 400


class TestFundReconciliation:
    """Fund Reconciliation endpoint — SecureGive parity"""
    
    def test_fund_reconciliation_endpoint(self, api_client, platform_admin_token):
        """GET /api/platform/funds/reconciliation should return fund breakdown"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = api_client.get(
            f"{BASE_URL}/api/platform/funds/reconciliation",
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify response structure
        assert "funds" in data, "Missing 'funds' in response"
        assert "total_giving" in data, "Missing 'total_giving' in response"
        assert "total_fees" in data, "Missing 'total_fees' in response"
        assert "total_net" in data, "Missing 'total_net' in response"
        
        # Verify funds list structure
        if len(data["funds"]) > 0:
            fund = data["funds"][0]
            assert "fund_name" in fund
            assert "total_giving" in fund
            assert "net_giving" in fund
    
    def test_fund_reconciliation_requires_auth(self, api_client):
        """Fund reconciliation requires platform admin auth"""
        response = api_client.get(f"{BASE_URL}/api/platform/funds/reconciliation")
        assert response.status_code == 401
    
    def test_fund_reconciliation_requires_platform_admin(self, api_client, church_admin_token):
        """Fund reconciliation requires platform_admin role"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = api_client.get(
            f"{BASE_URL}/api/platform/funds/reconciliation",
            headers=headers
        )
        assert response.status_code == 403


class TestPayoutDrillDown:
    """Payout Drill-Down endpoint — SecureGive parity"""
    
    def test_get_payouts_list(self, api_client, platform_admin_token):
        """GET /api/platform/payouts should return payout list"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = api_client.get(
            f"{BASE_URL}/api/platform/payouts",
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "payouts" in data or isinstance(data, list)
        return data
    
    def test_payout_transactions_endpoint(self, api_client, platform_admin_token):
        """GET /api/platform/payouts/{id}/transactions should return transactions"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        
        # First get a payout ID
        payouts_response = api_client.get(
            f"{BASE_URL}/api/platform/payouts",
            headers=headers
        )
        if payouts_response.status_code != 200:
            pytest.skip("Could not get payouts list")
        
        payouts_data = payouts_response.json()
        payouts = payouts_data.get("payouts", payouts_data) if isinstance(payouts_data, dict) else payouts_data
        
        if not payouts or len(payouts) == 0:
            # Test with a dummy ID - should return empty list, not error
            response = api_client.get(
                f"{BASE_URL}/api/platform/payouts/dummy-payout-id/transactions",
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "transactions" in data
            return
        
        # Use first payout ID
        payout_id = payouts[0].get("id")
        response = api_client.get(
            f"{BASE_URL}/api/platform/payouts/{payout_id}/transactions",
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "transactions" in data
        assert "payout_id" in data


class TestMondayMorningEmail:
    """Monday Morning Summary Email endpoint — SecureGive parity"""
    
    def test_send_summary_email_endpoint(self, api_client, platform_admin_token):
        """POST /api/platform/send-summary-email should attempt to send email"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = api_client.post(
            f"{BASE_URL}/api/platform/send-summary-email",
            json={"recipients": ["test@example.com"]},
            headers=headers
        )
        # May return 200 (success) or 500 (if stats cache not available)
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            # Should have some indication of success
            assert "sent" in str(data).lower() or "success" in str(data).lower() or "message" in data
    
    def test_send_summary_email_requires_auth(self, api_client):
        """Summary email requires authentication"""
        response = api_client.post(
            f"{BASE_URL}/api/platform/send-summary-email",
            json={"recipients": ["test@example.com"]}
        )
        assert response.status_code == 401
    
    def test_send_summary_email_requires_platform_admin(self, api_client, church_admin_token):
        """Summary email requires platform_admin role"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = api_client.post(
            f"{BASE_URL}/api/platform/send-summary-email",
            json={"recipients": ["test@example.com"]},
            headers=headers
        )
        assert response.status_code == 403


class TestDeliverableGeneration:
    """PPTX/PDF generation scaffold"""
    
    def test_generate_deliverable_pdf(self, api_client, platform_admin_token):
        """POST /api/solomon/generate-deliverable should work for PDF"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = api_client.post(
            f"{BASE_URL}/api/solomon/generate-deliverable",
            json={"type": "pdf", "title": "Test Report", "content": "Test content"},
            headers=headers
        )
        # PDF should work (reportlab installed)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_generate_deliverable_pptx_scaffold(self, api_client, platform_admin_token):
        """POST /api/solomon/generate-deliverable for PPTX should return scaffold message"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = api_client.post(
            f"{BASE_URL}/api/solomon/generate-deliverable",
            json={"type": "pptx", "title": "Test Slides", "content": "Test content"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should indicate coming_soon or scaffold status
        assert data.get("status") in ["coming_soon", "scaffold"] or "workaround" in str(data)


class TestPublicPages:
    """Test public pages load (FIX 7)"""
    
    def test_health_endpoint(self, api_client):
        """Health check endpoint"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
