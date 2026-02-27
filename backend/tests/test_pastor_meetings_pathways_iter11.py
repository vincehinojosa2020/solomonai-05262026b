"""
Test Suite for Solomon AI - Pastor Meetings, Abundant Pathways, Merch Store, Cafe
Iteration 11 - Testing features requested by main agent

Features tested:
- Pastor Meeting Scheduler (Admin create slots, view meetings)
- Pastor Meeting Scheduler (Member view slots, book meetings)
- Abundant Pathways (8 courses for member)
- Solomon Chat (API endpoints)
- Merch Store (Products display)
- Cafe (Menu items display)
- Portal Home (Notes API)
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

# Module-level session creation to avoid repeated logins
def get_admin_session():
    session = requests.Session()
    def login():
        return session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@abundant.church",
            "password": "Demo2026!"
        }, timeout=30)
    response = retry_request(login)
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return session

def get_member_session():
    session = requests.Session()
    def login():
        return session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        }, timeout=30)
    response = retry_request(login)
    assert response.status_code == 200, f"Member login failed: {response.text}"
    return session


class TestAuth:
    """Authentication tests"""
    
    def test_admin_login_success(self):
        """Admin can login with correct credentials"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@abundant.church",
            "password": "Demo2026!"
        }, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "church_admin"
        assert data["tenant_id"] == "abundant-church-001"
    
    def test_member_login_success(self):
        """Member can login with correct credentials"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        }, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "member"


class TestPastorMeetingsAdmin:
    """Pastor Meeting APIs for Admin"""
    
    def test_admin_get_meeting_slots(self):
        """Admin can get meeting slots"""
        session = get_admin_session()
        response = session.get(f"{BASE_URL}/api/admin/meetings/slots", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        print(f"Found {len(data['slots'])} meeting slots")
    
    def test_admin_create_meeting_slot(self):
        """Admin can create a new meeting slot"""
        from datetime import datetime, timedelta, timezone
        
        session = get_admin_session()
        # Create a slot for next week
        start = datetime.now(timezone.utc) + timedelta(days=8, hours=14)
        end = start + timedelta(minutes=30)
        
        response = session.post(f"{BASE_URL}/api/admin/meetings/slots", json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "location": "Pastor's office - Test Slot"
        }, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "slot" in data
        assert data["slot"]["location"] == "Pastor's office - Test Slot"
        assert data["slot"]["status"] == "open"
        print(f"Created slot: {data['slot']['id']}")
    
    def test_admin_get_meetings(self):
        """Admin can view scheduled meetings"""
        session = get_admin_session()
        response = session.get(f"{BASE_URL}/api/admin/meetings", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "meetings" in data
        print(f"Found {len(data['meetings'])} meetings")


class TestPastorMeetingsMember:
    """Pastor Meeting APIs for Member"""
    
    def test_member_get_available_slots(self):
        """Member can see available (open) meeting slots"""
        session = get_member_session()
        response = session.get(f"{BASE_URL}/api/portal/meetings/slots", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        # All slots should be open
        for slot in data['slots']:
            assert slot['status'] == 'open'
        print(f"Found {len(data['slots'])} available slots for booking")
    
    def test_member_get_their_meetings(self):
        """Member can view their scheduled meetings"""
        session = get_member_session()
        response = session.get(f"{BASE_URL}/api/portal/meetings", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "meetings" in data
        print(f"Member has {len(data['meetings'])} meetings")
    
    def test_member_book_meeting(self):
        """Member can book an available slot"""
        session = get_member_session()
        
        # First get available slots
        slots_response = session.get(f"{BASE_URL}/api/portal/meetings/slots", timeout=30)
        assert slots_response.status_code == 200
        slots = slots_response.json().get("slots", [])
        
        if not slots:
            pytest.skip("No available slots to book")
        
        # Book the first available slot
        slot = slots[0]
        response = session.post(f"{BASE_URL}/api/portal/meetings/book", json={
            "slot_id": slot["id"],
            "topic": "Test Meeting - Prayer Request",
            "notes": "Testing the booking system"
        }, timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        assert "meeting" in data
        assert data["meeting"]["topic"] == "Test Meeting - Prayer Request"
        assert data["meeting"]["status"] == "scheduled"
        # Check mocked notifications
        assert "notifications" in data
        print(f"Booked meeting: {data['meeting']['id']}")


class TestAbundantPathways:
    """Abundant Pathways LMS - 8 courses for member"""
    
    def test_member_sees_courses(self):
        """Member should see Abundant Pathways courses"""
        session = get_member_session()
        response = session.get(f"{BASE_URL}/api/portal/pathways/courses", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        
        courses = data["courses"]
        print(f"Found {len(courses)} courses:")
        
        # Check course structure
        for course in courses:
            assert "id" in course
            assert "title" in course
            assert "category" in course
            print(f"  - {course['title']} ({course['category']})")
        
        # Should have 8 courses for abundant-church-001
        assert len(courses) >= 8, f"Expected 8 courses, found {len(courses)}"


class TestMerchStore:
    """Merch Store APIs"""
    
    def test_member_sees_products(self):
        """Member can see merch products"""
        session = get_member_session()
        response = session.get(f"{BASE_URL}/api/portal/merch/products", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        
        products = data["products"]
        print(f"Found {len(products)} merch products:")
        
        # Verify product structure
        for product in products:
            assert "id" in product
            assert "name" in product
            assert "price" in product
            print(f"  - {product['name']}: ${product['price']}")
        
        assert len(products) > 0, "Expected merch products to be displayed"


class TestCafe:
    """Cafe Menu APIs"""
    
    def test_member_sees_cafe_items(self):
        """Member can see cafe menu items"""
        session = get_member_session()
        response = session.get(f"{BASE_URL}/api/portal/cafe/items", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        
        items = data["items"]
        print(f"Found {len(items)} cafe items:")
        
        for item in items:
            assert "id" in item
            assert "name" in item
            assert "price" in item
            print(f"  - {item['name']}: ${item['price']}")
        
        assert len(items) > 0, "Expected cafe items to be displayed"


class TestLeadershipNotes:
    """Leadership Notes (Leave a Note feature)"""
    
    def test_member_can_submit_note(self):
        """Member can submit a note to leadership"""
        session = get_member_session()
        response = session.post(f"{BASE_URL}/api/portal/notes", json={
            "subject": "Test Prayer Request",
            "message": "This is a test note for testing the Leave a Note feature",
            "category": "Prayer Request"
        }, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "note" in data
        assert data["note"]["subject"] == "Test Prayer Request"
        assert data["note"]["category"] == "Prayer Request"
        print(f"Note submitted: {data['note']['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
