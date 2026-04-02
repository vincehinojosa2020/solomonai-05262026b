"""
Solomon AI — Phase 6: Ask Solomon Agentic AI Tests
Tests for action execution via Solomon chat:
- POST /api/solomon/chat — returns pending_action when user requests an action
- POST /api/solomon/chat — returns NO pending_action for non-action queries
- POST /api/solomon/execute-action — all 7 action types
- Authentication requirements for execute-action
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials — from environment
MEMBER_EMAIL = os.environ.get('TEST_MEMBER_EMAIL', 'member@abundant.church')
MEMBER_PASSWORD = os.environ.get('TEST_MEMBER_PASSWORD', '')
ADMIN_EMAIL = os.environ.get('TEST_ADMIN_EMAIL', 'shannonnieman1030@gmail.com')
ADMIN_PASSWORD = os.environ.get('TEST_ADMIN_PASSWORD', '')


class TestSolomonAgenticPhase6:
    """Phase 6: Solomon Agentic AI Action Execution Tests"""
    
    @pytest.fixture(scope="class")
    def member_session(self):
        """Login as member and get session token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        assert response.status_code == 200, f"Member login failed: {response.text}"
        data = response.json()
        return {
            "token": data.get("session_token"),
            "user_id": data.get("user_id"),
            "tenant_id": data.get("tenant_id", "abundant-east-001")
        }
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login as admin and get session token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        return {
            "token": data.get("session_token"),
            "user_id": data.get("user_id"),
            "tenant_id": data.get("tenant_id", "abundant-east-001")
        }
    
    # ============== CHAT ENDPOINT TESTS ==============
    
    def test_chat_non_action_query_no_pending_action(self, member_session):
        """POST /api/solomon/chat — non-action query should NOT return pending_action"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        # Ask a simple question (not an action request)
        response = requests.post(f"{BASE_URL}/api/solomon/chat", 
            json={"message": "What time is the Sunday service?"},
            headers=headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        
        # Should have response and session_id
        assert "response" in data, "Missing response field"
        assert "session_id" in data, "Missing session_id field"
        assert len(data["response"]) > 0, "Empty response"
        
        # Should NOT have pending_action for non-action query
        assert data.get("pending_action") is None, f"Non-action query should not have pending_action, got: {data.get('pending_action')}"
        print(f"✓ Non-action query returned response without pending_action")
    
    def test_chat_action_query_returns_pending_action(self, member_session):
        """POST /api/solomon/chat — action query should return pending_action"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        # Request an action (order a latte)
        response = requests.post(f"{BASE_URL}/api/solomon/chat", 
            json={"message": "Order me a latte from the cafe"},
            headers=headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        
        # Should have response and session_id
        assert "response" in data, "Missing response field"
        assert "session_id" in data, "Missing session_id field"
        
        # Should have pending_action for action request
        pending = data.get("pending_action")
        assert pending is not None, f"Action query should have pending_action. Response: {data['response'][:200]}"
        assert "action_type" in pending, "pending_action missing action_type"
        assert "params" in pending, "pending_action missing params"
        assert "display_summary" in pending, "pending_action missing display_summary"
        assert pending["action_type"] == "cafe_order", f"Expected cafe_order, got {pending['action_type']}"
        
        print(f"✓ Action query returned pending_action: {pending['action_type']} - {pending['display_summary']}")
        return data["session_id"], pending
    
    # ============== EXECUTE-ACTION AUTHENTICATION TESTS ==============
    
    def test_execute_action_requires_auth(self):
        """POST /api/solomon/execute-action — should return 401 without auth"""
        response = requests.post(f"{BASE_URL}/api/solomon/execute-action", json={
            "session_id": "test-session",
            "action_type": "cafe_order",
            "params": {"items": [{"name": "Latte", "quantity": 1, "price": 5.00}]}
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("✓ Execute-action correctly requires authentication")
    
    # ============== CAFE ORDER ACTION TESTS ==============
    
    def test_execute_cafe_order_action(self, member_session):
        """POST /api/solomon/execute-action — cafe_order creates record in cafe_orders"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        test_session_id = f"test-cafe-{uuid.uuid4().hex[:8]}"
        
        response = requests.post(f"{BASE_URL}/api/solomon/execute-action", 
            json={
                "session_id": test_session_id,
                "action_type": "cafe_order",
                "params": {
                    "items": [{"name": "TEST_Latte", "quantity": 1, "price": 5.00}],
                    "pickup_time": "ASAP",
                    "notes": "Solomon AI test order"
                }
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Execute action failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"Action not successful: {data}"
        assert "order_id" in data, "Missing order_id in response"
        assert "message" in data, "Missing message in response"
        assert "TEST_Latte" in data["message"], f"Order message should mention item: {data['message']}"
        
        print(f"✓ Cafe order created: {data['order_id']} - {data['message']}")
    
    # ============== DONATION ACTION TESTS ==============
    
    def test_execute_donation_action(self, member_session):
        """POST /api/solomon/execute-action — donation creates record in donations"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        test_session_id = f"test-donation-{uuid.uuid4().hex[:8]}"
        
        response = requests.post(f"{BASE_URL}/api/solomon/execute-action", 
            json={
                "session_id": test_session_id,
                "action_type": "donation",
                "params": {
                    "amount": 25.00,
                    "fund": "TEST_Missions Fund"
                }
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Execute action failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"Action not successful: {data}"
        assert "donation_id" in data, "Missing donation_id in response"
        assert "message" in data, "Missing message in response"
        assert "$25" in data["message"], f"Donation message should mention amount: {data['message']}"
        
        print(f"✓ Donation created: {data['donation_id']} - {data['message']}")
    
    def test_execute_donation_invalid_amount(self, member_session):
        """POST /api/solomon/execute-action — donation with invalid amount should fail"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        test_session_id = f"test-donation-invalid-{uuid.uuid4().hex[:8]}"
        
        response = requests.post(f"{BASE_URL}/api/solomon/execute-action", 
            json={
                "session_id": test_session_id,
                "action_type": "donation",
                "params": {
                    "amount": 0,  # Invalid amount
                    "fund": "General Fund"
                }
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == False, f"Zero amount donation should fail: {data}"
        assert "positive" in data.get("message", "").lower(), f"Should mention positive amount: {data}"
        
        print(f"✓ Invalid donation correctly rejected: {data['message']}")
    
    # ============== RECURRING GIVING ACTION TESTS ==============
    
    def test_execute_recurring_giving_action(self, member_session):
        """POST /api/solomon/execute-action — recurring_giving creates record"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        test_session_id = f"test-recurring-{uuid.uuid4().hex[:8]}"
        
        response = requests.post(f"{BASE_URL}/api/solomon/execute-action", 
            json={
                "session_id": test_session_id,
                "action_type": "recurring_giving",
                "params": {
                    "amount": 50.00,
                    "frequency": "weekly",
                    "fund": "TEST_General Fund"
                }
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Execute action failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"Action not successful: {data}"
        assert "schedule_id" in data, "Missing schedule_id in response"
        assert "message" in data, "Missing message in response"
        assert "weekly" in data["message"].lower(), f"Message should mention frequency: {data['message']}"
        
        print(f"✓ Recurring giving created: {data['schedule_id']} - {data['message']}")
    
    # ============== EVENT REGISTRATION ACTION TESTS ==============
    
    def test_execute_event_registration_action(self, member_session):
        """POST /api/solomon/execute-action — event_registration registers user"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        test_session_id = f"test-event-{uuid.uuid4().hex[:8]}"
        
        # Try to register for an event (may or may not exist)
        response = requests.post(f"{BASE_URL}/api/solomon/execute-action", 
            json={
                "session_id": test_session_id,
                "action_type": "event_registration",
                "params": {
                    "event_name": "Abundant Event"  # Should match existing events
                }
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Execute action failed: {response.text}"
        data = response.json()
        
        # Either success (registered) or failure (event not found)
        assert "message" in data, "Missing message in response"
        
        if data.get("success"):
            print(f"✓ Event registration successful: {data['message']}")
        else:
            # If event not found, that's also valid behavior
            assert "could not find" in data["message"].lower() or "already registered" in data["message"].lower(), \
                f"Unexpected failure message: {data['message']}"
            print(f"✓ Event registration handled correctly: {data['message']}")
    
    def test_execute_event_registration_not_found(self, member_session):
        """POST /api/solomon/execute-action — event_registration with nonexistent event"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        test_session_id = f"test-event-notfound-{uuid.uuid4().hex[:8]}"
        
        response = requests.post(f"{BASE_URL}/api/solomon/execute-action", 
            json={
                "session_id": test_session_id,
                "action_type": "event_registration",
                "params": {
                    "event_name": "NONEXISTENT_EVENT_12345"
                }
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == False, f"Nonexistent event should fail: {data}"
        assert "could not find" in data.get("message", "").lower(), f"Should mention not found: {data}"
        
        print(f"✓ Nonexistent event correctly rejected: {data['message']}")
    
    # ============== GROUP JOIN ACTION TESTS ==============
    
    def test_execute_group_join_action(self, member_session):
        """POST /api/solomon/execute-action — group_join adds user to group"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        test_session_id = f"test-group-{uuid.uuid4().hex[:8]}"
        
        # Try to join a group (may or may not exist)
        response = requests.post(f"{BASE_URL}/api/solomon/execute-action", 
            json={
                "session_id": test_session_id,
                "action_type": "group_join",
                "params": {
                    "group_name": "Young Professionals"  # Common group name
                }
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Execute action failed: {response.text}"
        data = response.json()
        
        assert "message" in data, "Missing message in response"
        
        if data.get("success"):
            print(f"✓ Group join successful: {data['message']}")
        else:
            # If group not found or already member, that's valid
            assert "could not find" in data["message"].lower() or "already" in data["message"].lower(), \
                f"Unexpected failure message: {data['message']}"
            print(f"✓ Group join handled correctly: {data['message']}")
    
    def test_execute_group_join_not_found(self, member_session):
        """POST /api/solomon/execute-action — group_join with nonexistent group"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        test_session_id = f"test-group-notfound-{uuid.uuid4().hex[:8]}"
        
        response = requests.post(f"{BASE_URL}/api/solomon/execute-action", 
            json={
                "session_id": test_session_id,
                "action_type": "group_join",
                "params": {
                    "group_name": "NONEXISTENT_GROUP_12345"
                }
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == False, f"Nonexistent group should fail: {data}"
        assert "could not find" in data.get("message", "").lower(), f"Should mention not found: {data}"
        
        print(f"✓ Nonexistent group correctly rejected: {data['message']}")
    
    # ============== MERCH ORDER ACTION TESTS ==============
    
    def test_execute_merch_order_action(self, member_session):
        """POST /api/solomon/execute-action — merch_order creates record"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        test_session_id = f"test-merch-{uuid.uuid4().hex[:8]}"
        
        response = requests.post(f"{BASE_URL}/api/solomon/execute-action", 
            json={
                "session_id": test_session_id,
                "action_type": "merch_order",
                "params": {
                    "items": [{"name": "TEST_T-Shirt", "quantity": 1, "price": 25.00, "size": "M"}]
                }
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Execute action failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"Action not successful: {data}"
        assert "order_id" in data, "Missing order_id in response"
        assert "message" in data, "Missing message in response"
        assert "TEST_T-Shirt" in data["message"], f"Order message should mention item: {data['message']}"
        
        print(f"✓ Merch order created: {data['order_id']} - {data['message']}")
    
    # ============== UNKNOWN ACTION TYPE TEST ==============
    
    def test_execute_unknown_action_type(self, member_session):
        """POST /api/solomon/execute-action — unknown action type should fail gracefully"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        test_session_id = f"test-unknown-{uuid.uuid4().hex[:8]}"
        
        response = requests.post(f"{BASE_URL}/api/solomon/execute-action", 
            json={
                "session_id": test_session_id,
                "action_type": "unknown_action_type",
                "params": {}
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == False, f"Unknown action should fail: {data}"
        assert "unknown" in data.get("message", "").lower(), f"Should mention unknown: {data}"
        
        print(f"✓ Unknown action type correctly rejected: {data['message']}")
    
    # ============== CHAT HISTORY TEST ==============
    
    def test_solomon_history_endpoint(self, member_session):
        """GET /api/solomon/history/{session_id} — returns conversation history"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        # First create a conversation
        test_session_id = f"test-history-{uuid.uuid4().hex[:8]}"
        
        # Send a message
        chat_response = requests.post(f"{BASE_URL}/api/solomon/chat", 
            json={"message": "Hello Solomon", "session_id": test_session_id},
            headers=headers,
            timeout=30
        )
        assert chat_response.status_code == 200
        
        # Get history
        response = requests.get(f"{BASE_URL}/api/solomon/history/{test_session_id}", headers=headers)
        
        assert response.status_code == 200, f"History request failed: {response.text}"
        data = response.json()
        
        assert "messages" in data or "session_id" in data, f"Invalid history response: {data}"
        print(f"✓ Solomon history endpoint working")
    
    # ============== SESSION CLEAR TEST ==============
    
    def test_solomon_session_clear(self, member_session):
        """DELETE /api/solomon/session/{session_id} — clears session"""
        headers = {"Cookie": f"session_token={member_session['token']}"}
        
        test_session_id = f"test-clear-{uuid.uuid4().hex[:8]}"
        
        # First create a conversation
        chat_response = requests.post(f"{BASE_URL}/api/solomon/chat", 
            json={"message": "Test message", "session_id": test_session_id},
            headers=headers,
            timeout=30
        )
        assert chat_response.status_code == 200
        
        # Clear session
        response = requests.delete(f"{BASE_URL}/api/solomon/session/{test_session_id}", headers=headers)
        
        assert response.status_code == 200, f"Session clear failed: {response.text}"
        data = response.json()
        
        assert "message" in data, f"Missing message in response: {data}"
        assert "cleared" in data["message"].lower(), f"Should confirm cleared: {data}"
        
        print(f"✓ Solomon session clear working")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
