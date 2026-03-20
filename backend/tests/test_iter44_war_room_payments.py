"""
Iteration 44: War Room & Payment Orchestration Layer Tests
Tests for:
1. War Room - /api/admin/war-room endpoint
2. Payment Orchestration - /api/giving/processors, /api/admin/giving/processor-settings, /api/giving/process
3. Regression tests - health, solomon chat, aivy login
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Global session to reuse tokens and avoid rate limiting
_session_cache = {}

def get_token(email, password):
    """Get cached token or login"""
    cache_key = email
    if cache_key in _session_cache:
        return _session_cache[cache_key]
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        token = response.json().get("token")
        _session_cache[cache_key] = token
        return token
    return None

class TestRegression:
    """Regression tests for existing functionality"""
    
    def test_health_endpoint(self):
        """GET /api/health returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Health status not ok: {data}"
        print("PASS: GET /api/health returns 200 with status=ok")
    
    def test_solomon_chat(self):
        """POST /api/solomon/chat with message returns 200"""
        token = get_token("avopham@gmail.com", "SolomonTest2026!")
        assert token, "Failed to get token for Aivy"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/solomon/chat", 
            json={"message": "hello"},
            headers=headers
        )
        assert response.status_code == 200, f"Solomon chat failed: {response.text}"
        data = response.json()
        assert "response" in data or "message" in data, f"No response in chat: {data}"
        print("PASS: POST /api/solomon/chat returns 200")
    
    def test_aivy_login_returns_church_admin(self):
        """Aivy login returns role=church_admin"""
        token = get_token("avopham@gmail.com", "SolomonTest2026!")
        assert token, "Failed to get token for Aivy"
        
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert me_response.status_code == 200, f"Get me failed: {me_response.text}"
        user_data = me_response.json()
        assert user_data.get("role") == "church_admin", f"Expected church_admin role, got: {user_data.get('role')}"
        print("PASS: Aivy login returns role=church_admin")


class TestWarRoom:
    """War Room endpoint tests"""
    
    def test_war_room_endpoint_returns_200(self):
        """GET /api/admin/war-room returns 200 with counters, activity_feed, capacity"""
        token = get_token("avopham@gmail.com", "SolomonTest2026!")
        assert token, "Failed to get token"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/war-room", headers=headers)
        assert response.status_code == 200, f"War room failed: {response.text}"
        data = response.json()
        
        # Verify counters
        assert "counters" in data, f"No counters in response: {data}"
        counters = data["counters"]
        assert "total_members" in counters, f"No total_members in counters: {counters}"
        assert "kids_checked_in" in counters, f"No kids_checked_in in counters: {counters}"
        assert "cafe_orders_total" in counters, f"No cafe_orders_total in counters: {counters}"
        assert "mtd_giving" in counters, f"No mtd_giving in counters: {counters}"
        
        # Verify activity_feed
        assert "activity_feed" in data, f"No activity_feed in response: {data}"
        
        # Verify capacity
        assert "capacity" in data, f"No capacity in response: {data}"
        capacity = data["capacity"]
        assert "kids" in capacity, f"No kids in capacity: {capacity}"
        assert "cafe" in capacity, f"No cafe in capacity: {capacity}"
        assert "giving" in capacity, f"No giving in capacity: {capacity}"
        
        print(f"PASS: GET /api/admin/war-room returns 200 with counters={list(counters.keys())}, activity_feed, capacity")
    
    def test_war_room_requires_auth(self):
        """GET /api/admin/war-room without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/admin/war-room")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: GET /api/admin/war-room requires authentication")


class TestPaymentOrchestration:
    """Payment Orchestration Layer tests"""
    
    def test_list_processors_returns_6(self):
        """GET /api/giving/processors returns 200 with 6 processors"""
        response = requests.get(f"{BASE_URL}/api/giving/processors")
        assert response.status_code == 200, f"List processors failed: {response.text}"
        data = response.json()
        
        assert "processors" in data, f"No processors in response: {data}"
        processors = data["processors"]
        assert len(processors) == 6, f"Expected 6 processors, got {len(processors)}: {[p.get('id') for p in processors]}"
        
        # Verify expected processors
        processor_ids = [p.get("id") for p in processors]
        expected = ["stripe", "pushpay", "tithe_ly", "planning_center", "subsplash", "manual"]
        for exp in expected:
            assert exp in processor_ids, f"Missing processor: {exp}"
        
        print(f"PASS: GET /api/giving/processors returns 6 processors: {processor_ids}")
    
    def test_get_processor_settings(self):
        """GET /api/admin/giving/processor-settings returns 200"""
        token = get_token("admin@solomon.ai", "Demo2026!")
        assert token, "Failed to get platform admin token"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/giving/processor-settings", headers=headers)
        assert response.status_code == 200, f"Get processor settings failed: {response.text}"
        data = response.json()
        
        assert "active_processor" in data or "processors" in data, f"Invalid settings response: {data}"
        print(f"PASS: GET /api/admin/giving/processor-settings returns 200, active={data.get('active_processor')}")
    
    def test_connect_pushpay_processor(self):
        """POST /api/admin/giving/processor-settings with action=connect for pushpay returns 200"""
        token = get_token("admin@solomon.ai", "Demo2026!")
        assert token, "Failed to get platform admin token"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(f"{BASE_URL}/api/admin/giving/processor-settings", 
            json={
                "processor_id": "pushpay",
                "action": "connect",
                "config": {"test_mode": True}
            },
            headers=headers
        )
        assert response.status_code == 200, f"Connect pushpay failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"Connect not successful: {data}"
        assert data.get("active_processor") == "pushpay", f"Active processor not pushpay: {data}"
        print(f"PASS: POST /api/admin/giving/processor-settings connects pushpay, active={data.get('active_processor')}")
    
    def test_process_giving_returns_success(self):
        """POST /api/giving/process with amount=25 returns success with transaction_id and confirmation"""
        token = get_token("admin@solomon.ai", "Demo2026!")
        assert token, "Failed to get token"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(f"{BASE_URL}/api/giving/process",
            json={
                "amount": 25,
                "fund": "General",
                "payment_method": "card"
            },
            headers=headers
        )
        assert response.status_code == 200, f"Process giving failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"Giving not successful: {data}"
        assert "transaction_id" in data, f"No transaction_id in response: {data}"
        assert "confirmation" in data, f"No confirmation in response: {data}"
        assert data.get("amount") == 25, f"Amount mismatch: {data}"
        
        print(f"PASS: POST /api/giving/process returns success, txn_id={data.get('transaction_id')}, conf={data.get('confirmation')}")
    
    def test_process_giving_requires_auth(self):
        """POST /api/giving/process without auth returns 401"""
        # This test doesn't need the fixture's token - testing unauthenticated access
        response = requests.post(f"{BASE_URL}/api/giving/process",
            json={"amount": 10, "fund": "General"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: POST /api/giving/process requires authentication")
    
    def test_process_giving_validates_amount(self):
        """POST /api/giving/process with amount=0 returns 400"""
        token = get_token("admin@solomon.ai", "Demo2026!")
        assert token, "Failed to get token"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(f"{BASE_URL}/api/giving/process",
            json={"amount": 0, "fund": "General"},
            headers=headers
        )
        assert response.status_code == 400, f"Expected 400 for zero amount, got {response.status_code}: {response.text}"
        print("PASS: POST /api/giving/process validates amount > 0")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
