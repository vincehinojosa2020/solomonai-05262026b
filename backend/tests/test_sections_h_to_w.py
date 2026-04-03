"""
Solomon AI — Backend Tests for Sections H through W (UAT Final)
Tests: G.2, H, J (backend), N (backend), O (backend), Q, R, T, W
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test tokens for sessions created in mongosh
PLATFORM_TOKEN = "test_platform_session_h2w"
CHURCH_TOKEN = "test_church_session_h2w"


def platform_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PLATFORM_TOKEN}"
    }


def church_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHURCH_TOKEN}"
    }


# ============== R: Health Endpoint ==============

class TestHealthEndpoint:
    """R: GET /api/health returns status:ok"""

    def test_health_returns_ok(self):
        """R: GET /api/health should return {status: 'ok'}"""
        res = requests.get(f"{BASE_URL}/api/health")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("status") == "ok", f"Expected status='ok', got: {data}"
        print(f"PASS: /api/health returned status=ok, database={data.get('database')}")

    def test_health_has_required_fields(self):
        """R: Health endpoint should include status and timestamp/version"""
        res = requests.get(f"{BASE_URL}/api/health")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data, "Missing 'status' field in health response"
        # Version or timestamp is a valid additional field
        has_extra = "database" in data or "timestamp" in data or "version" in data
        assert has_extra, f"Expected at least one of database/timestamp/version: {data}"
        print(f"PASS: Health has fields: {list(data.keys())}")


# ============== G.2: Platform Churches with Health Scores ==============

class TestPlatformChurches:
    """G.2: /api/platform/churches returns churches with health.grade and health.score"""

    def test_platform_churches_returns_array(self):
        """G.2: GET /platform/churches should return churches array"""
        res = requests.get(f"{BASE_URL}/api/platform/churches", headers=platform_headers())
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "churches" in data, f"Missing 'churches' key in response: {data.keys()}"
        assert isinstance(data["churches"], list), "churches should be a list"
        assert len(data["churches"]) > 0, "Expected at least 1 church"
        print(f"PASS: /platform/churches returned {len(data['churches'])} churches")

    def test_platform_churches_have_health_score(self):
        """G.2: Each church should have health.grade and health.score"""
        res = requests.get(f"{BASE_URL}/api/platform/churches", headers=platform_headers())
        assert res.status_code == 200
        data = res.json()
        churches = data["churches"]
        for church in churches:
            assert "health" in church, f"Church {church.get('name')} missing 'health' field"
            health = church["health"]
            assert "grade" in health, f"Church {church.get('name')} health missing 'grade'"
            assert "score" in health, f"Church {church.get('name')} health missing 'score'"
            # Grade should be one of the valid grades
            assert health["grade"] in ["A+", "A", "B+", "B", "C", "D", "F", "N/A"], \
                f"Invalid grade: {health['grade']}"
            # Score should be 0-100
            assert 0 <= health["score"] <= 100, f"Score out of range: {health['score']}"
        print(f"PASS: All {len(churches)} churches have valid health.grade and health.score")

    def test_platform_churches_requires_auth(self):
        """G.2: /platform/churches should require authentication"""
        res = requests.get(f"{BASE_URL}/api/platform/churches")
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print("PASS: /platform/churches requires auth")

    def test_platform_churches_total_field(self):
        """G.2: /platform/churches should return total count"""
        res = requests.get(f"{BASE_URL}/api/platform/churches", headers=platform_headers())
        assert res.status_code == 200
        data = res.json()
        assert "total" in data, "Missing 'total' field"
        assert data["total"] > 0, "Expected total > 0"
        assert data["total"] == len(data["churches"]), "total should match churches array length"
        print(f"PASS: /platform/churches total={data['total']}")


# ============== T: Add New Church (Create Endpoint) ==============

class TestAddNewChurch:
    """T: POST /api/platform/churches/create creates a new church"""

    def test_create_church_returns_success(self):
        """T: POST /platform/churches/create should work for platform admin"""
        import time
        ts = int(time.time())
        payload = {
            "name": f"TEST_Church_{ts}",
            "subdomain": f"testchurch{ts}",
            "admin_email": f"admin.test{ts}@example.com",
            "admin_name": "Test Admin",
            "admin_password": "TestPass2026!",
            "admin_phone": "(555) 123-4567",
            "city": "Austin",
            "state": "TX",
            "denomination": "Baptist",
            "website": "https://testchurch.example.com",
            "primary_color": "#2563eb",
            "plan": "growth",
            "estimated_members": 150,
            "service_times": ["Sunday 10am"]  # Must be a list
        }
        res = requests.post(
            f"{BASE_URL}/api/platform/churches/create",
            json=payload,
            headers=platform_headers()
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "tenant_id" in data or "id" in data or "church" in data or "name" in data, \
            f"Expected church data in response: {data}"
        print(f"PASS: Created new church - response: {list(data.keys())}")

    def test_create_church_requires_platform_admin(self):
        """T: /platform/churches/create should reject non-platform-admin"""
        import time
        ts = int(time.time())
        payload = {
            "name": "Bad Church",
            "admin_email": f"bad.admin{ts}@example.com"
        }
        res = requests.post(
            f"{BASE_URL}/api/platform/churches/create",
            json=payload,
            headers=church_headers()
        )
        assert res.status_code in [403, 400], \
            f"Expected 403 for non-platform-admin, got {res.status_code}: {res.text}"
        print(f"PASS: /platform/churches/create rejects non-platform-admin ({res.status_code})")

    def test_create_church_duplicate_subdomain_rejected(self):
        """T: Duplicate subdomain should return 409"""
        payload = {
            "name": "Duplicate Test Church",
            "subdomain": "abundant",  # Already exists
            "admin_email": "unique.newadmin@testchurch.com",
            "admin_name": "Test Admin"
        }
        res = requests.post(
            f"{BASE_URL}/api/platform/churches/create",
            json=payload,
            headers=platform_headers()
        )
        assert res.status_code in [409, 400], \
            f"Expected 409 for duplicate subdomain, got {res.status_code}: {res.text}"
        print(f"PASS: Duplicate subdomain returns {res.status_code}")


# ============== H: Reports Tabs ==============

class TestReportsTabs:
    """H: Reports page tabs - backend endpoints"""

    def test_giving_by_fund_report(self):
        """H: GET /api/reports/giving-by-fund returns valid data"""
        params = "start_date=2024-01-01&end_date=2025-12-31"
        res = requests.get(
            f"{BASE_URL}/api/reports/giving-by-fund?{params}",
            headers=church_headers()
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        # Response could be a list or a dict
        if isinstance(data, list):
            print(f"PASS: /api/reports/giving-by-fund returned list of {len(data)} items")
        elif isinstance(data, dict):
            assert "by_fund" in data or "summary" in data or "funds" in data, \
                f"Expected by_fund/summary/funds in response: {list(data.keys())}"
            print(f"PASS: /api/reports/giving-by-fund returned: {list(data.keys())}")
        else:
            assert False, f"Unexpected response type: {type(data)}"

    def test_attendance_report(self):
        """H: GET /api/reports/attendance returns data"""
        params = "start_date=2024-01-01&end_date=2025-12-31"
        res = requests.get(
            f"{BASE_URL}/api/reports/attendance?{params}",
            headers=church_headers()
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "summary" in data or "weekly" in data or "weekly_trend" in data, \
            f"Expected summary/weekly in response: {list(data.keys())}"
        print(f"PASS: /api/reports/attendance returned: {list(data.keys())}")

    def test_groups_report(self):
        """H: GET /api/reports/groups returns data"""
        res = requests.get(
            f"{BASE_URL}/api/reports/groups",
            headers=church_headers()
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "summary" in data or "by_type" in data or "total_groups" in data, \
            f"Expected groups data in response: {list(data.keys())}"
        print(f"PASS: /api/reports/groups returned: {list(data.keys())}")

    def test_membership_report(self):
        """H: GET /api/reports/membership returns data"""
        res = requests.get(
            f"{BASE_URL}/api/reports/membership",
            headers=church_headers()
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "total_members" in data or "summary" in data or "by_status" in data, \
            f"Expected membership data: {list(data.keys())}"
        print(f"PASS: /api/reports/membership returned: {list(data.keys())}")

    def test_executive_summary_report(self):
        """H: GET /api/reports/executive-summary (Cross-Analysis tab)"""
        res = requests.get(
            f"{BASE_URL}/api/reports/executive-summary",
            headers=church_headers()
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        print(f"PASS: /api/reports/executive-summary returned: {list(data.keys())}")

    def test_audit_log_endpoint(self):
        """H: GET /api/admin/audit-log (Audit Log tab) returns data"""
        res = requests.get(
            f"{BASE_URL}/api/admin/audit-log?limit=50&page=1",
            headers=church_headers()
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "entries" in data or "logs" in data or "items" in data or isinstance(data, list), \
            f"Expected entries/logs in response: {list(data.keys()) if isinstance(data, dict) else type(data)}"
        print(f"PASS: /api/admin/audit-log returned: {type(data)}")

    def test_audit_log_category_filter(self):
        """H: Audit Log with category filter"""
        res = requests.get(
            f"{BASE_URL}/api/admin/audit-log?limit=50&page=1&category=giving",
            headers=church_headers()
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print(f"PASS: /api/admin/audit-log?category=giving returned 200")

    def test_kids_history_report(self):
        """H: GET /api/reports/kids-history (Check-In tab)"""
        params = "start_date=2024-01-01&end_date=2025-12-31"
        res = requests.get(
            f"{BASE_URL}/api/reports/kids-history?{params}",
            headers=church_headers()
        )
        assert res.status_code in [200, 404], \
            f"Expected 200 or 404, got {res.status_code}: {res.text}"
        if res.status_code == 200:
            print(f"PASS: /api/reports/kids-history returned 200")
        else:
            print(f"INFO: /api/reports/kids-history returned 404 (no data)")

    def test_cafe_report(self):
        """H: GET /api/reports/cafe (Cafe & Merch tab)"""
        params = "start_date=2024-01-01&end_date=2025-12-31"
        res = requests.get(
            f"{BASE_URL}/api/reports/cafe?{params}",
            headers=church_headers()
        )
        assert res.status_code in [200, 404], \
            f"Expected 200 or 404, got {res.status_code}: {res.text}"
        print(f"INFO: /api/reports/cafe returned {res.status_code}")


# ============== Q: Bulk Update People ==============

class TestBulkUpdatePeople:
    """Q: POST /api/admin/people/bulk-update"""

    def test_bulk_update_people_success(self):
        """Q: POST /admin/people/bulk-update with valid ids and updates"""
        # First get some people IDs
        res = requests.get(
            f"{BASE_URL}/api/people?per_page=3",
            headers=church_headers()
        )
        assert res.status_code == 200, f"Can't fetch people: {res.status_code}"
        people_data = res.json()
        people = people_data.get("data", [])
        if not people:
            pytest.skip("No people data to test bulk update")

        ids = [p["id"] for p in people[:2]]
        update_payload = {
            "ids": ids,
            "updates": {"membership_status": "member"}
        }
        res = requests.post(
            f"{BASE_URL}/api/admin/people/bulk-update",
            json=update_payload,
            headers=church_headers()
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "updated" in data or "message" in data, \
            f"Expected updated/message in response: {data}"
        print(f"PASS: /api/admin/people/bulk-update updated {data.get('updated', '?')} people")

    def test_bulk_update_no_ids_returns_400(self):
        """Q: Bulk update with empty ids should return 400"""
        res = requests.post(
            f"{BASE_URL}/api/admin/people/bulk-update",
            json={"ids": [], "updates": {"membership_status": "member"}},
            headers=church_headers()
        )
        assert res.status_code == 400, f"Expected 400 for empty ids, got {res.status_code}"
        print(f"PASS: bulk-update rejects empty ids with 400")

    def test_bulk_update_no_valid_fields_returns_400(self):
        """Q: Bulk update with invalid fields should return 400"""
        res = requests.get(f"{BASE_URL}/api/people?per_page=1", headers=church_headers())
        people = res.json().get("data", [])
        if not people:
            pytest.skip("No people for this test")
        res = requests.post(
            f"{BASE_URL}/api/admin/people/bulk-update",
            json={"ids": [people[0]["id"]], "updates": {"invalid_field": "value"}},
            headers=church_headers()
        )
        assert res.status_code == 400, f"Expected 400 for invalid fields, got {res.status_code}"
        print(f"PASS: bulk-update rejects invalid fields with 400")

    def test_bulk_update_requires_auth(self):
        """Q: /admin/people/bulk-update should require auth"""
        res = requests.post(
            f"{BASE_URL}/api/admin/people/bulk-update",
            json={"ids": ["some-id"], "updates": {"membership_status": "member"}}
        )
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print(f"PASS: bulk-update requires auth ({res.status_code})")


# ============== Platform Health Scores Endpoint ==============

class TestPlatformHealthScores:
    """G.2: /platform/health-scores endpoint"""

    def test_health_scores_endpoint(self):
        """G.2: GET /platform/health-scores returns churches with health data"""
        res = requests.get(
            f"{BASE_URL}/api/platform/health-scores",
            headers=platform_headers()
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "churches" in data, f"Missing 'churches' key: {data.keys()}"
        churches = data["churches"]
        assert len(churches) > 0, "Expected at least 1 church with health data"
        for c in churches:
            assert "health" in c, f"Church {c.get('name')} missing health"
            assert "grade" in c["health"], f"Church {c.get('name')} health missing grade"
            assert "score" in c["health"], f"Church {c.get('name')} health missing score"
        print(f"PASS: /api/platform/health-scores returned {len(churches)} churches with health")


# ============== Services Plans Check (N) ==============

class TestServicesPlans:
    """N: Services plans API"""

    def test_services_plans_endpoint(self):
        """N: GET /admin/services/plans returns plans"""
        res = requests.get(
            f"{BASE_URL}/api/admin/services/plans",
            headers=church_headers()
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "plans" in data, f"Expected 'plans' in response: {data.keys()}"
        print(f"PASS: /api/admin/services/plans returned {len(data.get('plans', []))} plans")


# ============== MultiPaymentSelector data-testid (code check) ==============

class TestMultiPaymentSelectorCode:
    """O: MultiPaymentSelector has pay-guest-card data-testid"""

    def test_multi_payment_selector_has_enter_card(self):
        """O: Verify MultiPaymentSelector.jsx has data-testid=pay-guest-card"""
        import subprocess
        result = subprocess.run(
            ["grep", "-r", "pay-guest-card", "/app/frontend/src/"],
            capture_output=True, text=True
        )
        assert "pay-guest-card" in result.stdout, \
            "data-testid='pay-guest-card' not found in MultiPaymentSelector"
        print(f"PASS: pay-guest-card found in: {result.stdout.strip()[:100]}")
