"""
Phase 6 Check-In Setup Module Tests
Tests: Locations, Stations, Labels, Medical Alerts, Guardians, Reports
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "shannonnieman1030@gmail.com"
TEST_PASSWORD = "Demo2026!"


class TestPhase6CheckInSetup:
    """Phase 6 Check-In Setup API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup session and authenticate"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Authenticate
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("token") or data.get("session_token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        yield
        
        # Cleanup test data
        self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """Clean up TEST_ prefixed data"""
        # Cleanup locations
        try:
            r = self.session.get(f"{BASE_URL}/api/admin/checkin/locations")
            if r.ok:
                for loc in r.json().get("locations", []):
                    if loc.get("name", "").startswith("TEST_"):
                        self.session.delete(f"{BASE_URL}/api/admin/checkin/locations/{loc['id']}")
        except:
            pass
        
        # Cleanup stations
        try:
            r = self.session.get(f"{BASE_URL}/api/admin/checkin/stations")
            if r.ok:
                for st in r.json().get("stations", []):
                    if st.get("name", "").startswith("TEST_"):
                        self.session.delete(f"{BASE_URL}/api/admin/checkin/stations/{st['id']}")
        except:
            pass
        
        # Cleanup labels
        try:
            r = self.session.get(f"{BASE_URL}/api/admin/checkin/labels")
            if r.ok:
                for lbl in r.json().get("templates", []):
                    if lbl.get("name", "").startswith("TEST_"):
                        self.session.delete(f"{BASE_URL}/api/admin/checkin/labels/{lbl['id']}")
        except:
            pass
    
    # ============== HEALTH CHECK ==============
    def test_api_health(self):
        """Test API is accessible"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ API health check passed")
    
    # ============== LOCATIONS TESTS ==============
    def test_get_locations_returns_seeded_data(self):
        """GET /api/admin/checkin/locations returns 8 seeded locations with folders"""
        response = self.session.get(f"{BASE_URL}/api/admin/checkin/locations")
        assert response.status_code == 200
        
        data = response.json()
        assert "locations" in data
        locations = data["locations"]
        
        # Should have at least 8 seeded locations
        assert len(locations) >= 8, f"Expected at least 8 locations, got {len(locations)}"
        
        # Check expected location names
        location_names = [loc["name"] for loc in locations]
        expected_names = ["Nursery", "Toddlers", "Pre-K", "K-1st Grade", "2nd-3rd Grade", "4th-5th Grade", "Middle School", "Special Needs"]
        for name in expected_names:
            assert name in location_names, f"Missing expected location: {name}"
        
        # Check folder structure
        folders = set(loc.get("folder", "") for loc in locations)
        expected_folders = {"Early Childhood", "Preschool", "Elementary", "Youth", "Specialized"}
        for folder in expected_folders:
            assert folder in folders, f"Missing expected folder: {folder}"
        
        # Check location structure
        sample_loc = locations[0]
        assert "id" in sample_loc
        assert "name" in sample_loc
        assert "room" in sample_loc
        assert "age_range" in sample_loc
        assert "capacity" in sample_loc
        assert "folder" in sample_loc
        
        print(f"✓ GET locations returned {len(locations)} locations with proper folder structure")
    
    def test_create_location(self):
        """POST /api/admin/checkin/locations creates a new location"""
        payload = {
            "name": "TEST_New Room",
            "room": "Room 999",
            "age_range": "10-12",
            "capacity": 25,
            "folder": "Elementary"
        }
        response = self.session.post(f"{BASE_URL}/api/admin/checkin/locations", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "location" in data
        location = data["location"]
        assert location["name"] == "TEST_New Room"
        assert location["room"] == "Room 999"
        assert location["age_range"] == "10-12"
        assert location["capacity"] == 25
        assert location["folder"] == "Elementary"
        assert "id" in location
        
        # Verify persistence with GET
        get_response = self.session.get(f"{BASE_URL}/api/admin/checkin/locations")
        assert get_response.status_code == 200
        locations = get_response.json().get("locations", [])
        created_loc = next((l for l in locations if l["name"] == "TEST_New Room"), None)
        assert created_loc is not None, "Created location not found in GET response"
        
        print("✓ POST location created and verified")
    
    def test_update_location(self):
        """PUT /api/admin/checkin/locations/{id} updates a location"""
        # First create a location
        create_payload = {
            "name": "TEST_Update Room",
            "room": "Room 888",
            "age_range": "5-7",
            "capacity": 20,
            "folder": "Elementary"
        }
        create_response = self.session.post(f"{BASE_URL}/api/admin/checkin/locations", json=create_payload)
        assert create_response.status_code == 200
        location_id = create_response.json()["location"]["id"]
        
        # Update the location
        update_payload = {
            "name": "TEST_Updated Room",
            "capacity": 35,
            "folder": "Youth"
        }
        update_response = self.session.put(f"{BASE_URL}/api/admin/checkin/locations/{location_id}", json=update_payload)
        assert update_response.status_code == 200
        
        # Verify update with GET
        get_response = self.session.get(f"{BASE_URL}/api/admin/checkin/locations")
        locations = get_response.json().get("locations", [])
        updated_loc = next((l for l in locations if l["id"] == location_id), None)
        assert updated_loc is not None
        assert updated_loc["name"] == "TEST_Updated Room"
        assert updated_loc["capacity"] == 35
        assert updated_loc["folder"] == "Youth"
        
        print("✓ PUT location updated and verified")
    
    def test_delete_location(self):
        """DELETE /api/admin/checkin/locations/{id} deletes a location"""
        # First create a location
        create_payload = {"name": "TEST_Delete Room", "room": "Room 777", "age_range": "3-5", "capacity": 15, "folder": "Preschool"}
        create_response = self.session.post(f"{BASE_URL}/api/admin/checkin/locations", json=create_payload)
        assert create_response.status_code == 200
        location_id = create_response.json()["location"]["id"]
        
        # Delete the location
        delete_response = self.session.delete(f"{BASE_URL}/api/admin/checkin/locations/{location_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion with GET
        get_response = self.session.get(f"{BASE_URL}/api/admin/checkin/locations")
        locations = get_response.json().get("locations", [])
        deleted_loc = next((l for l in locations if l["id"] == location_id), None)
        assert deleted_loc is None, "Location should be deleted"
        
        print("✓ DELETE location removed and verified")
    
    # ============== STATIONS TESTS ==============
    def test_get_stations_returns_seeded_data(self):
        """GET /api/admin/checkin/stations returns 2 seeded stations"""
        response = self.session.get(f"{BASE_URL}/api/admin/checkin/stations")
        assert response.status_code == 200
        
        data = response.json()
        assert "stations" in data
        stations = data["stations"]
        
        # Should have at least 2 seeded stations
        assert len(stations) >= 2, f"Expected at least 2 stations, got {len(stations)}"
        
        # Check expected station names
        station_names = [st["name"] for st in stations]
        assert "Main Lobby Kiosk" in station_names, "Missing Main Lobby Kiosk station"
        assert "Front Desk" in station_names, "Missing Front Desk station"
        
        # Check modes
        modes = [st.get("mode") for st in stations]
        assert "self" in modes, "Missing 'self' mode station"
        assert "manned" in modes, "Missing 'manned' mode station"
        
        # Check station structure
        sample_st = stations[0]
        assert "id" in sample_st
        assert "name" in sample_st
        assert "mode" in sample_st
        assert "description" in sample_st
        
        print(f"✓ GET stations returned {len(stations)} stations with proper modes")
    
    def test_create_station_with_mode(self):
        """POST /api/admin/checkin/stations creates station with mode field"""
        for mode in ["self", "manned", "roster", "quick"]:
            payload = {
                "name": f"TEST_Station_{mode}",
                "mode": mode,
                "description": f"Test station with {mode} mode",
                "location_ids": []
            }
            response = self.session.post(f"{BASE_URL}/api/admin/checkin/stations", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert "station" in data
            station = data["station"]
            assert station["name"] == f"TEST_Station_{mode}"
            assert station["mode"] == mode
            assert "id" in station
        
        print("✓ POST station created with all 4 modes (self, manned, roster, quick)")
    
    def test_delete_station(self):
        """DELETE /api/admin/checkin/stations/{id} deletes a station"""
        # First create a station
        create_payload = {"name": "TEST_Delete Station", "mode": "quick", "description": "To be deleted"}
        create_response = self.session.post(f"{BASE_URL}/api/admin/checkin/stations", json=create_payload)
        assert create_response.status_code == 200
        station_id = create_response.json()["station"]["id"]
        
        # Delete the station
        delete_response = self.session.delete(f"{BASE_URL}/api/admin/checkin/stations/{station_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = self.session.get(f"{BASE_URL}/api/admin/checkin/stations")
        stations = get_response.json().get("stations", [])
        deleted_st = next((s for s in stations if s["id"] == station_id), None)
        assert deleted_st is None, "Station should be deleted"
        
        print("✓ DELETE station removed and verified")
    
    # ============== LABELS TESTS ==============
    def test_get_labels_returns_seeded_templates(self):
        """GET /api/admin/checkin/labels returns 3 seeded label templates"""
        response = self.session.get(f"{BASE_URL}/api/admin/checkin/labels")
        assert response.status_code == 200
        
        data = response.json()
        assert "templates" in data
        templates = data["templates"]
        
        # Should have at least 3 seeded templates
        assert len(templates) >= 3, f"Expected at least 3 templates, got {len(templates)}"
        
        # Check expected template names
        template_names = [t["name"] for t in templates]
        assert "Standard Name Tag" in template_names, "Missing Standard Name Tag template"
        assert "Security Label (Parent)" in template_names, "Missing Security Label template"
        assert "Allergy Alert Tag" in template_names, "Missing Allergy Alert Tag template"
        
        # Check template structure
        sample_tpl = templates[0]
        assert "id" in sample_tpl
        assert "name" in sample_tpl
        assert "type" in sample_tpl
        assert "width" in sample_tpl
        assert "height" in sample_tpl
        assert "fields" in sample_tpl
        assert "layout" in sample_tpl
        
        print(f"✓ GET labels returned {len(templates)} templates with proper structure")
    
    def test_create_label_template(self):
        """POST /api/admin/checkin/labels creates a label template"""
        payload = {
            "name": "TEST_Custom Label",
            "type": "name_tag",
            "width": 3,
            "height": 1.5,
            "fields": ["child_name", "classroom", "security_code", "barcode"],
            "layout": {"font_size": 14, "show_allergies": False, "show_barcode": True, "show_logo": True},
            "is_default": False
        }
        response = self.session.post(f"{BASE_URL}/api/admin/checkin/labels", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "template" in data
        template = data["template"]
        assert template["name"] == "TEST_Custom Label"
        assert template["type"] == "name_tag"
        assert template["width"] == 3
        assert template["height"] == 1.5
        assert "child_name" in template["fields"]
        assert "id" in template
        
        # Verify persistence
        get_response = self.session.get(f"{BASE_URL}/api/admin/checkin/labels")
        templates = get_response.json().get("templates", [])
        created_tpl = next((t for t in templates if t["name"] == "TEST_Custom Label"), None)
        assert created_tpl is not None, "Created template not found in GET response"
        
        print("✓ POST label template created and verified")
    
    def test_delete_label_template(self):
        """DELETE /api/admin/checkin/labels/{id} deletes a template"""
        # First create a template
        create_payload = {"name": "TEST_Delete Label", "type": "security", "width": 4, "height": 1, "fields": ["child_name"]}
        create_response = self.session.post(f"{BASE_URL}/api/admin/checkin/labels", json=create_payload)
        assert create_response.status_code == 200
        label_id = create_response.json()["template"]["id"]
        
        # Delete the template
        delete_response = self.session.delete(f"{BASE_URL}/api/admin/checkin/labels/{label_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = self.session.get(f"{BASE_URL}/api/admin/checkin/labels")
        templates = get_response.json().get("templates", [])
        deleted_tpl = next((t for t in templates if t["id"] == label_id), None)
        assert deleted_tpl is None, "Template should be deleted"
        
        print("✓ DELETE label template removed and verified")
    
    # ============== MEDICAL ALERTS TESTS ==============
    def test_get_medical_alerts(self):
        """GET /api/admin/checkin/medical-alerts returns children with allergies"""
        response = self.session.get(f"{BASE_URL}/api/admin/checkin/medical-alerts")
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data
        assert "total" in data
        
        alerts = data["alerts"]
        # May be empty if no children with allergies exist
        if len(alerts) > 0:
            sample_alert = alerts[0]
            assert "id" in sample_alert
            assert "name" in sample_alert
            # Should have allergies or medical_notes
            has_medical_info = sample_alert.get("allergies") or sample_alert.get("medical_notes")
            assert has_medical_info, "Alert should have allergies or medical_notes"
        
        print(f"✓ GET medical-alerts returned {len(alerts)} children with medical info")
        return alerts  # Return for use in other tests
    
    def test_update_child_medical_info(self):
        """PUT /api/admin/checkin/children/{childId}/medical updates medical info"""
        # First get a child from medical alerts
        alerts_response = self.session.get(f"{BASE_URL}/api/admin/checkin/medical-alerts")
        alerts = alerts_response.json().get("alerts", [])
        
        if len(alerts) == 0:
            pytest.skip("No children with medical alerts to test update")
        
        child_id = alerts[0]["id"]
        
        # Update medical info
        payload = {
            "allergies": "TEST_Peanuts, Shellfish",
            "medical_notes": "TEST_Carries EpiPen",
            "medical_severity": "high"
        }
        response = self.session.put(f"{BASE_URL}/api/admin/checkin/children/{child_id}/medical", json=payload)
        assert response.status_code == 200
        
        # Verify update
        verify_response = self.session.get(f"{BASE_URL}/api/admin/checkin/medical-alerts")
        updated_alerts = verify_response.json().get("alerts", [])
        updated_child = next((a for a in updated_alerts if a["id"] == child_id), None)
        assert updated_child is not None
        assert "TEST_Peanuts" in updated_child.get("allergies", "")
        assert updated_child.get("medical_severity") == "high"
        
        print("✓ PUT child medical info updated and verified")
    
    # ============== GUARDIANS TESTS ==============
    def test_get_child_guardians(self):
        """GET /api/admin/checkin/children/{childId}/guardians returns guardian list"""
        # First get a child from medical alerts
        alerts_response = self.session.get(f"{BASE_URL}/api/admin/checkin/medical-alerts")
        alerts = alerts_response.json().get("alerts", [])
        
        if len(alerts) == 0:
            pytest.skip("No children to test guardians")
        
        child_id = alerts[0]["id"]
        child_name = alerts[0].get("name", "Unknown")
        
        response = self.session.get(f"{BASE_URL}/api/admin/checkin/children/{child_id}/guardians")
        assert response.status_code == 200
        
        data = response.json()
        assert "guardians" in data
        assert "child_name" in data
        
        print(f"✓ GET guardians for child '{child_name}' returned {len(data['guardians'])} guardians")
        return child_id  # Return for use in other tests
    
    def test_add_guardian(self):
        """POST /api/admin/checkin/children/{childId}/guardians adds a guardian"""
        # First get a child
        alerts_response = self.session.get(f"{BASE_URL}/api/admin/checkin/medical-alerts")
        alerts = alerts_response.json().get("alerts", [])
        
        if len(alerts) == 0:
            pytest.skip("No children to test adding guardian")
        
        child_id = alerts[0]["id"]
        
        # Add guardian
        payload = {
            "name": "TEST_Guardian John",
            "relationship": "Uncle",
            "phone": "555-1234",
            "pin_code": "9999"
        }
        response = self.session.post(f"{BASE_URL}/api/admin/checkin/children/{child_id}/guardians", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "guardian" in data
        guardian = data["guardian"]
        assert guardian["name"] == "TEST_Guardian John"
        assert guardian["relationship"] == "Uncle"
        assert guardian["phone"] == "555-1234"
        assert guardian["pin_code"] == "9999"
        assert "id" in guardian
        
        # Verify persistence
        verify_response = self.session.get(f"{BASE_URL}/api/admin/checkin/children/{child_id}/guardians")
        guardians = verify_response.json().get("guardians", [])
        added_guardian = next((g for g in guardians if g["name"] == "TEST_Guardian John"), None)
        assert added_guardian is not None, "Added guardian not found"
        
        # Store guardian_id for cleanup
        self._test_guardian_id = guardian["id"]
        self._test_child_id = child_id
        
        print("✓ POST guardian added and verified")
    
    def test_remove_guardian(self):
        """DELETE /api/admin/checkin/children/{childId}/guardians/{guardianId} removes guardian"""
        # First get a child and add a guardian
        alerts_response = self.session.get(f"{BASE_URL}/api/admin/checkin/medical-alerts")
        alerts = alerts_response.json().get("alerts", [])
        
        if len(alerts) == 0:
            pytest.skip("No children to test removing guardian")
        
        child_id = alerts[0]["id"]
        
        # Add a guardian to remove
        add_payload = {"name": "TEST_Remove Guardian", "relationship": "Aunt", "phone": "555-9999", "pin_code": "1111"}
        add_response = self.session.post(f"{BASE_URL}/api/admin/checkin/children/{child_id}/guardians", json=add_payload)
        assert add_response.status_code == 200
        guardian_id = add_response.json()["guardian"]["id"]
        
        # Remove the guardian
        delete_response = self.session.delete(f"{BASE_URL}/api/admin/checkin/children/{child_id}/guardians/{guardian_id}")
        assert delete_response.status_code == 200
        
        # Verify removal
        verify_response = self.session.get(f"{BASE_URL}/api/admin/checkin/children/{child_id}/guardians")
        guardians = verify_response.json().get("guardians", [])
        removed_guardian = next((g for g in guardians if g["id"] == guardian_id), None)
        assert removed_guardian is None, "Guardian should be removed"
        
        print("✓ DELETE guardian removed and verified")
    
    # ============== REPORTS TESTS ==============
    def test_get_checkin_trends(self):
        """GET /api/admin/checkin/reports/trends returns daily trend and room breakdown"""
        response = self.session.get(f"{BASE_URL}/api/admin/checkin/reports/trends")
        assert response.status_code == 200
        
        data = response.json()
        assert "daily_trend" in data
        assert "by_room" in data
        assert "total_checkins" in data
        assert "period_days" in data
        
        # daily_trend should be a list
        assert isinstance(data["daily_trend"], list)
        
        # by_room should be a list
        assert isinstance(data["by_room"], list)
        
        # If there are trends, check structure
        if len(data["daily_trend"]) > 0:
            trend_item = data["daily_trend"][0]
            assert "date" in trend_item
            assert "count" in trend_item
        
        if len(data["by_room"]) > 0:
            room_item = data["by_room"][0]
            assert "room" in room_item
            assert "count" in room_item
        
        print(f"✓ GET trends returned {data['total_checkins']} total check-ins over {data['period_days']} days")
    
    def test_get_first_time_visitors(self):
        """GET /api/admin/checkin/reports/first-timers returns first-time visitors"""
        response = self.session.get(f"{BASE_URL}/api/admin/checkin/reports/first-timers")
        assert response.status_code == 200
        
        data = response.json()
        assert "first_timers" in data
        assert "total" in data
        
        first_timers = data["first_timers"]
        assert isinstance(first_timers, list)
        
        # If there are first-timers, check structure
        if len(first_timers) > 0:
            ft = first_timers[0]
            assert "child_id" in ft
            assert "child_name" in ft
            assert "first_checkin" in ft
            assert "total_checkins" in ft
        
        print(f"✓ GET first-timers returned {data['total']} first-time visitors")
    
    # ============== CLEANUP ==============
    def test_cleanup_test_guardians(self):
        """Cleanup TEST_ prefixed guardians"""
        # Get all children with medical alerts
        alerts_response = self.session.get(f"{BASE_URL}/api/admin/checkin/medical-alerts")
        alerts = alerts_response.json().get("alerts", [])
        
        for child in alerts:
            child_id = child["id"]
            guardians_response = self.session.get(f"{BASE_URL}/api/admin/checkin/children/{child_id}/guardians")
            guardians = guardians_response.json().get("guardians", [])
            
            for guardian in guardians:
                if guardian.get("name", "").startswith("TEST_"):
                    self.session.delete(f"{BASE_URL}/api/admin/checkin/children/{child_id}/guardians/{guardian['id']}")
        
        print("✓ Cleanup completed for TEST_ prefixed data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
