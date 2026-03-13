"""
PWA Module 0 Tests - Solomon AI
Tests for PWA manifest, service worker, icons, and offline page
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPWAManifest:
    """Test PWA manifest.json is served correctly"""
    
    def test_manifest_served(self):
        """Verify manifest.json is accessible"""
        response = requests.get(f"{BASE_URL}/manifest.json", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ manifest.json served with status 200")
    
    def test_manifest_is_valid_json(self):
        """Verify manifest.json is valid JSON"""
        response = requests.get(f"{BASE_URL}/manifest.json", timeout=10)
        assert response.status_code == 200
        try:
            data = response.json()
            assert isinstance(data, dict), "Manifest should be a JSON object"
            print(f"✓ manifest.json is valid JSON")
        except json.JSONDecodeError as e:
            pytest.fail(f"manifest.json is not valid JSON: {e}")
    
    def test_manifest_required_fields(self):
        """Verify manifest has all required PWA fields"""
        response = requests.get(f"{BASE_URL}/manifest.json", timeout=10)
        data = response.json()
        
        # Required fields
        assert "name" in data, "Missing 'name' field"
        assert "short_name" in data, "Missing 'short_name' field"
        assert "start_url" in data, "Missing 'start_url' field"
        assert "display" in data, "Missing 'display' field"
        assert "icons" in data, "Missing 'icons' field"
        
        # Validate display mode
        assert data["display"] == "standalone", f"Expected display 'standalone', got '{data['display']}'"
        
        print(f"✓ manifest.json has all required fields")
        print(f"  - name: {data['name']}")
        print(f"  - short_name: {data['short_name']}")
        print(f"  - start_url: {data['start_url']}")
        print(f"  - display: {data['display']}")
    
    def test_manifest_icons_array(self):
        """Verify manifest has icons with correct sizes"""
        response = requests.get(f"{BASE_URL}/manifest.json", timeout=10)
        data = response.json()
        
        icons = data.get("icons", [])
        assert len(icons) >= 5, f"Expected at least 5 icons, got {len(icons)}"
        
        # Check required sizes
        required_sizes = ["72x72", "96x96", "128x128", "192x192", "512x512"]
        found_sizes = [icon.get("sizes") for icon in icons]
        
        for size in required_sizes:
            assert size in found_sizes, f"Missing icon size {size}"
        
        print(f"✓ manifest.json has all required icon sizes: {required_sizes}")


class TestServiceWorker:
    """Test service worker sw.js is served correctly"""
    
    def test_sw_served(self):
        """Verify sw.js is accessible"""
        response = requests.get(f"{BASE_URL}/sw.js", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ sw.js served with status 200")
    
    def test_sw_is_javascript(self):
        """Verify sw.js contains valid JavaScript patterns"""
        response = requests.get(f"{BASE_URL}/sw.js", timeout=10)
        assert response.status_code == 200
        
        content = response.text
        # Check for common service worker patterns
        assert "self.addEventListener" in content, "Missing event listener pattern"
        assert "caches" in content, "Missing caches API usage"
        assert "fetch" in content or "install" in content, "Missing fetch or install handler"
        
        print(f"✓ sw.js contains valid service worker JavaScript")
        print(f"  - File size: {len(content)} bytes")


class TestPWAIcons:
    """Test PWA icons are served correctly"""
    
    def test_icon_72(self):
        """Verify 72x72 icon"""
        response = requests.get(f"{BASE_URL}/icons/icon-72.png", timeout=10)
        assert response.status_code == 200, f"icon-72.png: Expected 200, got {response.status_code}"
        assert "image" in response.headers.get("content-type", ""), "Not an image"
        print(f"✓ icon-72.png served")
    
    def test_icon_96(self):
        """Verify 96x96 icon"""
        response = requests.get(f"{BASE_URL}/icons/icon-96.png", timeout=10)
        assert response.status_code == 200, f"icon-96.png: Expected 200, got {response.status_code}"
        print(f"✓ icon-96.png served")
    
    def test_icon_128(self):
        """Verify 128x128 icon"""
        response = requests.get(f"{BASE_URL}/icons/icon-128.png", timeout=10)
        assert response.status_code == 200, f"icon-128.png: Expected 200, got {response.status_code}"
        print(f"✓ icon-128.png served")
    
    def test_icon_192(self):
        """Verify 192x192 icon"""
        response = requests.get(f"{BASE_URL}/icons/icon-192.png", timeout=10)
        assert response.status_code == 200, f"icon-192.png: Expected 200, got {response.status_code}"
        print(f"✓ icon-192.png served")
    
    def test_icon_512(self):
        """Verify 512x512 icon"""
        response = requests.get(f"{BASE_URL}/icons/icon-512.png", timeout=10)
        assert response.status_code == 200, f"icon-512.png: Expected 200, got {response.status_code}"
        print(f"✓ icon-512.png served")
    
    def test_apple_touch_icon(self):
        """Verify apple-touch-icon.png"""
        response = requests.get(f"{BASE_URL}/apple-touch-icon.png", timeout=10)
        assert response.status_code == 200, f"apple-touch-icon.png: Expected 200, got {response.status_code}"
        print(f"✓ apple-touch-icon.png served")
    
    def test_favicon_32(self):
        """Verify favicon-32x32.png"""
        response = requests.get(f"{BASE_URL}/favicon-32x32.png", timeout=10)
        assert response.status_code == 200, f"favicon-32x32.png: Expected 200, got {response.status_code}"
        print(f"✓ favicon-32x32.png served")
    
    def test_favicon_16(self):
        """Verify favicon-16x16.png"""
        response = requests.get(f"{BASE_URL}/favicon-16x16.png", timeout=10)
        assert response.status_code == 200, f"favicon-16x16.png: Expected 200, got {response.status_code}"
        print(f"✓ favicon-16x16.png served")


class TestOfflinePage:
    """Test offline fallback page"""
    
    def test_offline_page_served(self):
        """Verify offline.html is accessible"""
        response = requests.get(f"{BASE_URL}/offline.html", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ offline.html served with status 200")
    
    def test_offline_page_content(self):
        """Verify offline.html has correct content"""
        response = requests.get(f"{BASE_URL}/offline.html", timeout=10)
        assert response.status_code == 200
        
        content = response.text
        # Check for expected content
        assert "You're Offline" in content or "Offline" in content, "Missing offline message"
        assert "Try Again" in content, "Missing retry button text"
        
        print(f"✓ offline.html has correct content (You're Offline, Try Again)")


class TestIndexHTMLPWATags:
    """Test index.html has correct PWA meta tags"""
    
    def test_index_served(self):
        """Verify index.html is accessible"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ index.html (/) served with status 200")
    
    def test_manifest_link(self):
        """Verify manifest link tag in index.html"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        content = response.text
        
        assert 'rel="manifest"' in content, "Missing manifest link rel"
        assert 'href="/manifest.json"' in content or "href='/manifest.json'" in content, "Missing manifest href"
        print(f"✓ index.html has manifest link")
    
    def test_apple_web_app_tags(self):
        """Verify Apple web app meta tags"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        content = response.text
        
        assert "apple-mobile-web-app-capable" in content, "Missing apple-mobile-web-app-capable"
        assert "apple-mobile-web-app-title" in content or "apple-mobile-web-app-status-bar-style" in content, "Missing Apple PWA meta tags"
        print(f"✓ index.html has Apple web app meta tags")
    
    def test_sw_registration_script(self):
        """Verify service worker registration script"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        content = response.text
        
        assert "serviceWorker" in content, "Missing serviceWorker reference"
        assert "register" in content and "sw.js" in content, "Missing SW registration"
        print(f"✓ index.html has service worker registration script")
    
    def test_apple_touch_icon_link(self):
        """Verify apple-touch-icon link"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        content = response.text
        
        assert "apple-touch-icon" in content, "Missing apple-touch-icon link"
        print(f"✓ index.html has apple-touch-icon link")


class TestLoginFlow:
    """Test login flow still works"""
    
    def test_login_endpoint(self):
        """Verify login endpoint works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "member@abundant.church",
                "password": "Demo2026!"
            },
            timeout=10
        )
        assert response.status_code == 200, f"Login failed with status {response.status_code}"
        
        data = response.json()
        assert "user" in data or "email" in data, "Missing user data in response"
        print(f"✓ Login endpoint works - member logged in successfully")
    
    def test_admin_login(self):
        """Verify admin login works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "admin@abundant.church",
                "password": "Demo2026!"
            },
            timeout=10
        )
        assert response.status_code == 200, f"Admin login failed with status {response.status_code}"
        print(f"✓ Admin login works")
