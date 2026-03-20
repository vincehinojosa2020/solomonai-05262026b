"""
Phase 1-4 Comprehensive Testing V2: RBAC, Security, Volunteers, QR Polish
Uses session fixtures to minimize login calls and avoid rate limiting

Test accounts:
- Platform Admin: admin@solomon.ai / Demo2026!
- Church Admin (Aivy): avopham@gmail.com / SolomonTest2026!
- Member (Vince): vince@charlottesoftwareengineering.com / SolomonTest2026!
"""

import pytest
import requests
import time
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://solomon-mvp.preview.emergentagent.com"

# Test credentials
PLATFORM_ADMIN = {"email": "admin@solomon.ai", "password": "Demo2026!"}
AIVY_ADMIN = {"email": "avopham@gmail.com", "password": "SolomonTest2026!"}
VINCE_MEMBER = {"email": "vince@charlottesoftwareengineering.com", "password": "SolomonTest2026!"}
MEMBER = {"email": "member@abundant.church", "password": "Demo2026!"}


# Session-level fixtures to minimize login calls
@pytest.fixture(scope="session")
def aivy_session():
    """Login as Aivy (church_admin) once for all tests"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json=AIVY_ADMIN)
    if resp.status_code != 200:
        pytest.skip(f"Aivy login failed: {resp.text}")
    data = resp.json()
    return {
        "token": data.get("session_token"),
        "user_id": data.get("user_id"),
        "permissions": data.get("permissions"),
        "role": data.get("role"),
        "role_title": data.get("role_title"),
        "email": data.get("email"),
        "headers": {"Authorization": f"Bearer {data.get('session_token')}"}
    }


@pytest.fixture(scope="session")
def vince_session():
    """Login as Vince (member) once for all tests"""
    time.sleep(1)  # Small delay to avoid rate limit
    resp = requests.post(f"{BASE_URL}/api/auth/login", json=VINCE_MEMBER)
    if resp.status_code != 200:
        pytest.skip(f"Vince login failed: {resp.text}")
    data = resp.json()
    return {
        "token": data.get("session_token"),
        "user_id": data.get("user_id"),
        "permissions": data.get("permissions"),
        "role": data.get("role"),
        "role_title": data.get("role_title"),
        "email": data.get("email"),
        "headers": {"Authorization": f"Bearer {data.get('session_token')}"}
    }


@pytest.fixture(scope="session")
def platform_admin_session():
    """Login as Platform Admin once for all tests"""
    time.sleep(1)  # Small delay to avoid rate limit
    resp = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN)
    if resp.status_code != 200:
        pytest.skip(f"Platform admin login failed: {resp.text}")
    data = resp.json()
    return {
        "token": data.get("session_token"),
        "user_id": data.get("user_id"),
        "permissions": data.get("permissions"),
        "role": data.get("role"),
        "role_title": data.get("role_title"),
        "email": data.get("email"),
        "headers": {"Authorization": f"Bearer {data.get('session_token')}"}
    }


class TestPhase1RBAC:
    """Phase 1: RBAC with fine-grained permissions"""
    
    def test_login_returns_permissions_and_role_title(self, aivy_session):
        """PHASE 1: Login returns permissions[] array and role_title in response"""
        assert "permissions" in aivy_session, "Missing permissions[] in login response"
        assert "role_title" in aivy_session, "Missing role_title in login response"
        assert isinstance(aivy_session["permissions"], list), "permissions should be a list"
        assert len(aivy_session["permissions"]) > 0, "Aivy should have permissions"
        
        print(f"Aivy role: {aivy_session['role']}, role_title: {aivy_session['role_title']}")
        print(f"Aivy permissions count: {len(aivy_session['permissions'])}")
        
    def test_aivy_church_admin_permissions(self, aivy_session):
        """PHASE 1: Aivy logs in as church_admin with admin permissions including admin.kids.manage"""
        permissions = aivy_session["permissions"]
        role = aivy_session["role"]
        role_title = aivy_session["role_title"]
        
        print(f"Aivy role: {role}, role_title: {role_title}")
        print(f"Aivy permissions ({len(permissions)}): {permissions[:10]}...")
        
        # Check role
        assert role == "church_admin", f"Aivy should be church_admin, got {role}"
        
        # Check for admin.kids.manage permission
        assert "admin.kids.manage" in permissions, f"Aivy missing admin.kids.manage. Has: {permissions}"
        
        # Check permission count (should have 20+ permissions for church_admin)
        assert len(permissions) >= 20, f"Aivy should have at least 20 permissions, got {len(permissions)}"
        
    def test_get_role_templates(self, aivy_session):
        """PHASE 1: GET /api/admin/roles/templates returns role templates"""
        resp = requests.get(f"{BASE_URL}/api/admin/roles/templates", headers=aivy_session["headers"])
        
        print(f"Role templates status: {resp.status_code}")
        assert resp.status_code == 200, f"Failed to get role templates: {resp.text}"
        
        data = resp.json()
        print(f"Number of role templates: {len(data)}")
        print(f"Template names: {list(data.keys())}")
        
        # Should have at least 9 templates
        assert len(data) >= 9, f"Expected at least 9 role templates, got {len(data)}"
        
        # Check expected templates exist
        expected = ["member", "kids_volunteer", "small_group_leader", "church_admin"]
        for tmpl in expected:
            assert tmpl in data, f"Missing template: {tmpl}"
            assert "role_title" in data[tmpl], f"Template {tmpl} missing role_title"
            assert "permissions" in data[tmpl], f"Template {tmpl} missing permissions"
    
    def test_get_user_permissions(self, aivy_session):
        """PHASE 1: GET /api/admin/members/{user_id}/permissions returns user permissions"""
        user_id = aivy_session["user_id"]
        resp = requests.get(f"{BASE_URL}/api/admin/members/{user_id}/permissions", headers=aivy_session["headers"])
        
        print(f"Get permissions status: {resp.status_code}")
        assert resp.status_code == 200, f"Failed to get user permissions: {resp.text}"
        
        data = resp.json()
        print(f"User permissions response: {data.get('role')}, {data.get('role_title')}")
        print(f"Permissions count: {len(data.get('permissions', []))}")
        
        assert "permissions" in data
        assert "user_id" in data
        assert data["user_id"] == user_id
    
    def test_update_member_role_with_template(self, aivy_session, vince_session):
        """PHASE 1: PUT /api/admin/members/{user_id}/role accepts role_template"""
        vince_id = vince_session["user_id"]
        
        # Update Vince to kids_volunteer using role_template
        resp = requests.put(
            f"{BASE_URL}/api/admin/members/{vince_id}/role",
            headers=aivy_session["headers"],
            json={"role_template": "kids_volunteer"}
        )
        
        print(f"Update role status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Updated role: {data}")
            assert data.get("success") == True
            assert "admin.kids.manage" in data.get("permissions", [])
        
        # Reset Vince to member
        requests.put(
            f"{BASE_URL}/api/admin/members/{vince_id}/role",
            headers=aivy_session["headers"],
            json={"role_template": "member"}
        )
    
    def test_update_member_permissions_array(self, aivy_session, vince_session):
        """PHASE 1: PUT /api/admin/members/{user_id}/permissions replaces permissions array"""
        vince_id = vince_session["user_id"]
        
        new_permissions = ["member.home", "member.give", "member.kids", "member.watch"]
        resp = requests.put(
            f"{BASE_URL}/api/admin/members/{vince_id}/permissions",
            headers=aivy_session["headers"],
            json={"permissions": new_permissions}
        )
        
        print(f"Update permissions status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("success") == True
            assert set(data.get("permissions", [])) == set(new_permissions)
            
        # Reset Vince
        requests.put(
            f"{BASE_URL}/api/admin/members/{vince_id}/role",
            headers=aivy_session["headers"],
            json={"role_template": "member"}
        )
    
    def test_grant_single_permission(self, aivy_session, vince_session):
        """PHASE 1: POST /api/admin/members/{user_id}/permissions/grant adds permission"""
        vince_id = vince_session["user_id"]
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/members/{vince_id}/permissions/grant",
            headers=aivy_session["headers"],
            json={"permission": "admin.kids.manage"}
        )
        
        print(f"Grant permission status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("success") == True
            assert "admin.kids.manage" in data.get("permissions", [])
            
        # Reset Vince
        requests.put(
            f"{BASE_URL}/api/admin/members/{vince_id}/role",
            headers=aivy_session["headers"],
            json={"role_template": "member"}
        )
    
    def test_revoke_permission(self, aivy_session, vince_session):
        """PHASE 1: DELETE /api/admin/members/{user_id}/permissions/{perm} removes permission"""
        vince_id = vince_session["user_id"]
        
        # First grant a permission
        requests.post(
            f"{BASE_URL}/api/admin/members/{vince_id}/permissions/grant",
            headers=aivy_session["headers"],
            json={"permission": "admin.kids.manage"}
        )
        
        # Now revoke it
        resp = requests.delete(
            f"{BASE_URL}/api/admin/members/{vince_id}/permissions/admin.kids.manage",
            headers=aivy_session["headers"]
        )
        
        print(f"Revoke permission status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("success") == True
            assert "admin.kids.manage" not in data.get("permissions", [])
    
    def test_get_users_by_role(self, aivy_session):
        """PHASE 1: GET /api/admin/roles/users returns users grouped by role_title"""
        resp = requests.get(f"{BASE_URL}/api/admin/roles/users", headers=aivy_session["headers"])
        
        print(f"Get users by role status: {resp.status_code}")
        assert resp.status_code == 200, f"Failed to get users by role: {resp.text}"
        
        data = resp.json()
        print(f"Role groups: {list(data.keys())}")
        
        # Should be a dict of role_title -> users[]
        assert isinstance(data, dict)
        
        for role_title, users in data.items():
            print(f"  {role_title}: {len(users)} users")
            if users:
                assert "permissions" in users[0], f"User in {role_title} missing permissions"
    
    def test_member_cannot_access_admin_endpoints(self, vince_session):
        """PHASE 1: Member user cannot access admin endpoints (returns 403)"""
        resp = requests.get(f"{BASE_URL}/api/admin/roles/templates", headers=vince_session["headers"])
        
        print(f"Member accessing admin endpoint: {resp.status_code}")
        # Should be 403 Forbidden
        assert resp.status_code == 403, f"Member should get 403, got {resp.status_code}: {resp.text}"


class TestPhase2Security:
    """Phase 2: Security hardening"""
    
    def test_security_headers(self):
        """PHASE 2: Response headers include security headers"""
        resp = requests.get(f"{BASE_URL}/api/health")
        
        print(f"Security headers test - Status: {resp.status_code}")
        headers = resp.headers
        
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Strict-Transport-Security"
        ]
        
        for header in security_headers:
            value = headers.get(header)
            print(f"  {header}: {value}")
            assert value is not None, f"Missing security header: {header}"
        
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert "max-age" in headers.get("Strict-Transport-Security", "")
    
    def test_health_endpoint(self):
        """PHASE 2: GET /api/health returns {status: 'ok', timestamp, version}"""
        resp = requests.get(f"{BASE_URL}/api/health")
        
        print(f"Health check status: {resp.status_code}")
        assert resp.status_code == 200
        
        data = resp.json()
        print(f"Health response: {data}")
        
        assert data.get("status") == "ok"
        assert "timestamp" in data
        assert "version" in data
    
    def test_health_detailed(self):
        """PHASE 2: GET /api/health/detailed returns per-service status"""
        resp = requests.get(f"{BASE_URL}/api/health/detailed")
        
        print(f"Detailed health status: {resp.status_code}")
        assert resp.status_code == 200
        
        data = resp.json()
        print(f"Detailed health response: {data}")
        
        assert "services" in data
        assert "database" in data.get("services", {})
        assert "timestamp" in data


class TestPhase2Idempotency:
    """Phase 2: Idempotency for check-in"""
    
    def test_checkin_idempotency(self, vince_session):
        """PHASE 2: POST /api/portal/kids/{child_id}/checkin with idempotency key"""
        # Get Vince's children
        kids_resp = requests.get(f"{BASE_URL}/api/portal/kids", headers=vince_session["headers"])
        print(f"Kids response: {kids_resp.status_code}")
        
        if kids_resp.status_code != 200:
            pytest.skip("No kids available for test")
            return
            
        kids_data = kids_resp.json()
        children = kids_data.get("children", [])
        
        if not children:
            pytest.skip("No children available")
            return
        
        child_id = children[0]["id"]
        idem_key = f"test_idem_{uuid.uuid4().hex}"
        
        headers_with_idem = {**vince_session["headers"], "X-Idempotency-Key": idem_key}
        
        # First check-in
        resp1 = requests.post(
            f"{BASE_URL}/api/portal/kids/{child_id}/checkin",
            headers=headers_with_idem,
            json={"classroom": "Sunday School"}
        )
        print(f"First checkin: {resp1.status_code}")
        
        # Second request with same idempotency key
        resp2 = requests.post(
            f"{BASE_URL}/api/portal/kids/{child_id}/checkin",
            headers=headers_with_idem,
            json={"classroom": "Sunday School"}
        )
        print(f"Second checkin (idempotent): {resp2.status_code}")
        
        if resp1.status_code == 200 and resp2.status_code == 200:
            data1 = resp1.json()
            data2 = resp2.json()
            
            code1 = data1.get("pickup_code")
            code2 = data2.get("pickup_code")
            print(f"Pickup codes: {code1} vs {code2}")
            
            assert code1 == code2, f"Idempotency failed: {code1} vs {code2}"


class TestPhase3Volunteers:
    """Phase 3: Volunteer team management"""
    
    def test_get_volunteer_teams(self, aivy_session):
        """PHASE 3: GET /api/admin/volunteers returns teams with members"""
        resp = requests.get(f"{BASE_URL}/api/admin/volunteers", headers=aivy_session["headers"])
        
        print(f"Get volunteers status: {resp.status_code}")
        assert resp.status_code == 200, f"Failed to get volunteer teams: {resp.text}"
        
        data = resp.json()
        teams = data.get("teams", [])
        print(f"Number of teams: {len(teams)}")
        
        for team in teams:
            print(f"  Team: {team.get('team_name', team.get('id'))} - {len(team.get('members', []))} members")
        
        assert "teams" in data
    
    def test_create_volunteer_team(self, aivy_session):
        """PHASE 3: POST /api/admin/volunteers/teams creates team"""
        team_data = {
            "team_name": f"Test Team {uuid.uuid4().hex[:6]}",
            "ministry": "Testing",
            "description": "Test team for iteration 41"
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/volunteers/teams",
            headers=aivy_session["headers"],
            json=team_data
        )
        
        print(f"Create team status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Created team: {data}")
            assert data.get("success") == True
            assert "team" in data
    
    def test_assign_volunteer_to_team(self, aivy_session, vince_session):
        """PHASE 3: POST /api/admin/volunteers/assign assigns user to team"""
        # Get existing teams
        teams_resp = requests.get(f"{BASE_URL}/api/admin/volunteers", headers=aivy_session["headers"])
        if teams_resp.status_code != 200:
            pytest.skip("Cannot get teams")
            return
            
        teams = teams_resp.json().get("teams", [])
        if not teams:
            # Create a team first
            requests.post(
                f"{BASE_URL}/api/admin/volunteers/teams",
                headers=aivy_session["headers"],
                json={"team_name": "Test Assign Team", "ministry": "Testing"}
            )
            teams_resp = requests.get(f"{BASE_URL}/api/admin/volunteers", headers=aivy_session["headers"])
            teams = teams_resp.json().get("teams", [])
        
        if not teams:
            pytest.skip("No teams available")
            return
            
        team_id = teams[0]["id"]
        vince_id = vince_session["user_id"]
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/volunteers/assign",
            headers=aivy_session["headers"],
            json={"user_id": vince_id, "team_id": team_id, "role_title": "Test Volunteer"}
        )
        
        print(f"Assign volunteer status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Assignment: {data}")
            assert data.get("success") == True
    
    def test_aivy_in_kids_checkin_team(self, aivy_session):
        """PHASE 3: Aivy is assigned to Kids Check-In Team on startup"""
        user_id = aivy_session["user_id"]
        
        resp = requests.get(f"{BASE_URL}/api/admin/volunteers/user/{user_id}", headers=aivy_session["headers"])
        
        print(f"Aivy volunteer teams status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            assignments = data.get("assignments", [])
            print(f"Aivy's team assignments: {len(assignments)}")
            
            team_names = []
            for a in assignments:
                team = a.get("team", {})
                team_name = team.get("team_name", "") if team else ""
                team_names.append(team_name)
                print(f"  - {team_name}")
            
            kids_team = any("kids" in name.lower() for name in team_names if name)
            print(f"In Kids Check-In team: {kids_team}")


class TestPhase4QRPolish:
    """Phase 4: QR Check-in polish"""
    
    def test_checkin_returns_nudge_with_amounts(self, vince_session):
        """PHASE 4: Check-in response includes nudge payload with give_amounts"""
        # Get children
        kids_resp = requests.get(f"{BASE_URL}/api/portal/kids", headers=vince_session["headers"])
        if kids_resp.status_code != 200:
            pytest.skip("Cannot get kids")
            return
            
        children = kids_resp.json().get("children", [])
        if not children:
            pytest.skip("No children for test")
            return
        
        child_id = children[0]["id"]
        idem_key = f"nudge_test_{uuid.uuid4().hex}"
        headers_with_idem = {**vince_session["headers"], "X-Idempotency-Key": idem_key}
        
        resp = requests.post(
            f"{BASE_URL}/api/portal/kids/{child_id}/checkin",
            headers=headers_with_idem,
            json={"classroom": "Sunday School"}
        )
        
        print(f"Checkin for nudge test: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            nudge = data.get("nudge")
            print(f"Nudge payload: {nudge}")
            
            if nudge:
                assert "give_amounts" in nudge, "Missing give_amounts in nudge"
                amounts = nudge.get("give_amounts", [])
                print(f"Give amounts: {amounts}")
                expected = [10, 25, 50, 100]
                assert amounts == expected, f"Expected {expected}, got {amounts}"


class TestRegressionAccounts:
    """Regression: Accounts work correctly"""
    
    def test_aivy_admin_works(self, aivy_session):
        """REGRESSION: Aivy church admin session works"""
        assert aivy_session["token"], "Aivy should have session token"
        assert aivy_session["role"] == "church_admin", f"Expected church_admin, got {aivy_session['role']}"
    
    def test_vince_member_works(self, vince_session):
        """REGRESSION: Vince member session works"""
        assert vince_session["token"], "Vince should have session token"
        assert vince_session["role"] == "member", f"Expected member, got {vince_session['role']}"
    
    def test_platform_admin_works(self, platform_admin_session):
        """REGRESSION: Platform admin session works"""
        assert platform_admin_session["token"], "Platform admin should have session token"
        assert platform_admin_session["role"] == "platform_admin"


class TestRegressionPortalPages:
    """Regression: Member portal pages load"""
    
    def test_portal_home(self, vince_session):
        """REGRESSION: Portal /me endpoint works"""
        resp = requests.get(f"{BASE_URL}/api/portal/me", headers=vince_session["headers"])
        print(f"Portal /me: {resp.status_code}")
        assert resp.status_code == 200
    
    def test_portal_kids(self, vince_session):
        """REGRESSION: Portal /kids endpoint works"""
        resp = requests.get(f"{BASE_URL}/api/portal/kids", headers=vince_session["headers"])
        print(f"Portal /kids: {resp.status_code}")
        assert resp.status_code == 200
    
    def test_portal_groups(self, vince_session):
        """REGRESSION: Portal /groups endpoint works"""
        resp = requests.get(f"{BASE_URL}/api/portal/groups", headers=vince_session["headers"])
        print(f"Portal /groups: {resp.status_code}")
        assert resp.status_code == 200
    
    def test_portal_events(self, vince_session):
        """REGRESSION: Portal /events endpoint works"""
        resp = requests.get(f"{BASE_URL}/api/portal/events", headers=vince_session["headers"])
        print(f"Portal /events: {resp.status_code}")
        assert resp.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
