#!/usr/bin/env python3
"""
Detailed Investigation of Production Data for Go-Live Verification
"""
import asyncio
import aiohttp
import json

BASE_URL = "https://solomon-church.preview.emergentagent.com/api"

async def investigate_data():
    """Get detailed data from key endpoints"""
    
    # Setup session
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(ssl=False)
    session = aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
        headers={
            "User-Agent": "Solomon-Church-Investigation/1.0",
            "Accept": "application/json", 
            "Content-Type": "application/json"
        }
    )
    
    try:
        # Login as member@abundant.church
        login_data = {"email": "member@abundant.church", "password": "Demo2026!"}
        async with session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
            login_result = await response.json()
            token = login_result["session_token"]
            print(f"✅ Logged in successfully")
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Investigate key endpoints with details
        endpoints_to_check = [
            ("/portal/merch/products", "merch products"),
            ("/portal/cafe/menu", "cafe items"), 
            ("/portal/kids/children", "children"),
            ("/portal/media/sermons", "videos"),
            ("/portal/courses", "courses"),
            ("/portal/prayer-requests", "prayer requests"),
            ("/portal/volunteer/opportunities", "volunteer opportunities"),
            ("/portal/announcements", "announcements"),
            ("/portal/giving/ytd", "YTD giving data"),
            ("/portal/attendance/streak", "attendance streak"),
            ("/portal/next-steps", "next steps")
        ]
        
        print("\n📊 DETAILED DATA INVESTIGATION:")
        print("=" * 70)
        
        for endpoint, description in endpoints_to_check:
            async with session.get(f"{BASE_URL}{endpoint}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        count = len(data)
                        print(f"{endpoint}: {count} {description}")
                        if count > 0 and count <= 3:
                            print(f"  Sample: {json.dumps(data[0], indent=2) if data else 'Empty'}")
                    else:
                        print(f"{endpoint}: {description}")
                        print(f"  Data: {json.dumps(data, indent=2)}")
                else:
                    print(f"{endpoint}: Error {response.status}")
                    
        # Test admin dashboard specifically
        print("\n📊 ADMIN DASHBOARD INVESTIGATION:")
        print("=" * 70)
        
        # Login as admin
        admin_login_data = {"email": "admin@abundant.church", "password": "Demo2026!"}
        async with session.post(f"{BASE_URL}/auth/login", json=admin_login_data) as response:
            admin_login_result = await response.json()
            admin_token = admin_login_result["session_token"]
            
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        async with session.get(f"{BASE_URL}/admin/dashboard", headers=admin_headers) as response:
            if response.status == 200:
                dashboard_data = await response.json()
                print("Admin Dashboard Fields:")
                for field, value in dashboard_data.items():
                    print(f"  {field}: {value}")
            else:
                print(f"Admin Dashboard Error: {response.status}")
                
    except Exception as e:
        print(f"❌ Investigation failed: {str(e)}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(investigate_data())