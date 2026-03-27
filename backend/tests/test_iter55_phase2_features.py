"""
Iteration 55: Phase 2 Features Testing
- Calendar Room Booking Approvals
- People Workflows
- Form Builder
- Duplicate Detection & Merge
- Smart Lists
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CHURCH_ADMIN_EMAIL = "shannonnieman1030@gmail.com"
CHURCH_ADMIN_PASSWORD = "Demo2026!"
PLATFORM_ADMIN_EMAIL = "admin@solomonai.us"
PLATFORM_ADMIN_PASSWORD = "Demo2026!"


class TestSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def church_admin_token(self):
        """Get church admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token") or data.get("token")
        pytest.skip(f"Church admin auth failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def platform_admin_token(self):
        """Get platform admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token") or data.get("token")
        pytest.skip(f"Platform admin auth failed: {response.status_code}")


class TestCalendarApprovals:
    """Calendar Room Booking Approval System Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for church admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Auth failed")
    
    def test_get_rooms_list(self, auth_headers):
        """GET /api/admin/calendar/rooms - returns rooms list"""
        response = requests.get(f"{BASE_URL}/api/admin/calendar/rooms", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "rooms" in data
        assert isinstance(data["rooms"], list)
        # Should have default rooms seeded
        if len(data["rooms"]) > 0:
            room = data["rooms"][0]
            assert "id" in room
            assert "name" in room
            print(f"Found {len(data['rooms'])} rooms")
    
    def test_create_booking_request(self, auth_headers):
        """POST /api/admin/calendar/booking-requests - creates booking request"""
        payload = {
            "event_name": "TEST_Youth Group Meeting",
            "description": "Weekly youth gathering",
            "event_date": "2026-02-15",
            "start_time": "18:00",
            "end_time": "20:00",
            "room_id": "fellowship-hall",
            "room_name": "Fellowship Hall",
            "notes": "Need projector setup"
        }
        response = requests.post(f"{BASE_URL}/api/admin/calendar/booking-requests", 
                                 headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"
        assert "message" in data
        print(f"Created booking request: {data['id']}")
        return data["id"]
    
    def test_get_calendar_approvals(self, auth_headers):
        """GET /api/admin/calendar/approvals - returns bookings with status counts"""
        response = requests.get(f"{BASE_URL}/api/admin/calendar/approvals", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "bookings" in data
        assert "counts" in data
        assert "pending" in data["counts"]
        assert "approved" in data["counts"]
        assert "rejected" in data["counts"]
        print(f"Approvals counts: {data['counts']}")
    
    def test_get_approvals_filtered_by_status(self, auth_headers):
        """GET /api/admin/calendar/approvals?status=pending - filters by status"""
        response = requests.get(f"{BASE_URL}/api/admin/calendar/approvals?status=pending", 
                                headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # All returned bookings should be pending
        for booking in data.get("bookings", []):
            assert booking["status"] == "pending"
    
    def test_approve_booking(self, auth_headers):
        """POST /api/admin/calendar/approvals/{id} - approve booking"""
        # First create a booking to approve
        payload = {
            "event_name": "TEST_Approval Test Event",
            "event_date": "2026-03-01",
            "start_time": "10:00",
            "end_time": "11:00",
            "room_id": "room-101"
        }
        create_res = requests.post(f"{BASE_URL}/api/admin/calendar/booking-requests", 
                                   headers=auth_headers, json=payload)
        assert create_res.status_code == 200
        booking_id = create_res.json()["id"]
        
        # Approve it
        approve_res = requests.post(f"{BASE_URL}/api/admin/calendar/approvals/{booking_id}",
                                    headers=auth_headers, json={"decision": "approved"})
        assert approve_res.status_code == 200, f"Expected 200, got {approve_res.status_code}: {approve_res.text}"
        data = approve_res.json()
        assert data["status"] == "approved"
        print(f"Approved booking: {booking_id}")
    
    def test_reject_booking(self, auth_headers):
        """POST /api/admin/calendar/approvals/{id} - reject booking"""
        # Create a booking to reject
        payload = {
            "event_name": "TEST_Rejection Test Event",
            "event_date": "2026-03-02",
            "start_time": "14:00",
            "end_time": "15:00",
            "room_id": "room-102"
        }
        create_res = requests.post(f"{BASE_URL}/api/admin/calendar/booking-requests", 
                                   headers=auth_headers, json=payload)
        assert create_res.status_code == 200
        booking_id = create_res.json()["id"]
        
        # Reject it
        reject_res = requests.post(f"{BASE_URL}/api/admin/calendar/approvals/{booking_id}",
                                   headers=auth_headers, json={"decision": "rejected", "notes": "Room unavailable"})
        assert reject_res.status_code == 200
        data = reject_res.json()
        assert data["status"] == "rejected"
        print(f"Rejected booking: {booking_id}")
    
    def test_bulk_approve_bookings(self, auth_headers):
        """POST /api/admin/calendar/approvals/bulk - bulk approve"""
        # Create two bookings
        booking_ids = []
        for i in range(2):
            payload = {
                "event_name": f"TEST_Bulk Approve {i}",
                "event_date": f"2026-04-0{i+1}",
                "start_time": "09:00",
                "end_time": "10:00",
                "room_id": "room-103"
            }
            res = requests.post(f"{BASE_URL}/api/admin/calendar/booking-requests", 
                               headers=auth_headers, json=payload)
            if res.status_code == 200:
                booking_ids.append(res.json()["id"])
        
        if len(booking_ids) < 2:
            pytest.skip("Could not create bookings for bulk test")
        
        # Bulk approve
        bulk_res = requests.post(f"{BASE_URL}/api/admin/calendar/approvals/bulk",
                                 headers=auth_headers, 
                                 json={"booking_ids": booking_ids, "decision": "approved"})
        assert bulk_res.status_code == 200
        data = bulk_res.json()
        assert data["updated"] >= 1
        print(f"Bulk approved {data['updated']} bookings")
    
    def test_get_calendar_conflicts(self, auth_headers):
        """GET /api/admin/calendar/conflicts - detects room conflicts"""
        response = requests.get(f"{BASE_URL}/api/admin/calendar/conflicts", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "conflicts" in data
        assert "total" in data
        print(f"Found {data['total']} conflicts")
    
    def test_conflict_detection_on_create(self, auth_headers):
        """Booking request should detect conflicts"""
        # Create first booking
        payload1 = {
            "event_name": "TEST_Conflict Test 1",
            "event_date": "2026-05-15",
            "start_time": "14:00",
            "end_time": "16:00",
            "room_id": "sanctuary"
        }
        res1 = requests.post(f"{BASE_URL}/api/admin/calendar/booking-requests", 
                            headers=auth_headers, json=payload1)
        assert res1.status_code == 200
        
        # Create overlapping booking
        payload2 = {
            "event_name": "TEST_Conflict Test 2",
            "event_date": "2026-05-15",
            "start_time": "15:00",
            "end_time": "17:00",
            "room_id": "sanctuary"
        }
        res2 = requests.post(f"{BASE_URL}/api/admin/calendar/booking-requests", 
                            headers=auth_headers, json=payload2)
        assert res2.status_code == 200
        data = res2.json()
        # Should detect conflict
        assert data.get("has_conflicts") == True or len(data.get("conflicts", [])) > 0
        print("Conflict detection working")


class TestWorkflows:
    """People Workflow Builder Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for church admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Auth failed")
    
    def test_create_workflow(self, auth_headers):
        """POST /api/admin/workflows - creates workflow with steps"""
        payload = {
            "name": "TEST_New Visitor Follow-up",
            "description": "Automated follow-up for first-time visitors",
            "trigger": "manual",
            "steps": [
                {"id": "s1", "order": 1, "type": "email", "title": "Welcome Email", "due_days": 1},
                {"id": "s2", "order": 2, "type": "task", "title": "Personal Call", "assignee": "Pastor", "due_days": 3},
                {"id": "s3", "order": 3, "type": "add_to_group", "title": "Add to Newcomers Group", "due_days": 7}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/admin/workflows", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "workflow" in data
        wf = data["workflow"]
        assert wf["name"] == "TEST_New Visitor Follow-up"
        assert len(wf["steps"]) == 3
        print(f"Created workflow: {wf['id']}")
        return wf["id"]
    
    def test_get_workflows_list(self, auth_headers):
        """GET /api/admin/workflows - lists workflows"""
        response = requests.get(f"{BASE_URL}/api/admin/workflows", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert isinstance(data["workflows"], list)
        print(f"Found {len(data['workflows'])} workflows")
    
    def test_update_workflow(self, auth_headers):
        """PUT /api/admin/workflows/{id} - updates workflow"""
        # First create a workflow
        create_res = requests.post(f"{BASE_URL}/api/admin/workflows", headers=auth_headers, json={
            "name": "TEST_Update Test Workflow",
            "steps": [{"id": "s1", "order": 1, "type": "task", "title": "Initial Step"}]
        })
        assert create_res.status_code == 200
        wf_id = create_res.json()["workflow"]["id"]
        
        # Update it
        update_res = requests.put(f"{BASE_URL}/api/admin/workflows/{wf_id}", headers=auth_headers, json={
            "name": "TEST_Updated Workflow Name",
            "description": "Updated description"
        })
        assert update_res.status_code == 200
        print(f"Updated workflow: {wf_id}")
    
    def test_delete_workflow(self, auth_headers):
        """DELETE /api/admin/workflows/{id} - deletes workflow"""
        # Create a workflow to delete
        create_res = requests.post(f"{BASE_URL}/api/admin/workflows", headers=auth_headers, json={
            "name": "TEST_Delete Test Workflow"
        })
        assert create_res.status_code == 200
        wf_id = create_res.json()["workflow"]["id"]
        
        # Delete it
        delete_res = requests.delete(f"{BASE_URL}/api/admin/workflows/{wf_id}", headers=auth_headers)
        assert delete_res.status_code == 200
        
        # Verify deleted
        get_res = requests.get(f"{BASE_URL}/api/admin/workflows", headers=auth_headers)
        workflows = get_res.json().get("workflows", [])
        assert not any(w["id"] == wf_id for w in workflows)
        print(f"Deleted workflow: {wf_id}")
    
    def test_enroll_in_workflow(self, auth_headers):
        """POST /api/admin/workflows/{id}/enroll - enrolls people in workflow"""
        # Create a workflow
        create_res = requests.post(f"{BASE_URL}/api/admin/workflows", headers=auth_headers, json={
            "name": "TEST_Enrollment Test Workflow"
        })
        assert create_res.status_code == 200
        wf_id = create_res.json()["workflow"]["id"]
        
        # Get a member to enroll (use current user)
        me_res = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        if me_res.status_code == 200:
            user_id = me_res.json().get("user_id")
            if user_id:
                enroll_res = requests.post(f"{BASE_URL}/api/admin/workflows/{wf_id}/enroll",
                                          headers=auth_headers, json={"person_ids": [user_id]})
                assert enroll_res.status_code == 200
                data = enroll_res.json()
                assert data["enrolled"] >= 0  # May be 0 if already enrolled
                print(f"Enrolled {data['enrolled']} people in workflow")


class TestFormBuilder:
    """Form Builder Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for church admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Auth failed")
    
    def test_create_form(self, auth_headers):
        """POST /api/admin/forms - creates form with configurable fields"""
        payload = {
            "name": "TEST_Visitor Connect Card",
            "description": "Collect visitor information",
            "is_public": True,
            "auto_create_profile": True,
            "fields": [
                {"id": "f1", "type": "text", "label": "First Name", "required": True},
                {"id": "f2", "type": "text", "label": "Last Name", "required": True},
                {"id": "f3", "type": "email", "label": "Email", "required": True},
                {"id": "f4", "type": "tel", "label": "Phone", "required": False},
                {"id": "f5", "type": "select", "label": "How did you hear about us?", "required": False,
                 "options": ["Friend", "Social Media", "Website", "Other"]}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/admin/forms", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "form" in data
        form = data["form"]
        assert form["name"] == "TEST_Visitor Connect Card"
        assert len(form["fields"]) == 5
        assert form["auto_create_profile"] == True
        print(f"Created form: {form['id']}")
        return form["id"]
    
    def test_get_forms_list(self, auth_headers):
        """GET /api/admin/forms - lists forms"""
        response = requests.get(f"{BASE_URL}/api/admin/forms", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "forms" in data
        print(f"Found {len(data['forms'])} forms")
    
    def test_public_form_access(self, auth_headers):
        """GET /api/forms/{id}/public - public form access (no auth)"""
        # First create a public form
        create_res = requests.post(f"{BASE_URL}/api/admin/forms", headers=auth_headers, json={
            "name": "TEST_Public Form",
            "is_public": True,
            "fields": [{"id": "f1", "type": "text", "label": "Name", "required": True}]
        })
        assert create_res.status_code == 200
        form_id = create_res.json()["form"]["id"]
        
        # Access without auth
        public_res = requests.get(f"{BASE_URL}/api/forms/{form_id}/public")
        assert public_res.status_code == 200, f"Expected 200, got {public_res.status_code}: {public_res.text}"
        data = public_res.json()
        assert "form" in data
        assert data["form"]["name"] == "TEST_Public Form"
        print(f"Public form accessible: {form_id}")
        return form_id
    
    def test_public_form_submission(self, auth_headers):
        """POST /api/forms/{id}/submit - public form submission (no auth)"""
        # Create a form
        create_res = requests.post(f"{BASE_URL}/api/admin/forms", headers=auth_headers, json={
            "name": "TEST_Submission Form",
            "is_public": True,
            "auto_create_profile": False,
            "fields": [
                {"id": "f1", "type": "text", "label": "Name", "required": True},
                {"id": "f2", "type": "email", "label": "Email", "required": True}
            ]
        })
        assert create_res.status_code == 200
        form_id = create_res.json()["form"]["id"]
        
        # Submit without auth
        submit_res = requests.post(f"{BASE_URL}/api/forms/{form_id}/submit", json={
            "data": {
                "Name": "Test Visitor",
                "Email": f"test_visitor_{int(time.time())}@example.com"
            }
        })
        assert submit_res.status_code == 200, f"Expected 200, got {submit_res.status_code}: {submit_res.text}"
        data = submit_res.json()
        assert "submission_id" in data
        print(f"Form submitted: {data['submission_id']}")
    
    def test_get_form_submissions(self, auth_headers):
        """GET /api/admin/forms/{id}/submissions - view form submissions"""
        # Create form and submit
        create_res = requests.post(f"{BASE_URL}/api/admin/forms", headers=auth_headers, json={
            "name": "TEST_Submissions View Form",
            "is_public": True
        })
        assert create_res.status_code == 200
        form_id = create_res.json()["form"]["id"]
        
        # Submit something
        requests.post(f"{BASE_URL}/api/forms/{form_id}/submit", json={
            "data": {"test": "data"}
        })
        
        # Get submissions
        subs_res = requests.get(f"{BASE_URL}/api/admin/forms/{form_id}/submissions", headers=auth_headers)
        assert subs_res.status_code == 200
        data = subs_res.json()
        assert "submissions" in data
        print(f"Found {len(data['submissions'])} submissions")


class TestDuplicateDetection:
    """Duplicate Detection & Merge Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for church admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Auth failed")
    
    def test_detect_duplicates(self, auth_headers):
        """GET /api/admin/people/duplicates - detects duplicate members"""
        response = requests.get(f"{BASE_URL}/api/admin/people/duplicates", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "duplicates" in data
        assert "total" in data
        print(f"Found {data['total']} potential duplicates")
        
        # Check structure if duplicates exist
        if len(data["duplicates"]) > 0:
            dup = data["duplicates"][0]
            assert "person_a" in dup
            assert "person_b" in dup
            assert "score" in dup
            assert dup["score"] >= 40  # Minimum threshold
    
    def test_merge_profiles_validation(self, auth_headers):
        """POST /api/admin/people/merge - validates required fields"""
        # Test missing fields
        response = requests.post(f"{BASE_URL}/api/admin/people/merge", 
                                headers=auth_headers, json={})
        assert response.status_code == 400
        
        # Test with invalid IDs
        response = requests.post(f"{BASE_URL}/api/admin/people/merge", 
                                headers=auth_headers, json={
                                    "keep_id": "invalid-id-1",
                                    "merge_id": "invalid-id-2"
                                })
        assert response.status_code == 404


class TestSmartLists:
    """Smart Lists Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for church admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Auth failed")
    
    def test_create_smart_list(self, auth_headers):
        """POST /api/admin/smart-lists - creates smart list with rules"""
        payload = {
            "name": "TEST_Active Members",
            "description": "All active church members",
            "rules": [
                {"field": "membership_status", "operator": "equals", "value": "active"},
                {"field": "role", "operator": "equals", "value": "member"}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/admin/smart-lists", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "list" in data
        sl = data["list"]
        assert sl["name"] == "TEST_Active Members"
        assert len(sl["rules"]) == 2
        print(f"Created smart list: {sl['id']}")
        return sl["id"]
    
    def test_get_smart_lists(self, auth_headers):
        """GET /api/admin/smart-lists - lists smart lists"""
        response = requests.get(f"{BASE_URL}/api/admin/smart-lists", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "lists" in data
        print(f"Found {len(data['lists'])} smart lists")
    
    def test_run_smart_list(self, auth_headers):
        """POST /api/admin/smart-lists/{id}/run - executes smart list filter"""
        # Create a smart list
        create_res = requests.post(f"{BASE_URL}/api/admin/smart-lists", headers=auth_headers, json={
            "name": "TEST_Run Test List",
            "rules": [{"field": "role", "operator": "equals", "value": "member"}]
        })
        assert create_res.status_code == 200
        list_id = create_res.json()["list"]["id"]
        
        # Run it
        run_res = requests.post(f"{BASE_URL}/api/admin/smart-lists/{list_id}/run", headers=auth_headers)
        assert run_res.status_code == 200, f"Expected 200, got {run_res.status_code}: {run_res.text}"
        data = run_res.json()
        assert "members" in data
        assert "count" in data
        assert "list_name" in data
        print(f"Smart list returned {data['count']} members")
    
    def test_smart_list_operators(self, auth_headers):
        """Test different smart list operators"""
        operators_to_test = [
            {"field": "membership_status", "operator": "equals", "value": "active"},
            {"field": "membership_status", "operator": "not_equals", "value": "inactive"},
            {"field": "name", "operator": "contains", "value": "John"},
            {"field": "email", "operator": "exists", "value": ""},
        ]
        
        for rule in operators_to_test:
            create_res = requests.post(f"{BASE_URL}/api/admin/smart-lists", headers=auth_headers, json={
                "name": f"TEST_Operator {rule['operator']}",
                "rules": [rule]
            })
            assert create_res.status_code == 200, f"Failed to create list with operator {rule['operator']}"
            list_id = create_res.json()["list"]["id"]
            
            run_res = requests.post(f"{BASE_URL}/api/admin/smart-lists/{list_id}/run", headers=auth_headers)
            assert run_res.status_code == 200, f"Failed to run list with operator {rule['operator']}"
        
        print("All operators working")


class TestSidebarNavigation:
    """Test that new nav items are accessible"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for church admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Auth failed")
    
    def test_workflows_endpoint_accessible(self, auth_headers):
        """Workflows endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/admin/workflows", headers=auth_headers)
        assert response.status_code == 200
    
    def test_forms_endpoint_accessible(self, auth_headers):
        """Forms endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/admin/forms", headers=auth_headers)
        assert response.status_code == 200
    
    def test_smart_lists_endpoint_accessible(self, auth_headers):
        """Smart lists endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/admin/smart-lists", headers=auth_headers)
        assert response.status_code == 200
    
    def test_duplicates_endpoint_accessible(self, auth_headers):
        """Duplicates endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/admin/people/duplicates", headers=auth_headers)
        assert response.status_code == 200
    
    def test_calendar_approvals_endpoint_accessible(self, auth_headers):
        """Calendar approvals endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/admin/calendar/approvals", headers=auth_headers)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
