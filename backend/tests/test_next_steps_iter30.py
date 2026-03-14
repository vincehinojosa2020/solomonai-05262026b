"""
Test Suite for Abundant Next Steps Membership Journey (Iteration 30)
Tests:
- Portal Next Steps status endpoint
- Portal Pathways courses endpoint (regression)
- Admin Next Steps approval queue
- Admin approve/reject actions
- Certificate download (only after approval)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MEMBER_EMAIL = "member@abundant.church"
MEMBER_PASSWORD = "Demo2026!"
ADMIN_EMAIL = "admin@abundant.church"
ADMIN_PASSWORD = "Demo2026!"


class TestAuthHelpers:
    """Helper methods for authentication"""
    
    @staticmethod
    def login(email: str, password: str) -> str:
        """Login and return session token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        assert response.status_code == 200, f"Login failed for {email}: {response.text}"
        data = response.json()
        token = data.get("session_token") or data.get("token") or data.get("access_token")
        assert token, f"No token in response: {data}"
        return token


@pytest.fixture(scope="module")
def member_token():
    """Get member token"""
    return TestAuthHelpers.login(MEMBER_EMAIL, MEMBER_PASSWORD)


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token"""
    return TestAuthHelpers.login(ADMIN_EMAIL, ADMIN_PASSWORD)


class TestNextStepsStatusEndpoint:
    """Test GET /api/portal/next-steps/status endpoint"""
    
    def test_next_steps_status_returns_json(self, member_token):
        """Verify /portal/next-steps/status returns JSON with expected fields"""
        response = requests.get(
            f"{BASE_URL}/api/portal/next-steps/status",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200, f"Status endpoint failed: {response.text}"
        
        data = response.json()
        
        # Assert required fields exist
        assert "completion_percent" in data, f"Missing completion_percent: {data}"
        assert "approval_status" in data, f"Missing approval_status: {data}"
        assert "thinkific_url" in data, f"Missing thinkific_url: {data}"
        assert "required_courses" in data, f"Missing required_courses: {data}"
        
        # Validate types
        assert isinstance(data["completion_percent"], (int, float)), f"completion_percent should be number: {data}"
        assert isinstance(data["thinkific_url"], str), f"thinkific_url should be string: {data}"
        assert isinstance(data["required_courses"], list), f"required_courses should be list: {data}"
        
        print(f"Next Steps Status: {data['completion_percent']}% complete, status={data['approval_status']}")
        print(f"Thinkific URL: {data['thinkific_url']}")
        print(f"Required courses: {len(data['required_courses'])}")
    
    def test_next_steps_status_includes_certificate_availability(self, member_token):
        """Verify certificate_available field is present"""
        response = requests.get(
            f"{BASE_URL}/api/portal/next-steps/status",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "certificate_available" in data, f"Missing certificate_available: {data}"
        assert isinstance(data["certificate_available"], bool), "certificate_available should be boolean"
        print(f"Certificate available: {data['certificate_available']}")
    
    def test_next_steps_status_requires_auth(self):
        """Verify 401 without authentication"""
        response = requests.get(f"{BASE_URL}/api/portal/next-steps/status")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestPortalPathwaysRegression:
    """Regression tests for existing pathways courses endpoint"""
    
    def test_pathways_courses_endpoint_returns_courses(self, member_token):
        """Verify existing /portal/pathways/courses endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/portal/pathways/courses",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200, f"Pathways courses failed: {response.text}"
        
        data = response.json()
        assert "courses" in data, f"Missing courses key: {data}"
        
        courses = data["courses"]
        assert isinstance(courses, list), "courses should be a list"
        print(f"Found {len(courses)} pathways courses")
        
        # Verify course structure if courses exist
        if len(courses) > 0:
            course = courses[0]
            assert "id" in course, "Course missing id"
            assert "title" in course, "Course missing title"
            print(f"Sample course: {course.get('title', 'No title')}")


class TestAdminNextStepsApprovals:
    """Test admin approval queue endpoint"""
    
    def test_admin_approvals_endpoint(self, admin_token):
        """Verify GET /admin/next-steps/approvals returns approval queue"""
        response = requests.get(
            f"{BASE_URL}/api/admin/next-steps/approvals",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Admin approvals failed: {response.text}"
        
        data = response.json()
        assert "approvals" in data, f"Missing approvals key: {data}"
        
        approvals = data["approvals"]
        assert isinstance(approvals, list), "approvals should be a list"
        print(f"Found {len(approvals)} items in approval queue")
        
        # Verify approval structure if items exist
        if len(approvals) > 0:
            approval = approvals[0]
            assert "user_id" in approval, "Approval missing user_id"
            assert "completion_percent" in approval, "Approval missing completion_percent"
            assert "approval_status" in approval, "Approval missing approval_status"
            print(f"Sample approval: user_id={approval.get('user_id')}, status={approval.get('approval_status')}")
    
    def test_admin_approvals_requires_admin_role(self, member_token):
        """Verify member role cannot access admin approvals"""
        response = requests.get(
            f"{BASE_URL}/api/admin/next-steps/approvals",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


class TestApproveRejectActions:
    """Test approve/reject actions"""
    
    def test_get_member_user_id(self, admin_token):
        """Get member user_id for approval testing"""
        # First get the member from portal/me
        response = requests.get(
            f"{BASE_URL}/api/admin/next-steps/approvals",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        approvals = data.get("approvals", [])
        
        # Look for the test member
        for approval in approvals:
            member = approval.get("member", {})
            if member.get("email") == MEMBER_EMAIL:
                return approval.get("user_id")
        
        # If not found in queue, that's okay - member might not have started
        print("Test member not found in approval queue (may not have started Next Steps)")
        return None
    
    def test_approve_action_requires_eligibility(self, admin_token):
        """Test that approve action validates eligibility"""
        # Get member user_id
        response = requests.get(
            f"{BASE_URL}/api/admin/next-steps/approvals",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        approvals = data.get("approvals", [])
        
        # Find a non-eligible member to test validation
        for approval in approvals:
            if not approval.get("eligible") and approval.get("approval_status") != "approved":
                user_id = approval.get("user_id")
                
                # Try to approve non-eligible member - should fail
                response = requests.post(
                    f"{BASE_URL}/api/admin/next-steps/approvals/{user_id}",
                    headers={"Authorization": f"Bearer {admin_token}"},
                    json={"action": "approve"}
                )
                # If not eligible, should get 400 error
                if approval.get("completion_percent", 0) < 100:
                    assert response.status_code == 400, f"Expected 400 for non-eligible, got {response.status_code}"
                    print(f"Correctly blocked approval for non-eligible member {user_id}")
                return
        
        print("No non-eligible members found to test validation")
    
    def test_reject_action(self, admin_token):
        """Test reject action works"""
        # Get member user_id from approvals queue
        response = requests.get(
            f"{BASE_URL}/api/admin/next-steps/approvals",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        approvals = data.get("approvals", [])
        
        # Find any member to test reject on
        for approval in approvals:
            if approval.get("approval_status") in ["in_progress", "eligible_pending_approval"]:
                user_id = approval.get("user_id")
                
                # Reject should work regardless of eligibility
                response = requests.post(
                    f"{BASE_URL}/api/admin/next-steps/approvals/{user_id}",
                    headers={"Authorization": f"Bearer {admin_token}"},
                    json={"action": "reject", "notes": "Test rejection from pytest"}
                )
                assert response.status_code == 200, f"Reject failed: {response.text}"
                
                result = response.json()
                assert result.get("approval_status") == "rejected", f"Expected rejected status: {result}"
                print(f"Successfully rejected membership for {user_id}")
                return
        
        print("No members available to test rejection")
    
    def test_invalid_action_rejected(self, admin_token):
        """Test that invalid action is rejected"""
        response = requests.post(
            f"{BASE_URL}/api/admin/next-steps/approvals/test-user-123",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"action": "invalid_action"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid action, got {response.status_code}"


class TestCertificateDownload:
    """Test certificate download endpoint"""
    
    def test_certificate_requires_approval(self, member_token):
        """Verify certificate returns 403 if not approved"""
        # First check member's approval status
        response = requests.get(
            f"{BASE_URL}/api/portal/next-steps/status",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200
        
        status_data = response.json()
        
        # Try to download certificate
        cert_response = requests.get(
            f"{BASE_URL}/api/portal/next-steps/certificate",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        if status_data.get("approval_status") == "approved":
            # Should succeed
            assert cert_response.status_code == 200, f"Certificate download failed: {cert_response.text}"
            assert cert_response.headers.get("content-type") == "application/pdf"
            print("Certificate download successful (member is approved)")
        else:
            # Should fail with 403
            assert cert_response.status_code == 403, f"Expected 403, got {cert_response.status_code}"
            print(f"Certificate correctly blocked (status: {status_data.get('approval_status')})")
    
    def test_certificate_requires_auth(self):
        """Verify certificate endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/portal/next-steps/certificate")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestApprovalWorkflow:
    """Test full approval workflow - approve eligible member and verify certificate access"""
    
    def test_full_approval_workflow(self, admin_token, member_token):
        """Test: Approve eligible member -> certificate becomes available"""
        
        # Step 1: Check member's next steps status
        status_response = requests.get(
            f"{BASE_URL}/api/portal/next-steps/status",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        print(f"Member status: {status_data.get('approval_status')}, completion: {status_data.get('completion_percent')}%")
        
        # Step 2: If member is eligible and not yet approved, approve them
        if status_data.get("eligible") and status_data.get("approval_status") != "approved":
            # Get member's user_id
            me_response = requests.get(
                f"{BASE_URL}/api/auth/me",
                headers={"Authorization": f"Bearer {member_token}"}
            )
            assert me_response.status_code == 200
            user_id = me_response.json().get("user_id")
            
            # Approve the member
            approve_response = requests.post(
                f"{BASE_URL}/api/admin/next-steps/approvals/{user_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"action": "approve", "notes": "Approved via pytest workflow test"}
            )
            assert approve_response.status_code == 200, f"Approval failed: {approve_response.text}"
            print(f"Approved member {user_id}")
            
            # Verify certificate is now available
            cert_response = requests.get(
                f"{BASE_URL}/api/portal/next-steps/certificate",
                headers={"Authorization": f"Bearer {member_token}"}
            )
            assert cert_response.status_code == 200, f"Certificate should be available after approval: {cert_response.text}"
            assert cert_response.headers.get("content-type") == "application/pdf"
            print("Certificate download successful after approval")
        
        elif status_data.get("approval_status") == "approved":
            # Already approved - just verify certificate works
            cert_response = requests.get(
                f"{BASE_URL}/api/portal/next-steps/certificate",
                headers={"Authorization": f"Bearer {member_token}"}
            )
            assert cert_response.status_code == 200
            assert cert_response.headers.get("content-type") == "application/pdf"
            print("Member already approved - certificate verified")
        
        else:
            # Not eligible - certificate should not be available
            print(f"Member not yet eligible (completion: {status_data.get('completion_percent')}%)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
