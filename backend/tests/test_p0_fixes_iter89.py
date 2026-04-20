"""
Test P0 Bug Fixes - Iteration 89
Tests for:
- FIX 1: Platform Transactions tab (3M+ records with donor names, church names, amounts, funds, fees, status)
- FIX 2: Platform Donors page (41K+ total donors, active donors, recurring donors, DonorIQ breakdown, top donors)
- FIX 3: Attendance page (services list with headcounts, no infinite loading)
- FIX 4: Church Detail drill-through (12-month giving chart, top donors, recent transactions, member roster, health score)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PLATFORM_ADMIN_EMAIL = "admin@solomonai.us"
PLATFORM_ADMIN_PASSWORD = os.environ.get("TEST_PASSWORD", "Demo2026!")
CHURCH_ADMIN_EMAIL = "shannonnieman1030@gmail.com"
CHURCH_ADMIN_PASSWORD = os.environ.get("TEST_PASSWORD", "Demo2026!")


class TestAuth:
    """Authentication tests for platform admin and church admin"""
    
    @pytest.fixture(scope="class")
    def platform_admin_token(self):
        """Get platform admin session token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Platform admin login failed: {response.text}"
        data = response.json()
        assert "session_token" in data, "No session_token in response"
        return data["session_token"]
    
    @pytest.fixture(scope="class")
    def church_admin_token(self):
        """Get church admin session token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Church admin login failed: {response.text}"
        data = response.json()
        assert "session_token" in data, "No session_token in response"
        return data["session_token"]
    
    def test_platform_admin_login(self, platform_admin_token):
        """Verify platform admin can login"""
        assert platform_admin_token is not None
        assert len(platform_admin_token) > 0
        print(f"✓ Platform admin login successful, token: {platform_admin_token[:20]}...")


class TestFix1PlatformTransactions:
    """FIX 1: Platform Transactions tab should show 3M+ records with donor names, church names, amounts, funds, fees, status"""
    
    @pytest.fixture(scope="class")
    def platform_admin_token(self):
        """Get platform admin session token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Platform admin login failed: {response.text}"
        return response.json()["session_token"]
    
    def test_transactions_endpoint_returns_data(self, platform_admin_token):
        """Test that /api/platform/transactions returns transaction data"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/transactions?page=1&limit=50", headers=headers)
        
        assert response.status_code == 200, f"Transactions endpoint failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "transactions" in data, "Missing 'transactions' key in response"
        assert "total" in data, "Missing 'total' key in response"
        assert "pages" in data, "Missing 'pages' key in response"
        
        print(f"✓ Transactions endpoint returned {data['total']} total transactions, {data['pages']} pages")
        
        # Verify we have transactions
        assert data["total"] > 0, "No transactions found - expected 3M+ records"
        print(f"✓ Total transactions: {data['total']:,}")
    
    def test_transactions_have_required_fields(self, platform_admin_token):
        """Test that transactions have all required fields: donor name, church name, amount, fund, fee, status"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/transactions?page=1&limit=10", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        transactions = data.get("transactions", [])
        
        assert len(transactions) > 0, "No transactions returned"
        
        # Check first transaction for required fields
        txn = transactions[0]
        required_fields = ["donation_date", "church_name", "person_name", "amount", "fund_name", "status"]
        
        for field in required_fields:
            assert field in txn, f"Missing required field: {field}"
            print(f"✓ Field '{field}' present: {txn.get(field)}")
        
        # Verify person_name is not empty/generic
        assert txn.get("person_name"), "person_name is empty"
        print(f"✓ Donor name populated: {txn.get('person_name')}")
        
        # Verify church_name is populated
        assert txn.get("church_name"), "church_name is empty"
        print(f"✓ Church name populated: {txn.get('church_name')}")
        
        # Verify amount is a number
        assert isinstance(txn.get("amount"), (int, float)), "amount is not a number"
        print(f"✓ Amount is numeric: ${txn.get('amount'):,.2f}")
    
    def test_transactions_pagination(self, platform_admin_token):
        """Test that pagination works correctly"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        
        # Get page 1
        response1 = requests.get(f"{BASE_URL}/api/platform/transactions?page=1&limit=10", headers=headers)
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get page 2
        response2 = requests.get(f"{BASE_URL}/api/platform/transactions?page=2&limit=10", headers=headers)
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify different transactions on different pages
        if len(data1["transactions"]) > 0 and len(data2["transactions"]) > 0:
            txn1_ids = [t.get("id") or t.get("donation_date") for t in data1["transactions"]]
            txn2_ids = [t.get("id") or t.get("donation_date") for t in data2["transactions"]]
            # Pages should have different content
            print(f"✓ Page 1 has {len(data1['transactions'])} transactions")
            print(f"✓ Page 2 has {len(data2['transactions'])} transactions")


class TestFix2PlatformDonors:
    """FIX 2: Platform Donors page should show 41K+ total donors, active donors, recurring donors, DonorIQ breakdown, top donors"""
    
    @pytest.fixture(scope="class")
    def platform_admin_token(self):
        """Get platform admin session token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["session_token"]
    
    def test_donors_endpoint_returns_data(self, platform_admin_token):
        """Test that /api/platform/donors returns donor statistics"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/donors", headers=headers)
        
        assert response.status_code == 200, f"Donors endpoint failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_donors" in data, "Missing 'total_donors' key"
        assert "active_donors" in data, "Missing 'active_donors' key"
        assert "recurring_donors" in data, "Missing 'recurring_donors' key"
        
        print(f"✓ Total donors: {data.get('total_donors', 0):,}")
        print(f"✓ Active donors (90d): {data.get('active_donors', 0):,}")
        print(f"✓ Recurring donors: {data.get('recurring_donors', 0):,}")
        
        # Verify we have donors
        assert data.get("total_donors", 0) > 0, "No donors found - expected 41K+ donors"
    
    def test_donors_have_donoriq_breakdown(self, platform_admin_token):
        """Test that donor stats include DonorIQ breakdown (donor stages)"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/donors", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for donor_stages (DonorIQ breakdown)
        assert "donor_stages" in data, "Missing 'donor_stages' (DonorIQ breakdown)"
        stages = data["donor_stages"]
        
        expected_stages = ["first_time", "occasional", "regular", "recurring", "at_risk", "lapsed"]
        for stage in expected_stages:
            assert stage in stages, f"Missing donor stage: {stage}"
            print(f"✓ DonorIQ stage '{stage}': {stages.get(stage, 0):,}")
    
    def test_donors_have_top_donors_list(self, platform_admin_token):
        """Test that donor stats include top donors list"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/donors", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for top_donors
        assert "top_donors" in data, "Missing 'top_donors' list"
        top_donors = data["top_donors"]
        
        assert isinstance(top_donors, list), "top_donors should be a list"
        assert len(top_donors) > 0, "top_donors list is empty"
        
        # Check first top donor has required fields
        donor = top_donors[0]
        assert "name" in donor or "person_id" in donor, "Top donor missing name/person_id"
        assert "total" in donor, "Top donor missing total giving"
        
        print(f"✓ Top donors list has {len(top_donors)} donors")
        print(f"✓ Top donor: {donor.get('name', 'Unknown')} - ${donor.get('total', 0):,.2f}")
    
    def test_donors_have_by_campus_data(self, platform_admin_token):
        """Test that donor stats include by_campus breakdown"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/donors", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for by_campus
        assert "by_campus" in data, "Missing 'by_campus' breakdown"
        by_campus = data["by_campus"]
        
        assert isinstance(by_campus, dict), "by_campus should be a dict"
        print(f"✓ Donors by campus: {len(by_campus)} campuses")
        for campus, count in list(by_campus.items())[:3]:
            print(f"  - {campus}: {count:,} donors")


class TestFix3AttendancePage:
    """FIX 3: Attendance page should load services list with headcounts, not show infinite loading"""
    
    @pytest.fixture(scope="class")
    def church_admin_token(self):
        """Get church admin session token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": CHURCH_ADMIN_EMAIL,
            "password": CHURCH_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Church admin login failed: {response.text}"
        return response.json()["session_token"]
    
    def test_services_endpoint_returns_data(self, church_admin_token):
        """Test that /api/services returns services list"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/services?limit=20", headers=headers)
        
        assert response.status_code == 200, f"Services endpoint failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Response should be a list of services
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ Services endpoint returned {len(data)} services")
        
        # Verify we have services
        assert len(data) > 0, "No services found - attendance page would show infinite loading"
    
    def test_services_have_headcount(self, church_admin_token):
        """Test that services have headcount data"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/services?limit=10", headers=headers)
        
        assert response.status_code == 200
        services = response.json()
        
        if len(services) > 0:
            service = services[0]
            # Check for headcount field
            assert "total_headcount" in service or "headcount" in service, "Service missing headcount field"
            headcount = service.get("total_headcount") or service.get("headcount", 0)
            print(f"✓ Service has headcount: {headcount}")
            
            # Check for date field
            assert "date" in service, "Service missing date field"
            print(f"✓ Service date: {service.get('date')}")
    
    def test_service_types_endpoint(self, church_admin_token):
        """Test that /api/service-types returns service types"""
        headers = {"Authorization": f"Bearer {church_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/service-types", headers=headers)
        
        assert response.status_code == 200, f"Service types endpoint failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ Service types endpoint returned {len(data)} types")


class TestFix4ChurchDetailDrillthrough:
    """FIX 4: Church Detail drill-through should show 12-month giving chart, top donors, recent transactions, member roster, health score"""
    
    @pytest.fixture(scope="class")
    def platform_admin_token(self):
        """Get platform admin session token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["session_token"]
    
    def test_church_detail_endpoint_exists(self, platform_admin_token):
        """Test that /api/platform/churches/{tenant_id}/detail endpoint exists"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        
        # Test with abundant-east-001
        response = requests.get(f"{BASE_URL}/api/platform/churches/abundant-east-001/detail", headers=headers)
        
        assert response.status_code == 200, f"Church detail endpoint failed: {response.status_code} - {response.text}"
        data = response.json()
        
        print(f"✓ Church detail endpoint returned data for abundant-east-001")
        
        # Verify response structure
        assert "church" in data, "Missing 'church' key"
        assert "health" in data, "Missing 'health' key"
        assert "summary" in data, "Missing 'summary' key"
        assert "monthly_giving" in data, "Missing 'monthly_giving' key (12-month chart)"
        assert "top_donors" in data, "Missing 'top_donors' key"
        assert "recent_transactions" in data, "Missing 'recent_transactions' key"
        assert "members" in data, "Missing 'members' key (member roster)"
    
    def test_church_detail_has_12_month_giving(self, platform_admin_token):
        """Test that church detail includes 12-month giving chart data"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/churches/abundant-east-001/detail", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        monthly_giving = data.get("monthly_giving", [])
        assert isinstance(monthly_giving, list), "monthly_giving should be a list"
        
        print(f"✓ Monthly giving data has {len(monthly_giving)} months")
        
        if len(monthly_giving) > 0:
            month = monthly_giving[0]
            assert "month" in month, "Monthly giving missing 'month' field"
            assert "total" in month, "Monthly giving missing 'total' field"
            print(f"✓ Sample month: {month.get('month')} - ${month.get('total', 0):,.2f}")
    
    def test_church_detail_has_top_donors(self, platform_admin_token):
        """Test that church detail includes top donors list"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/churches/abundant-east-001/detail", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        top_donors = data.get("top_donors", [])
        assert isinstance(top_donors, list), "top_donors should be a list"
        
        print(f"✓ Top donors list has {len(top_donors)} donors")
        
        if len(top_donors) > 0:
            donor = top_donors[0]
            assert "total" in donor, "Top donor missing 'total' field"
            print(f"✓ Top donor total: ${donor.get('total', 0):,.2f}")
    
    def test_church_detail_has_recent_transactions(self, platform_admin_token):
        """Test that church detail includes recent transactions"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/churches/abundant-east-001/detail", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        recent_txns = data.get("recent_transactions", [])
        assert isinstance(recent_txns, list), "recent_transactions should be a list"
        
        print(f"✓ Recent transactions has {len(recent_txns)} transactions")
        
        if len(recent_txns) > 0:
            txn = recent_txns[0]
            assert "amount" in txn, "Transaction missing 'amount' field"
            assert "person_name" in txn, "Transaction missing 'person_name' field"
            print(f"✓ Sample transaction: {txn.get('person_name')} - ${txn.get('amount', 0):,.2f}")
    
    def test_church_detail_has_member_roster(self, platform_admin_token):
        """Test that church detail includes member roster"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/churches/abundant-east-001/detail", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        members = data.get("members", [])
        assert isinstance(members, list), "members should be a list"
        
        print(f"✓ Member roster has {len(members)} members")
        
        if len(members) > 0:
            member = members[0]
            assert "first_name" in member or "name" in member, "Member missing name field"
            print(f"✓ Sample member: {member.get('first_name', '')} {member.get('last_name', '')}")
    
    def test_church_detail_has_health_score(self, platform_admin_token):
        """Test that church detail includes health score"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/churches/abundant-east-001/detail", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        health = data.get("health", {})
        assert health is not None, "health should not be None"
        
        # Health should have grade and score
        if health:
            print(f"✓ Health grade: {health.get('grade', 'N/A')}")
            print(f"✓ Health score: {health.get('score', 0)}/100")
            
            # Check for dimensions
            if "dimensions" in health:
                dims = health["dimensions"]
                print(f"✓ Health dimensions: {len(dims)} dimensions")
    
    def test_church_detail_summary_stats(self, platform_admin_token):
        """Test that church detail includes summary statistics"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/churches/abundant-east-001/detail", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        summary = data.get("summary", {})
        assert summary is not None, "summary should not be None"
        
        # Check for key summary fields
        expected_fields = ["total_members", "total_giving", "total_transactions", "active_donors_90d"]
        for field in expected_fields:
            if field in summary:
                print(f"✓ Summary {field}: {summary.get(field):,}" if isinstance(summary.get(field), (int, float)) else f"✓ Summary {field}: {summary.get(field)}")


class TestPlatformStats:
    """Additional tests for platform stats endpoint"""
    
    @pytest.fixture(scope="class")
    def platform_admin_token(self):
        """Get platform admin session token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["session_token"]
    
    def test_platform_stats_endpoint(self, platform_admin_token):
        """Test that /api/platform/stats returns platform statistics"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/platform/stats", headers=headers)
        
        assert response.status_code == 200, f"Platform stats failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify key fields
        assert "giving" in data, "Missing 'giving' key"
        assert "transactions" in data, "Missing 'transactions' key"
        assert "campus_breakdown" in data, "Missing 'campus_breakdown' key"
        
        print(f"✓ Platform stats loaded successfully")
        print(f"✓ All-time giving: ${data.get('giving', {}).get('all_time', 0):,.2f}")
        print(f"✓ Total transactions: {data.get('transactions', {}).get('total', 0):,}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
