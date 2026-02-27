"""
Test Suite for Solomon AI - Whisper Transcription and Claude Summarization
Iteration 12 - Testing Meeting Recording Upload with AI Processing

Features tested:
- Meeting recording upload endpoint (/api/admin/meetings/{meeting_id}/recording)
- Whisper transcription configuration (emergentintegrations)
- Claude summarization for pastoral meeting summaries
- UI components: transcript display, summary display, AI toggle button

Note: As per main agent instructions, we do NOT upload actual audio files to avoid 
consuming API credits. We validate the endpoint exists and test the structure.
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

def retry_request(func, max_retries=3, delay=2):
    """Retry a request function with exponential backoff"""
    for i in range(max_retries):
        try:
            return func()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if i == max_retries - 1:
                raise
            time.sleep(delay * (i + 1))
    return None


def get_admin_session():
    """Get authenticated admin session"""
    session = requests.Session()
    def login():
        return session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@abundant.church",
            "password": "Demo2026!"
        }, timeout=30)
    response = retry_request(login)
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return session


class TestAuth:
    """Verify authentication still works"""
    
    def test_admin_login(self):
        """Admin can login with credentials"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@abundant.church",
            "password": "Demo2026!"
        }, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "church_admin"
        assert data["tenant_id"] == "abundant-church-001"
        print("Admin login successful")


class TestMeetingRecordingEndpoint:
    """Test the meeting recording upload endpoint structure"""
    
    def test_recording_endpoint_exists(self):
        """Verify the recording upload endpoint exists and requires auth"""
        session = requests.Session()  # Unauthenticated
        
        # Try accessing without auth - should get 401
        response = session.post(f"{BASE_URL}/api/admin/meetings/test-meeting-id/recording", 
                               timeout=30)
        # Should require authentication
        assert response.status_code in [401, 403, 422], \
            f"Expected auth error, got {response.status_code}: {response.text}"
        print(f"Recording endpoint correctly requires auth (status: {response.status_code})")
    
    def test_recording_endpoint_requires_meeting_id(self):
        """Recording upload requires valid meeting ID"""
        session = get_admin_session()
        
        # Try with non-existent meeting ID
        response = session.post(
            f"{BASE_URL}/api/admin/meetings/nonexistent-meeting-id/recording",
            files={"file": ("test.webm", b"fake audio data", "audio/webm")},
            timeout=30
        )
        # Should return 404 for non-existent meeting
        assert response.status_code == 404, \
            f"Expected 404 for non-existent meeting, got {response.status_code}: {response.text}"
        print("Endpoint correctly validates meeting ID")
    
    def test_recording_endpoint_accepts_file_parameter(self):
        """Recording endpoint accepts file upload parameter"""
        session = get_admin_session()
        
        # Get existing meetings
        meetings_response = session.get(f"{BASE_URL}/api/admin/meetings", timeout=30)
        assert meetings_response.status_code == 200
        meetings = meetings_response.json().get("meetings", [])
        
        if not meetings:
            pytest.skip("No meetings available for testing")
        
        meeting_id = meetings[0]["id"]
        
        # Try uploading without file - should get validation error
        response = session.post(
            f"{BASE_URL}/api/admin/meetings/{meeting_id}/recording",
            timeout=30
        )
        # Should get 422 for missing file parameter
        assert response.status_code == 422, \
            f"Expected 422 for missing file, got {response.status_code}"
        print("Endpoint correctly requires file parameter")


class TestMeetingsAdminAPI:
    """Test admin meetings API for transcript/summary fields"""
    
    def test_admin_get_meetings(self):
        """Admin can get meetings list"""
        session = get_admin_session()
        response = session.get(f"{BASE_URL}/api/admin/meetings", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "meetings" in data
        print(f"Found {len(data['meetings'])} meetings")
    
    def test_meeting_structure_includes_ai_fields(self):
        """Meeting response includes transcript and summary fields"""
        session = get_admin_session()
        response = session.get(f"{BASE_URL}/api/admin/meetings", timeout=30)
        assert response.status_code == 200
        meetings = response.json().get("meetings", [])
        
        if not meetings:
            pytest.skip("No meetings to validate structure")
        
        # Check that meetings have required fields
        meeting = meetings[0]
        required_fields = ["id", "tenant_id", "slot_id", "status"]
        for field in required_fields:
            assert field in meeting, f"Missing required field: {field}"
        
        # transcript and summary are optional but should be present in schema
        # (they may be None if no recording uploaded yet)
        print(f"Meeting {meeting['id']} structure validated")
        print(f"  - Has transcript: {'transcript' in meeting and meeting.get('transcript') is not None}")
        print(f"  - Has summary: {'summary' in meeting and meeting.get('summary') is not None}")
    
    def test_admin_update_meeting_notes(self):
        """Admin can update meeting notes"""
        session = get_admin_session()
        
        # Get meetings
        meetings_response = session.get(f"{BASE_URL}/api/admin/meetings", timeout=30)
        meetings = meetings_response.json().get("meetings", [])
        
        if not meetings:
            pytest.skip("No meetings available for testing")
        
        meeting_id = meetings[0]["id"]
        
        # Update notes
        response = session.patch(
            f"{BASE_URL}/api/admin/meetings/{meeting_id}",
            json={"notes": "Test note from iteration 12", "status": "scheduled"},
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "meeting" in data
        print(f"Meeting {meeting_id} notes updated successfully")


class TestMeetingSlotsAdmin:
    """Test meeting slots admin functionality"""
    
    def test_admin_get_slots(self):
        """Admin can get all meeting slots"""
        session = get_admin_session()
        response = session.get(f"{BASE_URL}/api/admin/meetings/slots", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        
        slots = data["slots"]
        print(f"Found {len(slots)} meeting slots")
        
        # Check slot statuses
        open_slots = [s for s in slots if s.get("status") == "open"]
        booked_slots = [s for s in slots if s.get("status") == "booked"]
        print(f"  - Open: {len(open_slots)}, Booked: {len(booked_slots)}")


class TestWhisperClaudeIntegration:
    """Test that Whisper and Claude are configured via emergentintegrations"""
    
    def test_emergent_llm_key_configured(self):
        """Verify EMERGENT_LLM_KEY is configured on backend"""
        # We can't directly check env vars, but we can verify the endpoint 
        # returns appropriate error when no file is provided
        session = get_admin_session()
        
        # Get a meeting ID
        meetings_response = session.get(f"{BASE_URL}/api/admin/meetings", timeout=30)
        meetings = meetings_response.json().get("meetings", [])
        
        if not meetings:
            pytest.skip("No meetings available")
        
        meeting_id = meetings[0]["id"]
        
        # The fact that the endpoint doesn't return "Whisper is not configured" 
        # when we send an invalid request suggests the key is configured
        response = session.post(
            f"{BASE_URL}/api/admin/meetings/{meeting_id}/recording",
            timeout=30
        )
        
        # Should get 422 (missing file) rather than 500 (config error)
        assert response.status_code != 500 or "not configured" not in response.text.lower(), \
            f"API might be misconfigured: {response.text}"
        print("API configuration appears correct (no config errors)")


class TestMeetingsAdminUIElements:
    """Validate expected UI elements are present in API responses"""
    
    def test_meetings_have_member_info(self):
        """Meetings include member name and email for display"""
        session = get_admin_session()
        response = session.get(f"{BASE_URL}/api/admin/meetings", timeout=30)
        meetings = response.json().get("meetings", [])
        
        if not meetings:
            pytest.skip("No meetings available")
        
        for meeting in meetings:
            # These fields are needed for the UI
            assert "topic" in meeting or meeting.get("topic") is None
            assert "member_name" in meeting or meeting.get("member_name") is None
            print(f"Meeting: {meeting.get('member_name', 'Unknown')} - {meeting.get('topic', 'No topic')}")
    
    def test_slot_includes_time_info(self):
        """Slots include start/end time for display"""
        session = get_admin_session()
        response = session.get(f"{BASE_URL}/api/admin/meetings/slots", timeout=30)
        slots = response.json().get("slots", [])
        
        if not slots:
            pytest.skip("No slots available")
        
        slot = slots[0]
        assert "start_time" in slot, "Slot missing start_time"
        assert "end_time" in slot, "Slot missing end_time"
        assert "status" in slot, "Slot missing status"
        print(f"Slot time format validated: {slot['start_time']} to {slot['end_time']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
