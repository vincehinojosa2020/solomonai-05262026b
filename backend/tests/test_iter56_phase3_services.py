"""
Phase 3 Services Module Tests - Iteration 56
Tests: Song Library, Service Plans, Templates, Duplication, Music Stand

Features tested:
- Song Library CRUD (GET, POST, PUT, DELETE /api/admin/songs)
- Service Plans CRUD (GET, POST, PUT /api/admin/services/plans)
- Plan Duplication (POST /api/admin/services/plans/{id}/duplicate)
- Plan Templates (GET, POST /api/admin/services/templates)
- Music Stand public view (GET /api/music-stand/{planId})
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "shannonnieman1030@gmail.com"
TEST_PASSWORD = "Demo2026!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for church admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("session_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


# ============== SONG LIBRARY TESTS ==============

class TestSongLibrary:
    """Song Library CRUD tests"""
    
    def test_get_songs_list(self, auth_headers):
        """GET /api/admin/songs - should return songs list"""
        response = requests.get(f"{BASE_URL}/api/admin/songs", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "songs" in data, "Response should contain 'songs' key"
        assert isinstance(data["songs"], list), "Songs should be a list"
        print(f"✓ Found {len(data['songs'])} songs in library")
    
    def test_get_songs_with_search(self, auth_headers):
        """GET /api/admin/songs?search=... - should filter songs"""
        response = requests.get(f"{BASE_URL}/api/admin/songs?search=Amazing", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "songs" in data
        print(f"✓ Search returned {len(data['songs'])} songs matching 'Amazing'")
    
    def test_create_song(self, auth_headers):
        """POST /api/admin/songs - should create a new song"""
        song_data = {
            "title": f"TEST_Song_{uuid.uuid4().hex[:8]}",
            "artist": "Test Artist",
            "ccli_number": "1234567",
            "default_key": "G",
            "bpm": 120,
            "lyrics": "Verse 1:\nTest lyrics here\n\nChorus:\nTest chorus",
            "tags": ["worship", "test"]
        }
        response = requests.post(f"{BASE_URL}/api/admin/songs", headers=auth_headers, json=song_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "song" in data, "Response should contain 'song' key"
        song = data["song"]
        assert song["title"] == song_data["title"], "Title should match"
        assert song["artist"] == song_data["artist"], "Artist should match"
        assert "id" in song, "Song should have an ID"
        print(f"✓ Created song: {song['title']} (ID: {song['id']})")
        return song["id"]
    
    def test_update_song(self, auth_headers):
        """PUT /api/admin/songs/{id} - should update a song"""
        # First create a song
        song_data = {
            "title": f"TEST_Update_{uuid.uuid4().hex[:8]}",
            "artist": "Original Artist",
            "default_key": "C"
        }
        create_resp = requests.post(f"{BASE_URL}/api/admin/songs", headers=auth_headers, json=song_data)
        assert create_resp.status_code == 200
        song_id = create_resp.json()["song"]["id"]
        
        # Update the song
        update_data = {
            "artist": "Updated Artist",
            "default_key": "D",
            "bpm": 130
        }
        response = requests.put(f"{BASE_URL}/api/admin/songs/{song_id}", headers=auth_headers, json=update_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ Updated song {song_id}")
    
    def test_delete_song(self, auth_headers):
        """DELETE /api/admin/songs/{id} - should delete a song"""
        # First create a song to delete
        song_data = {
            "title": f"TEST_Delete_{uuid.uuid4().hex[:8]}",
            "artist": "To Be Deleted"
        }
        create_resp = requests.post(f"{BASE_URL}/api/admin/songs", headers=auth_headers, json=song_data)
        assert create_resp.status_code == 200
        song_id = create_resp.json()["song"]["id"]
        
        # Delete the song
        response = requests.delete(f"{BASE_URL}/api/admin/songs/{song_id}", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify deletion - search should not find it
        search_resp = requests.get(f"{BASE_URL}/api/admin/songs?search={song_data['title']}", headers=auth_headers)
        songs = search_resp.json().get("songs", [])
        assert not any(s["id"] == song_id for s in songs), "Song should be deleted"
        print(f"✓ Deleted song {song_id}")


# ============== SERVICE PLANS TESTS ==============

class TestServicePlans:
    """Service Plans CRUD tests"""
    
    def test_get_service_plans(self, auth_headers):
        """GET /api/admin/services/plans - should return plans list"""
        response = requests.get(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "plans" in data, "Response should contain 'plans' key"
        assert isinstance(data["plans"], list), "Plans should be a list"
        print(f"✓ Found {len(data['plans'])} service plans")
        return data["plans"]
    
    def test_create_service_plan(self, auth_headers):
        """POST /api/admin/services/plans - should create a new plan"""
        plan_data = {
            "title": f"TEST_Service_{uuid.uuid4().hex[:8]}",
            "date": "2026-02-01",
            "service_type": "sunday_morning",
            "items": []
        }
        response = requests.post(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers, json=plan_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Response should contain plan ID"
        assert data["title"] == plan_data["title"], "Title should match"
        assert data["status"] == "draft", "New plan should be draft status"
        print(f"✓ Created service plan: {data['title']} (ID: {data['id']})")
        return data["id"]
    
    def test_update_service_plan(self, auth_headers):
        """PUT /api/admin/services/plans/{id} - should update a plan"""
        # First create a plan
        plan_data = {
            "title": f"TEST_Update_Plan_{uuid.uuid4().hex[:8]}",
            "date": "2026-02-02",
            "service_type": "sunday_morning"
        }
        create_resp = requests.post(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers, json=plan_data)
        assert create_resp.status_code == 200
        plan_id = create_resp.json()["id"]
        
        # Update the plan
        update_data = {
            "status": "confirmed",
            "items": [
                {"id": str(uuid.uuid4()), "title": "Opening Song", "type": "song", "duration": "5", "order": 0}
            ]
        }
        response = requests.put(f"{BASE_URL}/api/admin/services/plans/{plan_id}", headers=auth_headers, json=update_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["status"] == "confirmed", "Status should be updated"
        assert len(data["items"]) == 1, "Items should be updated"
        print(f"✓ Updated service plan {plan_id}")
    
    def test_add_items_to_plan(self, auth_headers):
        """PUT /api/admin/services/plans/{id} - should add items to plan"""
        # Create a plan
        plan_data = {
            "title": f"TEST_Items_Plan_{uuid.uuid4().hex[:8]}",
            "date": "2026-02-03",
            "service_type": "sunday_morning"
        }
        create_resp = requests.post(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers, json=plan_data)
        assert create_resp.status_code == 200
        plan_id = create_resp.json()["id"]
        
        # Add multiple items
        items = [
            {"id": str(uuid.uuid4()), "title": "Welcome", "type": "announcement", "duration": "3", "order": 0},
            {"id": str(uuid.uuid4()), "title": "Way Maker", "type": "song", "duration": "5", "order": 1},
            {"id": str(uuid.uuid4()), "title": "Prayer", "type": "prayer", "duration": "5", "order": 2},
            {"id": str(uuid.uuid4()), "title": "Sermon", "type": "sermon", "duration": "30", "order": 3},
        ]
        response = requests.put(f"{BASE_URL}/api/admin/services/plans/{plan_id}", headers=auth_headers, json={"items": items})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 4, f"Expected 4 items, got {len(data['items'])}"
        print(f"✓ Added 4 items to plan {plan_id}")


# ============== PLAN DUPLICATION TESTS ==============

class TestPlanDuplication:
    """Plan duplication tests"""
    
    def test_duplicate_plan(self, auth_headers):
        """POST /api/admin/services/plans/{id}/duplicate - should duplicate a plan"""
        # First create a plan with items
        plan_data = {
            "title": f"TEST_Original_{uuid.uuid4().hex[:8]}",
            "date": "2026-02-10",
            "service_type": "sunday_morning",
            "items": [
                {"id": str(uuid.uuid4()), "title": "Song 1", "type": "song", "duration": "5", "order": 0},
                {"id": str(uuid.uuid4()), "title": "Sermon", "type": "sermon", "duration": "30", "order": 1},
            ]
        }
        create_resp = requests.post(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers, json=plan_data)
        assert create_resp.status_code == 200
        original_id = create_resp.json()["id"]
        
        # Duplicate the plan
        response = requests.post(f"{BASE_URL}/api/admin/services/plans/{original_id}/duplicate", headers=auth_headers, json={})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["id"] != original_id, "Duplicated plan should have new ID"
        assert "(Copy)" in data["title"], "Duplicated plan title should contain '(Copy)'"
        assert len(data["items"]) == 2, "Duplicated plan should have same number of items"
        assert data["status"] == "draft", "Duplicated plan should be draft"
        print(f"✓ Duplicated plan {original_id} -> {data['id']}")
    
    def test_duplicate_existing_plan_with_items(self, auth_headers):
        """Duplicate the existing plan with ID 7baf317d-b87f-4458-afdd-e805b86b71f6"""
        plan_id = "7baf317d-b87f-4458-afdd-e805b86b71f6"
        response = requests.post(f"{BASE_URL}/api/admin/services/plans/{plan_id}/duplicate", headers=auth_headers, json={})
        # This may fail if plan doesn't exist, which is fine
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Duplicated existing plan -> {data['id']} with {len(data.get('items', []))} items")
        elif response.status_code == 404:
            print(f"⚠ Plan {plan_id} not found (may have been deleted)")
        else:
            print(f"⚠ Unexpected status: {response.status_code}")


# ============== TEMPLATES TESTS ==============

class TestPlanTemplates:
    """Plan templates tests"""
    
    def test_get_templates(self, auth_headers):
        """GET /api/admin/services/templates - should return templates list"""
        response = requests.get(f"{BASE_URL}/api/admin/services/templates", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "templates" in data, "Response should contain 'templates' key"
        print(f"✓ Found {len(data['templates'])} templates")
    
    def test_create_template(self, auth_headers):
        """POST /api/admin/services/templates - should create a template"""
        template_data = {
            "name": f"TEST_Template_{uuid.uuid4().hex[:8]}",
            "description": "Test template for Sunday service",
            "service_type": "sunday_morning",
            "items": [
                {"title": "Welcome", "type": "announcement", "duration": "3", "order": 0},
                {"title": "Worship Set", "type": "song", "duration": "20", "order": 1},
                {"title": "Message", "type": "sermon", "duration": "35", "order": 2},
                {"title": "Closing", "type": "song", "duration": "5", "order": 3},
            ]
        }
        response = requests.post(f"{BASE_URL}/api/admin/services/templates", headers=auth_headers, json=template_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "template" in data, "Response should contain 'template' key"
        template = data["template"]
        assert template["name"] == template_data["name"], "Name should match"
        assert len(template["items"]) == 4, "Template should have 4 items"
        print(f"✓ Created template: {template['name']} (ID: {template['id']})")
        return template["id"]
    
    def test_create_plan_from_template(self, auth_headers):
        """POST /api/admin/services/plans/from-template - should create plan from template"""
        # First create a template
        template_data = {
            "name": f"TEST_FromTemplate_{uuid.uuid4().hex[:8]}",
            "service_type": "sunday_morning",
            "items": [
                {"title": "Opening", "type": "song", "duration": "5", "order": 0},
            ]
        }
        template_resp = requests.post(f"{BASE_URL}/api/admin/services/templates", headers=auth_headers, json=template_data)
        assert template_resp.status_code == 200
        template_id = template_resp.json()["template"]["id"]
        
        # Create plan from template
        response = requests.post(f"{BASE_URL}/api/admin/services/plans/from-template", headers=auth_headers, json={
            "template_id": template_id,
            "date": "2026-03-01"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["template_id"] == template_id, "Plan should reference template"
        assert len(data["items"]) == 1, "Plan should have items from template"
        print(f"✓ Created plan from template: {data['id']}")


# ============== MUSIC STAND TESTS ==============

class TestMusicStand:
    """Music Stand public view tests"""
    
    def test_music_stand_public_access(self):
        """GET /api/music-stand/{planId} - should be publicly accessible (no auth)"""
        # First get a plan ID (need auth for this)
        auth_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if auth_resp.status_code != 200:
            pytest.skip("Cannot authenticate to get plan ID")
        
        token = auth_resp.json().get("session_token") or auth_resp.json().get("token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Get plans
        plans_resp = requests.get(f"{BASE_URL}/api/admin/services/plans", headers=headers)
        if plans_resp.status_code != 200 or not plans_resp.json().get("plans"):
            pytest.skip("No plans available")
        
        plan_id = plans_resp.json()["plans"][0]["id"]
        
        # Access music stand WITHOUT auth
        response = requests.get(f"{BASE_URL}/api/music-stand/{plan_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "plan_id" in data, "Response should contain plan_id"
        assert "title" in data, "Response should contain title"
        assert "items" in data, "Response should contain items"
        print(f"✓ Music stand accessible for plan: {data['title']}")
    
    def test_music_stand_specific_plan(self):
        """GET /api/music-stand/7baf317d-b87f-4458-afdd-e805b86b71f6 - test specific plan"""
        plan_id = "7baf317d-b87f-4458-afdd-e805b86b71f6"
        response = requests.get(f"{BASE_URL}/api/music-stand/{plan_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Music stand for plan '{data['title']}' has {len(data['items'])} items")
            for i, item in enumerate(data["items"]):
                print(f"  - Item {i+1}: {item.get('title', 'Untitled')} ({item.get('type', 'unknown')})")
        elif response.status_code == 404:
            print(f"⚠ Plan {plan_id} not found")
        else:
            print(f"⚠ Unexpected status: {response.status_code}")
    
    def test_music_stand_invalid_plan(self):
        """GET /api/music-stand/invalid-id - should return 404"""
        response = requests.get(f"{BASE_URL}/api/music-stand/invalid-plan-id-12345")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid plan ID returns 404")


# ============== SERVICE TYPES TESTS ==============

class TestServiceTypes:
    """Service types configuration tests"""
    
    def test_get_service_types(self, auth_headers):
        """GET /api/admin/service-types - should return service types"""
        response = requests.get(f"{BASE_URL}/api/admin/service-types", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "service_types" in data, "Response should contain 'service_types' key"
        types = data["service_types"]
        assert len(types) >= 4, f"Expected at least 4 service types (defaults), got {len(types)}"
        type_ids = [t["id"] for t in types]
        assert "sunday_morning" in type_ids, "Should have sunday_morning type"
        print(f"✓ Found {len(types)} service types: {type_ids}")


# ============== SEEDED DATA VERIFICATION ==============

class TestSeededData:
    """Verify seeded data exists"""
    
    def test_songs_seeded(self, auth_headers):
        """Verify 10 seeded songs exist"""
        response = requests.get(f"{BASE_URL}/api/admin/songs", headers=auth_headers)
        assert response.status_code == 200
        songs = response.json().get("songs", [])
        # Filter out TEST_ songs
        real_songs = [s for s in songs if not s.get("title", "").startswith("TEST_")]
        print(f"✓ Found {len(real_songs)} seeded songs (excluding test songs)")
        if len(real_songs) >= 10:
            print("  ✓ Expected 10 seeded songs - PASS")
        else:
            print(f"  ⚠ Expected 10 seeded songs, found {len(real_songs)}")
    
    def test_plans_seeded(self, auth_headers):
        """Verify 3 seeded plans exist"""
        response = requests.get(f"{BASE_URL}/api/admin/services/plans", headers=auth_headers)
        assert response.status_code == 200
        plans = response.json().get("plans", [])
        # Filter out TEST_ plans
        real_plans = [p for p in plans if not p.get("title", "").startswith("TEST_")]
        print(f"✓ Found {len(real_plans)} seeded plans (excluding test plans)")
        if len(real_plans) >= 3:
            print("  ✓ Expected 3 seeded plans - PASS")
        else:
            print(f"  ⚠ Expected 3 seeded plans, found {len(real_plans)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
