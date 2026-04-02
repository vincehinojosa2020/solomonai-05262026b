"""
Test Platform Revenue API - Iteration 74
Tests the Godmode Revenue Dashboard endpoint for Solomon AI processing fees
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PLATFORM_ADMIN_EMAIL = "admin@solomonai.us"
PLATFORM_ADMIN_PASSWORD = "Demo2026!"
CHURCH_ADMIN_EMAIL = "shannonnieman1030@gmail.com"
CHURCH_ADMIN_PASSWORD = "Demo2026!"


class TestPlatformRevenue:
    """Tests for GET /api/platform/revenue endpoint"""
    
    @classmethod
    def setup_class(cls):
        """Setup test session once for all tests"""
        cls.session = requests.Session()
        cls.session.headers.update({"Content-Type": "application/json"})
        cls.platform_admin_token = None
        cls.church_admin_token = None
    
    def get_platform_admin_session(self):
        """Get session with platform admin auth"""
        if not self.__class__.platform_admin_token:
            session = requests.Session()
            session.headers.update({"Content-Type": "application/json"})
            response = session.post(f"{BASE_URL}/api/auth/login", json={
                "email": PLATFORM_ADMIN_EMAIL,
                "password": PLATFORM_ADMIN_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                self.__class__.platform_admin_token = data.get("session_token")
        
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.__class__.platform_admin_token}"
        })
        return session
    
    def get_church_admin_session(self):
        """Get session with church admin auth"""
        if not self.__class__.church_admin_token:
            session = requests.Session()
            session.headers.update({"Content-Type": "application/json"})
            response = session.post(f"{BASE_URL}/api/auth/login", json={
                "email": CHURCH_ADMIN_EMAIL,
                "password": CHURCH_ADMIN_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                self.__class__.church_admin_token = data.get("session_token")
        
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.__class__.church_admin_token}"
        })
        return session
    
    def login(self, email, password):
        """Helper to login and get session token"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            data = response.json()
            token = data.get("session_token")
            if token:
                self.session = session
                self.session.headers.update({"Authorization": f"Bearer {token}"})
            return data
        return None
    
    def test_revenue_endpoint_requires_auth(self):
        """Test that revenue endpoint returns 401 without authentication"""
        # Clear any existing auth
        clean_session = requests.Session()
        clean_session.headers.update({"Content-Type": "application/json"})
        
        response = clean_session.get(f"{BASE_URL}/api/platform/revenue")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Revenue endpoint requires authentication (401)")
    
    def test_revenue_endpoint_requires_platform_admin(self):
        """Test that revenue endpoint returns 403 for non-platform-admin users"""
        session = self.get_church_admin_session()
        response = session.get(f"{BASE_URL}/api/platform/revenue")
        assert response.status_code == 403, f"Expected 403 for church admin, got {response.status_code}"
        print("PASS: Revenue endpoint returns 403 for non-platform-admin users")
    
    def test_revenue_endpoint_success_for_platform_admin(self):
        """Test that revenue endpoint returns 200 with data for platform admin"""
        session = self.get_platform_admin_session()
        response = session.get(f"{BASE_URL}/api/platform/revenue")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "summary" in data, "Response missing 'summary' field"
        assert "by_church" in data, "Response missing 'by_church' field"
        assert "by_year" in data, "Response missing 'by_year' field"
        assert "by_church_year" in data, "Response missing 'by_church_year' field"
        assert "monthly_trend" in data, "Response missing 'monthly_trend' field"
        
        print("PASS: Revenue endpoint returns 200 with correct structure for platform admin")
    
    def test_revenue_summary_fields(self):
        """Test that revenue summary contains expected fields"""
        session = self.get_platform_admin_session()
        response = session.get(f"{BASE_URL}/api/platform/revenue")
        assert response.status_code == 200
        
        data = response.json()
        summary = data.get("summary", {})
        
        # Check required summary fields
        assert "total_processing_volume" in summary, "Missing total_processing_volume"
        assert "total_fees_earned" in summary, "Missing total_fees_earned"
        assert "total_transactions" in summary, "Missing total_transactions"
        assert "active_churches" in summary, "Missing active_churches"
        assert "fee_rate" in summary, "Missing fee_rate"
        
        # Verify fee rate format (2.2% + $0.22)
        assert "2.2%" in summary["fee_rate"], f"Fee rate should contain 2.2%, got {summary['fee_rate']}"
        assert "$0.22" in summary["fee_rate"], f"Fee rate should contain $0.22, got {summary['fee_rate']}"
        
        print(f"PASS: Revenue summary fields correct - Volume: ${summary['total_processing_volume']:,.2f}, Fees: ${summary['total_fees_earned']:,.2f}")
    
    def test_revenue_volume_exceeds_threshold(self):
        """Test that total processing volume is at least $82M (seeded data)"""
        session = self.get_platform_admin_session()
        response = session.get(f"{BASE_URL}/api/platform/revenue")
        assert response.status_code == 200
        
        data = response.json()
        total_volume = data["summary"]["total_processing_volume"]
        
        # Should have at least $82M in processing volume from seeded data
        assert total_volume >= 82_000_000, f"Expected at least $82M volume, got ${total_volume:,.2f}"
        print(f"PASS: Total processing volume ${total_volume:,.2f} exceeds $82M threshold")
    
    def test_revenue_fees_exceed_threshold(self):
        """Test that total fees earned is at least $1.1M"""
        session = self.get_platform_admin_session()
        response = session.get(f"{BASE_URL}/api/platform/revenue")
        assert response.status_code == 200
        
        data = response.json()
        total_fees = data["summary"]["total_fees_earned"]
        
        # Should have at least $1.1M in fees (2.2% + $0.22 on $82M+)
        assert total_fees >= 1_100_000, f"Expected at least $1.1M fees, got ${total_fees:,.2f}"
        print(f"PASS: Total fees earned ${total_fees:,.2f} exceeds $1.1M threshold")
    
    def test_revenue_has_8_churches(self):
        """Test that revenue data includes 8 churches"""
        session = self.get_platform_admin_session()
        response = session.get(f"{BASE_URL}/api/platform/revenue")
        assert response.status_code == 200
        
        data = response.json()
        active_churches = data["summary"]["active_churches"]
        by_church = data.get("by_church", [])
        
        assert active_churches >= 8, f"Expected at least 8 churches, got {active_churches}"
        assert len(by_church) >= 8, f"Expected at least 8 churches in by_church, got {len(by_church)}"
        print(f"PASS: Revenue data includes {active_churches} churches")
    
    def test_revenue_by_year_has_3_years(self):
        """Test that revenue by year includes 2023, 2024, 2025"""
        session = self.get_platform_admin_session()
        response = session.get(f"{BASE_URL}/api/platform/revenue")
        assert response.status_code == 200
        
        data = response.json()
        by_year = data.get("by_year", [])
        years = [y["year"] for y in by_year]
        
        assert "2023" in years, "Missing 2023 in by_year data"
        assert "2024" in years, "Missing 2024 in by_year data"
        assert "2025" in years, "Missing 2025 in by_year data"
        
        print(f"PASS: Revenue by year includes years: {years}")
    
    def test_revenue_by_church_structure(self):
        """Test that each church in by_church has required fields"""
        session = self.get_platform_admin_session()
        response = session.get(f"{BASE_URL}/api/platform/revenue")
        assert response.status_code == 200
        
        data = response.json()
        by_church = data.get("by_church", [])
        
        assert len(by_church) > 0, "by_church should not be empty"
        
        for church in by_church:
            assert "tenant_id" in church, "Church missing tenant_id"
            assert "name" in church, "Church missing name"
            assert "total_volume" in church, "Church missing total_volume"
            assert "total_fees" in church, "Church missing total_fees"
            assert "txn_count" in church, "Church missing txn_count"
        
        print(f"PASS: All {len(by_church)} churches have correct structure")
    
    def test_revenue_by_church_year_structure(self):
        """Test that by_church_year has yearly breakdown for each church"""
        session = self.get_platform_admin_session()
        response = session.get(f"{BASE_URL}/api/platform/revenue")
        assert response.status_code == 200
        
        data = response.json()
        by_church_year = data.get("by_church_year", {})
        
        assert len(by_church_year) > 0, "by_church_year should not be empty"
        
        for tenant_id, church_data in by_church_year.items():
            assert "name" in church_data, f"Church {tenant_id} missing name"
            assert "years" in church_data, f"Church {tenant_id} missing years"
            
            years = church_data["years"]
            for year, year_data in years.items():
                assert "volume" in year_data, f"Year {year} missing volume"
                assert "fees" in year_data, f"Year {year} missing fees"
                assert "txn_count" in year_data, f"Year {year} missing txn_count"
        
        print(f"PASS: by_church_year has correct structure for {len(by_church_year)} churches")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
