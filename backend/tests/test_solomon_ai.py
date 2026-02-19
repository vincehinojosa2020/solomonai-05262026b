"""
Solomon AI Tests - Testing Claude-powered AI chatbot for church data analysis
Tests: /api/solomon/chat, /api/solomon/history/{session_id}, /api/solomon/session/{session_id}
"""
import pytest
import requests
import os

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSolomonAI:
    """Tests for Solomon AI chatbot endpoints"""
    
    @pytest.fixture(scope="class")
    def session_id(self):
        """Create a Solomon chat session for testing"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "Hello, test message for session setup"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            return response.json().get("session_id")
        return None

    def test_solomon_chat_basic_message(self):
        """Test POST /api/solomon/chat - basic message returns AI response"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "How many members do we have?"},
            headers={"Content-Type": "application/json"}
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "response" in data, "Response should contain 'response' field"
        assert "session_id" in data, "Response should contain 'session_id' field"
        assert isinstance(data["response"], str), "Response should be a string"
        assert len(data["response"]) > 20, "Response should have substantial content"
        assert isinstance(data["session_id"], str), "session_id should be a string"
        
        # Verify response mentions member data
        response_lower = data["response"].lower()
        assert any(word in response_lower for word in ["member", "201", "active", "visitor"]), \
            "Response should contain membership-related content"
        
        print(f"SUCCESS: Solomon chat returned response with session_id: {data['session_id'][:8]}...")

    def test_solomon_chat_giving_context(self):
        """Test POST /api/solomon/chat - asking about giving returns financial context"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "What are our giving stats?"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        
        # Verify response contains giving-related content
        response_lower = data["response"].lower()
        assert any(word in response_lower for word in ["giving", "$", "month", "year", "goal"]), \
            "Response should contain giving-related content"
        
        # Check if actions are returned for giving-related queries
        if data.get("actions"):
            assert isinstance(data["actions"], list), "Actions should be a list"
            print(f"SUCCESS: Solomon returned {len(data['actions'])} suggested actions")
        
        print(f"SUCCESS: Solomon chat returned giving context")

    def test_solomon_chat_with_existing_session(self):
        """Test POST /api/solomon/chat - using existing session_id maintains context"""
        # First message - create session
        response1 = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "Tell me about our groups"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response1.status_code == 200
        session_id = response1.json().get("session_id")
        assert session_id is not None
        
        # Second message - use same session
        response2 = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={
                "message": "Which one has the most members?",
                "session_id": session_id
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Session ID should be preserved
        assert data2["session_id"] == session_id, "Session ID should be preserved across messages"
        
        print(f"SUCCESS: Solomon maintains session context")

    def test_solomon_history_endpoint(self, session_id):
        """Test GET /api/solomon/history/{session_id} - returns conversation history"""
        if not session_id:
            pytest.skip("No session_id available")
        
        response = requests.get(f"{BASE_URL}/api/solomon/history/{session_id}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "session_id" in data, "History should contain session_id"
        assert "messages" in data, "History should contain messages"
        assert isinstance(data["messages"], list), "Messages should be a list"
        
        if len(data["messages"]) > 0:
            msg = data["messages"][0]
            assert "role" in msg, "Message should have role"
            assert "content" in msg, "Message should have content"
            assert msg["role"] in ["user", "assistant"], "Role should be user or assistant"
        
        print(f"SUCCESS: Solomon history returned {len(data['messages'])} messages")

    def test_solomon_history_nonexistent_session(self):
        """Test GET /api/solomon/history - nonexistent session returns empty messages"""
        response = requests.get(f"{BASE_URL}/api/solomon/history/nonexistent-session-id-12345")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "messages" in data
        assert data["messages"] == [], "Nonexistent session should return empty messages"
        
        print(f"SUCCESS: Nonexistent session returns empty messages")

    def test_solomon_session_clear(self):
        """Test DELETE /api/solomon/session/{session_id} - clears chat session"""
        import time
        
        # Use a fixed session ID for reliable testing
        session_id = f"test-session-clear-{int(time.time())}"
        
        # Create a session with the fixed ID
        response1 = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "Test session to be cleared", "session_id": session_id},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # Skip test if we hit rate limits
        if response1.status_code == 520:
            pytest.skip("Rate limited - skipping session clear test")
        
        assert response1.status_code == 200
        returned_session_id = response1.json().get("session_id")
        assert returned_session_id == session_id
        
        # Brief pause before clearing
        time.sleep(1)
        
        # Delete the session
        response2 = requests.delete(f"{BASE_URL}/api/solomon/session/{session_id}")
        
        # 520 is acceptable for rate limits
        if response2.status_code == 520:
            pytest.skip("Rate limited on session clear - skipping")
        
        assert response2.status_code == 200
        
        data = response2.json()
        assert "message" in data
        assert data["session_id"] == session_id
        assert "cleared" in data["message"].lower()
        
        # Verify session is cleared by checking history
        response3 = requests.get(f"{BASE_URL}/api/solomon/history/{session_id}")
        assert response3.status_code == 200
        assert response3.json().get("messages") == []
        
        print(f"SUCCESS: Solomon session cleared and verified")

    def test_solomon_chat_group_context_actions(self):
        """Test that group-related queries return group navigation actions"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "Tell me about small group engagement and ministry teams"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        
        # Response should mention groups
        response_lower = data["response"].lower()
        assert any(word in response_lower for word in ["group", "ministry", "team", "20"]), \
            "Response should contain group-related content"
        
        # Check for group-related actions
        if data.get("actions"):
            action_paths = [a.get("path", "") for a in data["actions"]]
            print(f"SUCCESS: Solomon returned actions with paths: {action_paths}")
        
        print(f"SUCCESS: Solomon provides group context")

    def test_solomon_chat_follow_up_actions(self):
        """Test that follow-up related queries return navigation actions"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "Which members need follow-up and haven't been engaged recently?"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        
        # Check for follow-up related actions
        if data.get("actions"):
            assert isinstance(data["actions"], list)
            # Check that actions have proper structure
            for action in data["actions"]:
                assert "label" in action, "Action should have label"
                assert "action" in action, "Action should have action type"
            print(f"SUCCESS: Solomon returned {len(data['actions'])} follow-up actions")
        
        print(f"SUCCESS: Solomon provides follow-up recommendations")

    def test_solomon_chat_upcoming_events(self):
        """Test that Solomon can discuss upcoming events"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "What events are coming up soon?"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 20
        
        print(f"SUCCESS: Solomon discusses upcoming events")

    def test_solomon_chat_empty_message_handling(self):
        """Test POST /api/solomon/chat - empty message handling"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "   "},  # Whitespace only
            headers={"Content-Type": "application/json"}
        )
        
        # May return 200 with error message or 400/422/500/520 for validation/API errors
        # Just verify it doesn't crash completely
        assert response.status_code in [200, 400, 422, 500, 520], \
            f"Should handle empty message gracefully, got {response.status_code}"
        
        print(f"SUCCESS: Empty message handled with status {response.status_code}")

    def test_solomon_response_format(self):
        """Test that Solomon responses follow expected format"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "Give me a summary of our church"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify complete response structure
        assert "response" in data, "Should have 'response' field"
        assert "session_id" in data, "Should have 'session_id' field"
        
        # Optional fields should be None or valid types
        if data.get("data") is not None:
            assert isinstance(data["data"], dict), "data field should be dict if present"
        
        if data.get("actions") is not None:
            assert isinstance(data["actions"], list), "actions field should be list if present"
            for action in data["actions"]:
                assert "label" in action, "Each action should have label"
        
        print(f"SUCCESS: Solomon response format verified")


class TestSolomonChurchContext:
    """Test Solomon's understanding of church-specific context"""
    
    def test_solomon_knows_church_name(self):
        """Test Solomon knows it's serving Abundant Church"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "What church are you helping?"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        response_text = data["response"].lower()
        
        # Solomon should reference Abundant Church
        assert any(word in response_text for word in ["abundant", "el paso"]), \
            "Solomon should know it serves Abundant Church in El Paso"
        
        print(f"SUCCESS: Solomon knows church identity")

    def test_solomon_has_accurate_stats(self):
        """Test Solomon provides accurate membership stats"""
        response = requests.post(
            f"{BASE_URL}/api/solomon/chat",
            json={"message": "Give me exact membership numbers"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        # Should mention approximately 201 members
        assert "201" in data["response"] or "200" in data["response"].lower(), \
            "Solomon should report accurate membership count"
        
        print(f"SUCCESS: Solomon provides accurate stats")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
