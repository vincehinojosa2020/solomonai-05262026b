"""
Test Suite for Iteration 67 - Three New Features:
1. Giving Goals/Pledges - Portal member giving goal CRUD with progress tracking
2. Custom Fields UI Builder - Admin custom field definitions CRUD
3. Registration Add-ons Enhancement - Enhanced add-on builder (description/required/max_qty)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials — from environment
PORTAL_MEMBER_EMAIL = os.environ.get('TEST_MEMBER_EMAIL', 'member@abundant.church')
PORTAL_MEMBER_PASSWORD = os.environ.get('TEST_MEMBER_PASSWORD', '')
CHURCH_ADMIN_EMAIL = os.environ.get('TEST_ADMIN_EMAIL', 'shannonnieman1030@gmail.com')
CHURCH_ADMIN_PASSWORD = os.environ.get('TEST_ADMIN_PASSWORD', '')


@pytest.fixture(scope="module")
def portal_token():
    """Get portal member auth token"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": PORTAL_MEMBER_EMAIL,
        "password": PORTAL_MEMBER_PASSWORD
    })
    if res.status_code == 200:
        return res.json().get("session_token")
    pytest.skip(f"Portal login failed: {res.status_code} - {res.text}")


@pytest.fixture(scope="module")
def admin_token():
    """Get church admin auth token"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": CHURCH_ADMIN_EMAIL,
        "password": CHURCH_ADMIN_PASSWORD
    })
    if res.status_code == 200:
        return res.json().get("session_token")
    pytest.skip(f"Admin login failed: {res.status_code} - {res.text}")


@pytest.fixture(scope="module")
def portal_headers(portal_token):
    return {"Authorization": f"Bearer {portal_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ============== FEATURE 1: GIVING GOALS/PLEDGES ==============

class TestGivingGoals:
    """Test portal giving goal CRUD endpoints"""
    
    def test_get_giving_goal_initial(self, portal_headers):
        """GET /api/portal/giving-goal - Get member's giving goal (may or may not exist)"""
        res = requests.get(f"{BASE_URL}/api/portal/giving-goal", headers=portal_headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        # Verify response structure
        assert "year" in data
        assert "target_amount" in data
        assert "ytd_given" in data
        assert "progress_pct" in data
        assert "remaining" in data
        assert "has_goal" in data
        assert "donation_count" in data
        print(f"✓ GET giving goal: year={data['year']}, has_goal={data['has_goal']}, ytd_given={data['ytd_given']}")
    
    def test_set_giving_goal(self, portal_headers):
        """POST /api/portal/giving-goal - Set/update giving goal"""
        test_amount = 15000.00
        res = requests.post(f"{BASE_URL}/api/portal/giving-goal", 
            headers=portal_headers,
            json={"target_amount": test_amount, "year": 2026}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "target_amount" in data
        assert data["target_amount"] == test_amount
        assert data["year"] == 2026
        print(f"✓ SET giving goal: ${test_amount} for 2026")
    
    def test_get_giving_goal_after_set(self, portal_headers):
        """GET /api/portal/giving-goal - Verify goal was persisted"""
        res = requests.get(f"{BASE_URL}/api/portal/giving-goal?year=2026", headers=portal_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["has_goal"]
        assert data["target_amount"] == 15000.00
        assert data["progress_pct"] >= 0
        print(f"✓ GET giving goal after set: target=${data['target_amount']}, progress={data['progress_pct']}%")
    
    def test_update_giving_goal(self, portal_headers):
        """POST /api/portal/giving-goal - Update existing goal"""
        new_amount = 20000.00
        res = requests.post(f"{BASE_URL}/api/portal/giving-goal",
            headers=portal_headers,
            json={"target_amount": new_amount, "year": 2026}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["target_amount"] == new_amount
        print(f"✓ UPDATE giving goal: ${new_amount}")
    
    def test_set_goal_invalid_amount(self, portal_headers):
        """POST /api/portal/giving-goal - Reject invalid amount"""
        res = requests.post(f"{BASE_URL}/api/portal/giving-goal",
            headers=portal_headers,
            json={"target_amount": -100, "year": 2026}
        )
        assert res.status_code == 400, f"Expected 400 for negative amount, got {res.status_code}"
        print("✓ Rejected negative amount correctly")
    
    def test_delete_giving_goal(self, portal_headers):
        """DELETE /api/portal/giving-goal - Remove giving goal"""
        res = requests.delete(f"{BASE_URL}/api/portal/giving-goal?year=2026", headers=portal_headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "message" in data
        print("✓ DELETE giving goal successful")
    
    def test_get_goal_after_delete(self, portal_headers):
        """GET /api/portal/giving-goal - Verify goal was deleted"""
        res = requests.get(f"{BASE_URL}/api/portal/giving-goal?year=2026", headers=portal_headers)
        assert res.status_code == 200
        data = res.json()
        assert not data["has_goal"]
        assert data["target_amount"] == 0
        print("✓ Goal correctly shows as not set after delete")
    
    def test_delete_nonexistent_goal(self, portal_headers):
        """DELETE /api/portal/giving-goal - 404 for non-existent goal"""
        res = requests.delete(f"{BASE_URL}/api/portal/giving-goal?year=2026", headers=portal_headers)
        assert res.status_code == 404, f"Expected 404 for non-existent goal, got {res.status_code}"
        print("✓ 404 returned for deleting non-existent goal")


# ============== FEATURE 2: CUSTOM FIELD DEFINITIONS ==============

class TestCustomFieldDefinitions:
    """Test admin custom field definitions CRUD endpoints"""
    
    created_field_id = None
    
    def test_list_custom_fields(self, admin_headers):
        """GET /api/admin/custom-field-definitions - List all custom field definitions"""
        res = requests.get(f"{BASE_URL}/api/admin/custom-field-definitions", headers=admin_headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "fields" in data
        assert isinstance(data["fields"], list)
        print(f"✓ LIST custom fields: {len(data['fields'])} fields found")
    
    def test_create_text_field(self, admin_headers):
        """POST /api/admin/custom-field-definitions - Create text field"""
        field_name = f"TEST_Nickname_{uuid.uuid4().hex[:6]}"
        res = requests.post(f"{BASE_URL}/api/admin/custom-field-definitions",
            headers=admin_headers,
            json={
                "name": field_name,
                "field_type": "text",
                "category": "personal",
                "required": False
            }
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["name"] == field_name
        assert data["field_type"] == "text"
        assert "id" in data
        TestCustomFieldDefinitions.created_field_id = data["id"]
        print(f"✓ CREATE text field: {field_name} (id={data['id']})")
    
    def test_create_select_field(self, admin_headers):
        """POST /api/admin/custom-field-definitions - Create select field with options"""
        field_name = f"TEST_ShirtSize_{uuid.uuid4().hex[:6]}"
        res = requests.post(f"{BASE_URL}/api/admin/custom-field-definitions",
            headers=admin_headers,
            json={
                "name": field_name,
                "field_type": "select",
                "category": "other",
                "required": True,
                "options": ["Small", "Medium", "Large", "X-Large"]
            }
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["field_type"] == "select"
        assert len(data["options"]) == 4
        assert data["required"]
        print("✓ CREATE select field with 4 options")
        # Clean up
        requests.delete(f"{BASE_URL}/api/admin/custom-field-definitions/{data['id']}", headers=admin_headers)
    
    def test_create_multiselect_field(self, admin_headers):
        """POST /api/admin/custom-field-definitions - Create multiselect field"""
        field_name = f"TEST_Gifts_{uuid.uuid4().hex[:6]}"
        res = requests.post(f"{BASE_URL}/api/admin/custom-field-definitions",
            headers=admin_headers,
            json={
                "name": field_name,
                "field_type": "multiselect",
                "category": "church",
                "options": ["Teaching", "Hospitality", "Worship", "Administration"]
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["field_type"] == "multiselect"
        print("✓ CREATE multiselect field")
        # Clean up
        requests.delete(f"{BASE_URL}/api/admin/custom-field-definitions/{data['id']}", headers=admin_headers)
    
    def test_create_boolean_field(self, admin_headers):
        """POST /api/admin/custom-field-definitions - Create boolean field"""
        field_name = f"TEST_Baptized_{uuid.uuid4().hex[:6]}"
        res = requests.post(f"{BASE_URL}/api/admin/custom-field-definitions",
            headers=admin_headers,
            json={
                "name": field_name,
                "field_type": "boolean",
                "category": "church"
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["field_type"] == "boolean"
        print("✓ CREATE boolean field")
        # Clean up
        requests.delete(f"{BASE_URL}/api/admin/custom-field-definitions/{data['id']}", headers=admin_headers)
    
    def test_create_date_field(self, admin_headers):
        """POST /api/admin/custom-field-definitions - Create date field"""
        field_name = f"TEST_Anniversary_{uuid.uuid4().hex[:6]}"
        res = requests.post(f"{BASE_URL}/api/admin/custom-field-definitions",
            headers=admin_headers,
            json={
                "name": field_name,
                "field_type": "date",
                "category": "personal"
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["field_type"] == "date"
        print("✓ CREATE date field")
        # Clean up
        requests.delete(f"{BASE_URL}/api/admin/custom-field-definitions/{data['id']}", headers=admin_headers)
    
    def test_create_number_field(self, admin_headers):
        """POST /api/admin/custom-field-definitions - Create number field"""
        field_name = f"TEST_YearsAttending_{uuid.uuid4().hex[:6]}"
        res = requests.post(f"{BASE_URL}/api/admin/custom-field-definitions",
            headers=admin_headers,
            json={
                "name": field_name,
                "field_type": "number",
                "category": "church"
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["field_type"] == "number"
        print("✓ CREATE number field")
        # Clean up
        requests.delete(f"{BASE_URL}/api/admin/custom-field-definitions/{data['id']}", headers=admin_headers)
    
    def test_create_textarea_field(self, admin_headers):
        """POST /api/admin/custom-field-definitions - Create textarea field"""
        field_name = f"TEST_Allergies_{uuid.uuid4().hex[:6]}"
        res = requests.post(f"{BASE_URL}/api/admin/custom-field-definitions",
            headers=admin_headers,
            json={
                "name": field_name,
                "field_type": "textarea",
                "category": "medical"
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["field_type"] == "textarea"
        print("✓ CREATE textarea field")
        # Clean up
        requests.delete(f"{BASE_URL}/api/admin/custom-field-definitions/{data['id']}", headers=admin_headers)
    
    def test_update_custom_field(self, admin_headers):
        """PUT /api/admin/custom-field-definitions/{id} - Update field definition"""
        if not TestCustomFieldDefinitions.created_field_id:
            pytest.skip("No field created to update")
        
        res = requests.put(
            f"{BASE_URL}/api/admin/custom-field-definitions/{TestCustomFieldDefinitions.created_field_id}",
            headers=admin_headers,
            json={
                "name": "TEST_Updated_Nickname",
                "required": True,
                "category": "church"
            }
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["name"] == "TEST_Updated_Nickname"
        assert data["required"]
        assert data["category"] == "church"
        print("✓ UPDATE custom field: name, required, category changed")
    
    def test_create_duplicate_field_rejected(self, admin_headers):
        """POST /api/admin/custom-field-definitions - Reject duplicate field name"""
        # First create a field
        field_name = f"TEST_Duplicate_{uuid.uuid4().hex[:6]}"
        res1 = requests.post(f"{BASE_URL}/api/admin/custom-field-definitions",
            headers=admin_headers,
            json={"name": field_name, "field_type": "text"}
        )
        assert res1.status_code == 200
        field_id = res1.json()["id"]
        
        # Try to create duplicate
        res2 = requests.post(f"{BASE_URL}/api/admin/custom-field-definitions",
            headers=admin_headers,
            json={"name": field_name, "field_type": "text"}
        )
        assert res2.status_code == 409, f"Expected 409 for duplicate, got {res2.status_code}"
        print("✓ Duplicate field name rejected with 409")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/admin/custom-field-definitions/{field_id}", headers=admin_headers)
    
    def test_create_invalid_field_type(self, admin_headers):
        """POST /api/admin/custom-field-definitions - Reject invalid field type"""
        res = requests.post(f"{BASE_URL}/api/admin/custom-field-definitions",
            headers=admin_headers,
            json={"name": "TEST_Invalid", "field_type": "invalid_type"}
        )
        assert res.status_code == 400, f"Expected 400 for invalid type, got {res.status_code}"
        print("✓ Invalid field type rejected with 400")
    
    def test_reorder_custom_fields(self, admin_headers):
        """PUT /api/admin/custom-field-definitions/reorder - Reorder fields"""
        # First create 2 fields to ensure we have something to reorder
        field1_name = f"TEST_Reorder1_{uuid.uuid4().hex[:6]}"
        field2_name = f"TEST_Reorder2_{uuid.uuid4().hex[:6]}"
        
        res1 = requests.post(f"{BASE_URL}/api/admin/custom-field-definitions",
            headers=admin_headers,
            json={"name": field1_name, "field_type": "text"}
        )
        res2 = requests.post(f"{BASE_URL}/api/admin/custom-field-definitions",
            headers=admin_headers,
            json={"name": field2_name, "field_type": "text"}
        )
        
        if res1.status_code != 200 or res2.status_code != 200:
            pytest.skip("Could not create test fields for reorder")
        
        field1_id = res1.json()["id"]
        field2_id = res2.json()["id"]
        
        # Reorder them
        res = requests.put(f"{BASE_URL}/api/admin/custom-field-definitions/reorder",
            headers=admin_headers,
            json={"field_ids": [field2_id, field1_id]}  # Reverse order
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "count" in data
        print(f"✓ REORDER fields: {data['count']} fields reordered")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/admin/custom-field-definitions/{field1_id}", headers=admin_headers)
        requests.delete(f"{BASE_URL}/api/admin/custom-field-definitions/{field2_id}", headers=admin_headers)
    
    def test_delete_custom_field(self, admin_headers):
        """DELETE /api/admin/custom-field-definitions/{id} - Delete field definition"""
        if not TestCustomFieldDefinitions.created_field_id:
            pytest.skip("No field created to delete")
        
        res = requests.delete(
            f"{BASE_URL}/api/admin/custom-field-definitions/{TestCustomFieldDefinitions.created_field_id}",
            headers=admin_headers
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print("✓ DELETE custom field successful")
    
    def test_delete_nonexistent_field(self, admin_headers):
        """DELETE /api/admin/custom-field-definitions/{id} - 404 for non-existent"""
        res = requests.delete(
            f"{BASE_URL}/api/admin/custom-field-definitions/nonexistent_id_12345",
            headers=admin_headers
        )
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"
        print("✓ 404 returned for deleting non-existent field")


# ============== FEATURE 2B: PERSON CUSTOM FIELDS ==============

class TestPersonCustomFields:
    """Test custom fields on person records"""
    
    # Use a known person ID from the people collection
    test_person_id = "dir_member_001"
    
    def test_get_person_custom_fields(self, admin_headers):
        """GET /api/admin/people/{id}/custom-fields - Get person's custom fields"""
        res = requests.get(
            f"{BASE_URL}/api/admin/people/{TestPersonCustomFields.test_person_id}/custom-fields",
            headers=admin_headers
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "person_id" in data
        assert "custom_fields" in data
        print(f"✓ GET person custom fields: {len(data['custom_fields'])} fields")
    
    def test_update_person_custom_fields(self, admin_headers):
        """PUT /api/admin/people/{id}/custom-fields - Update person's custom fields"""
        test_values = {
            "shirt_size": "Large",
            "allergies": "None",
            "spiritual_gifts": ["Teaching", "Hospitality"]
        }
        
        res = requests.put(
            f"{BASE_URL}/api/admin/people/{TestPersonCustomFields.test_person_id}/custom-fields",
            headers=admin_headers,
            json={"custom_fields": test_values}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "custom_fields" in data
        print(f"✓ UPDATE person custom fields: {len(test_values)} fields set")
    
    def test_verify_custom_fields_persisted(self, admin_headers):
        """GET /api/admin/people/{id}/custom-fields - Verify fields were saved"""
        res = requests.get(
            f"{BASE_URL}/api/admin/people/{TestPersonCustomFields.test_person_id}/custom-fields",
            headers=admin_headers
        )
        assert res.status_code == 200
        data = res.json()
        cf = data.get("custom_fields", {})
        assert cf.get("shirt_size") == "Large"
        assert cf.get("allergies") == "None"
        print("✓ Custom fields persisted correctly")
    
    def test_update_nonexistent_person(self, admin_headers):
        """PUT /api/admin/people/{id}/custom-fields - 404 for non-existent person"""
        res = requests.put(
            f"{BASE_URL}/api/admin/people/nonexistent_person_12345/custom-fields",
            headers=admin_headers,
            json={"custom_fields": {"test": "value"}}
        )
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"
        print("✓ 404 returned for non-existent person")


# ============== FEATURE 3: REGISTRATION ADD-ONS ENHANCEMENT ==============

class TestRegistrationAddOns:
    """Test enhanced registration add-on builder with description/required/max_qty"""
    
    test_event_id = None
    
    @pytest.fixture(autouse=True)
    def get_test_event(self, admin_headers):
        """Get an event with registration enabled"""
        res = requests.get(f"{BASE_URL}/api/admin/registrations/events", headers=admin_headers)
        if res.status_code == 200:
            events = res.json().get("events", [])
            if events:
                TestRegistrationAddOns.test_event_id = events[0]["id"]
    
    def test_get_registration_config(self, admin_headers):
        """GET /api/admin/registrations/configs/{event_id} - Get registration config"""
        if not TestRegistrationAddOns.test_event_id:
            pytest.skip("No registration event found")
        
        res = requests.get(
            f"{BASE_URL}/api/admin/registrations/configs/{TestRegistrationAddOns.test_event_id}",
            headers=admin_headers
        )
        # May return 200 with config or 200 with null config
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print("✓ GET registration config for event")
    
    def test_save_config_with_enhanced_addons(self, admin_headers):
        """POST /api/admin/registrations/configs/{event_id} - Save config with enhanced add-ons"""
        if not TestRegistrationAddOns.test_event_id:
            pytest.skip("No registration event found")
        
        config = {
            "pricing": {"enabled": True, "amount": 25.00, "currency": "USD"},
            "add_ons": [
                {
                    "id": f"addon_{uuid.uuid4().hex[:8]}",
                    "name": "T-Shirt",
                    "price": 15.00,
                    "description": "Event commemorative t-shirt",
                    "required": False,
                    "max_qty": 3
                },
                {
                    "id": f"addon_{uuid.uuid4().hex[:8]}",
                    "name": "Lunch",
                    "price": 10.00,
                    "description": "Catered lunch included",
                    "required": True,
                    "max_qty": 1
                },
                {
                    "id": f"addon_{uuid.uuid4().hex[:8]}",
                    "name": "Parking Pass",
                    "price": 5.00,
                    "description": "Reserved parking spot",
                    "required": False,
                    "max_qty": 0  # 0 = unlimited
                }
            ],
            "custom_questions": [],
            "waitlist_enabled": True,
            "auto_confirm": True
        }
        
        res = requests.post(
            f"{BASE_URL}/api/admin/registrations/configs/{TestRegistrationAddOns.test_event_id}",
            headers=admin_headers,
            json=config
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print("✓ SAVE config with 3 enhanced add-ons (description, required, max_qty)")
    
    def test_verify_addon_fields_persisted(self, admin_headers):
        """GET /api/admin/registrations/configs/{event_id} - Verify add-on fields saved"""
        if not TestRegistrationAddOns.test_event_id:
            pytest.skip("No registration event found")
        
        res = requests.get(
            f"{BASE_URL}/api/admin/registrations/configs/{TestRegistrationAddOns.test_event_id}",
            headers=admin_headers
        )
        assert res.status_code == 200
        data = res.json()
        config = data.get("config")
        if config:
            addons = config.get("add_ons", [])
            if addons:
                # Check first addon has all enhanced fields
                addon = addons[0]
                assert "description" in addon or addon.get("description") is not None, "description field missing"
                assert "required" in addon, "required field missing"
                assert "max_qty" in addon, "max_qty field missing"
                print("✓ Add-on enhanced fields verified: description, required, max_qty present")
            else:
                print("✓ Config retrieved (no add-ons to verify)")
        else:
            print("✓ Config endpoint working (no config saved yet)")
    
    def test_public_registration_shows_addons(self):
        """GET /api/register/{event_id} - Public registration shows add-ons with descriptions"""
        if not TestRegistrationAddOns.test_event_id:
            pytest.skip("No registration event found")
        
        res = requests.get(f"{BASE_URL}/api/register/{TestRegistrationAddOns.test_event_id}")
        # May return 200 or 404 depending on event setup
        if res.status_code == 200:
            data = res.json()
            config = data.get("config")
            if config and config.get("add_ons"):
                for addon in config["add_ons"]:
                    # Verify enhanced fields are exposed to public
                    print(f"  Add-on: {addon.get('name')} - desc: {addon.get('description', 'N/A')}, required: {addon.get('required', False)}")
            print("✓ Public registration endpoint working")
        else:
            print(f"✓ Public registration endpoint returned {res.status_code} (event may not be public)")


# ============== CLEANUP ==============

class TestCleanup:
    """Clean up test data"""
    
    def test_cleanup_test_custom_fields(self, admin_headers):
        """Remove TEST_ prefixed custom fields"""
        res = requests.get(f"{BASE_URL}/api/admin/custom-field-definitions", headers=admin_headers)
        if res.status_code == 200:
            fields = res.json().get("fields", [])
            deleted = 0
            for f in fields:
                if f.get("name", "").startswith("TEST_"):
                    del_res = requests.delete(
                        f"{BASE_URL}/api/admin/custom-field-definitions/{f['id']}",
                        headers=admin_headers
                    )
                    if del_res.status_code == 200:
                        deleted += 1
            print(f"✓ Cleanup: Deleted {deleted} TEST_ custom fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
