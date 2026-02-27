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

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdminAuth:
    """Admin authentication for testing"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get authenticated admin session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@abundant.church",
            "password": "Demo2026!"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert data["role"] == "church_admin"
        assert data["tenant_id"] == "abundant-church-001"
        return session
    
    def test_admin_login(self, admin_session):
        """Test admin login returns correct role and tenant"""
        response = admin_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@abundant.church"
        assert data["role"] in ["church_admin", "admin"]


class TestMemberAuth:
    """Member authentication for testing"""
    
    @pytest.fixture(scope="class")
    def member_session(self):
        """Get authenticated member session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        })
        assert response.status_code == 200, f"Member login failed: {response.text}"
        data = response.json()
        assert data["role"] == "member"
        return session
    
    def test_member_login(self, member_session):
        """Test member login returns correct role"""
        response = member_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "member@abundant.church"
        assert data["role"] == "member"


class TestPastorMeetingsAdmin:
    """Pastor Meeting APIs for Admin"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@abundant.church",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        return session
    
    def test_admin_get_meeting_slots(self, admin_session):
        """Admin can get meeting slots"""
        response = admin_session.get(f"{BASE_URL}/api/admin/meetings/slots")
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        # Should have demo slots seeded
        print(f"Found {len(data['slots'])} meeting slots")
    
    def test_admin_create_meeting_slot(self, admin_session):
        """Admin can create a new meeting slot"""
        from datetime import datetime, timedelta, timezone
        
        # Create a slot for next week
        start = datetime.now(timezone.utc) + timedelta(days=7, hours=10)
        end = start + timedelta(minutes=30)
        
        response = admin_session.post(f"{BASE_URL}/api/admin/meetings/slots", json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "location": "Pastor's office - Test Slot"
        })
        assert response.status_code == 200
        data = response.json()
        assert "slot" in data
        assert data["slot"]["location"] == "Pastor's office - Test Slot"
        assert data["slot"]["status"] == "open"
        print(f"Created slot: {data['slot']['id']}")
    
    def test_admin_get_meetings(self, admin_session):
        """Admin can view scheduled meetings"""
        response = admin_session.get(f"{BASE_URL}/api/admin/meetings")
        assert response.status_code == 200
        data = response.json()
        assert "meetings" in data
        print(f"Found {len(data['meetings'])} meetings")
        # Verify meeting structure if any exist
        if data['meetings']:
            meeting = data['meetings'][0]
            assert "id" in meeting
            assert "slot_id" in meeting
            assert "member_name" in meeting or "topic" in meeting


class TestPastorMeetingsMember:
    """Pastor Meeting APIs for Member"""
    
    @pytest.fixture(scope="class")
    def member_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        return session
    
    def test_member_get_available_slots(self, member_session):
        """Member can see available (open) meeting slots"""
        response = member_session.get(f"{BASE_URL}/api/portal/meetings/slots")
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        # All slots should be open (booked ones filtered out)
        for slot in data['slots']:
            assert slot['status'] == 'open'
        print(f"Found {len(data['slots'])} available slots for booking")
    
    def test_member_get_their_meetings(self, member_session):
        """Member can view their scheduled meetings"""
        response = member_session.get(f"{BASE_URL}/api/portal/meetings")
        assert response.status_code == 200
        data = response.json()
        assert "meetings" in data
        print(f"Member has {len(data['meetings'])} meetings")
    
    def test_member_book_meeting(self, member_session):
        """Member can book an available slot"""
        # First get available slots
        slots_response = member_session.get(f"{BASE_URL}/api/portal/meetings/slots")
        assert slots_response.status_code == 200
        slots = slots_response.json().get("slots", [])
        
        if not slots:
            pytest.skip("No available slots to book")
        
        # Book the first available slot
        slot = slots[0]
        response = member_session.post(f"{BASE_URL}/api/portal/meetings/book", json={
            "slot_id": slot["id"],
            "topic": "Test Meeting - Prayer Request",
            "notes": "Testing the booking system"
        })
        
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
    
    @pytest.fixture(scope="class")
    def member_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        return session
    
    def test_member_sees_8_courses(self, member_session):
        """Member should see 8 Abundant Pathways courses"""
        response = member_session.get(f"{BASE_URL}/api/portal/pathways/courses")
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        
        courses = data["courses"]
        print(f"Found {len(courses)} courses")
        
        # Verify we have the expected courses
        expected_categories = [
            "New Members Track",
            "Baptism Track", 
            "Discipleship Track",
            "Stewardship Track",
            "Leadership Track",
            "Spiritual Practices",
            "Family Track",
            "Outreach Track"
        ]
        
        # Check course structure
        for course in courses:
            assert "id" in course
            assert "title" in course
            assert "category" in course
            print(f"  - {course['title']} ({course['category']})")
        
        # Should have 8 courses for abundant-church-001
        assert len(courses) >= 8, f"Expected 8 courses, found {len(courses)}"
    
    def test_course_has_lessons(self, member_session):
        """Courses have lessons"""
        # Get first course
        courses_response = member_session.get(f"{BASE_URL}/api/portal/pathways/courses")
        assert courses_response.status_code == 200
        courses = courses_response.json().get("courses", [])
        
        if not courses:
            pytest.skip("No courses available")
        
        course_id = courses[0]["id"]
        response = member_session.get(f"{BASE_URL}/api/portal/pathways/courses/{course_id}/lessons")
        assert response.status_code == 200
        data = response.json()
        assert "lessons" in data
        print(f"Course '{courses[0]['title']}' has {len(data['lessons'])} lessons")


class TestSolomonChat:
    """Solomon AI Chat APIs"""
    
    def test_solomon_chat_endpoint(self):
        """Solomon chat API responds"""
        response = requests.post(f"{BASE_URL}/api/solomon/chat", json={
            "message": "How can I access Abundant Pathways?",
            "session_id": None
        })
        # May require auth but should not 500
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "session_id" in data
            print(f"Solomon response: {data['response'][:100]}...")


class TestMerchStore:
    """Merch Store APIs"""
    
    @pytest.fixture(scope="class")
    def member_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        return session
    
    def test_member_sees_products(self, member_session):
        """Member can see merch products"""
        response = member_session.get(f"{BASE_URL}/api/portal/merch/products")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        
        products = data["products"]
        print(f"Found {len(products)} merch products")
        
        # Verify product structure
        for product in products:
            assert "id" in product
            assert "name" in product
            assert "price" in product
            print(f"  - {product['name']}: ${product['price']}")
        
        # Should have demo products seeded
        assert len(products) > 0, "Expected merch products to be displayed"


class TestCafe:
    """Cafe Menu APIs"""
    
    @pytest.fixture(scope="class")
    def member_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        return session
    
    def test_member_sees_cafe_items(self, member_session):
        """Member can see cafe menu items"""
        response = member_session.get(f"{BASE_URL}/api/portal/cafe/items")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        
        items = data["items"]
        print(f"Found {len(items)} cafe items")
        
        # Verify item structure
        for item in items:
            assert "id" in item
            assert "name" in item
            assert "price" in item
            print(f"  - {item['name']}: ${item['price']}")
        
        # Should have demo items seeded
        assert len(items) > 0, "Expected cafe items to be displayed"
    
    def test_cafe_settings(self, member_session):
        """Member can see cafe settings"""
        response = member_session.get(f"{BASE_URL}/api/portal/cafe/settings")
        assert response.status_code == 200
        data = response.json()
        # Should have pickup times
        assert "pickup_start" in data or "settings" in data


class TestLeadershipNotes:
    """Leadership Notes (Leave a Note feature)"""
    
    @pytest.fixture(scope="class")
    def member_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": "Demo2026!"
        })
        assert response.status_code == 200
        return session
    
    def test_member_can_submit_note(self, member_session):
        """Member can submit a note to leadership"""
        response = member_session.post(f"{BASE_URL}/api/portal/notes", json={
            "subject": "Test Prayer Request",
            "message": "This is a test note for testing the Leave a Note feature",
            "category": "Prayer Request"
        })
        assert response.status_code == 200
        data = response.json()
        assert "note" in data
        assert data["note"]["subject"] == "Test Prayer Request"
        assert data["note"]["category"] == "Prayer Request"
        print(f"Note submitted: {data['note']['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
