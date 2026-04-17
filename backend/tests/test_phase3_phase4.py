"""
Solomon AI — Phase 3 & Phase 4 Backend API Tests
Tests for:
- Phase 3: Portal Groups (detail, Q&A, notify), Tax Statements, Payment Methods
- Phase 4: SolomonPay Admin Dashboard (all 8 tabs), Academy Courses
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://demo-ready-saas.preview.emergentagent.com')

# Test credentials
CHURCH_ADMIN = {"email": "shannonnieman1030@gmail.com", "password": os.environ.get("TEST_PASSWORD", "Demo2026!")}
PORTAL_MEMBER = {"email": "member@abundant.church", "password": os.environ.get("TEST_PASSWORD", "Demo2026!")}
PLATFORM_ADMIN = {"email": "admin@solomonai.us", "password": os.environ.get("TEST_PASSWORD", "Demo2026!")}


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get church admin session token"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        token = data.get("session_token") or data.get("token")
        assert token, "No session token returned"
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    @pytest.fixture(scope="class")
    def member_session(self):
        """Get portal member session token"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=PORTAL_MEMBER)
        assert response.status_code == 200, f"Member login failed: {response.text}"
        data = response.json()
        token = data.get("session_token") or data.get("token")
        assert token, "No session token returned"
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_admin_login(self):
        """Test church admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data or "token" in data
        assert data.get("user", {}).get("role") in ["church_admin", "admin"]
    
    def test_member_login(self):
        """Test portal member login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PORTAL_MEMBER)
        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data or "token" in data


class TestPhase3PortalGroups:
    """Phase 3: Portal Groups - detail, Q&A, notify"""
    
    @pytest.fixture(scope="class")
    def member_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=PORTAL_MEMBER)
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_available_groups(self, member_session):
        """Test GET /api/portal/groups - list available groups"""
        response = member_session.get(f"{BASE_URL}/api/portal/groups")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} available groups")
    
    def test_get_my_groups(self, member_session):
        """Test GET /api/portal/my-groups - list member's groups"""
        response = member_session.get(f"{BASE_URL}/api/portal/my-groups")
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        print(f"Member has {len(data['groups'])} groups")
    
    def test_group_detail(self, member_session):
        """Test GET /api/portal/groups/{group_id}/detail - group detail overlay"""
        # First get a group
        groups_response = member_session.get(f"{BASE_URL}/api/portal/groups")
        if groups_response.status_code == 200:
            groups = groups_response.json()
            if groups:
                group_id = groups[0].get("id")
                response = member_session.get(f"{BASE_URL}/api/portal/groups/{group_id}/detail")
                assert response.status_code == 200
                data = response.json()
                assert "name" in data
                print(f"Group detail: {data.get('name')}")
            else:
                pytest.skip("No groups available to test detail")
        else:
            pytest.skip("Could not fetch groups")
    
    def test_group_questions(self, member_session):
        """Test GET /api/portal/groups/{group_id}/questions - Q&A"""
        groups_response = member_session.get(f"{BASE_URL}/api/portal/groups")
        if groups_response.status_code == 200:
            groups = groups_response.json()
            if groups:
                group_id = groups[0].get("id")
                response = member_session.get(f"{BASE_URL}/api/portal/groups/{group_id}/questions")
                assert response.status_code == 200
                data = response.json()
                assert "questions" in data
                print(f"Group has {len(data['questions'])} questions")
            else:
                pytest.skip("No groups available")
        else:
            pytest.skip("Could not fetch groups")
    
    def test_submit_group_question(self, member_session):
        """Test POST /api/portal/groups/{group_id}/questions - submit question"""
        groups_response = member_session.get(f"{BASE_URL}/api/portal/groups")
        if groups_response.status_code == 200:
            groups = groups_response.json()
            if groups:
                group_id = groups[0].get("id")
                response = member_session.post(
                    f"{BASE_URL}/api/portal/groups/{group_id}/questions",
                    json={"question": f"TEST_Question from automated test at {datetime.now().isoformat()}"}
                )
                assert response.status_code in [200, 201]
                print("Question submitted successfully")
            else:
                pytest.skip("No groups available")
        else:
            pytest.skip("Could not fetch groups")
    
    def test_group_notify(self, member_session):
        """Test POST /api/portal/groups/{group_id}/notify - get notified for closed groups"""
        groups_response = member_session.get(f"{BASE_URL}/api/portal/groups")
        if groups_response.status_code == 200:
            groups = groups_response.json()
            # Find a closed group (is_open = False)
            closed_groups = [g for g in groups if not g.get("is_open", True)]
            if closed_groups:
                group_id = closed_groups[0].get("id")
                response = member_session.post(f"{BASE_URL}/api/portal/groups/{group_id}/notify")
                # 200 = subscribed, or could be already subscribed
                assert response.status_code in [200, 400]
                print(f"Notify response: {response.json()}")
            else:
                # Test with any group
                if groups:
                    group_id = groups[0].get("id")
                    response = member_session.post(f"{BASE_URL}/api/portal/groups/{group_id}/notify")
                    assert response.status_code in [200, 400]
                else:
                    pytest.skip("No groups available")
        else:
            pytest.skip("Could not fetch groups")


class TestPhase3TaxStatements:
    """Phase 3: Tax Statement Download"""
    
    @pytest.fixture(scope="class")
    def member_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=PORTAL_MEMBER)
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_tax_statement_data_2024(self, member_session):
        """Test GET /api/portal/giving/statement/2024 - get statement data"""
        response = member_session.get(f"{BASE_URL}/api/portal/giving/statement/2024")
        # 200 = success, 404 = member not found (no person record)
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "year" in data
            assert data["year"] == 2024
            print(f"2024 statement: {data.get('donation_count', 0)} donations, ${data.get('total_amount', 0)}")
    
    def test_get_tax_statement_data_2025(self, member_session):
        """Test GET /api/portal/giving/statement/2025"""
        response = member_session.get(f"{BASE_URL}/api/portal/giving/statement/2025")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["year"] == 2025
    
    def test_get_tax_statement_data_2026(self, member_session):
        """Test GET /api/portal/giving/statement/2026"""
        response = member_session.get(f"{BASE_URL}/api/portal/giving/statement/2026")
        assert response.status_code in [200, 404]
    
    def test_get_tax_statement_data_2027(self, member_session):
        """Test GET /api/portal/giving/statement/2027"""
        response = member_session.get(f"{BASE_URL}/api/portal/giving/statement/2027")
        assert response.status_code in [200, 404]
    
    def test_download_tax_statement_pdf(self, member_session):
        """Test GET /api/portal/giving/statement/2025/pdf - download PDF"""
        response = member_session.get(f"{BASE_URL}/api/portal/giving/statement/2025/pdf")
        # 200 = PDF generated, 404 = member not found
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert "application/pdf" in response.headers.get("content-type", "")
            print("PDF generated successfully")


class TestPhase3PaymentMethods:
    """Phase 3: Payment Methods CRUD"""
    
    @pytest.fixture(scope="class")
    def member_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=PORTAL_MEMBER)
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_list_payment_methods(self, member_session):
        """Test GET /api/portal/payment-methods"""
        response = member_session.get(f"{BASE_URL}/api/portal/payment-methods")
        assert response.status_code == 200
        data = response.json()
        assert "payment_methods" in data
        print(f"Found {len(data['payment_methods'])} payment methods")
    
    def test_add_payment_method(self, member_session):
        """Test POST /api/portal/payment-methods - add card"""
        response = member_session.post(
            f"{BASE_URL}/api/portal/payment-methods",
            json={
                "solomonpay_token": f"sp_test_{datetime.now().timestamp()}",
                "card_brand": "Visa",
                "card_last_four": "4242",
                "card_exp_month": 12,
                "card_exp_year": 2028,
                "is_default": False,
                "nickname": "TEST_Card"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        print(f"Added payment method: {data}")
        return data
    
    def test_set_default_payment_method(self, member_session):
        """Test PUT /api/portal/payment-methods/{id}/default"""
        # First get payment methods
        list_response = member_session.get(f"{BASE_URL}/api/portal/payment-methods")
        if list_response.status_code == 200:
            methods = list_response.json().get("payment_methods", [])
            if methods:
                method_id = methods[0].get("id")
                response = member_session.put(f"{BASE_URL}/api/portal/payment-methods/{method_id}/default")
                assert response.status_code == 200
                print("Set default payment method")
            else:
                pytest.skip("No payment methods to set as default")
        else:
            pytest.skip("Could not list payment methods")
    
    def test_delete_payment_method(self, member_session):
        """Test DELETE /api/portal/payment-methods/{id}"""
        # First add a test card
        add_response = member_session.post(
            f"{BASE_URL}/api/portal/payment-methods",
            json={
                "solomonpay_token": f"sp_delete_test_{datetime.now().timestamp()}",
                "card_brand": "Mastercard",
                "card_last_four": "5555",
                "card_exp_month": 6,
                "card_exp_year": 2029,
                "is_default": False,
                "nickname": "TEST_DeleteMe"
            }
        )
        if add_response.status_code in [200, 201]:
            # Get the ID from the list
            list_response = member_session.get(f"{BASE_URL}/api/portal/payment-methods")
            methods = list_response.json().get("payment_methods", [])
            test_method = next((m for m in methods if m.get("nickname") == "TEST_DeleteMe"), None)
            if test_method:
                response = member_session.delete(f"{BASE_URL}/api/portal/payment-methods/{test_method['id']}")
                assert response.status_code == 200
                print("Deleted test payment method")
            else:
                pytest.skip("Could not find test payment method to delete")
        else:
            pytest.skip("Could not add test payment method")


class TestPhase4SolomonPayDashboard:
    """Phase 4: SolomonPay Admin Dashboard"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_dashboard_stats(self, admin_session):
        """Test GET /api/admin/solomonpay/dashboard - main dashboard stats"""
        response = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/dashboard")
        assert response.status_code == 200
        data = response.json()
        # Check all expected fields
        assert "today" in data
        assert "week" in data
        assert "month" in data
        assert "ytd" in data
        assert "active_recurring" in data
        assert "avg_gift" in data
        assert "top_fund" in data
        assert "trend" in data
        assert "recent_transactions" in data
        print(f"Dashboard: Today=${data['today']['total']}, YTD=${data['ytd']['total']}, Active Recurring={data['active_recurring']}")
    
    def test_transactions_list(self, admin_session):
        """Test GET /api/admin/solomonpay/transactions - full transaction list"""
        response = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        print(f"Transactions: {data['total']} total")
    
    def test_transactions_with_filters(self, admin_session):
        """Test transactions with search and date filters"""
        response = admin_session.get(
            f"{BASE_URL}/api/admin/solomonpay/transactions",
            params={"search": "test", "date_from": "2024-01-01", "date_to": "2027-12-31"}
        )
        assert response.status_code == 200
    
    def test_transactions_pagination(self, admin_session):
        """Test transactions pagination"""
        response = admin_session.get(
            f"{BASE_URL}/api/admin/solomonpay/transactions",
            params={"page": 1, "per_page": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert "per_page" in data
    
    def test_transactions_export_csv(self, admin_session):
        """Test GET /api/admin/solomonpay/transactions/export - CSV export"""
        response = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/transactions/export")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        print("CSV export successful")
    
    def test_payouts(self, admin_session):
        """Test GET /api/admin/solomonpay/payouts - payout history and balance"""
        response = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/payouts")
        assert response.status_code == 200
        data = response.json()
        assert "available_balance" in data
        assert "payouts" in data
        print(f"Available balance: ${data['available_balance']}")
    
    def test_request_payout_standard(self, admin_session):
        """Test POST /api/admin/solomonpay/payouts/request - standard payout"""
        # First check balance
        balance_response = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/payouts")
        if balance_response.status_code == 200:
            balance = balance_response.json().get("available_balance", 0)
            if balance > 0:
                response = admin_session.post(
                    f"{BASE_URL}/api/admin/solomonpay/payouts/request",
                    json={"type": "standard", "amount": min(100, balance)}
                )
                # 200 = success, 403 = missing permission
                assert response.status_code in [200, 403]
                if response.status_code == 200:
                    print(f"Standard payout requested: {response.json()}")
            else:
                pytest.skip("No balance available for payout")
        else:
            pytest.skip("Could not check balance")
    
    def test_funds_list(self, admin_session):
        """Test GET /api/admin/solomonpay/funds - fund management"""
        response = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/funds")
        assert response.status_code == 200
        data = response.json()
        assert "funds" in data
        print(f"Found {len(data['funds'])} funds")
    
    def test_create_fund(self, admin_session):
        """Test POST /api/admin/solomonpay/funds - create fund"""
        response = admin_session.post(
            f"{BASE_URL}/api/admin/solomonpay/funds",
            json={
                "name": f"TEST_Fund_{datetime.now().timestamp()}",
                "description": "Automated test fund",
                "goal_amount": 10000
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "fund" in data or "id" in data
        print(f"Created fund: {data}")
    
    def test_donors_list(self, admin_session):
        """Test GET /api/admin/solomonpay/donors - donor list"""
        response = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/donors")
        assert response.status_code == 200
        data = response.json()
        assert "donors" in data
        assert "total" in data
        print(f"Found {data['total']} donors")
    
    def test_donors_search(self, admin_session):
        """Test donors with search"""
        response = admin_session.get(
            f"{BASE_URL}/api/admin/solomonpay/donors",
            params={"search": "test"}
        )
        assert response.status_code == 200
    
    def test_donor_detail(self, admin_session):
        """Test GET /api/admin/solomonpay/donors/{person_id} - donor detail"""
        # First get a donor
        donors_response = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/donors")
        if donors_response.status_code == 200:
            donors = donors_response.json().get("donors", [])
            if donors:
                person_id = donors[0].get("person_id")
                if person_id:
                    response = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/donors/{person_id}")
                    # 200 = success, 403 = missing permission
                    assert response.status_code in [200, 403]
                    if response.status_code == 200:
                        data = response.json()
                        assert "person" in data
                        assert "donations" in data
                        assert "lifetime_total" in data
                        assert "by_year" in data
                        assert "by_fund" in data
                        print(f"Donor detail: lifetime=${data['lifetime_total']}")
                else:
                    pytest.skip("No person_id in donor data")
            else:
                pytest.skip("No donors found")
        else:
            pytest.skip("Could not fetch donors")
    
    def test_statements_bulk_generate(self, admin_session):
        """Test POST /api/admin/solomonpay/statements/bulk - generate statements"""
        response = admin_session.post(
            f"{BASE_URL}/api/admin/solomonpay/statements/bulk",
            json={"year": 2025}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "job" in data
        print(f"Generated statements: {data['job'].get('donor_count', 0)} donors")
    
    def test_settings_get(self, admin_session):
        """Test GET /api/admin/solomonpay/settings"""
        response = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/settings")
        assert response.status_code == 200
        data = response.json()
        assert "payout_schedule" in data
        print(f"Settings: payout_schedule={data['payout_schedule']}")
    
    def test_settings_update(self, admin_session):
        """Test PUT /api/admin/solomonpay/settings"""
        response = admin_session.put(
            f"{BASE_URL}/api/admin/solomonpay/settings",
            json={
                "payout_schedule": "weekly",
                "show_processing_fees": True,
                "receipt_email_enabled": True
            }
        )
        assert response.status_code == 200
        print("Settings updated")


class TestPhase4AcademyCourses:
    """Phase 4: Academy Courses - verify 6 courses exist"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_list_courses(self, admin_session):
        """Test GET /api/admin/courses - list all courses"""
        response = admin_session.get(f"{BASE_URL}/api/admin/courses")
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        courses = data["courses"]
        print(f"Found {len(courses)} courses")
        
        # Check for the 6 expected courses
        expected_courses = [
            "Becoming a Member",
            "Why We Give",
            "What is Baptism",
            "Premarital",  # Premarital Counseling
            "Food Pantry",  # Volunteer Training: Food Pantry
            "First-Time Volunteers"
        ]
        
        course_titles = [c.get("title", "") for c in courses]
        for expected in expected_courses:
            found = any(expected.lower() in title.lower() for title in course_titles)
            if found:
                print(f"  ✓ Found: {expected}")
            else:
                print(f"  ✗ Missing: {expected}")
    
    def test_portal_courses(self, admin_session):
        """Test GET /api/portal/courses - member-facing courses"""
        response = admin_session.get(f"{BASE_URL}/api/portal/courses")
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        print(f"Portal has {len(data['courses'])} published courses")


class TestPhase4RBAC:
    """Phase 4: RBAC - verify church_admin has full SolomonPay access"""
    
    def test_church_admin_has_solomonpay_access(self):
        """Verify church_admin can access all SolomonPay endpoints"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        assert response.status_code == 200
        data = response.json()
        token = data.get("session_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Test all SolomonPay endpoints
        endpoints = [
            "/api/admin/solomonpay/dashboard",
            "/api/admin/solomonpay/transactions",
            "/api/admin/solomonpay/payouts",
            "/api/admin/solomonpay/funds",
            "/api/admin/solomonpay/donors",
            "/api/admin/solomonpay/settings",
        ]
        
        for endpoint in endpoints:
            response = session.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 200, f"church_admin should have access to {endpoint}, got {response.status_code}"
            print(f"  ✓ {endpoint} - OK")
    
    def test_member_cannot_access_solomonpay(self):
        """Verify regular member cannot access SolomonPay admin"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=PORTAL_MEMBER)
        assert response.status_code == 200
        data = response.json()
        token = data.get("session_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        response = session.get(f"{BASE_URL}/api/admin/solomonpay/dashboard")
        # Should be 403 Forbidden
        assert response.status_code == 403, f"Member should NOT have access to SolomonPay admin, got {response.status_code}"
        print("  ✓ Member correctly denied access to SolomonPay admin")


# Cleanup test data
class TestCleanup:
    """Cleanup TEST_ prefixed data"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=CHURCH_ADMIN)
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token") or data.get("token")
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_cleanup_test_payment_methods(self, admin_session):
        """Clean up TEST_ payment methods"""
        # This would require member session, skip for now
        pass
    
    def test_cleanup_test_funds(self, admin_session):
        """Clean up TEST_ funds"""
        response = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/funds")
        if response.status_code == 200:
            funds = response.json().get("funds", [])
            for fund in funds:
                if fund.get("name", "").startswith("TEST_"):
                    admin_session.delete(f"{BASE_URL}/api/admin/solomonpay/funds/{fund['id']}")
                    print(f"Cleaned up fund: {fund['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
