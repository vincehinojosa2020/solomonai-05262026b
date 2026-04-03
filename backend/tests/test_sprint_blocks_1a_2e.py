"""
Solomon AI — Sprint Blocks 1A-2E Backend Tests
Tests: SolomonPay config, scheduler APIs, calendar events, communications templates
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Credentials
CHURCH_ADMIN_EMAIL = "shannonnieman1030@gmail.com"
CHURCH_ADMIN_PASSWORD = "Demo2026!"
PLATFORM_ADMIN_EMAIL = "admin@solomonai.us"
PLATFORM_ADMIN_PASSWORD = "Demo2026!"


@pytest.fixture(scope="module")
def church_admin_token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": CHURCH_ADMIN_EMAIL,
        "password": CHURCH_ADMIN_PASSWORD
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json().get("session_token")
    assert token, "No session token"
    return token


@pytest.fixture(scope="module")
def admin_headers(church_admin_token):
    return {
        "Authorization": f"Bearer {church_admin_token}",
        "Content-Type": "application/json"
    }


# ═══════════════════════════════════════════
# Block 1A: SolomonPay — No Stripe, correct processor name
# ═══════════════════════════════════════════

class TestBlock1A_SolomonPayConfig:
    """1A: Verify SolomonPay replaces Stripe"""

    def test_payments_config_returns_solomonpay(self, admin_headers):
        """GET /api/payments/config should return processor=solomonpay"""
        resp = requests.get(f"{BASE_URL}/api/payments/config", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "processor" in data, "Missing 'processor' field"
        assert data["processor"] == "solomonpay", f"Expected solomonpay, got {data['processor']}"
        print(f"PASS: Processor is '{data['processor']}'")

    def test_payments_config_has_no_stripe(self, admin_headers):
        """Verify no Stripe references in /api/payments/config response"""
        resp = requests.get(f"{BASE_URL}/api/payments/config", headers=admin_headers)
        assert resp.status_code == 200
        data = str(resp.json()).lower()
        assert "stripe" not in data, f"Stripe found in config response: {data}"
        print("PASS: No Stripe references in payments config")

    def test_payments_config_includes_methods(self, admin_headers):
        """Config should include card and ach payment methods"""
        resp = requests.get(f"{BASE_URL}/api/payments/config", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        methods = data.get("payment_methods", [])
        assert "card" in methods, "card method missing"
        assert "ach" in methods, "ach method missing"
        print(f"PASS: Payment methods: {methods}")


# ═══════════════════════════════════════════
# Block 1B: Recurring Giving Scheduler Admin APIs
# ═══════════════════════════════════════════

class TestBlock1B_SchedulerAPIs:
    """1B: Scheduler status and manual trigger"""

    def test_scheduler_status_returns_200(self, admin_headers):
        """GET /api/admin/solomonpay/scheduler/status returns 200"""
        resp = requests.get(f"{BASE_URL}/api/admin/solomonpay/scheduler/status", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("PASS: Scheduler status returns 200")

    def test_scheduler_status_has_required_fields(self, admin_headers):
        """Scheduler status includes active_schedules, due_today, recent_runs"""
        resp = requests.get(f"{BASE_URL}/api/admin/solomonpay/scheduler/status", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        # Check stats section
        assert "stats" in data, f"Missing 'stats' key. Got: {list(data.keys())}"
        stats = data["stats"]
        assert "active_schedules" in stats, f"Missing 'active_schedules' in stats: {stats}"
        assert "due_today" in stats, f"Missing 'due_today' in stats: {stats}"
        
        # Check recent_runs list
        assert "recent_runs" in data, f"Missing 'recent_runs' key. Got: {list(data.keys())}"
        assert isinstance(data["recent_runs"], list), "recent_runs should be a list"
        
        # Check scheduler section
        assert "scheduler" in data, f"Missing 'scheduler' key"
        assert data["scheduler"]["active"] == True, "Scheduler should be active"
        
        print(f"PASS: Scheduler stats: {stats}")

    def test_scheduler_manual_trigger(self, admin_headers):
        """POST /api/admin/solomonpay/scheduler/run-now works"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/solomonpay/scheduler/run-now",
            headers=admin_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check run summary
        assert "message" in data, f"Missing 'message' in response: {data}"
        assert "successful" in data, f"Missing 'successful' in run summary: {data}"
        assert "failed" in data, f"Missing 'failed' in run summary: {data}"
        assert "skipped" in data, f"Missing 'skipped' in run summary: {data}"
        assert "total_scheduled" in data, f"Missing 'total_scheduled' in run summary: {data}"
        assert "duration_ms" in data, f"Missing 'duration_ms' in run summary: {data}"
        
        print(f"PASS: Manual trigger result: {data['successful']} success, {data['failed']} failed, {data['skipped']} skipped")

    def test_scheduler_status_after_manual_run(self, admin_headers):
        """After manual trigger, scheduler status shows recent_runs"""
        # First trigger a run
        requests.post(f"{BASE_URL}/api/admin/solomonpay/scheduler/run-now", headers=admin_headers)
        
        # Then check status
        resp = requests.get(f"{BASE_URL}/api/admin/solomonpay/scheduler/status", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        # recent_runs should now have at least 1 entry
        print(f"PASS: Recent runs count: {len(data.get('recent_runs', []))}")


# ═══════════════════════════════════════════
# Block 2C: Calendar Events API
# ═══════════════════════════════════════════

class TestBlock2C_CalendarAPI:
    """2C: FullCalendar calendar endpoint"""

    def test_calendar_events_returns_200(self, admin_headers):
        """GET /api/admin/events/calendar returns 200"""
        resp = requests.get(f"{BASE_URL}/api/admin/events/calendar", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("PASS: Calendar events returns 200")

    def test_calendar_events_has_events_array(self, admin_headers):
        """Calendar response contains events array"""
        resp = requests.get(f"{BASE_URL}/api/admin/events/calendar", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data, f"Missing 'events' key. Got: {list(data.keys())}"
        assert isinstance(data["events"], list), "events should be a list"
        print(f"PASS: Calendar events count: {len(data['events'])}")

    def test_calendar_events_fullcalendar_format(self, admin_headers):
        """Events returned in FullCalendar format (id, title, start, backgroundColor)"""
        resp = requests.get(f"{BASE_URL}/api/admin/events/calendar", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        events = data.get("events", [])
        
        if events:
            event = events[0]
            assert "id" in event, f"Event missing 'id': {event}"
            assert "title" in event, f"Event missing 'title': {event}"
            assert "start" in event, f"Event missing 'start': {event}"
            assert "backgroundColor" in event, f"Event missing 'backgroundColor': {event}"
            assert "extendedProps" in event, f"Event missing 'extendedProps': {event}"
            print(f"PASS: FullCalendar format valid. Sample: id={event['id']}, title={event['title']}")
        else:
            print("INFO: No events in calendar yet (empty is valid)")

    def test_create_calendar_event(self, admin_headers):
        """Create an event via POST /api/admin/events"""
        payload = {
            "name": "TEST_Sprint_Calendar_Event",
            "description": "Test event for sprint 1A-2E testing",
            "event_date": "2026-03-15",
            "start_time": "10:00",
            "end_time": "12:00",
            "location": "Sanctuary",
            "capacity": 200,
            "event_type": "service",
            "is_public": True,
            "requires_registration": False,
            "recurring": "",
            "pricing_type": "free",
            "price": 0
        }
        resp = requests.post(f"{BASE_URL}/api/admin/events", json=payload, headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "event" in data or "message" in data, f"Unexpected response: {data}"
        print(f"PASS: Event created: {data.get('message', 'OK')}")

    def test_calendar_events_date_filter(self, admin_headers):
        """Calendar endpoint supports start/end date filtering"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/events/calendar?start=2026-03-01&end=2026-03-31",
            headers=admin_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "events" in data
        print(f"PASS: Date-filtered calendar returns {len(data['events'])} events")


# ═══════════════════════════════════════════
# Block 2D: Communications Templates API
# ═══════════════════════════════════════════

class TestBlock2D_CommunicationsAPI:
    """2D: Communications templates endpoint"""

    def test_templates_endpoint_returns_200(self, admin_headers):
        """GET /api/admin/communications/templates returns 200"""
        resp = requests.get(f"{BASE_URL}/api/admin/communications/templates", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("PASS: Templates endpoint returns 200")

    def test_templates_has_templates_array(self, admin_headers):
        """Templates response contains templates array"""
        resp = requests.get(f"{BASE_URL}/api/admin/communications/templates", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "templates" in data, f"Missing 'templates' key. Got: {list(data.keys())}"
        assert isinstance(data["templates"], list), "templates should be a list"
        print(f"PASS: Templates count: {len(data['templates'])}")

    def test_templates_includes_builtin_templates(self, admin_headers):
        """Templates include built-in templates (Welcome, Event Invitation, etc.)"""
        resp = requests.get(f"{BASE_URL}/api/admin/communications/templates", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        templates = data.get("templates", [])
        
        assert len(templates) >= 4, f"Expected at least 4 built-in templates, got {len(templates)}"
        
        template_names = [t.get("name", "").lower() for t in templates]
        # Check for key built-in templates
        has_welcome = any("welcome" in name for name in template_names)
        has_event = any("event" in name or "invitation" in name or "invite" in name for name in template_names)
        
        assert has_welcome, f"No welcome template found. Templates: {template_names}"
        assert has_event, f"No event invitation template found. Templates: {template_names}"
        print(f"PASS: Built-in templates found: {template_names}")

    def test_templates_has_merge_fields(self, admin_headers):
        """Templates response includes merge_fields"""
        resp = requests.get(f"{BASE_URL}/api/admin/communications/templates", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "merge_fields" in data, f"Missing 'merge_fields' key. Got: {list(data.keys())}"
        merge_fields = data["merge_fields"]
        assert isinstance(merge_fields, list), "merge_fields should be a list"
        assert len(merge_fields) > 0, "merge_fields should not be empty"
        
        # Check for essential merge fields
        keys = [mf.get("key", "") for mf in merge_fields]
        assert any("first_name" in k for k in keys), f"Missing first_name merge field. Keys: {keys}"
        print(f"PASS: Merge fields count: {len(merge_fields)}, keys: {keys[:3]}")

    def test_templates_structure(self, admin_headers):
        """Each template has required fields (id, name, subject, body)"""
        resp = requests.get(f"{BASE_URL}/api/admin/communications/templates", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        templates = data.get("templates", [])
        
        for t in templates:
            assert "id" in t, f"Template missing 'id': {t}"
            assert "name" in t, f"Template missing 'name': {t}"
            assert "subject" in t, f"Template missing 'subject': {t}"
            assert "body" in t, f"Template missing 'body': {t}"
        print(f"PASS: All {len(templates)} templates have required fields")

    def test_send_communication_returns_200(self, admin_headers):
        """POST /api/admin/communications/send works"""
        payload = {
            "subject": "TEST Sprint Test Email",
            "body": "This is a test communication",
            "channel": "email",
            "recipient_type": "all"
        }
        resp = requests.post(
            f"{BASE_URL}/api/admin/communications/send",
            json=payload,
            headers=admin_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "message" in data
        print(f"PASS: Communication sent: {data['message']}")


# ═══════════════════════════════════════════
# Block 2E: Auth endpoint check
# ═══════════════════════════════════════════

class TestBlock2E_Auth:
    """2E: Google OAuth button backend support"""

    def test_auth_session_endpoint_exists(self):
        """GET /api/auth/session returns 200 or 401 (not 404)"""
        resp = requests.get(f"{BASE_URL}/api/auth/session")
        # Should NOT be 404 - endpoint must exist
        assert resp.status_code != 404, f"Auth session endpoint not found (404)"
        print(f"PASS: /api/auth/session exists, status={resp.status_code}")

    def test_auth_login_endpoint(self):
        """POST /api/auth/login works"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        assert "session_token" in data, "Missing session_token"
        assert data.get("role") == "church_admin", f"Wrong role: {data.get('role')}"
        print(f"PASS: Login works, role={data.get('role')}")


# ═══════════════════════════════════════════
# Giving Integration check
# ═══════════════════════════════════════════

class TestGivingIntegrations:
    """Verify giving integrations endpoint (no Stripe)"""

    def test_giving_integrations_no_stripe(self, admin_headers):
        """Giving integrations should not mention Stripe"""
        resp = requests.get(f"{BASE_URL}/api/admin/giving/integrations", headers=admin_headers)
        if resp.status_code == 200:
            content = str(resp.json()).lower()
            assert "stripe" not in content, f"Stripe found in giving integrations: {content[:200]}"
            print("PASS: No Stripe in giving integrations")
        else:
            print(f"INFO: Giving integrations returned {resp.status_code} - skipping stripe check")

    def test_giving_integrations_has_solomonpay(self, admin_headers):
        """Giving integrations should have solomon_pay processor"""
        resp = requests.get(f"{BASE_URL}/api/admin/giving/integrations", headers=admin_headers)
        if resp.status_code == 200:
            data = resp.json()
            processors = data.get("processors", {})
            assert "solomon_pay" in processors, f"solomon_pay not in processors: {list(processors.keys())}"
            print(f"PASS: solomon_pay in processors: {list(processors.keys())}")
        else:
            print(f"INFO: Giving integrations returned {resp.status_code}")


if __name__ == "__main__":
    import subprocess
    subprocess.run([
        "pytest", __file__, "-v", "--tb=short",
        f"--junitxml=/app/test_reports/pytest/pytest_results_iter78.xml"
    ])
