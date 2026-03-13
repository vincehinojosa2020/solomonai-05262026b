import requests
import json
import sys
from datetime import datetime

class SamsonAPITester:
    def __init__(self, base_url="https://solomon-church.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status=200, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}" if not endpoint.startswith('/api/') else f"{self.base_url}{endpoint}"
        
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    self.test_results.append({
                        "name": name,
                        "status": "PASSED",
                        "status_code": response.status_code,
                        "response_size": len(str(response_data)) if response_data else 0
                    })
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.test_results.append({
                    "name": name,
                    "status": "FAILED", 
                    "expected": expected_status,
                    "actual": response.status_code,
                    "error": response.text[:200]
                })
                return False, {}

        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED - Request Error: {str(e)}")
            self.test_results.append({
                "name": name,
                "status": "ERROR",
                "error": str(e)
            })
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "")

    def test_dashboard_endpoints(self):
        """Test all dashboard endpoints"""
        print("\n📊 TESTING DASHBOARD ENDPOINTS")
        
        success_count = 0
        
        # Dashboard stats
        success, stats = self.run_test("Dashboard Stats", "GET", "dashboard/stats")
        if success and isinstance(stats, dict):
            required_keys = ['total_members', 'active_groups', 'mtd_giving', 'ytd_giving']
            if all(key in stats for key in required_keys):
                print("   ✓ Contains required stats keys")
                success_count += 1
            else:
                print("   ⚠ Missing required stats keys")

        # Giving trend
        success, trend = self.run_test("Giving Trend", "GET", "dashboard/giving-trend")
        if success and isinstance(trend, list):
            success_count += 1

        # Attendance trend  
        success, attendance = self.run_test("Attendance Trend", "GET", "dashboard/attendance-trend")
        if success and isinstance(attendance, list):
            success_count += 1

        # Recent activity
        success, activity = self.run_test("Recent Activity", "GET", "dashboard/activity")
        if success:
            success_count += 1

        # Upcoming events
        success, events = self.run_test("Upcoming Events", "GET", "dashboard/upcoming-events")
        if success:
            success_count += 1

        return success_count == 5

    def test_people_endpoints(self):
        """Test people/members endpoints"""
        print("\n👥 TESTING PEOPLE ENDPOINTS")
        
        success_count = 0

        # Get people list
        success, people_data = self.run_test("Get People List", "GET", "people")
        if success and 'data' in people_data and isinstance(people_data['data'], list):
            print(f"   ✓ Retrieved {len(people_data['data'])} people")
            success_count += 1
            
            # Test with pagination
            success, _ = self.run_test("Get People Page 2", "GET", "people?page=2&per_page=10")
            if success:
                success_count += 1
            
            # Test with search
            success, _ = self.run_test("Search People", "GET", "people?search=John")
            if success:
                success_count += 1
            
            # Test with status filter
            success, _ = self.run_test("Filter People by Status", "GET", "people?status=member")
            if success:
                success_count += 1

            # Get individual person if people exist
            if people_data['data']:
                person_id = people_data['data'][0]['id']
                success, person = self.run_test("Get Person Details", "GET", f"people/{person_id}")
                if success:
                    success_count += 1
                
                # Test person's giving
                success, _ = self.run_test("Get Person Giving", "GET", f"people/{person_id}/giving")
                if success:
                    success_count += 1
                
                # Test person's attendance
                success, _ = self.run_test("Get Person Attendance", "GET", f"people/{person_id}/attendance")
                if success:
                    success_count += 1
                
                # Test person's groups
                success, _ = self.run_test("Get Person Groups", "GET", f"people/{person_id}/groups")
                if success:
                    success_count += 1

        # Test creating a new person
        new_person_data = {
            "first_name": "Test",
            "last_name": "Person",
            "email": f"test.person.{datetime.now().strftime('%H%M%S')}@example.com",
            "membership_status": "visitor"
        }
        success, created_person = self.run_test("Create Person", "POST", "people", 200, new_person_data)
        if success and 'id' in created_person:
            print("   ✓ Successfully created new person")
            success_count += 1
            
            # Test updating the person
            updated_data = {"first_name": "Updated", "last_name": "Person"}
            success, _ = self.run_test("Update Person", "PUT", f"people/{created_person['id']}", 200, updated_data)
            if success:
                success_count += 1

        return success_count >= 6

    def test_groups_endpoints(self):
        """Test groups endpoints"""
        print("\n👥 TESTING GROUPS ENDPOINTS")
        
        success_count = 0

        # Get groups list
        success, groups_data = self.run_test("Get Groups List", "GET", "groups")
        if success and 'data' in groups_data:
            print(f"   ✓ Retrieved {len(groups_data['data'])} groups")
            success_count += 1
            
            # Get group types
            success, _ = self.run_test("Get Group Types", "GET", "group-types")
            if success:
                success_count += 1

            # Get individual group if groups exist
            if groups_data['data']:
                group_id = groups_data['data'][0]['id']
                success, group = self.run_test("Get Group Details", "GET", f"groups/{group_id}")
                if success:
                    success_count += 1
                
                # Get group members
                success, _ = self.run_test("Get Group Members", "GET", f"groups/{group_id}/members")
                if success:
                    success_count += 1

        return success_count >= 2

    def test_giving_endpoints(self):
        """Test giving/donations endpoints"""
        print("\n💰 TESTING GIVING ENDPOINTS")
        
        success_count = 0

        # Get giving stats
        success, stats = self.run_test("Get Giving Stats", "GET", "giving/stats")
        if success and isinstance(stats, dict):
            success_count += 1

        # Get funds
        success, funds = self.run_test("Get Funds", "GET", "funds")
        if success and isinstance(funds, list):
            print(f"   ✓ Retrieved {len(funds)} funds")
            success_count += 1
            
            # Create a test donation if funds exist
            if funds:
                donation_data = {
                    "fund_id": funds[0]['id'],
                    "amount": 100.00,
                    "donation_date": datetime.now().strftime('%Y-%m-%d'),
                    "payment_method": "cash",
                    "notes": "API Test Donation"
                }
                success, donation = self.run_test("Create Donation", "POST", "donations", 200, donation_data)
                if success:
                    success_count += 1

        # Get donations list
        success, donations = self.run_test("Get Donations List", "GET", "donations")
        if success and 'data' in donations:
            print(f"   ✓ Retrieved {len(donations['data'])} donations")
            success_count += 1

        # Get batches
        success, _ = self.run_test("Get Batches", "GET", "batches")
        if success:
            success_count += 1

        return success_count >= 3

    def test_attendance_endpoints(self):
        """Test attendance/services endpoints"""
        print("\n📅 TESTING ATTENDANCE ENDPOINTS")
        
        success_count = 0

        # Get services
        success, services = self.run_test("Get Services", "GET", "services")
        if success and isinstance(services, list):
            success_count += 1
            
            # Get service types
            success, _ = self.run_test("Get Service Types", "GET", "service-types")
            if success:
                success_count += 1

        return success_count >= 1

    def test_events_endpoints(self):
        """Test events endpoints"""
        print("\n🎉 TESTING EVENTS ENDPOINTS")
        
        success_count = 0

        # Get events
        success, events = self.run_test("Get Events", "GET", "events")
        if success and isinstance(events, list):
            print(f"   ✓ Retrieved {len(events)} events")
            success_count += 1
            
            # Get individual event if events exist
            if events:
                event_id = events[0]['id']
                success, _ = self.run_test("Get Event Details", "GET", f"events/{event_id}")
                if success:
                    success_count += 1

        return success_count >= 1

    def test_communications_endpoints(self):
        """Test communications endpoints"""
        print("\n📧 TESTING COMMUNICATIONS ENDPOINTS")
        
        success_count = 0

        # Get communications
        success, _ = self.run_test("Get Communications", "GET", "communications")
        if success:
            success_count += 1

        return success_count >= 1

    def test_reports_endpoints(self):
        """Test reports endpoints"""
        print("\n📊 TESTING REPORTS ENDPOINTS")
        
        success_count = 0
        current_date = datetime.now().strftime('%Y-%m-%d')
        start_date = "2024-01-01"

        # Test giving reports
        success, _ = self.run_test("Giving by Fund Report", "GET", f"reports/giving-by-fund?start_date={start_date}&end_date={current_date}")
        if success:
            success_count += 1

        success, _ = self.run_test("Giving by Method Report", "GET", f"reports/giving-by-method?start_date={start_date}&end_date={current_date}")
        if success:
            success_count += 1

        success, _ = self.run_test("Top Donors Report", "GET", f"reports/top-donors?start_date={start_date}&end_date={current_date}")
        if success:
            success_count += 1

        success, _ = self.run_test("Membership Report", "GET", "reports/membership")
        if success:
            success_count += 1

        return success_count >= 2

    def test_search_endpoint(self):
        """Test global search"""
        print("\n🔍 TESTING SEARCH ENDPOINT")
        
        success, results = self.run_test("Global Search", "GET", "search?q=John")
        if success and isinstance(results, list):
            return True
        return False

    def test_tenant_endpoint(self):
        """Test tenant endpoint"""
        print("\n🏢 TESTING TENANT ENDPOINT")
        
        success, tenant = self.run_test("Get Tenant", "GET", "tenant")
        if success and isinstance(tenant, dict):
            required_keys = ['id', 'name', 'subdomain']
            if all(key in tenant for key in required_keys):
                print("   ✓ Contains required tenant keys")
                return True
        return False

def main():
    """Run comprehensive API tests for Samson ChMS"""
    print("🚀 Starting Samson Church Management System API Tests")
    print("=" * 60)
    
    tester = SamsonAPITester()
    
    # Track which test categories passed
    category_results = {}
    
    # Test API Root
    category_results['api_root'] = tester.test_api_root()
    
    # Test Tenant
    category_results['tenant'] = tester.test_tenant_endpoint()
    
    # Test Dashboard
    category_results['dashboard'] = tester.test_dashboard_endpoints()
    
    # Test People
    category_results['people'] = tester.test_people_endpoints()
    
    # Test Groups  
    category_results['groups'] = tester.test_groups_endpoints()
    
    # Test Giving
    category_results['giving'] = tester.test_giving_endpoints()
    
    # Test Attendance
    category_results['attendance'] = tester.test_attendance_endpoints()
    
    # Test Events
    category_results['events'] = tester.test_events_endpoints()
    
    # Test Communications
    category_results['communications'] = tester.test_communications_endpoints()
    
    # Test Reports
    category_results['reports'] = tester.test_reports_endpoints()
    
    # Test Search
    category_results['search'] = tester.test_search_endpoint()
    
    # Print final results
    print("\n" + "=" * 60)
    print("🏁 FINAL TEST RESULTS")
    print("=" * 60)
    
    passed_categories = sum(1 for passed in category_results.values() if passed)
    total_categories = len(category_results)
    
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"📋 Categories passed: {passed_categories}/{total_categories}")
    
    print("\n📈 Category Results:")
    for category, passed in category_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {category.title()}: {status}")
    
    # Success criteria: 80% of tests pass and critical endpoints work
    success_rate = (tester.tests_passed / tester.tests_run) * 100
    critical_categories = ['api_root', 'dashboard', 'people', 'giving']
    critical_passed = all(category_results.get(cat, False) for cat in critical_categories)
    
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}%")
    print(f"🔑 Critical Categories: {'✅ PASSED' if critical_passed else '❌ FAILED'}")
    
    if success_rate >= 80 and critical_passed:
        print("\n🎉 BACKEND API TESTING: SUCCESS")
        return 0
    else:
        print("\n⚠️  BACKEND API TESTING: NEEDS ATTENTION")
        return 1

if __name__ == "__main__":
    sys.exit(main())