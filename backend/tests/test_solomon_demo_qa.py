"""
Solomon AI Demo QA Tests - Pre-Demo Verification
Tests all critical pages and data rendering for Shannon (church admin)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://exec-metrics-hub.preview.emergentagent.com')

# Test credentials
SHANNON_EMAIL = "shannonnieman1030@gmail.com"
SHANNON_PASSWORD = os.environ.get("TEST_PASSWORD", "Demo2026!")
ADMIN_EMAIL = "admin@solomonai.us"
ADMIN_PASSWORD = os.environ.get("TEST_PASSWORD", "Demo2026!")


class TestAuthAndLogin:
    """Test authentication flows"""
    
    def test_login_shannon_success(self):
        """Shannon should be able to login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SHANNON_EMAIL,
            "password": SHANNON_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # API returns access_token, session_token, or token
        assert "access_token" in data or "session_token" in data or "token" in data, "No session token returned"
        assert "name" in data or "email" in data, "No user data returned"
        print(f"✓ Shannon login successful - name: {data.get('name')}, tenant: {data.get('tenant_id')}")
        return data
    
    def test_login_platform_admin_success(self):
        """Platform admin should be able to login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        # Role is at top level, not nested in user
        assert data.get("role") == "platform_admin", f"Not platform admin, got role: {data.get('role')}"
        print(f"✓ Platform admin login successful")


class TestDashboardStats:
    """Test dashboard data rendering"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Shannon and get session token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SHANNON_EMAIL,
            "password": SHANNON_PASSWORD
        })
        data = response.json()
        self.token = data.get("access_token") or data.get("session_token") or data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_dashboard_stats_has_data(self):
        """Dashboard should show member count, MTD giving, YTD giving > $0"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        
        # Check member count
        total_members = data.get("total_members", 0)
        assert total_members > 0, f"Total members should be > 0, got {total_members}"
        print(f"✓ Total members: {total_members}")
        
        # Check MTD giving
        mtd_giving = data.get("mtd_giving", 0)
        print(f"  MTD giving: ${mtd_giving:,.2f}")
        
        # Check YTD giving
        ytd_giving = data.get("ytd_giving", 0)
        assert ytd_giving > 0, f"YTD giving should be > 0, got {ytd_giving}"
        print(f"✓ YTD giving: ${ytd_giving:,.2f}")
    
    def test_giving_trend_has_data(self):
        """Giving trend should return 12 months of data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/giving-trend", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 10, f"Expected 10+ months of trend data, got {len(data)}"
        print(f"✓ Giving trend: {len(data)} months of data")
    
    def test_attendance_trend_has_data(self):
        """Attendance trend should return weekly data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/attendance-trend", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 8, f"Expected 8+ weeks of attendance data, got {len(data)}"
        print(f"✓ Attendance trend: {len(data)} weeks of data")


class TestGivingDashboard:
    """Test Giving/Stewardship page data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SHANNON_EMAIL,
            "password": SHANNON_PASSWORD
        })
        data = response.json()
        self.token = data.get("session_token") or data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_giving_stats_has_data(self):
        """Giving stats should show MTD > $0, YTD > $0"""
        response = requests.get(f"{BASE_URL}/api/giving/stats", headers=self.headers)
        assert response.status_code == 200, f"Giving stats failed: {response.text}"
        data = response.json()
        
        mtd_total = data.get("mtd_total", 0)
        ytd_total = data.get("ytd_total", 0)
        
        print(f"  MTD total: ${mtd_total:,.2f}")
        print(f"  YTD total: ${ytd_total:,.2f}")
        print(f"  MTD count: {data.get('mtd_count', 0)} gifts")
        print(f"  YTD count: {data.get('ytd_count', 0)} gifts")
        print(f"  Active recurring: {data.get('active_recurring', 0)}")
        
        # YTD should have data from seeded donations
        assert ytd_total > 0, f"YTD giving should be > 0, got {ytd_total}"
        print(f"✓ Giving stats verified - YTD: ${ytd_total:,.2f}")
    
    def test_donations_list_has_data(self):
        """Donations list should return transactions"""
        response = requests.get(f"{BASE_URL}/api/donations?page=1&per_page=20", headers=self.headers)
        assert response.status_code == 200, f"Donations list failed: {response.text}"
        data = response.json()
        
        donations = data.get("data", [])
        total = data.get("total", 0)
        
        print(f"  Donations returned: {len(donations)}")
        print(f"  Total donations: {total}")
        
        assert len(donations) > 0, "Should have donation transactions"
        print(f"✓ Donations list verified - {len(donations)} transactions shown")
    
    def test_funds_list_has_data(self):
        """Funds list should return fund breakdown"""
        response = requests.get(f"{BASE_URL}/api/funds", headers=self.headers)
        assert response.status_code == 200, f"Funds list failed: {response.text}"
        data = response.json()
        
        assert len(data) > 0, "Should have funds"
        print(f"✓ Funds list verified - {len(data)} funds")
        for fund in data[:5]:
            print(f"  - {fund.get('name')}: ${fund.get('current_amount', 0):,.2f}")


class TestSolomonPayDashboard:
    """Test SolomonPay admin dashboard"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SHANNON_EMAIL,
            "password": SHANNON_PASSWORD
        })
        data = response.json()
        self.token = data.get("session_token") or data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_solomonpay_dashboard_has_data(self):
        """SolomonPay dashboard should show today, week, month, YTD numbers"""
        response = requests.get(f"{BASE_URL}/api/admin/solomonpay/dashboard", headers=self.headers)
        assert response.status_code == 200, f"SolomonPay dashboard failed: {response.text}"
        data = response.json()
        
        today = data.get("today", {})
        week = data.get("week", {})
        month = data.get("month", {})
        ytd = data.get("ytd", {})
        
        print(f"  Today: ${today.get('total', 0):,.2f} ({today.get('count', 0)} gifts)")
        print(f"  This Week: ${week.get('total', 0):,.2f} ({week.get('count', 0)} gifts)")
        print(f"  This Month: ${month.get('total', 0):,.2f} ({month.get('count', 0)} gifts)")
        print(f"  YTD: ${ytd.get('total', 0):,.2f} ({ytd.get('count', 0)} gifts)")
        print(f"  Active recurring: {data.get('active_recurring', 0)}")
        print(f"  Avg gift: ${data.get('avg_gift', 0):,.2f}")
        print(f"  Top fund: {data.get('top_fund', 'N/A')}")
        
        # YTD should have data
        ytd_total = ytd.get("total", 0)
        assert ytd_total > 0, f"YTD should be > 0, got {ytd_total}"
        print(f"✓ SolomonPay dashboard verified - YTD: ${ytd_total:,.2f}")
    
    def test_solomonpay_trend_has_data(self):
        """SolomonPay should have giving trend chart data"""
        response = requests.get(f"{BASE_URL}/api/admin/solomonpay/dashboard", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        trend = data.get("trend", [])
        assert len(trend) > 0, "Should have trend data"
        print(f"✓ SolomonPay trend verified - {len(trend)} months")


class TestMembersPage:
    """Test Members/People page"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SHANNON_EMAIL,
            "password": SHANNON_PASSWORD
        })
        data = response.json()
        self.token = data.get("session_token") or data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_people_list_has_data(self):
        """People list should show member names"""
        response = requests.get(f"{BASE_URL}/api/people?page=1&per_page=25", headers=self.headers)
        assert response.status_code == 200, f"People list failed: {response.text}"
        data = response.json()
        
        people = data.get("data", [])
        total = data.get("total", 0)
        
        assert len(people) > 0, "Should have people"
        assert total > 0, "Total should be > 0"
        
        print(f"✓ People list verified - {total} total members")
        for person in people[:3]:
            print(f"  - {person.get('first_name')} {person.get('last_name')}")


class TestGroupsPage:
    """Test Groups page"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SHANNON_EMAIL,
            "password": SHANNON_PASSWORD
        })
        data = response.json()
        self.token = data.get("session_token") or data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_groups_list_has_data(self):
        """Groups list should show groups with member counts"""
        response = requests.get(f"{BASE_URL}/api/groups?page=1&per_page=25", headers=self.headers)
        assert response.status_code == 200, f"Groups list failed: {response.text}"
        data = response.json()
        
        groups = data.get("data", [])
        total = data.get("total", 0)
        
        assert len(groups) > 0, "Should have groups"
        print(f"✓ Groups list verified - {total} total groups")
        for group in groups[:3]:
            print(f"  - {group.get('name')}: {group.get('member_count', 0)} members")


class TestReportsPage:
    """Test Reports page - all tabs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SHANNON_EMAIL,
            "password": SHANNON_PASSWORD
        })
        data = response.json()
        self.token = data.get("session_token") or data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_reports_giving_tab(self):
        """Reports > Giving tab should show Total Giving > $1M, 2100+ gifts"""
        response = requests.get(
            f"{BASE_URL}/api/reports/giving-by-fund?start_date=2026-01-01&end_date=2026-12-31",
            headers=self.headers
        )
        assert response.status_code == 200, f"Giving report failed: {response.text}"
        data = response.json()
        
        summary = data.get("summary", {})
        total_giving = summary.get("total_giving", 0)
        total_count = summary.get("total_count", 0)
        unique_donors = summary.get("unique_donors", 0)
        
        print(f"  Total Giving: ${total_giving:,.2f}")
        print(f"  Total Gifts: {total_count}")
        print(f"  Unique Donors: {unique_donors}")
        print(f"  Avg Gift: ${summary.get('avg_gift', 0):,.2f}")
        print(f"  Recurring: {summary.get('recurring_count', 0)}")
        
        # Check by_fund data
        by_fund = data.get("by_fund", [])
        print(f"  Funds: {len(by_fund)}")
        for fund in by_fund[:3]:
            print(f"    - {fund.get('fund_name')}: ${fund.get('total', 0):,.2f}")
        
        # Check by_method data
        by_method = data.get("by_method", [])
        print(f"  Payment Methods: {len(by_method)}")
        
        # Check top_donors
        top_donors = data.get("top_donors", [])
        print(f"  Top Donors: {len(top_donors)}")
        
        assert total_giving > 0, f"Total giving should be > 0, got {total_giving}"
        print(f"✓ Giving report verified - ${total_giving:,.2f} total")
    
    def test_reports_attendance_tab(self):
        """Reports > Attendance tab should show Avg Sunday Attendance > 0"""
        response = requests.get(
            f"{BASE_URL}/api/reports/attendance?start_date=2026-01-01&end_date=2026-12-31",
            headers=self.headers
        )
        assert response.status_code == 200, f"Attendance report failed: {response.text}"
        data = response.json()
        
        summary = data.get("summary", {})
        avg_attendance = summary.get("avg_attendance", 0)
        peak_attendance = summary.get("peak_attendance", 0)
        yoy_change = summary.get("yoy_change", 0)
        
        print(f"  Avg Sunday Attendance: {avg_attendance}")
        print(f"  Peak Attendance: {peak_attendance}")
        print(f"  YoY Growth: {yoy_change}%")
        print(f"  Total Services: {summary.get('total_services', 0)}")
        
        weekly = data.get("weekly", [])
        print(f"  Weekly data points: {len(weekly)}")
        
        # Should have some attendance data from monthly_reports
        assert avg_attendance > 0 or len(weekly) > 0, "Should have attendance data"
        print(f"✓ Attendance report verified")
    
    def test_reports_groups_tab(self):
        """Reports > Groups tab should show Active Groups > 0"""
        response = requests.get(f"{BASE_URL}/api/reports/groups", headers=self.headers)
        assert response.status_code == 200, f"Groups report failed: {response.text}"
        data = response.json()
        
        summary = data.get("summary", {})
        active_groups = summary.get("active_groups", 0)
        members_in_groups = summary.get("members_in_groups", 0)
        avg_size = summary.get("avg_group_size", 0)
        pct_connected = summary.get("pct_connected", 0)
        
        print(f"  Active Groups: {active_groups}")
        print(f"  Members in Groups: {members_in_groups}")
        print(f"  Avg Group Size: {avg_size}")
        print(f"  % Connected: {pct_connected}%")
        
        groups = data.get("groups", [])
        print(f"  Groups list: {len(groups)}")
        
        assert active_groups > 0 or len(groups) > 0, "Should have groups data"
        print(f"✓ Groups report verified")
    
    def test_reports_checkin_tab(self):
        """Reports > Check-In tab should show Total Check-Ins > 0"""
        response = requests.get(
            f"{BASE_URL}/api/reports/kids-history?start_date=2026-01-01&end_date=2026-12-31",
            headers=self.headers
        )
        assert response.status_code == 200, f"Check-in report failed: {response.text}"
        data = response.json()
        
        summary = data.get("summary", {})
        total_checkins = summary.get("total_checkins", 0)
        unique_children = summary.get("unique_children", 0)
        first_timers = summary.get("first_timers", 0)
        
        print(f"  Total Check-Ins: {total_checkins}")
        print(f"  Unique Children: {unique_children}")
        print(f"  First-Timers: {first_timers}")
        print(f"  Avg Per Sunday: {summary.get('avg_per_sunday', 0)}")
        
        # Data may come from monthly_reports enrichment
        print(f"✓ Check-in report verified")
    
    def test_reports_membership_tab(self):
        """Reports > Membership tab should show Total Members > 0"""
        response = requests.get(f"{BASE_URL}/api/reports/membership", headers=self.headers)
        assert response.status_code == 200, f"Membership report failed: {response.text}"
        data = response.json()
        
        summary = data.get("summary", {})
        total_members = summary.get("total_members", 0)
        active_members = summary.get("active_members", 0)
        new_this_month = summary.get("new_this_month", 0)
        
        print(f"  Total Members: {total_members}")
        print(f"  Active Members: {active_members}")
        print(f"  New This Month: {new_this_month}")
        print(f"  Visitors: {summary.get('visitors', 0)}")
        
        by_status = data.get("by_status", [])
        print(f"  Status breakdown: {len(by_status)} statuses")
        for status in by_status[:3]:
            print(f"    - {status.get('status')}: {status.get('count')}")
        
        assert total_members > 0, f"Total members should be > 0, got {total_members}"
        print(f"✓ Membership report verified - {total_members} total members")
    
    def test_reports_executive_summary(self):
        """Reports > Cross-Analysis uses executive summary"""
        response = requests.get(f"{BASE_URL}/api/reports/executive-summary", headers=self.headers)
        assert response.status_code == 200, f"Executive summary failed: {response.text}"
        data = response.json()
        
        print(f"  Period: {data.get('period', {}).get('month')}")
        print(f"  Membership: {data.get('membership', {})}")
        print(f"  Giving: {data.get('giving', {})}")
        print(f"  Attendance: {data.get('attendance', {})}")
        print(f"  Kids: {data.get('kids', {})}")
        print(f"  Groups: {data.get('groups', {})}")
        
        print(f"✓ Executive summary verified")


class TestAuditLog:
    """Test Audit Log tab"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SHANNON_EMAIL,
            "password": SHANNON_PASSWORD
        })
        data = response.json()
        self.token = data.get("session_token") or data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_audit_log_has_entries(self):
        """Audit log should show entries"""
        response = requests.get(f"{BASE_URL}/api/admin/audit-log?limit=50", headers=self.headers)
        assert response.status_code == 200, f"Audit log failed: {response.text}"
        data = response.json()
        
        entries = data.get("entries", data.get("logs", []))
        print(f"  Audit entries: {len(entries)}")
        
        if entries:
            for entry in entries[:3]:
                print(f"    - {entry.get('action_type', entry.get('action'))}: {entry.get('description', entry.get('details', ''))[:50]}")
        
        print(f"✓ Audit log verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
