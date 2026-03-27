"""
Iteration 48: Solomon Academy Course/LMS Testing
Tests all course-related endpoints for admin and portal functionality.
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://solomon-demo-2.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "shannonnieman1030@gmail.com"
ADMIN_PASSWORD = "Demo2026!"

# Seeded course data
SEEDED_COURSE_ID = "abundant-next-steps"
SEEDED_LESSON_IDS = {
    "video": "les-1",
    "text": "les-2",
    "text2": "les-3",
    "video2": "les-4",
    "text3": "les-5",
    "text4": "les-6",
    "quiz": "les-7"
}


@pytest.fixture(scope="module")
def auth_session():
    """Setup authenticated session for all tests"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if response.status_code != 200:
        pytest.skip(f"Login failed with status {response.status_code}: {response.text}")
    
    data = response.json()
    token = data.get("token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    return session


class TestAdminCourses:
    """Test Admin Course CRUD operations"""
    
    def test_01_admin_list_courses(self, auth_session):
        """Test GET /api/admin/courses - List all courses"""
        response = auth_session.get(f"{BASE_URL}/api/admin/courses")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "courses" in data, "Response should contain 'courses' key"
        
        # Check for seeded course
        courses = data["courses"]
        seeded_course = next((c for c in courses if c["id"] == SEEDED_COURSE_ID), None)
        assert seeded_course is not None, f"Seeded course '{SEEDED_COURSE_ID}' should exist"
        assert seeded_course["title"] == "Abundant Next Steps", "Course title should match"
        assert seeded_course["status"] == "published", "Course should be published"
        print(f"✓ Found {len(courses)} courses, including seeded 'Abundant Next Steps'")
    
    def test_02_admin_get_course_detail(self, auth_session):
        """Test GET /api/admin/courses/{id} - Get course with modules and lessons"""
        response = auth_session.get(f"{BASE_URL}/api/admin/courses/{SEEDED_COURSE_ID}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        course = response.json()
        assert course["id"] == SEEDED_COURSE_ID
        assert course["title"] == "Abundant Next Steps"
        assert "modules" in course, "Course should have modules"
        
        # Verify 5 modules
        modules = course["modules"]
        assert len(modules) == 5, f"Expected 5 modules, got {len(modules)}"
        
        # Verify lessons exist in modules
        total_lessons = sum(len(m.get("lessons", [])) for m in modules)
        assert total_lessons == 7, f"Expected 7 lessons total, got {total_lessons}"
        print(f"✓ Course has {len(modules)} modules with {total_lessons} lessons")
    
    def test_03_admin_create_course(self, auth_session):
        """Test POST /api/admin/courses - Create new course"""
        response = auth_session.post(f"{BASE_URL}/api/admin/courses", json={
            "title": "TEST_New Course",
            "description": "Test course description",
            "status": "draft"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        course = response.json()
        assert "id" in course, "Created course should have an ID"
        assert course["title"] == "TEST_New Course"
        assert course["status"] == "draft"
        print(f"✓ Created course with ID: {course['id']}")
        
        # Cleanup - delete the test course
        delete_response = auth_session.delete(f"{BASE_URL}/api/admin/courses/{course['id']}")
        assert delete_response.status_code == 200, "Cleanup delete should succeed"
    
    def test_04_admin_update_course(self, auth_session):
        """Test PUT /api/admin/courses/{id} - Update course info"""
        # First create a test course
        create_response = auth_session.post(f"{BASE_URL}/api/admin/courses", json={
            "title": "TEST_Update Course",
            "status": "draft"
        })
        assert create_response.status_code == 200
        course_id = create_response.json()["id"]
        
        # Update the course
        update_response = auth_session.put(f"{BASE_URL}/api/admin/courses/{course_id}", json={
            "title": "TEST_Updated Title",
            "description": "Updated description",
            "instructor_name": "Test Instructor",
            "category": "leadership",
            "status": "published"
        })
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        
        # Verify update
        get_response = auth_session.get(f"{BASE_URL}/api/admin/courses/{course_id}")
        updated_course = get_response.json()
        assert updated_course["title"] == "TEST_Updated Title"
        assert updated_course["instructor_name"] == "Test Instructor"
        assert updated_course["status"] == "published"
        print("✓ Course updated successfully")
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/admin/courses/{course_id}")
    
    def test_05_admin_delete_course(self, auth_session):
        """Test DELETE /api/admin/courses/{id} - Delete course"""
        # Create a course to delete
        create_response = auth_session.post(f"{BASE_URL}/api/admin/courses", json={
            "title": "TEST_Delete Course"
        })
        course_id = create_response.json()["id"]
        
        # Delete it
        delete_response = auth_session.delete(f"{BASE_URL}/api/admin/courses/{course_id}")
        assert delete_response.status_code == 200
        
        # Verify it's gone
        get_response = auth_session.get(f"{BASE_URL}/api/admin/courses/{course_id}")
        assert get_response.status_code == 404, "Deleted course should return 404"
        print("✓ Course deleted successfully")


class TestAdminModules:
    """Test Admin Module operations"""
    
    def test_06_admin_create_module(self, auth_session):
        """Test POST /api/admin/courses/{id}/modules - Create module"""
        # Create test course
        course = auth_session.post(f"{BASE_URL}/api/admin/courses", json={"title": "TEST_Module Course"}).json()
        course_id = course["id"]
        
        # Create module
        response = auth_session.post(f"{BASE_URL}/api/admin/courses/{course_id}/modules", json={
            "title": "Test Module 1"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        module = response.json()
        assert "id" in module
        assert module["title"] == "Test Module 1"
        assert module["order"] == 1
        print(f"✓ Created module with ID: {module['id']}")
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/admin/courses/{course_id}")
    
    def test_07_admin_move_module(self, auth_session):
        """Test POST /api/admin/courses/{id}/modules/{mid}/move - Reorder modules"""
        # Create test course with 2 modules
        course = auth_session.post(f"{BASE_URL}/api/admin/courses", json={"title": "TEST_Move Module"}).json()
        course_id = course["id"]
        
        mod1 = auth_session.post(f"{BASE_URL}/api/admin/courses/{course_id}/modules", json={"title": "Module 1"}).json()
        mod2 = auth_session.post(f"{BASE_URL}/api/admin/courses/{course_id}/modules", json={"title": "Module 2"}).json()
        
        # Move module 2 up
        response = auth_session.post(f"{BASE_URL}/api/admin/courses/{course_id}/modules/{mod2['id']}/move", json={
            "direction": "up"
        })
        assert response.status_code == 200
        
        # Verify order changed
        course_data = auth_session.get(f"{BASE_URL}/api/admin/courses/{course_id}").json()
        modules = course_data["modules"]
        assert modules[0]["title"] == "Module 2", "Module 2 should now be first"
        print("✓ Module reordering works")
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/admin/courses/{course_id}")


class TestAdminLessons:
    """Test Admin Lesson operations"""
    
    def test_08_admin_create_lesson_video(self, auth_session):
        """Test creating a video lesson"""
        course = auth_session.post(f"{BASE_URL}/api/admin/courses", json={"title": "TEST_Lesson Course"}).json()
        module = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules", json={"title": "Module"}).json()
        
        response = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules/{module['id']}/lessons", json={
            "title": "Video Lesson",
            "type": "video",
            "content": {"video_url": "https://www.youtube.com/watch?v=test123"},
            "duration_minutes": 10
        })
        assert response.status_code == 200
        
        lesson = response.json()
        assert lesson["type"] == "video"
        assert lesson["content"]["video_url"] == "https://www.youtube.com/watch?v=test123"
        print("✓ Video lesson created")
        
        auth_session.delete(f"{BASE_URL}/api/admin/courses/{course['id']}")
    
    def test_09_admin_create_lesson_text(self, auth_session):
        """Test creating a text lesson"""
        course = auth_session.post(f"{BASE_URL}/api/admin/courses", json={"title": "TEST_Text Lesson"}).json()
        module = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules", json={"title": "Module"}).json()
        
        response = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules/{module['id']}/lessons", json={
            "title": "Text Lesson",
            "type": "text",
            "content": {"body": "# Heading\n\nThis is markdown content."},
            "duration_minutes": 5
        })
        assert response.status_code == 200
        
        lesson = response.json()
        assert lesson["type"] == "text"
        assert "# Heading" in lesson["content"]["body"]
        print("✓ Text lesson created")
        
        auth_session.delete(f"{BASE_URL}/api/admin/courses/{course['id']}")
    
    def test_10_admin_create_lesson_quiz(self, auth_session):
        """Test creating a quiz lesson"""
        course = auth_session.post(f"{BASE_URL}/api/admin/courses", json={"title": "TEST_Quiz Lesson"}).json()
        module = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules", json={"title": "Module"}).json()
        
        response = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules/{module['id']}/lessons", json={
            "title": "Quiz Lesson",
            "type": "quiz",
            "content": {
                "questions": [
                    {"question": "What is 2+2?", "options": ["3", "4", "5", "6"], "correct": 1}
                ],
                "passing_score": 70
            },
            "duration_minutes": 5
        })
        assert response.status_code == 200
        
        lesson = response.json()
        assert lesson["type"] == "quiz"
        assert len(lesson["content"]["questions"]) == 1
        print("✓ Quiz lesson created")
        
        auth_session.delete(f"{BASE_URL}/api/admin/courses/{course['id']}")
    
    def test_11_admin_create_lesson_download(self, auth_session):
        """Test creating a download lesson"""
        course = auth_session.post(f"{BASE_URL}/api/admin/courses", json={"title": "TEST_Download Lesson"}).json()
        module = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules", json={"title": "Module"}).json()
        
        response = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules/{module['id']}/lessons", json={
            "title": "Download Lesson",
            "type": "download",
            "content": {"file_url": "https://example.com/file.pdf", "file_name": "worksheet.pdf"},
            "duration_minutes": 2
        })
        assert response.status_code == 200
        
        lesson = response.json()
        assert lesson["type"] == "download"
        assert lesson["content"]["file_name"] == "worksheet.pdf"
        print("✓ Download lesson created")
        
        auth_session.delete(f"{BASE_URL}/api/admin/courses/{course['id']}")
    
    def test_12_admin_update_lesson(self, auth_session):
        """Test PUT /api/admin/courses/{id}/lessons/{lid} - Update lesson"""
        course = auth_session.post(f"{BASE_URL}/api/admin/courses", json={"title": "TEST_Update Lesson"}).json()
        module = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules", json={"title": "Module"}).json()
        lesson = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules/{module['id']}/lessons", json={
            "title": "Original Title", "type": "text", "content": {"body": "Original"}
        }).json()
        
        response = auth_session.put(f"{BASE_URL}/api/admin/courses/{course['id']}/lessons/{lesson['id']}", json={
            "title": "Updated Title",
            "content": {"body": "Updated content"}
        })
        assert response.status_code == 200
        print("✓ Lesson updated")
        
        auth_session.delete(f"{BASE_URL}/api/admin/courses/{course['id']}")
    
    def test_13_admin_delete_lesson(self, auth_session):
        """Test DELETE /api/admin/courses/{id}/lessons/{lid} - Delete lesson"""
        course = auth_session.post(f"{BASE_URL}/api/admin/courses", json={"title": "TEST_Delete Lesson"}).json()
        module = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules", json={"title": "Module"}).json()
        lesson = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules/{module['id']}/lessons", json={
            "title": "To Delete", "type": "text"
        }).json()
        
        response = auth_session.delete(f"{BASE_URL}/api/admin/courses/{course['id']}/lessons/{lesson['id']}")
        assert response.status_code == 200
        print("✓ Lesson deleted")
        
        auth_session.delete(f"{BASE_URL}/api/admin/courses/{course['id']}")
    
    def test_14_admin_move_lesson(self, auth_session):
        """Test POST /api/admin/courses/{id}/lessons/{lid}/move - Reorder lessons"""
        course = auth_session.post(f"{BASE_URL}/api/admin/courses", json={"title": "TEST_Move Lesson"}).json()
        module = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules", json={"title": "Module"}).json()
        
        les1 = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules/{module['id']}/lessons", json={
            "title": "Lesson 1", "type": "text"
        }).json()
        les2 = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules/{module['id']}/lessons", json={
            "title": "Lesson 2", "type": "text"
        }).json()
        
        response = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/lessons/{les2['id']}/move", json={
            "direction": "up"
        })
        assert response.status_code == 200
        print("✓ Lesson reordering works")
        
        auth_session.delete(f"{BASE_URL}/api/admin/courses/{course['id']}")


class TestAdminEnrollments:
    """Test Admin Enrollment operations"""
    
    def test_15_admin_get_enrollments(self, auth_session):
        """Test GET /api/admin/courses/{id}/enrollments - Get enrolled members"""
        response = auth_session.get(f"{BASE_URL}/api/admin/courses/{SEEDED_COURSE_ID}/enrollments")
        assert response.status_code == 200
        
        data = response.json()
        assert "enrollments" in data
        assert "total" in data
        print(f"✓ Found {data['total']} enrollments for seeded course")


class TestPortalCourses:
    """Test Portal (Member-facing) Course operations"""
    
    def test_16_portal_list_courses(self, auth_session):
        """Test GET /api/portal/courses - List published courses for members"""
        response = auth_session.get(f"{BASE_URL}/api/portal/courses")
        assert response.status_code == 200
        
        data = response.json()
        assert "courses" in data
        
        # Should only see published courses
        courses = data["courses"]
        for c in courses:
            assert c["status"] == "published", "Portal should only show published courses"
        
        # Seeded course should be visible
        seeded = next((c for c in courses if c["id"] == SEEDED_COURSE_ID), None)
        assert seeded is not None, "Seeded published course should be visible in portal"
        print(f"✓ Portal shows {len(courses)} published courses")
    
    def test_17_portal_course_detail(self, auth_session):
        """Test GET /api/portal/courses/{id} - Get course detail for members"""
        response = auth_session.get(f"{BASE_URL}/api/portal/courses/{SEEDED_COURSE_ID}")
        assert response.status_code == 200
        
        course = response.json()
        assert course["id"] == SEEDED_COURSE_ID
        assert course["title"] == "Abundant Next Steps"
        assert "modules" in course
        assert "enrolled" in course
        assert "progress" in course
        print(f"✓ Portal course detail loaded, enrolled={course['enrolled']}, progress={course['progress']}%")
    
    def test_18_portal_enroll(self, auth_session):
        """Test POST /api/portal/courses/{id}/enroll - Enroll in course"""
        response = auth_session.post(f"{BASE_URL}/api/portal/courses/{SEEDED_COURSE_ID}/enroll")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        print("✓ Enrollment successful (or already enrolled)")
    
    def test_19_portal_get_lesson(self, auth_session):
        """Test GET /api/portal/courses/{id}/lessons/{lid} - Get lesson content"""
        # First ensure enrolled
        auth_session.post(f"{BASE_URL}/api/portal/courses/{SEEDED_COURSE_ID}/enroll")
        
        # Get video lesson
        response = auth_session.get(f"{BASE_URL}/api/portal/courses/{SEEDED_COURSE_ID}/lessons/{SEEDED_LESSON_IDS['video']}")
        assert response.status_code == 200
        
        lesson = response.json()
        assert lesson["id"] == SEEDED_LESSON_IDS["video"]
        assert lesson["type"] == "video"
        assert "content" in lesson
        assert "prev_lesson_id" in lesson
        assert "next_lesson_id" in lesson
        print(f"✓ Video lesson loaded: {lesson['title']}")
    
    def test_20_portal_get_text_lesson(self, auth_session):
        """Test getting text lesson with markdown content"""
        response = auth_session.get(f"{BASE_URL}/api/portal/courses/{SEEDED_COURSE_ID}/lessons/{SEEDED_LESSON_IDS['text']}")
        assert response.status_code == 200
        
        lesson = response.json()
        assert lesson["type"] == "text"
        assert "body" in lesson.get("content", {}), "Text lesson should have body content"
        print(f"✓ Text lesson loaded: {lesson['title']}")
    
    def test_21_portal_get_quiz_lesson(self, auth_session):
        """Test getting quiz lesson with questions"""
        response = auth_session.get(f"{BASE_URL}/api/portal/courses/{SEEDED_COURSE_ID}/lessons/{SEEDED_LESSON_IDS['quiz']}")
        assert response.status_code == 200
        
        lesson = response.json()
        assert lesson["type"] == "quiz"
        assert "questions" in lesson.get("content", {}), "Quiz should have questions"
        questions = lesson["content"]["questions"]
        assert len(questions) == 3, f"Expected 3 quiz questions, got {len(questions)}"
        print(f"✓ Quiz lesson loaded with {len(questions)} questions")
    
    def test_22_portal_complete_lesson(self, auth_session):
        """Test POST /api/portal/courses/{id}/lessons/{lid}/complete - Mark lesson complete"""
        response = auth_session.post(f"{BASE_URL}/api/portal/courses/{SEEDED_COURSE_ID}/lessons/{SEEDED_LESSON_IDS['video']}/complete")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "progress" in data
        print(f"✓ Lesson marked complete, course progress: {data['progress']}%")
    
    def test_23_portal_submit_quiz(self, auth_session):
        """Test POST /api/portal/courses/{id}/lessons/{lid}/quiz - Submit quiz answers"""
        # Submit correct answers (all correct answers are index 1)
        response = auth_session.post(f"{BASE_URL}/api/portal/courses/{SEEDED_COURSE_ID}/lessons/{SEEDED_LESSON_IDS['quiz']}/quiz", json={
            "answers": [1, 1, 1]  # All correct answers
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "score" in data
        assert "passed" in data
        assert "correct" in data
        assert "total" in data
        print(f"✓ Quiz submitted: score={data['score']}%, passed={data['passed']}, {data['correct']}/{data['total']} correct")
    
    def test_24_portal_my_courses(self, auth_session):
        """Test GET /api/portal/courses/my - Get enrolled courses"""
        response = auth_session.get(f"{BASE_URL}/api/portal/courses/my")
        assert response.status_code == 200
        
        data = response.json()
        assert "courses" in data
        
        # Should include the course we enrolled in
        enrolled_ids = [c["id"] for c in data["courses"]]
        assert SEEDED_COURSE_ID in enrolled_ids, "Seeded course should be in my courses after enrollment"
        print(f"✓ My courses: {len(data['courses'])} enrolled")
    
    def test_25_portal_lesson_requires_enrollment(self, auth_session):
        """Test that lesson access requires enrollment"""
        # Create a new course that user is NOT enrolled in
        course = auth_session.post(f"{BASE_URL}/api/admin/courses", json={
            "title": "TEST_No Enroll Course",
            "status": "published"
        }).json()
        module = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules", json={"title": "Module"}).json()
        lesson = auth_session.post(f"{BASE_URL}/api/admin/courses/{course['id']}/modules/{module['id']}/lessons", json={
            "title": "Locked Lesson", "type": "text"
        }).json()
        
        # Try to access lesson without enrollment
        response = auth_session.get(f"{BASE_URL}/api/portal/courses/{course['id']}/lessons/{lesson['id']}")
        assert response.status_code == 403, "Should get 403 when not enrolled"
        print("✓ Lesson access correctly requires enrollment")
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/admin/courses/{course['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
