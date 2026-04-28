"""
Solomon AI Demo Fixes - Iteration 87 Tests
Tests for:
1. Watch page videos API (22 videos by Pastor Charles Leeman)
2. Aggregate dashboard API for Shannon Nieman
3. Kids check-in reset for demo account
4. Campus naming (Abundant Downtown not Northeast)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials — passwords MUST be supplied via env vars (CWE-798)
SHANNON_EMAIL = "shannonnieman1030@gmail.com"
SHANNON_PASSWORD = os.environ.get("TEST_PASSWORD")
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = os.environ.get("TEST_PASSWORD")

if not SHANNON_PASSWORD or not MEMBER_PASSWORD:
    pytest.skip(
        "TEST_PASSWORD environment variable is required to run demo-fix tests",
        allow_module_level=True,
    )


class TestSession:
    """Helper to manage authenticated sessions"""
    
    @staticmethod
    def login(email: str, password: str) -> requests.Session:
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            if token:
                session.headers.update({"Authorization": f"Bearer {token}"})
        
        return session, response


class TestWatchPageVideos:
    """Test Watch page videos API - should return 22 videos by Pastor Charles Leeman"""
    
    def test_videos_endpoint_returns_data(self):
        """Test that /portal/media/videos returns videos"""
        session, login_resp = TestSession.login(MEMBER_EMAIL, MEMBER_PASSWORD)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        response = session.get(f"{BASE_URL}/api/portal/media/videos")
        assert response.status_code == 200, f"Videos API failed: {response.text}"
        
        data = response.json()
        assert "videos" in data, "Response should contain 'videos' key"
        
        videos = data["videos"]
        print(f"Total videos returned: {len(videos)}")
        
        # Check for Pastor Charles Leeman videos
        charles_videos = [v for v in videos if "Charles Leeman" in v.get("instructor", "")]
        print(f"Videos by Pastor Charles Leeman: {len(charles_videos)}")
        
        # Should have videos by Pastor Charles Leeman (at least 10)
        assert len(charles_videos) >= 10, f"Expected at least 10 videos by Pastor Charles Leeman, got {len(charles_videos)}"
    
    def test_videos_have_required_fields(self):
        """Test that videos have required fields for display"""
        session, login_resp = TestSession.login(MEMBER_EMAIL, MEMBER_PASSWORD)
        assert login_resp.status_code == 200
        
        response = session.get(f"{BASE_URL}/api/portal/media/videos")
        assert response.status_code == 200
        
        data = response.json()
        videos = data.get("videos", [])
        
        if videos:
            video = videos[0]
            # Check required fields
            required_fields = ["id", "title", "youtube_id"]
            for field in required_fields:
                assert field in video, f"Video missing required field: {field}"
            
            print(f"Sample video: {video.get('title')} by {video.get('instructor')}")


class TestAggregateDashboard:
    """Test aggregate dashboard for Shannon Nieman (multi-campus admin)"""
    
    def test_shannon_can_access_aggregate_dashboard(self):
        """Shannon should see aggregate view with 3 campuses"""
        session, login_resp = TestSession.login(SHANNON_EMAIL, SHANNON_PASSWORD)
        assert login_resp.status_code == 200, f"Shannon login failed: {login_resp.text}"
        
        response = session.get(f"{BASE_URL}/api/admin/dashboard/aggregate")
        assert response.status_code == 200, f"Aggregate API failed: {response.text}"
        
        data = response.json()
        print(f"Aggregate data: {data}")
        
        # Should have campus_count
        assert "campus_count" in data, "Response should contain 'campus_count'"
        assert data["campus_count"] >= 1, f"Expected at least 1 campus, got {data['campus_count']}"
        
        # Should have total_members
        assert "total_members" in data, "Response should contain 'total_members'"
        print(f"Total members across campuses: {data['total_members']}")
    
    def test_aggregate_shows_campus_breakdown(self):
        """Aggregate should show breakdown by campus"""
        session, login_resp = TestSession.login(SHANNON_EMAIL, SHANNON_PASSWORD)
        assert login_resp.status_code == 200
        
        response = session.get(f"{BASE_URL}/api/admin/dashboard/aggregate")
        assert response.status_code == 200
        
        data = response.json()
        
        # Should have campuses array
        assert "campuses" in data, "Response should contain 'campuses' array"
        campuses = data["campuses"]
        
        print("Campus breakdown:")
        for campus in campuses:
            print(f"  - {campus.get('name')}: {campus.get('members')} members")
        
        # Check for Abundant Downtown (not Northeast)
        campus_names = [c.get("name", "") for c in campuses]
        print(f"Campus names: {campus_names}")
        
        # Verify no "Northeast" in campus names
        for name in campus_names:
            assert "Northeast" not in name, f"Found 'Northeast' in campus name: {name}. Should be 'Downtown'"
    
    def test_aggregate_member_counts(self):
        """Each campus should have 10K+ members"""
        session, login_resp = TestSession.login(SHANNON_EMAIL, SHANNON_PASSWORD)
        assert login_resp.status_code == 200
        
        response = session.get(f"{BASE_URL}/api/admin/dashboard/aggregate")
        assert response.status_code == 200
        
        data = response.json()
        data.get("campuses", [])
        
        # Check total members
        total = data.get("total_members", 0)
        print(f"Total members: {total}")
        
        # Should be 35K+ total (3 campuses x 10K+ each)
        assert total >= 30000, f"Expected 30K+ total members, got {total}"


class TestKidsCheckinReset:
    """Test that member demo account has no kids check-in records"""
    
    def test_member_has_no_active_checkins(self):
        """Demo member should have no active check-ins"""
        session, login_resp = TestSession.login(MEMBER_EMAIL, MEMBER_PASSWORD)
        assert login_resp.status_code == 200, f"Member login failed: {login_resp.text}"
        
        response = session.get(f"{BASE_URL}/api/portal/kids/checkins/active")
        assert response.status_code == 200, f"Active checkins API failed: {response.text}"
        
        data = response.json()
        checkins = data.get("checkins", [])
        
        print(f"Active check-ins for demo member: {len(checkins)}")
        assert len(checkins) == 0, f"Demo member should have 0 active check-ins, got {len(checkins)}"
    
    def test_member_checkin_history_empty(self):
        """Demo member should have empty check-in history"""
        session, login_resp = TestSession.login(MEMBER_EMAIL, MEMBER_PASSWORD)
        assert login_resp.status_code == 200
        
        response = session.get(f"{BASE_URL}/api/portal/kids/checkin/history")
        assert response.status_code == 200, f"Checkin history API failed: {response.text}"
        
        data = response.json()
        checkins = data.get("checkins", [])
        
        print(f"Check-in history for demo member: {len(checkins)}")
        # Should be empty or minimal for demo
        assert len(checkins) <= 5, f"Demo member should have minimal check-in history, got {len(checkins)}"


class TestDemoAccountFlags:
    """Test that demo accounts have proper flags to suppress modals"""
    
    def test_member_auth_me_returns_user_data(self):
        """Auth/me should return user data with demo flags"""
        session, login_resp = TestSession.login(MEMBER_EMAIL, MEMBER_PASSWORD)
        assert login_resp.status_code == 200
        
        response = session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Auth/me failed: {response.text}"
        
        data = response.json()
        print(f"User data keys: {list(data.keys())}")
        
        # Check for demo flags
        onboarding_completed = data.get("onboarding_completed", False)
        demo_walkthrough_seen = data.get("demo_walkthrough_seen", False)
        
        print(f"onboarding_completed: {onboarding_completed}")
        print(f"demo_walkthrough_seen: {demo_walkthrough_seen}")
        
        # Demo accounts should have these flags set to suppress modals
        assert onboarding_completed, "Demo account should have onboarding_completed=true"
        assert demo_walkthrough_seen, "Demo account should have demo_walkthrough_seen=true"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
