"""
Iteration 46: Multi-Campus Admin Access & Health Scores Tests
Tests for:
- Shannon Nieman (Lead Pastor) login with church_admin role and 38 permissions
- Jacob Pacheco (member) login with member role and 11 permissions
- Shannon's /auth/me returns accessible_campuses with 3 Abundant campuses
- POST /auth/switch-campus switches Shannon's active tenant
- After campus switch, /auth/me reflects new active_tenant_id
- GET /platform/health-scores shows Abundant churches with A+ (90+)
- GET /platform/health-scores shows non-Abundant churches with D/F (<40)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://solomon-phase-a.preview.emergentagent.com').rstrip('/')

# Global session storage to avoid rate limiting
_sessions = {}

def get_session(email, password):
    """Get or create a session, caching to avoid rate limits"""
    if email in _sessions:
        return _sessions[email]
    
    time.sleep(0.5)  # Small delay to avoid rate limiting
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        data = response.json()
        _sessions[email] = data
        return data
    elif response.status_code == 429:
        # Rate limited, wait and retry
        time.sleep(5)
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            data = response.json()
            _sessions[email] = data
            return data
    return None


class TestShannonNiemanLogin:
    """Tests for Shannon Nieman (Lead Pastor) authentication and permissions"""
    
    def test_shannon_login_success(self):
        """Shannon can login with correct credentials"""
        data = get_session("shannonnieman1030@gmail.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        
        # Verify user identity
        assert data["email"] == "shannonnieman1030@gmail.com"
        assert data["name"] == "Shannon Nieman"
        
        # Verify role is church_admin
        assert data["role"] == "church_admin", f"Expected church_admin, got {data['role']}"
        assert data["role_title"] == "Lead Pastor", f"Expected Lead Pastor, got {data.get('role_title')}"
    
    def test_shannon_has_38_permissions(self):
        """Shannon should have 38 permissions (god mode)"""
        data = get_session("shannonnieman1030@gmail.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        
        permissions = data.get("permissions", [])
        assert len(permissions) == 38, f"Expected 38 permissions, got {len(permissions)}: {permissions}"
        
        # Verify key admin permissions
        assert "admin.dashboard" in permissions
        assert "admin.members.view" in permissions
        assert "admin.members.edit" in permissions
        assert "admin.giving.view" in permissions
        assert "admin.users.create" in permissions
        assert "admin.users.roles" in permissions
        
        # Verify platform permissions
        assert "platform.churches.view" in permissions
        assert "platform.churches.create" in permissions
        assert "platform.users.create" in permissions
        assert "platform.billing" in permissions
        assert "platform.reports" in permissions
    
    def test_shannon_has_accessible_campuses(self):
        """Shannon should have 3 accessible campuses in login response"""
        data = get_session("shannonnieman1030@gmail.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        
        campuses = data.get("accessible_campuses", [])
        assert len(campuses) == 3, f"Expected 3 campuses, got {len(campuses)}"
        
        campus_ids = [c["id"] for c in campuses]
        assert "abundant-east-001" in campus_ids
        assert "abundant-downtown-001" in campus_ids
        assert "abundant-west-001" in campus_ids
        
        # Verify organization info
        assert data.get("organization_id") == "abundant-org-001"
        assert data.get("organization_name") == "Abundant Church"


class TestJacobPachecoLogin:
    """Tests for Jacob Pacheco (member) authentication and permissions"""
    
    def test_jacob_login_success(self):
        """Jacob can login with correct credentials"""
        data = get_session("jacobpacheco@abundanteast.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        
        # Verify user identity
        assert data["email"] == "jacobpacheco@abundanteast.com"
        assert data["name"] == "Jacob Pacheco"
        
        # Verify role is member
        assert data["role"] == "member", f"Expected member, got {data['role']}"
        assert data["role_title"] == "Church Member", f"Expected Church Member, got {data.get('role_title')}"
        
        # Verify tenant
        assert data["tenant_id"] == "abundant-east-001"
        assert data["tenant_name"] == "Abundant East"
    
    def test_jacob_has_11_permissions(self):
        """Jacob should have 11 member permissions only"""
        data = get_session("jacobpacheco@abundanteast.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        
        permissions = data.get("permissions", [])
        assert len(permissions) == 11, f"Expected 11 permissions, got {len(permissions)}: {permissions}"
        
        # Verify all member permissions
        expected_perms = [
            "member.home", "member.give", "member.kids", "member.watch",
            "member.merch", "member.cafe", "member.groups", "member.events",
            "member.nextsteps", "member.prayer", "member.volunteer"
        ]
        for perm in expected_perms:
            assert perm in permissions, f"Missing permission: {perm}"
        
        # Verify NO admin permissions
        admin_perms = [p for p in permissions if p.startswith("admin.")]
        assert len(admin_perms) == 0, f"Member should not have admin permissions: {admin_perms}"
    
    def test_jacob_no_multi_campus_access(self):
        """Jacob should NOT have multi-campus access"""
        data = get_session("jacobpacheco@abundanteast.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        
        # Jacob should not have accessible_campuses
        assert "accessible_campuses" not in data or data.get("accessible_campuses") is None, \
            f"Jacob should not have multi-campus access: {data.get('accessible_campuses')}"


class TestAuthMeEndpoint:
    """Tests for /auth/me endpoint with multi-campus support"""
    
    def test_auth_me_returns_accessible_campuses(self):
        """GET /auth/me should return accessible_campuses for Shannon"""
        data = get_session("shannonnieman1030@gmail.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        token = data["session_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        me_data = response.json()
        
        campuses = me_data.get("accessible_campuses", [])
        assert len(campuses) == 3, f"Expected 3 campuses, got {len(campuses)}"
        
        # Verify campus details
        campus_names = [c["name"] for c in campuses]
        assert "Abundant East" in campus_names
        assert "Abundant Downtown" in campus_names
        assert "Abundant West" in campus_names
    
    def test_auth_me_returns_organization_info(self):
        """GET /auth/me should return organization info"""
        data = get_session("shannonnieman1030@gmail.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        token = data["session_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        me_data = response.json()
        
        assert me_data.get("organization_id") == "abundant-org-001"
        assert me_data.get("organization_name") == "Abundant Church"


class TestCampusSwitching:
    """Tests for POST /auth/switch-campus endpoint"""
    
    def test_switch_to_downtown_campus(self):
        """Shannon can switch to Abundant Downtown"""
        data = get_session("shannonnieman1030@gmail.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        token = data["session_token"]
        
        response = requests.post(
            f"{BASE_URL}/api/auth/switch-campus",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"tenant_id": "abundant-downtown-001"}
        )
        assert response.status_code == 200, f"Switch failed: {response.text}"
        switch_data = response.json()
        
        assert switch_data["active_tenant_id"] == "abundant-downtown-001"
        assert switch_data["active_tenant_name"] == "Abundant Downtown"
        assert "Switched to Abundant Downtown" in switch_data["message"]
    
    def test_switch_to_west_campus(self):
        """Shannon can switch to Abundant West"""
        data = get_session("shannonnieman1030@gmail.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        token = data["session_token"]
        
        response = requests.post(
            f"{BASE_URL}/api/auth/switch-campus",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"tenant_id": "abundant-west-001"}
        )
        assert response.status_code == 200
        switch_data = response.json()
        
        assert switch_data["active_tenant_id"] == "abundant-west-001"
        assert switch_data["active_tenant_name"] == "Abundant West"
    
    def test_switch_to_east_campus(self):
        """Shannon can switch to Abundant East"""
        data = get_session("shannonnieman1030@gmail.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        token = data["session_token"]
        
        response = requests.post(
            f"{BASE_URL}/api/auth/switch-campus",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"tenant_id": "abundant-east-001"}
        )
        assert response.status_code == 200
        switch_data = response.json()
        
        assert switch_data["active_tenant_id"] == "abundant-east-001"
        assert switch_data["active_tenant_name"] == "Abundant East"
    
    def test_auth_me_reflects_campus_switch(self):
        """After switch, /auth/me should reflect new active_tenant_id"""
        data = get_session("shannonnieman1030@gmail.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        token = data["session_token"]
        
        # First switch to downtown
        requests.post(
            f"{BASE_URL}/api/auth/switch-campus",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"tenant_id": "abundant-downtown-001"}
        )
        
        # Then check /auth/me
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        me_data = response.json()
        
        assert me_data.get("active_tenant_id") == "abundant-downtown-001"
        assert me_data.get("active_tenant_name") == "Abundant Downtown"
    
    def test_switch_to_unauthorized_campus_fails(self):
        """Shannon cannot switch to a campus she doesn't have access to"""
        data = get_session("shannonnieman1030@gmail.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        token = data["session_token"]
        
        response = requests.post(
            f"{BASE_URL}/api/auth/switch-campus",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"tenant_id": "cristoviene-church-001"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    
    def test_switch_without_tenant_id_fails(self):
        """Switch without tenant_id should fail"""
        data = get_session("shannonnieman1030@gmail.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        token = data["session_token"]
        
        response = requests.post(
            f"{BASE_URL}/api/auth/switch-campus",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={}
        )
        assert response.status_code == 400


class TestHealthScores:
    """Tests for GET /platform/health-scores endpoint"""
    
    def test_health_scores_requires_platform_admin(self):
        """Health scores endpoint requires platform admin role"""
        # Use Shannon's token (church_admin, not platform_admin)
        data = get_session("shannonnieman1030@gmail.com", "SolomonTest2026!")
        assert data is not None, "Login failed"
        shannon_token = data["session_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/platform/health-scores",
            headers={"Authorization": f"Bearer {shannon_token}"}
        )
        assert response.status_code == 403, f"Expected 403 for non-platform admin, got {response.status_code}"
    
    def test_abundant_east_has_a_plus_score(self):
        """Abundant East should have A+ health score (90+)"""
        data = get_session("admin@solomon.ai", "Demo2026!")
        assert data is not None, "Login failed"
        admin_token = data["session_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/platform/health-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        scores_data = response.json()
        
        abundant_east = next((t for t in scores_data if t["tenant_id"] == "abundant-east-001"), None)
        assert abundant_east is not None, "Abundant East not found in health scores"
        
        health = abundant_east["health"]
        assert health["score"] >= 90, f"Expected score >= 90, got {health['score']}"
        assert health["grade"] == "A+", f"Expected A+, got {health['grade']}"
    
    def test_abundant_downtown_has_a_plus_score(self):
        """Abundant Downtown should have A+ health score (90+)"""
        data = get_session("admin@solomon.ai", "Demo2026!")
        assert data is not None, "Login failed"
        admin_token = data["session_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/platform/health-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        scores_data = response.json()
        
        abundant_downtown = next((t for t in scores_data if t["tenant_id"] == "abundant-downtown-001"), None)
        assert abundant_downtown is not None, "Abundant Downtown not found"
        
        health = abundant_downtown["health"]
        assert health["score"] >= 90, f"Expected score >= 90, got {health['score']}"
        assert health["grade"] == "A+", f"Expected A+, got {health['grade']}"
    
    def test_abundant_west_has_a_plus_score(self):
        """Abundant West should have A+ health score (90+)"""
        data = get_session("admin@solomon.ai", "Demo2026!")
        assert data is not None, "Login failed"
        admin_token = data["session_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/platform/health-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        scores_data = response.json()
        
        abundant_west = next((t for t in scores_data if t["tenant_id"] == "abundant-west-001"), None)
        assert abundant_west is not None, "Abundant West not found"
        
        health = abundant_west["health"]
        assert health["score"] >= 90, f"Expected score >= 90, got {health['score']}"
        assert health["grade"] == "A+", f"Expected A+, got {health['grade']}"
    
    def test_non_abundant_churches_have_low_scores(self):
        """Non-Abundant churches should have low health scores (D/F, <40)"""
        data = get_session("admin@solomon.ai", "Demo2026!")
        assert data is not None, "Login failed"
        admin_token = data["session_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/platform/health-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        scores_data = response.json()
        
        # Find non-Abundant churches
        non_abundant = [t for t in scores_data if not t["tenant_id"].startswith("abundant-")]
        assert len(non_abundant) > 0, "No non-Abundant churches found"
        
        for church in non_abundant:
            health = church["health"]
            assert health["score"] < 40, f"{church['name']} has score {health['score']}, expected < 40"
            assert health["grade"] in ["D", "F"], f"{church['name']} has grade {health['grade']}, expected D or F"
    
    def test_health_scores_sorted_by_score(self):
        """Health scores should be sorted by score descending"""
        data = get_session("admin@solomon.ai", "Demo2026!")
        assert data is not None, "Login failed"
        admin_token = data["session_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/platform/health-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        scores_data = response.json()
        
        scores = [t["health"]["score"] for t in scores_data]
        assert scores == sorted(scores, reverse=True), "Health scores not sorted descending"


class TestRegressionChecks:
    """Basic regression tests to ensure core functionality still works"""
    
    def test_health_endpoint(self):
        """API health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_unauthenticated_auth_me_fails(self):
        """Unauthenticated /auth/me should fail"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
