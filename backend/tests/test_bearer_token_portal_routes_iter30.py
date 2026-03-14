"""
Test Bearer Token Direct API Calls for Portal Routes - Iteration 30

This test verifies that the pre-go-live bug is fixed:
- 4 portal routes should work with Bearer token direct API calls
- Token aliases (session_token, token, access_token) should persist in login response

Endpoints tested:
- POST /api/auth/login - token aliases
- GET /api/portal/merch/products - Bearer token auth
- GET /api/portal/cafe/menu - Bearer token auth
- GET /api/portal/kids/children - Bearer token auth
- GET /api/portal/media/sermons - Bearer token auth

Role coverage:
- member@abundant.church (role=member)
- admin@abundant.church (role=church_admin)
- admin@solomon.ai (role=platform_admin)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MEMBER_CREDS = {"email": "member@abundant.church", "password": "Demo2026!"}
ADMIN_CREDS = {"email": "admin@abundant.church", "password": "Demo2026!"}
PLATFORM_ADMIN_CREDS = {"email": "admin@solomon.ai", "password": "Demo2026!"}


class TestLoginTokenAliases:
    """Verify that login response includes all 3 token aliases"""
    
    def test_member_login_returns_all_token_aliases(self):
        """POST /api/auth/login for member should return session_token, token, and access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=MEMBER_CREDS)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        
        # Verify all 3 token aliases are present
        assert "session_token" in data, "Missing session_token in login response"
        assert "token" in data, "Missing token alias in login response"
        assert "access_token" in data, "Missing access_token alias in login response"
        
        # Verify they all contain the same value
        assert data["session_token"] == data["token"], "token should equal session_token"
        assert data["session_token"] == data["access_token"], "access_token should equal session_token"
        
        # Verify token format
        assert data["session_token"].startswith("sess_"), "Token should start with sess_"
        
        print(f"✓ Member login returns all token aliases: session_token={data['session_token'][:20]}...")

    def test_admin_login_returns_all_token_aliases(self):
        """POST /api/auth/login for admin should return session_token, token, and access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        
        # Verify all 3 token aliases are present
        assert "session_token" in data, "Missing session_token in login response"
        assert "token" in data, "Missing token alias in login response"
        assert "access_token" in data, "Missing access_token alias in login response"
        
        # Verify they all contain the same value
        assert data["session_token"] == data["token"], "token should equal session_token"
        assert data["session_token"] == data["access_token"], "access_token should equal session_token"
        
        print(f"✓ Admin login returns all token aliases: session_token={data['session_token'][:20]}...")

    def test_platform_admin_login_returns_all_token_aliases(self):
        """POST /api/auth/login for platform admin should return session_token, token, and access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN_CREDS)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        
        # Verify all 3 token aliases are present
        assert "session_token" in data, "Missing session_token in login response"
        assert "token" in data, "Missing token alias in login response"
        assert "access_token" in data, "Missing access_token alias in login response"
        
        # Verify they all contain the same value
        assert data["session_token"] == data["token"], "token should equal session_token"
        assert data["session_token"] == data["access_token"], "access_token should equal session_token"
        
        print(f"✓ Platform admin login returns all token aliases: session_token={data['session_token'][:20]}...")


@pytest.fixture(scope="class")
def member_token():
    """Get Bearer token for member account"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=MEMBER_CREDS)
    assert response.status_code == 200, f"Member login failed: {response.text}"
    return response.json()["session_token"]


@pytest.fixture(scope="class")
def admin_token():
    """Get Bearer token for admin account"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["session_token"]


@pytest.fixture(scope="class")
def platform_admin_token():
    """Get Bearer token for platform admin account"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=PLATFORM_ADMIN_CREDS)
    assert response.status_code == 200, f"Platform admin login failed: {response.text}"
    return response.json()["session_token"]


class TestMerchProductsWithBearerToken:
    """Test GET /api/portal/merch/products with Bearer token"""
    
    def test_member_can_access_merch_products(self, member_token):
        """Member should be able to access merch products with Bearer token"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/merch/products", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "products" in data, "Response should contain products array"
        assert isinstance(data["products"], list), "products should be a list"
        
        print(f"✓ Member access to merch/products: {len(data['products'])} products returned")
    
    def test_admin_can_access_merch_products(self, admin_token):
        """Admin should be able to access merch products with Bearer token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/merch/products", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "products" in data, "Response should contain products array"
        assert isinstance(data["products"], list), "products should be a list"
        
        print(f"✓ Admin access to merch/products: {len(data['products'])} products returned")
    
    def test_platform_admin_can_access_merch_products(self, platform_admin_token):
        """Platform admin should be able to access merch products with Bearer token"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/merch/products", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "products" in data, "Response should contain products array"
        assert isinstance(data["products"], list), "products should be a list"
        
        print(f"✓ Platform admin access to merch/products: {len(data['products'])} products returned")

    def test_unauthorized_access_returns_401(self):
        """Request without token should return 401"""
        response = requests.get(f"{BASE_URL}/api/portal/merch/products")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthorized access to merch/products correctly returns 401")


class TestCafeMenuWithBearerToken:
    """Test GET /api/portal/cafe/menu with Bearer token"""
    
    def test_member_can_access_cafe_menu(self, member_token):
        """Member should be able to access cafe menu with Bearer token"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/cafe/menu", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should contain items array"
        assert isinstance(data["items"], list), "items should be a list"
        
        print(f"✓ Member access to cafe/menu: {len(data['items'])} items returned")
    
    def test_admin_can_access_cafe_menu(self, admin_token):
        """Admin should be able to access cafe menu with Bearer token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/cafe/menu", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should contain items array"
        assert isinstance(data["items"], list), "items should be a list"
        
        print(f"✓ Admin access to cafe/menu: {len(data['items'])} items returned")
    
    def test_platform_admin_can_access_cafe_menu(self, platform_admin_token):
        """Platform admin should be able to access cafe menu with Bearer token"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/cafe/menu", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should contain items array"
        assert isinstance(data["items"], list), "items should be a list"
        
        print(f"✓ Platform admin access to cafe/menu: {len(data['items'])} items returned")

    def test_unauthorized_access_returns_401(self):
        """Request without token should return 401"""
        response = requests.get(f"{BASE_URL}/api/portal/cafe/menu")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthorized access to cafe/menu correctly returns 401")


class TestKidsChildrenWithBearerToken:
    """Test GET /api/portal/kids/children with Bearer token"""
    
    def test_member_can_access_kids_children(self, member_token):
        """Member should be able to access kids/children with Bearer token"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/kids/children", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "children" in data, "Response should contain children array"
        assert isinstance(data["children"], list), "children should be a list"
        
        print(f"✓ Member access to kids/children: {len(data['children'])} children returned")
    
    def test_admin_can_access_kids_children(self, admin_token):
        """Admin should be able to access kids/children with Bearer token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/kids/children", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "children" in data, "Response should contain children array"
        assert isinstance(data["children"], list), "children should be a list"
        
        print(f"✓ Admin access to kids/children: {len(data['children'])} children returned")
    
    def test_platform_admin_can_access_kids_children(self, platform_admin_token):
        """Platform admin should be able to access kids/children with Bearer token"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/kids/children", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "children" in data, "Response should contain children array"
        assert isinstance(data["children"], list), "children should be a list"
        
        print(f"✓ Platform admin access to kids/children: {len(data['children'])} children returned")

    def test_unauthorized_access_returns_401(self):
        """Request without token should return 401"""
        response = requests.get(f"{BASE_URL}/api/portal/kids/children")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthorized access to kids/children correctly returns 401")


class TestMediaSermonsWithBearerToken:
    """Test GET /api/portal/media/sermons with Bearer token"""
    
    def test_member_can_access_media_sermons(self, member_token):
        """Member should be able to access media/sermons with Bearer token"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/media/sermons", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "videos" in data, "Response should contain videos array"
        assert isinstance(data["videos"], list), "videos should be a list"
        
        print(f"✓ Member access to media/sermons: {len(data['videos'])} videos returned")
    
    def test_admin_can_access_media_sermons(self, admin_token):
        """Admin should be able to access media/sermons with Bearer token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/media/sermons", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "videos" in data, "Response should contain videos array"
        assert isinstance(data["videos"], list), "videos should be a list"
        
        print(f"✓ Admin access to media/sermons: {len(data['videos'])} videos returned")
    
    def test_platform_admin_can_access_media_sermons(self, platform_admin_token):
        """Platform admin should be able to access media/sermons with Bearer token"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/portal/media/sermons", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "videos" in data, "Response should contain videos array"
        assert isinstance(data["videos"], list), "videos should be a list"
        
        print(f"✓ Platform admin access to media/sermons: {len(data['videos'])} videos returned")

    def test_unauthorized_access_returns_401(self):
        """Request without token should return 401"""
        response = requests.get(f"{BASE_URL}/api/portal/media/sermons")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthorized access to media/sermons correctly returns 401")


class TestUsingTokenAlias:
    """Test that using 'token' field from login response works as Bearer token"""
    
    def test_can_use_token_alias_for_auth(self):
        """Login, extract 'token' field, and use it for API call"""
        # Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=MEMBER_CREDS)
        assert login_response.status_code == 200
        
        # Use the 'token' alias (not session_token)
        token = login_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make API call
        response = requests.get(f"{BASE_URL}/api/portal/merch/products", headers=headers)
        assert response.status_code == 200, f"Using 'token' alias failed: {response.text}"
        
        print("✓ 'token' alias from login response works for Bearer auth")

    def test_can_use_access_token_alias_for_auth(self):
        """Login, extract 'access_token' field, and use it for API call"""
        # Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=MEMBER_CREDS)
        assert login_response.status_code == 200
        
        # Use the 'access_token' alias
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Make API call
        response = requests.get(f"{BASE_URL}/api/portal/cafe/menu", headers=headers)
        assert response.status_code == 200, f"Using 'access_token' alias failed: {response.text}"
        
        print("✓ 'access_token' alias from login response works for Bearer auth")


class TestAuthMeWithBearerToken:
    """Test GET /api/auth/me works with Bearer token"""
    
    def test_auth_me_with_bearer_token(self, member_token):
        """GET /api/auth/me should work with Bearer token"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "email" in data, "Response should contain email"
        assert data["email"] == MEMBER_CREDS["email"], "Email should match logged in user"
        
        print(f"✓ /api/auth/me works with Bearer token: user={data['email']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
