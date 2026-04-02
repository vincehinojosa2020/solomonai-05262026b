"""
Solomon AI — Recurring Giving Feature Tests
Tests for the new Recurring Giving Management feature:
- Portal member CRUD operations (create, list, edit, pause, resume, cancel)
- Admin management operations (list all, change status)
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials — from environment
PORTAL_MEMBER_EMAIL = os.environ.get('TEST_MEMBER_EMAIL', 'member@abundant.church')
PORTAL_MEMBER_PASSWORD = os.environ.get('TEST_MEMBER_PASSWORD', '')
CHURCH_ADMIN_EMAIL = os.environ.get('TEST_ADMIN_EMAIL', 'shannonnieman1030@gmail.com')
CHURCH_ADMIN_PASSWORD = os.environ.get('TEST_ADMIN_PASSWORD', '')


class TestRecurringGivingPortal:
    """Portal member recurring giving CRUD tests"""
    
    @pytest.fixture(scope="class")
    def member_session(self):
        """Get authenticated portal member session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as portal member
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": PORTAL_MEMBER_EMAIL,
            "password": PORTAL_MEMBER_PASSWORD
        })
        assert response.status_code == 200, f"Portal member login failed: {response.text}"
        data = response.json()
        token = data.get("session_token") or data.get("token")
        assert token, "No session token returned"
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    @pytest.fixture(scope="class")
    def test_schedule_id(self, member_session):
        """Create a test schedule and return its ID for subsequent tests"""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "amount": 25.00,
            "fund_id": "general",
            "fund_name": f"TEST_Fund_{unique_id}",
            "frequency": "weekly",
            "start_date": "2026-01-15"
        }
        response = member_session.post(f"{BASE_URL}/api/portal/recurring-giving", json=payload)
        assert response.status_code == 200, f"Failed to create test schedule: {response.text}"
        data = response.json()
        assert "id" in data, "No schedule ID returned"
        return data["id"]
    
    def test_create_recurring_giving(self, member_session):
        """POST /api/portal/recurring-giving - Create recurring donation schedule"""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "amount": 50.00,
            "fund_id": "general",
            "fund_name": "General Fund",
            "frequency": "monthly",
            "start_date": "2026-01-20"
        }
        response = member_session.post(f"{BASE_URL}/api/portal/recurring-giving", json=payload)
        
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "id" in data, "Missing schedule ID"
        assert data["amount"] == 50.00, f"Amount mismatch: {data.get('amount')}"
        assert data["frequency"] == "monthly", f"Frequency mismatch: {data.get('frequency')}"
        assert data["status"] == "active", f"Status should be active: {data.get('status')}"
        assert "next_charge_date" in data, "Missing next_charge_date"
        assert "message" in data, "Missing success message"
        print(f"✓ Created recurring schedule: {data['id']}")
    
    def test_create_recurring_giving_validation_amount(self, member_session):
        """POST /api/portal/recurring-giving - Validate amount must be positive"""
        payload = {
            "amount": 0,
            "fund_id": "general",
            "fund_name": "General Fund",
            "frequency": "monthly"
        }
        response = member_session.post(f"{BASE_URL}/api/portal/recurring-giving", json=payload)
        assert response.status_code == 400, f"Should reject zero amount: {response.status_code}"
        print("✓ Correctly rejected zero amount")
    
    def test_create_recurring_giving_validation_frequency(self, member_session):
        """POST /api/portal/recurring-giving - Validate frequency"""
        payload = {
            "amount": 50.00,
            "fund_id": "general",
            "fund_name": "General Fund",
            "frequency": "invalid_frequency"
        }
        response = member_session.post(f"{BASE_URL}/api/portal/recurring-giving", json=payload)
        assert response.status_code == 400, f"Should reject invalid frequency: {response.status_code}"
        print("✓ Correctly rejected invalid frequency")
    
    def test_list_recurring_giving(self, member_session):
        """GET /api/portal/recurring-giving - List member's recurring schedules"""
        response = member_session.get(f"{BASE_URL}/api/portal/recurring-giving")
        
        assert response.status_code == 200, f"List failed: {response.text}"
        data = response.json()
        
        assert "schedules" in data, "Missing schedules array"
        assert isinstance(data["schedules"], list), "Schedules should be a list"
        print(f"✓ Listed {len(data['schedules'])} recurring schedules")
        
        # Verify schedule structure if any exist
        if data["schedules"]:
            schedule = data["schedules"][0]
            assert "id" in schedule, "Schedule missing id"
            assert "amount" in schedule, "Schedule missing amount"
            assert "frequency" in schedule, "Schedule missing frequency"
            assert "status" in schedule, "Schedule missing status"
            print(f"✓ Schedule structure validated: {schedule['id']}")
    
    def test_update_recurring_giving(self, member_session, test_schedule_id):
        """PUT /api/portal/recurring-giving/{id} - Edit recurring schedule"""
        payload = {
            "amount": 75.00,
            "frequency": "biweekly",
            "fund_name": "Updated Fund"
        }
        response = member_session.put(
            f"{BASE_URL}/api/portal/recurring-giving/{test_schedule_id}",
            json=payload
        )
        
        assert response.status_code == 200, f"Update failed: {response.text}"
        data = response.json()
        
        assert "schedule" in data, "Missing updated schedule"
        assert data["schedule"]["amount"] == 75.00, f"Amount not updated: {data['schedule'].get('amount')}"
        assert data["schedule"]["frequency"] == "biweekly", f"Frequency not updated: {data['schedule'].get('frequency')}"
        print(f"✓ Updated schedule {test_schedule_id}: amount=75.00, frequency=biweekly")
    
    def test_pause_recurring_giving(self, member_session, test_schedule_id):
        """PUT /api/portal/recurring-giving/{id}/pause - Pause active schedule"""
        response = member_session.put(f"{BASE_URL}/api/portal/recurring-giving/{test_schedule_id}/pause")
        
        assert response.status_code == 200, f"Pause failed: {response.text}"
        data = response.json()
        
        assert data.get("status") == "paused", f"Status should be paused: {data.get('status')}"
        print(f"✓ Paused schedule {test_schedule_id}")
    
    def test_pause_already_paused_schedule(self, member_session, test_schedule_id):
        """PUT /api/portal/recurring-giving/{id}/pause - Cannot pause already paused"""
        response = member_session.put(f"{BASE_URL}/api/portal/recurring-giving/{test_schedule_id}/pause")
        assert response.status_code == 400, f"Should reject pausing paused schedule: {response.status_code}"
        print("✓ Correctly rejected pausing already paused schedule")
    
    def test_resume_recurring_giving(self, member_session, test_schedule_id):
        """PUT /api/portal/recurring-giving/{id}/resume - Resume paused schedule"""
        response = member_session.put(f"{BASE_URL}/api/portal/recurring-giving/{test_schedule_id}/resume")
        
        assert response.status_code == 200, f"Resume failed: {response.text}"
        data = response.json()
        
        assert data.get("status") == "active", f"Status should be active: {data.get('status')}"
        assert "next_charge_date" in data, "Missing next_charge_date after resume"
        print(f"✓ Resumed schedule {test_schedule_id}")
    
    def test_resume_active_schedule(self, member_session, test_schedule_id):
        """PUT /api/portal/recurring-giving/{id}/resume - Cannot resume active schedule"""
        response = member_session.put(f"{BASE_URL}/api/portal/recurring-giving/{test_schedule_id}/resume")
        assert response.status_code == 400, f"Should reject resuming active schedule: {response.status_code}"
        print("✓ Correctly rejected resuming already active schedule")
    
    def test_cancel_recurring_giving(self, member_session, test_schedule_id):
        """DELETE /api/portal/recurring-giving/{id} - Cancel (soft-delete) schedule"""
        response = member_session.delete(f"{BASE_URL}/api/portal/recurring-giving/{test_schedule_id}")
        
        assert response.status_code == 200, f"Cancel failed: {response.text}"
        data = response.json()
        
        assert data.get("status") == "cancelled", f"Status should be cancelled: {data.get('status')}"
        print(f"✓ Cancelled schedule {test_schedule_id}")
    
    def test_cancel_already_cancelled(self, member_session, test_schedule_id):
        """DELETE /api/portal/recurring-giving/{id} - Cannot cancel already cancelled"""
        response = member_session.delete(f"{BASE_URL}/api/portal/recurring-giving/{test_schedule_id}")
        assert response.status_code == 400, f"Should reject cancelling cancelled schedule: {response.status_code}"
        print("✓ Correctly rejected cancelling already cancelled schedule")
    
    def test_edit_cancelled_schedule(self, member_session, test_schedule_id):
        """PUT /api/portal/recurring-giving/{id} - Cannot edit cancelled schedule"""
        payload = {"amount": 100.00}
        response = member_session.put(
            f"{BASE_URL}/api/portal/recurring-giving/{test_schedule_id}",
            json=payload
        )
        assert response.status_code == 400, f"Should reject editing cancelled schedule: {response.status_code}"
        print("✓ Correctly rejected editing cancelled schedule")
    
    def test_not_found_schedule(self, member_session):
        """Test 404 for non-existent schedule"""
        fake_id = "rec_nonexistent123"
        response = member_session.get(f"{BASE_URL}/api/portal/recurring-giving/{fake_id}/pause")
        # PUT method for pause
        response = member_session.put(f"{BASE_URL}/api/portal/recurring-giving/{fake_id}/pause")
        assert response.status_code == 404, f"Should return 404: {response.status_code}"
        print("✓ Correctly returned 404 for non-existent schedule")


class TestRecurringGivingAdmin:
    """Admin recurring giving management tests"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get authenticated admin session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as church admin
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        token = data.get("session_token") or data.get("token")
        assert token, "No session token returned"
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    @pytest.fixture(scope="class")
    def member_session_for_admin(self):
        """Get member session to create test data for admin tests"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": PORTAL_MEMBER_EMAIL,
            "password": PORTAL_MEMBER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        token = data.get("session_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    @pytest.fixture(scope="class")
    def admin_test_schedule_id(self, member_session_for_admin):
        """Create a test schedule for admin tests"""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "amount": 100.00,
            "fund_id": "general",
            "fund_name": f"ADMIN_TEST_Fund_{unique_id}",
            "frequency": "monthly"
        }
        response = member_session_for_admin.post(f"{BASE_URL}/api/portal/recurring-giving", json=payload)
        assert response.status_code == 200, f"Failed to create admin test schedule: {response.text}"
        return response.json()["id"]
    
    def test_admin_list_all_recurring(self, admin_session):
        """GET /api/admin/recurring-giving - Admin list all recurring schedules"""
        response = admin_session.get(f"{BASE_URL}/api/admin/recurring-giving")
        
        assert response.status_code == 200, f"Admin list failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "schedules" in data, "Missing schedules array"
        assert "total" in data, "Missing total count"
        assert "stats" in data, "Missing stats"
        
        # Validate stats structure
        stats = data["stats"]
        assert "active" in stats, "Missing active stats"
        assert "paused" in stats, "Missing paused stats"
        assert "cancelled" in stats, "Missing cancelled stats"
        
        # Validate stats have count and total_amount
        assert "count" in stats["active"], "Active stats missing count"
        assert "total_amount" in stats["active"], "Active stats missing total_amount"
        
        print(f"✓ Admin listed {data['total']} total schedules")
        print(f"  Active: {stats['active']['count']} (${stats['active']['total_amount']})")
        print(f"  Paused: {stats['paused']['count']}")
        print(f"  Cancelled: {stats['cancelled']['count']}")
    
    def test_admin_list_filter_active(self, admin_session):
        """GET /api/admin/recurring-giving?status=active - Filter by active status"""
        response = admin_session.get(f"{BASE_URL}/api/admin/recurring-giving?status=active")
        
        assert response.status_code == 200, f"Filter active failed: {response.text}"
        data = response.json()
        
        # All returned schedules should be active
        for schedule in data["schedules"]:
            assert schedule["status"] == "active", f"Non-active schedule in active filter: {schedule['status']}"
        
        print(f"✓ Admin filtered {len(data['schedules'])} active schedules")
    
    def test_admin_list_filter_paused(self, admin_session):
        """GET /api/admin/recurring-giving?status=paused - Filter by paused status"""
        response = admin_session.get(f"{BASE_URL}/api/admin/recurring-giving?status=paused")
        
        assert response.status_code == 200, f"Filter paused failed: {response.text}"
        data = response.json()
        
        for schedule in data["schedules"]:
            assert schedule["status"] == "paused", f"Non-paused schedule in paused filter: {schedule['status']}"
        
        print(f"✓ Admin filtered {len(data['schedules'])} paused schedules")
    
    def test_admin_list_filter_cancelled(self, admin_session):
        """GET /api/admin/recurring-giving?status=cancelled - Filter by cancelled status"""
        response = admin_session.get(f"{BASE_URL}/api/admin/recurring-giving?status=cancelled")
        
        assert response.status_code == 200, f"Filter cancelled failed: {response.text}"
        data = response.json()
        
        for schedule in data["schedules"]:
            assert schedule["status"] == "cancelled", f"Non-cancelled schedule in cancelled filter: {schedule['status']}"
        
        print(f"✓ Admin filtered {len(data['schedules'])} cancelled schedules")
    
    def test_admin_list_pagination(self, admin_session):
        """GET /api/admin/recurring-giving?page=1&per_page=5 - Test pagination"""
        response = admin_session.get(f"{BASE_URL}/api/admin/recurring-giving?page=1&per_page=5")
        
        assert response.status_code == 200, f"Pagination failed: {response.text}"
        data = response.json()
        
        assert "page" in data, "Missing page number"
        assert "per_page" in data, "Missing per_page"
        assert data["page"] == 1, f"Page should be 1: {data['page']}"
        assert data["per_page"] == 5, f"Per page should be 5: {data['per_page']}"
        assert len(data["schedules"]) <= 5, f"Should return max 5 schedules: {len(data['schedules'])}"
        
        print(f"✓ Admin pagination working: page {data['page']}, {len(data['schedules'])} items")
    
    def test_admin_change_status_to_paused(self, admin_session, admin_test_schedule_id):
        """PUT /api/admin/recurring-giving/{id}/status - Admin pause schedule"""
        payload = {"status": "paused"}
        response = admin_session.put(
            f"{BASE_URL}/api/admin/recurring-giving/{admin_test_schedule_id}/status",
            json=payload
        )
        
        assert response.status_code == 200, f"Admin pause failed: {response.text}"
        data = response.json()
        
        assert data.get("status") == "paused", f"Status should be paused: {data.get('status')}"
        print(f"✓ Admin paused schedule {admin_test_schedule_id}")
    
    def test_admin_change_status_to_active(self, admin_session, admin_test_schedule_id):
        """PUT /api/admin/recurring-giving/{id}/status - Admin resume schedule"""
        payload = {"status": "active"}
        response = admin_session.put(
            f"{BASE_URL}/api/admin/recurring-giving/{admin_test_schedule_id}/status",
            json=payload
        )
        
        assert response.status_code == 200, f"Admin resume failed: {response.text}"
        data = response.json()
        
        assert data.get("status") == "active", f"Status should be active: {data.get('status')}"
        print(f"✓ Admin resumed schedule {admin_test_schedule_id}")
    
    def test_admin_change_status_to_cancelled(self, admin_session, admin_test_schedule_id):
        """PUT /api/admin/recurring-giving/{id}/status - Admin cancel schedule"""
        payload = {"status": "cancelled"}
        response = admin_session.put(
            f"{BASE_URL}/api/admin/recurring-giving/{admin_test_schedule_id}/status",
            json=payload
        )
        
        assert response.status_code == 200, f"Admin cancel failed: {response.text}"
        data = response.json()
        
        assert data.get("status") == "cancelled", f"Status should be cancelled: {data.get('status')}"
        print(f"✓ Admin cancelled schedule {admin_test_schedule_id}")
    
    def test_admin_invalid_status(self, admin_session, admin_test_schedule_id):
        """PUT /api/admin/recurring-giving/{id}/status - Invalid status rejected"""
        payload = {"status": "invalid_status"}
        response = admin_session.put(
            f"{BASE_URL}/api/admin/recurring-giving/{admin_test_schedule_id}/status",
            json=payload
        )
        
        assert response.status_code == 400, f"Should reject invalid status: {response.status_code}"
        print("✓ Admin correctly rejected invalid status")
    
    def test_admin_not_found_schedule(self, admin_session):
        """PUT /api/admin/recurring-giving/{id}/status - 404 for non-existent"""
        fake_id = "rec_nonexistent456"
        payload = {"status": "paused"}
        response = admin_session.put(
            f"{BASE_URL}/api/admin/recurring-giving/{fake_id}/status",
            json=payload
        )
        
        assert response.status_code == 404, f"Should return 404: {response.status_code}"
        print("✓ Admin correctly returned 404 for non-existent schedule")


class TestRecurringGivingDataIntegrity:
    """Data integrity and persistence tests"""
    
    @pytest.fixture(scope="class")
    def member_session(self):
        """Get authenticated portal member session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": PORTAL_MEMBER_EMAIL,
            "password": PORTAL_MEMBER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        token = data.get("session_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_create_and_verify_persistence(self, member_session):
        """Create schedule and verify it appears in list"""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "amount": 123.45,
            "fund_id": "general",
            "fund_name": f"PERSIST_TEST_{unique_id}",
            "frequency": "annually"
        }
        
        # Create
        create_response = member_session.post(f"{BASE_URL}/api/portal/recurring-giving", json=payload)
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        
        # List and verify
        list_response = member_session.get(f"{BASE_URL}/api/portal/recurring-giving")
        assert list_response.status_code == 200
        schedules = list_response.json()["schedules"]
        
        found = next((s for s in schedules if s["id"] == created_id), None)
        assert found is not None, f"Created schedule {created_id} not found in list"
        assert found["amount"] == 123.45, f"Amount mismatch: {found['amount']}"
        assert found["frequency"] == "annually", f"Frequency mismatch: {found['frequency']}"
        
        print(f"✓ Schedule {created_id} persisted and verified in list")
    
    def test_update_and_verify_persistence(self, member_session):
        """Update schedule and verify changes persist"""
        # Create first
        payload = {
            "amount": 50.00,
            "fund_id": "general",
            "fund_name": "Update Test",
            "frequency": "weekly"
        }
        create_response = member_session.post(f"{BASE_URL}/api/portal/recurring-giving", json=payload)
        assert create_response.status_code == 200
        schedule_id = create_response.json()["id"]
        
        # Update
        update_payload = {"amount": 99.99, "frequency": "monthly"}
        update_response = member_session.put(
            f"{BASE_URL}/api/portal/recurring-giving/{schedule_id}",
            json=update_payload
        )
        assert update_response.status_code == 200
        
        # Verify in list
        list_response = member_session.get(f"{BASE_URL}/api/portal/recurring-giving")
        schedules = list_response.json()["schedules"]
        found = next((s for s in schedules if s["id"] == schedule_id), None)
        
        assert found["amount"] == 99.99, f"Updated amount not persisted: {found['amount']}"
        assert found["frequency"] == "monthly", f"Updated frequency not persisted: {found['frequency']}"
        
        print(f"✓ Schedule {schedule_id} updates persisted correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
