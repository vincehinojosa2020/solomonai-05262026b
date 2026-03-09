"""
Test Suite for Share Feature and My Notes Feature (Iteration 15)

Tests:
- Video Notes CRUD operations
- Note sharing functionality
- Church members listing for sharing
- Share modal pre-populated messages

This test file covers the new features:
1. Video sharing with personalized messages
2. My Notes (Masterclass-style notes) feature
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = "Demo2026!"

# Global session for all tests
session = requests.Session()


@pytest.fixture(scope="module", autouse=True)
def login_member():
    """Login as member before running tests"""
    global session
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    print(f"\n✓ Logged in as: {response.json().get('name')}")
    yield
    # Cleanup after all tests


class TestVideoNotesCRUD:
    """Test Video Notes CRUD operations"""
    
    created_note_id = None
    test_video_id = None
    
    def test_01_member_login_success(self):
        """Verify member is logged in"""
        response = session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data.get("email") == MEMBER_EMAIL
        assert data.get("role") == "member"
        print(f"✓ Member session valid: {data.get('name')}")
    
    def test_02_get_videos_for_notes(self):
        """Verify videos are available for note-taking"""
        response = session.get(f"{BASE_URL}/api/portal/media/videos")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        videos = data.get("videos", [])
        print(f"✓ Found {len(videos)} videos available for notes")
        
        # Store first video ID for subsequent tests
        if videos:
            TestVideoNotesCRUD.test_video_id = videos[0].get("id")
            print(f"✓ Test video ID: {TestVideoNotesCRUD.test_video_id}")
    
    def test_03_create_video_note(self):
        """Create a new note for a video"""
        if not TestVideoNotesCRUD.test_video_id:
            pytest.skip("No video available for testing")
        
        note_content = f"TEST_note_created_at_{datetime.now().isoformat()}"
        
        response = session.post(
            f"{BASE_URL}/api/portal/video-notes",
            json={
                "video_id": TestVideoNotesCRUD.test_video_id,
                "content": note_content,
                "timestamp": "12:34",
                "is_public": False
            }
        )
        
        assert response.status_code == 200, f"Create note failed: {response.text}"
        data = response.json()
        assert "note" in data
        
        note = data["note"]
        assert note.get("content") == note_content
        assert note.get("timestamp") == "12:34"
        assert note.get("is_public") == False
        
        TestVideoNotesCRUD.created_note_id = note.get("id")
        print(f"✓ Note created with ID: {TestVideoNotesCRUD.created_note_id}")
    
    def test_04_get_my_notes(self):
        """Get all notes created by current user"""
        response = session.get(f"{BASE_URL}/api/portal/video-notes")
        
        assert response.status_code == 200
        data = response.json()
        notes = data.get("notes", [])
        print(f"✓ User has {len(notes)} notes")
        
        # Verify created note is in the list
        if TestVideoNotesCRUD.created_note_id:
            note_ids = [n.get("id") for n in notes]
            assert TestVideoNotesCRUD.created_note_id in note_ids, "Created note not found in my notes"
            print(f"✓ Created note found in user's notes")
    
    def test_05_get_notes_for_video(self):
        """Get all notes for a specific video"""
        if not TestVideoNotesCRUD.test_video_id:
            pytest.skip("No video available for testing")
        
        response = session.get(
            f"{BASE_URL}/api/portal/video-notes/video/{TestVideoNotesCRUD.test_video_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        notes = data.get("notes", [])
        print(f"✓ Video has {len(notes)} notes (own + shared)")
        
        # Verify is_own flag is present
        if notes:
            assert "is_own" in notes[0], "is_own flag missing from note"
            own_notes = [n for n in notes if n.get("is_own")]
            print(f"✓ User owns {len(own_notes)} notes on this video")
    
    def test_06_update_video_note(self):
        """Update an existing note"""
        if not TestVideoNotesCRUD.created_note_id:
            pytest.skip("No note created to update")
        
        updated_content = f"TEST_updated_note_at_{datetime.now().isoformat()}"
        
        response = session.put(
            f"{BASE_URL}/api/portal/video-notes/{TestVideoNotesCRUD.created_note_id}",
            json={"content": updated_content}
        )
        
        assert response.status_code == 200, f"Update failed: {response.text}"
        data = response.json()
        assert data.get("note", {}).get("content") == updated_content
        print(f"✓ Note updated successfully")
    
    def test_07_get_shared_notes(self):
        """Get notes shared with the current user"""
        response = session.get(f"{BASE_URL}/api/portal/video-notes/shared")
        
        assert response.status_code == 200
        data = response.json()
        notes = data.get("notes", [])
        print(f"✓ Found {len(notes)} notes shared with user")


class TestNoteSharing:
    """Test note sharing functionality"""
    
    note_id = None
    
    def test_01_get_church_members_for_sharing(self):
        """Get list of church members to share notes with"""
        response = session.get(f"{BASE_URL}/api/portal/church-members")
        
        assert response.status_code == 200, f"Failed to get church members: {response.text}"
        data = response.json()
        members = data.get("members", [])
        print(f"✓ Found {len(members)} church members available for sharing")
        
        # Verify members have required fields
        if members:
            member = members[0]
            assert "user_id" in member, "user_id missing from member"
            assert "name" in member or "email" in member, "name or email missing from member"
            print(f"✓ Member data structure is correct")
    
    def test_02_search_church_members(self):
        """Search for church members by name"""
        response = session.get(f"{BASE_URL}/api/portal/church-members?search=admin")
        
        assert response.status_code == 200
        data = response.json()
        members = data.get("members", [])
        print(f"✓ Search returned {len(members)} members matching 'admin'")
    
    def test_03_create_note_for_sharing(self):
        """Create a note specifically for sharing tests"""
        # First get a video
        videos_resp = session.get(f"{BASE_URL}/api/portal/media/videos")
        if videos_resp.status_code != 200:
            pytest.skip("Could not get videos")
        
        videos = videos_resp.json().get("videos", [])
        if not videos:
            pytest.skip("No videos available")
        
        video_id = videos[0].get("id")
        
        # Create note
        note_resp = session.post(
            f"{BASE_URL}/api/portal/video-notes",
            json={
                "video_id": video_id,
                "content": "TEST_Note_for_sharing_test",
                "is_public": False
            }
        )
        
        assert note_resp.status_code == 200
        TestNoteSharing.note_id = note_resp.json().get("note", {}).get("id")
        print(f"✓ Created note for sharing: {TestNoteSharing.note_id}")
    
    def test_04_share_note_public(self):
        """Share a note with entire church (public)"""
        if not TestNoteSharing.note_id:
            pytest.skip("No note available for sharing")
        
        response = session.post(
            f"{BASE_URL}/api/portal/video-notes/{TestNoteSharing.note_id}/share",
            json={"is_public": True, "user_ids": []}
        )
        
        assert response.status_code == 200, f"Share failed: {response.text}"
        data = response.json()
        assert data.get("note", {}).get("is_public") == True
        print(f"✓ Note shared publicly with church")
    
    def test_05_share_note_with_specific_users(self):
        """Share a note with specific church members"""
        if not TestNoteSharing.note_id:
            pytest.skip("No note available for sharing")
        
        # First get some members
        members_resp = session.get(f"{BASE_URL}/api/portal/church-members")
        
        if members_resp.status_code != 200:
            pytest.skip("Could not get members list")
        
        members = members_resp.json().get("members", [])
        if not members:
            pytest.skip("No other members to share with")
        
        # Share with first member
        user_ids = [members[0].get("user_id")]
        
        response = session.post(
            f"{BASE_URL}/api/portal/video-notes/{TestNoteSharing.note_id}/share",
            json={"user_ids": user_ids, "is_public": False}
        )
        
        assert response.status_code == 200, f"Share with users failed: {response.text}"
        data = response.json()
        shared_with = data.get("note", {}).get("shared_with", [])
        assert user_ids[0] in shared_with, "User not added to shared_with list"
        print(f"✓ Note shared with specific user: {user_ids[0]}")


class TestShareFeaturePrereqs:
    """Test prerequisites for Share feature"""
    
    def test_01_videos_have_required_fields_for_sharing(self):
        """Verify videos have all fields needed for share modal"""
        response = session.get(f"{BASE_URL}/api/portal/media/videos")
        
        assert response.status_code == 200
        videos = response.json().get("videos", [])
        
        if not videos:
            pytest.skip("No videos available")
        
        video = videos[0]
        
        # Check required fields for share modal
        assert "id" in video, "Video missing 'id' field"
        assert "title" in video, "Video missing 'title' field"
        
        print(f"✓ Video has required fields for sharing:")
        print(f"  - ID: {video.get('id')}")
        print(f"  - Title: {video.get('title')}")
        print(f"  - Thumbnail: {str(video.get('thumbnail_url', 'N/A'))[:50]}...")
        print(f"  - Instructor: {video.get('instructor', 'N/A')}")
    
    def test_02_get_user_session_info(self):
        """Verify session has user info needed for personalized messages"""
        response = session.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 200
        user = response.json()
        
        # Check required fields for personalized sharing messages
        assert "name" in user, "User missing 'name' field"
        assert "tenant_id" in user or "tenant_name" in user, "User missing tenant info"
        
        print(f"✓ User has required fields for personalized sharing:")
        print(f"  - Name: {user.get('name')}")
        print(f"  - Tenant: {user.get('tenant_name', user.get('tenant_id'))}")


class TestNoteCleanup:
    """Clean up test notes"""
    
    def test_99_delete_test_notes(self):
        """Delete test notes created during testing"""
        # Get all user's notes
        response = session.get(f"{BASE_URL}/api/portal/video-notes")
        
        assert response.status_code == 200
        notes = response.json().get("notes", [])
        
        # Delete notes with test content (prefixed with TEST_)
        deleted_count = 0
        for note in notes:
            content = note.get("content", "")
            if content.startswith("TEST_"):
                note_id = note.get("id")
                del_resp = session.delete(f"{BASE_URL}/api/portal/video-notes/{note_id}")
                if del_resp.status_code == 200:
                    deleted_count += 1
        
        print(f"✓ Cleaned up {deleted_count} test notes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
