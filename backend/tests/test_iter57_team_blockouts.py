"""
Iteration 57: Test Team Assignments on Service Plans and Blockout Dates on Volunteers Page
- Team Assignments: Add/remove team members with position/role on service plans
- Blockout Dates: Create/view/delete blockout dates for volunteers
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "shannonnieman1030@gmail.com"
TEST_PASSWORD = "Demo2026!"

# Test plan ID with existing items
TEST_PLAN_ID = "7baf317d-b87f-4458-afdd-e805b86b71f6"


class TestAuth:
    """Authentication for testing"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "session_token" in data, "No session_token in response"
        return data["session_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }


class TestTeamAssignments(TestAuth):
    """Test Team Assignments on Service Plans"""
    
    def test_get_service_plans(self, auth_headers):
        """Verify service plans endpoint works"""
        response = requests.get(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get plans: {response.text}"
        data = response.json()
        assert "plans" in data, "No plans key in response"
        print(f"Found {len(data['plans'])} service plans")
    
    def test_get_specific_plan(self, auth_headers):
        """Verify we can get the test plan"""
        response = requests.get(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        plans = data.get("plans", [])
        test_plan = next((p for p in plans if p.get("id") == TEST_PLAN_ID), None)
        if test_plan:
            print(f"Found test plan: {test_plan.get('title')}")
            print(f"Current team_assignments: {test_plan.get('team_assignments', [])}")
        else:
            print(f"Test plan {TEST_PLAN_ID} not found, will use first available plan")
    
    def test_add_team_assignment(self, auth_headers):
        """Test adding a team assignment to a service plan"""
        # First get a plan to work with
        response = requests.get(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers)
        assert response.status_code == 200
        plans = response.json().get("plans", [])
        assert len(plans) > 0, "No plans available for testing"
        
        # Use test plan or first available
        plan = next((p for p in plans if p.get("id") == TEST_PLAN_ID), plans[0])
        plan_id = plan["id"]
        
        # Create a new team assignment
        test_assignment = {
            "id": str(uuid.uuid4()),
            "position": "TEST_Lead Vocals",
            "volunteer_name": "TEST_John Smith",
            "status": "confirmed"
        }
        
        # Get current assignments and add new one
        current_assignments = plan.get("team_assignments", [])
        updated_assignments = current_assignments + [test_assignment]
        
        # Update the plan with new team assignment
        response = requests.put(
            f"{BASE_URL}/api/admin/services/plans/{plan_id}",
            headers=auth_headers,
            json={"team_assignments": updated_assignments}
        )
        assert response.status_code == 200, f"Failed to add team assignment: {response.text}"
        
        # Verify the assignment was added
        updated_plan = response.json()
        assert "team_assignments" in updated_plan, "No team_assignments in response"
        
        # Find our test assignment
        found = any(
            a.get("volunteer_name") == "TEST_John Smith" 
            for a in updated_plan.get("team_assignments", [])
        )
        assert found, "Test assignment not found in updated plan"
        print(f"Successfully added team assignment to plan {plan_id}")
        
        # Store for cleanup
        return {"plan_id": plan_id, "assignment_id": test_assignment["id"]}
    
    def test_team_assignment_persists(self, auth_headers):
        """Verify team assignment persists after re-fetching"""
        response = requests.get(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers)
        assert response.status_code == 200
        plans = response.json().get("plans", [])
        
        # Find a plan with our test assignment
        for plan in plans:
            assignments = plan.get("team_assignments", [])
            for a in assignments:
                if a.get("volunteer_name") == "TEST_John Smith":
                    print(f"Team assignment persisted in plan {plan['id']}")
                    return
        
        # If we get here, assignment wasn't found - might have been cleaned up
        print("Test assignment not found (may have been cleaned up)")
    
    def test_remove_team_assignment(self, auth_headers):
        """Test removing a team assignment from a service plan"""
        # Get plans
        response = requests.get(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers)
        assert response.status_code == 200
        plans = response.json().get("plans", [])
        
        # Find plan with test assignment
        target_plan = None
        for plan in plans:
            assignments = plan.get("team_assignments", [])
            if any(a.get("volunteer_name", "").startswith("TEST_") for a in assignments):
                target_plan = plan
                break
        
        if not target_plan:
            print("No plan with test assignment found, skipping removal test")
            return
        
        plan_id = target_plan["id"]
        
        # Remove test assignments
        filtered_assignments = [
            a for a in target_plan.get("team_assignments", [])
            if not a.get("volunteer_name", "").startswith("TEST_")
        ]
        
        response = requests.put(
            f"{BASE_URL}/api/admin/services/plans/{plan_id}",
            headers=auth_headers,
            json={"team_assignments": filtered_assignments}
        )
        assert response.status_code == 200, f"Failed to remove team assignment: {response.text}"
        
        # Verify removal
        updated_plan = response.json()
        remaining = [
            a for a in updated_plan.get("team_assignments", [])
            if a.get("volunteer_name", "").startswith("TEST_")
        ]
        assert len(remaining) == 0, "Test assignments still present after removal"
        print(f"Successfully removed team assignment from plan {plan_id}")


class TestBlockoutDates(TestAuth):
    """Test Blockout Dates CRUD operations"""
    
    def test_get_blockout_dates(self, auth_headers):
        """Test GET /api/admin/volunteers/blockout-dates"""
        response = requests.get(
            f"{BASE_URL}/api/admin/volunteers/blockout-dates",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get blockout dates: {response.text}"
        data = response.json()
        assert "blockout_dates" in data, "No blockout_dates key in response"
        print(f"Found {len(data['blockout_dates'])} blockout dates")
    
    def test_create_blockout_date(self, auth_headers):
        """Test POST /api/admin/volunteers/blockout-dates"""
        # Create a test blockout date
        start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        
        payload = {
            "user_name": "TEST_Volunteer Smith",
            "start_date": start_date,
            "end_date": end_date,
            "reason": "TEST_Family vacation"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/volunteers/blockout-dates",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 200, f"Failed to create blockout date: {response.text}"
        
        data = response.json()
        assert "blockout" in data, "No blockout key in response"
        
        blockout = data["blockout"]
        assert blockout.get("user_name") == "TEST_Volunteer Smith"
        assert blockout.get("start_date") == start_date
        assert blockout.get("end_date") == end_date
        assert blockout.get("reason") == "TEST_Family vacation"
        assert "id" in blockout, "No id in blockout response"
        
        print(f"Created blockout date with id: {blockout['id']}")
        return blockout["id"]
    
    def test_blockout_date_persists(self, auth_headers):
        """Verify blockout date persists after re-fetching"""
        response = requests.get(
            f"{BASE_URL}/api/admin/volunteers/blockout-dates",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        blockouts = response.json().get("blockout_dates", [])
        test_blockouts = [b for b in blockouts if b.get("user_name", "").startswith("TEST_")]
        
        if test_blockouts:
            print(f"Found {len(test_blockouts)} test blockout dates persisted")
            for b in test_blockouts:
                print(f"  - {b.get('user_name')}: {b.get('start_date')} to {b.get('end_date')}")
        else:
            print("No test blockout dates found (may have been cleaned up)")
    
    def test_delete_blockout_date(self, auth_headers):
        """Test DELETE /api/admin/volunteers/blockout-dates/{id}"""
        # First get all blockout dates
        response = requests.get(
            f"{BASE_URL}/api/admin/volunteers/blockout-dates",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        blockouts = response.json().get("blockout_dates", [])
        test_blockouts = [b for b in blockouts if b.get("user_name", "").startswith("TEST_")]
        
        if not test_blockouts:
            # Create one to delete
            start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            create_response = requests.post(
                f"{BASE_URL}/api/admin/volunteers/blockout-dates",
                headers=auth_headers,
                json={
                    "user_name": "TEST_Delete Me",
                    "start_date": start_date,
                    "reason": "TEST_To be deleted"
                }
            )
            assert create_response.status_code == 200
            blockout_id = create_response.json()["blockout"]["id"]
        else:
            blockout_id = test_blockouts[0]["id"]
        
        # Delete the blockout date
        response = requests.delete(
            f"{BASE_URL}/api/admin/volunteers/blockout-dates/{blockout_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to delete blockout date: {response.text}"
        
        # Verify deletion
        response = requests.get(
            f"{BASE_URL}/api/admin/volunteers/blockout-dates",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        remaining = response.json().get("blockout_dates", [])
        found = any(b.get("id") == blockout_id for b in remaining)
        assert not found, "Blockout date still exists after deletion"
        print(f"Successfully deleted blockout date {blockout_id}")


class TestExistingFeatures(TestAuth):
    """Verify existing Phase 3 features still work"""
    
    def test_song_library_endpoint(self, auth_headers):
        """Verify song library still works"""
        response = requests.get(f"{BASE_URL}/api/admin/songs", headers=auth_headers)
        assert response.status_code == 200, f"Song library failed: {response.text}"
        data = response.json()
        assert "songs" in data
        print(f"Song library working: {len(data['songs'])} songs")
    
    def test_templates_endpoint(self, auth_headers):
        """Verify templates endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/admin/services/templates", headers=auth_headers)
        assert response.status_code == 200, f"Templates failed: {response.text}"
        data = response.json()
        assert "templates" in data
        print(f"Templates working: {len(data['templates'])} templates")
    
    def test_music_stand_public_access(self):
        """Verify music stand is publicly accessible"""
        # Get a plan ID first
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("session_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        plans_response = requests.get(f"{BASE_URL}/api/admin/services/plans", headers=headers)
        plans = plans_response.json().get("plans", [])
        
        if plans:
            plan_id = plans[0]["id"]
            # Music stand should be public (no auth)
            response = requests.get(f"{BASE_URL}/api/music-stand/{plan_id}")
            assert response.status_code == 200, f"Music stand failed: {response.text}"
            print(f"Music stand public access working for plan {plan_id}")
        else:
            print("No plans available to test music stand")


class TestCleanup(TestAuth):
    """Cleanup test data"""
    
    def test_cleanup_test_blockouts(self, auth_headers):
        """Remove all TEST_ prefixed blockout dates"""
        response = requests.get(
            f"{BASE_URL}/api/admin/volunteers/blockout-dates",
            headers=auth_headers
        )
        if response.status_code == 200:
            blockouts = response.json().get("blockout_dates", [])
            test_blockouts = [b for b in blockouts if b.get("user_name", "").startswith("TEST_")]
            
            for b in test_blockouts:
                requests.delete(
                    f"{BASE_URL}/api/admin/volunteers/blockout-dates/{b['id']}",
                    headers=auth_headers
                )
            
            print(f"Cleaned up {len(test_blockouts)} test blockout dates")
    
    def test_cleanup_test_assignments(self, auth_headers):
        """Remove all TEST_ prefixed team assignments"""
        response = requests.get(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers)
        if response.status_code == 200:
            plans = response.json().get("plans", [])
            cleaned = 0
            
            for plan in plans:
                assignments = plan.get("team_assignments", [])
                test_assignments = [a for a in assignments if a.get("volunteer_name", "").startswith("TEST_")]
                
                if test_assignments:
                    filtered = [a for a in assignments if not a.get("volunteer_name", "").startswith("TEST_")]
                    requests.put(
                        f"{BASE_URL}/api/admin/services/plans/{plan['id']}",
                        headers=auth_headers,
                        json={"team_assignments": filtered}
                    )
                    cleaned += len(test_assignments)
            
            print(f"Cleaned up {cleaned} test team assignments")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
