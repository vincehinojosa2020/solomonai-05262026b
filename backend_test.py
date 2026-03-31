#!/usr/bin/env python3
"""
Backend Go-Live Verification Tests for Solomon Church Management System
Testing production environment: https://church-crud-verified.preview.emergentagent.com/api
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
import sys

# Production base URL
BASE_URL = "https://church-crud-verified.preview.emergentagent.com/api"

# Test credentials provided in review request
TEST_ACCOUNTS = [
    {"email": "member@abundant.church", "password": "Demo2026!", "role": "member"},
    {"email": "member@cristoviene.church", "password": "Demo2026!", "role": "member"},
    {"email": "admin@abundant.church", "password": "Demo2026!", "role": "admin"},
    {"email": "admin@cristoviene.church", "password": "Demo2026!", "role": "admin"},
    {"email": "admin@pottershouse.church", "password": "Demo2026!", "role": "admin"},
    {"email": "admin@solomon.ai", "password": "Demo2026!", "role": "platform_admin"},
]

# Expected data counts for member@abundant.church
EXPECTED_DATA_COUNTS = {
    "events": 50,
    "groups": 100,
    "ytd_total": 500,
    "merch_products": 5,
    "cafe_items": 5,
    "children": 1,
    "current_streak": 1,  # minimum
    "videos": 3,
    "courses": 2,  # minimum
    "requests": 2,  # minimum
    "opportunities": 5,  # minimum
    "announcements": 3,  # minimum
}

# Admin dashboard required fields
REQUIRED_DASHBOARD_FIELDS = [
    "total_members", "active_members", "new_this_week", "last_sunday_attendance",
    "mtd_giving", "ytd_giving", "recurring_donors", "cafe_orders_this_week",
    "merch_sales_this_week", "event_signups_this_month", "small_groups_count",
    "at_risk_members"
]

class ProductionTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.failed_tests = []
        self.successful_tests = []
        
    async def setup(self):
        """Setup aiohttp session with proper headers"""
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                "User-Agent": "Solomon-Church-Test-Client/1.0",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )
        
    async def cleanup(self):
        """Cleanup session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, passed: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "passed": passed
        }
        self.test_results.append(result)
        if passed:
            self.successful_tests.append(result)
        else:
            self.failed_tests.append(result)
        print(f"{status}: {test_name} - {details}")
        
    async def login_user(self, email: str, password: str) -> Optional[Dict]:
        """Test login for a user account"""
        try:
            login_data = {"email": email, "password": password}
            async with self.session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.log_test(f"Login {email}", False, f"Status {response.status}: {error_text}")
                    return None
                    
                data = await response.json()
                
                # Check for required fields
                required_fields = ["session_token", "token", "access_token"]
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_test(f"Login {email}", False, f"Missing fields: {missing_fields}")
                    return None
                    
                # Verify all three tokens have same value
                token_values = [data.get(field) for field in required_fields]
                if not all(token == token_values[0] for token in token_values):
                    self.log_test(f"Login {email}", False, "Token values are not identical")
                    return None
                    
                self.log_test(f"Login {email}", True, "Login successful with matching tokens")
                return data
                
        except Exception as e:
            self.log_test(f"Login {email}", False, f"Exception: {str(e)}")
            return None
            
    async def test_endpoint_with_auth(self, endpoint: str, token: str, expected_data: Any = None, 
                                      check_count: bool = False, min_count: int = 0) -> Dict:
        """Test authenticated endpoint"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with self.session.get(f"{BASE_URL}{endpoint}", headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {"success": False, "error": f"Status {response.status}: {error_text}"}
                    
                data = await response.json()
                result = {"success": True, "data": data}
                
                # Check specific data expectations
                if expected_data is not None:
                    if isinstance(expected_data, dict):
                        for key, expected_value in expected_data.items():
                            if key not in data:
                                result["success"] = False
                                result["error"] = f"Missing field: {key}"
                                break
                            if data[key] != expected_value:
                                result["success"] = False
                                result["error"] = f"{key}: expected {expected_value}, got {data[key]}"
                                break
                                
                if check_count and isinstance(data, list):
                    count = len(data)
                    if count < min_count:
                        result["success"] = False
                        result["error"] = f"Expected minimum {min_count} items, got {count}"
                    else:
                        result["count"] = count
                        
                return result
                
        except Exception as e:
            return {"success": False, "error": f"Exception: {str(e)}"}
            
    async def test_cors_preflight(self, endpoint: str) -> bool:
        """Test CORS preflight request"""
        try:
            headers = {
                "Origin": "https://test-domain.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type"
            }
            
            async with self.session.options(f"{BASE_URL}{endpoint}", headers=headers) as response:
                cors_headers = {
                    "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                    "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                    "access-control-allow-headers": response.headers.get("access-control-allow-headers")
                }
                
                # Check CORS headers
                checks = []
                checks.append(("allow-origin", "*" in str(cors_headers.get("access-control-allow-origin", ""))))
                checks.append(("allow-methods", all(method in str(cors_headers.get("access-control-allow-methods", "")).upper() 
                              for method in ["GET", "POST", "PUT", "DELETE", "OPTIONS"])))
                checks.append(("allow-headers", "*" in str(cors_headers.get("access-control-allow-headers", ""))))
                
                all_passed = all(check[1] for check in checks)
                failed_checks = [check[0] for check in checks if not check[1]]
                
                details = f"CORS headers: {cors_headers}"
                if failed_checks:
                    details += f" | Failed: {failed_checks}"
                    
                self.log_test("CORS Preflight", all_passed, details)
                return all_passed
                
        except Exception as e:
            self.log_test("CORS Preflight", False, f"Exception: {str(e)}")
            return False
            
    async def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Go-Live Verification Tests...")
        print(f"Testing: {BASE_URL}")
        print("=" * 80)
        
        # Step 1: Test login for all accounts
        print("\n📋 STEP 1: Testing Login for All Accounts")
        login_tokens = {}
        
        for account in TEST_ACCOUNTS:
            login_result = await self.login_user(account["email"], account["password"])
            if login_result:
                login_tokens[account["email"]] = {
                    "token": login_result["session_token"],
                    "role": account["role"]
                }
                
        if not login_tokens:
            print("❌ All logins failed - cannot proceed with endpoint tests")
            return
            
        # Step 2: Test member@abundant.church specific endpoints
        print("\n📋 STEP 2: Testing member@abundant.church Portal Endpoints")
        member_email = "member@abundant.church"
        
        if member_email in login_tokens:
            member_token = login_tokens[member_email]["token"]
            
            # Test each portal endpoint with expected data
            endpoint_tests = [
                ("/portal/events", "events", 50),
                ("/portal/groups", "groups", 100), 
                ("/portal/merch/products", "merch_products", 5),
                ("/portal/cafe/menu", "cafe_items", 5),
                ("/portal/kids/children", "children", 1),
                ("/portal/media/sermons", "videos", 3),
                ("/portal/courses", "courses", 2),
                ("/portal/prayer-requests", "requests", 2),
                ("/portal/volunteer/opportunities", "opportunities", 5),
                ("/portal/announcements", "announcements", 3),
            ]
            
            for endpoint, data_type, min_count in endpoint_tests:
                result = await self.test_endpoint_with_auth(endpoint, member_token, check_count=True, min_count=min_count)
                test_name = f"Member Portal: {endpoint}"
                if result["success"]:
                    actual_count = result.get("count", 0)
                    self.log_test(test_name, True, f"Got {actual_count} {data_type} (expected min {min_count})")
                else:
                    self.log_test(test_name, False, result["error"])
                    
            # Test specific data structure endpoints
            ytd_result = await self.test_endpoint_with_auth("/portal/giving/ytd", member_token)
            if ytd_result["success"] and "ytd_total" in ytd_result["data"]:
                ytd_value = ytd_result["data"]["ytd_total"]
                expected_ytd = EXPECTED_DATA_COUNTS["ytd_total"]
                self.log_test("Member Portal: /portal/giving/ytd", ytd_value >= expected_ytd, 
                             f"YTD total: {ytd_value} (expected min {expected_ytd})")
            else:
                self.log_test("Member Portal: /portal/giving/ytd", False, 
                             ytd_result.get("error", "Missing ytd_total field"))
                             
            streak_result = await self.test_endpoint_with_auth("/portal/attendance/streak", member_token)
            if streak_result["success"] and "current_streak" in streak_result["data"]:
                streak_value = streak_result["data"]["current_streak"]
                expected_streak = EXPECTED_DATA_COUNTS["current_streak"]
                self.log_test("Member Portal: /portal/attendance/streak", streak_value >= expected_streak,
                             f"Current streak: {streak_value} (expected min {expected_streak})")
            else:
                self.log_test("Member Portal: /portal/attendance/streak", False,
                             streak_result.get("error", "Missing current_streak field"))
                             
            next_steps_result = await self.test_endpoint_with_auth("/portal/next-steps", member_token)
            if next_steps_result["success"]:
                data = next_steps_result["data"]
                has_steps = "steps" in data or "next_steps" in data
                has_percentage = "percentage_complete" in data
                self.log_test("Member Portal: /portal/next-steps", has_steps and has_percentage,
                             f"Has steps: {has_steps}, Has percentage: {has_percentage}")
            else:
                self.log_test("Member Portal: /portal/next-steps", False, next_steps_result["error"])
        else:
            print(f"⚠️ Cannot test member endpoints - {member_email} login failed")
            
        # Step 3: Test admin access
        print("\n📋 STEP 3: Testing Admin Access")
        admin_email = "admin@abundant.church"
        
        if admin_email in login_tokens:
            admin_token = login_tokens[admin_email]["token"]
            
            admin_endpoints = [
                "/portal/merch/products",
                "/portal/cafe/menu", 
                "/portal/kids/children",
                "/portal/media/sermons"
            ]
            
            for endpoint in admin_endpoints:
                result = await self.test_endpoint_with_auth(endpoint, admin_token)
                self.log_test(f"Admin Access: {endpoint}", result["success"], 
                             result.get("error", "200 OK"))
        else:
            print(f"⚠️ Cannot test admin endpoints - {admin_email} login failed")
            
        # Step 4: Test admin dashboard
        print("\n📋 STEP 4: Testing Admin Dashboard")
        if admin_email in login_tokens:
            admin_token = login_tokens[admin_email]["token"]
            
            dashboard_result = await self.test_endpoint_with_auth("/admin/dashboard", admin_token)
            if dashboard_result["success"]:
                data = dashboard_result["data"]
                missing_fields = [field for field in REQUIRED_DASHBOARD_FIELDS if field not in data]
                if missing_fields:
                    self.log_test("Admin Dashboard", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Admin Dashboard", True, "All required fields present")
            else:
                self.log_test("Admin Dashboard", False, dashboard_result["error"])
        else:
            print(f"⚠️ Cannot test admin dashboard - {admin_email} login failed")
            
        # Step 5: Test CORS preflight
        print("\n📋 STEP 5: Testing CORS Configuration")
        await self.test_cors_preflight("/portal/merch/products")
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len(self.successful_tests)
        failed_tests = len(self.failed_tests)
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  • {test['test']}: {test['details']}")
                
        if self.successful_tests:
            print(f"\n✅ SUCCESSFUL TESTS ({len(self.successful_tests)}):")
            for test in self.successful_tests:
                print(f"  • {test['test']}")
                
        print("\n" + "=" * 80)
        
        # Return exit code
        return 0 if failed_tests == 0 else 1

async def main():
    """Main test runner"""
    tester = ProductionTester()
    
    try:
        await tester.setup()
        exit_code = await tester.run_all_tests()
        return exit_code
    except Exception as e:
        print(f"❌ Test runner failed: {str(e)}")
        return 1
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)