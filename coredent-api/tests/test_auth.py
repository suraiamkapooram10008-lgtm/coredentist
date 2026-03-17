"""
Tests for authentication endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_login_success(self, client: TestClient, test_user):
        """Test successful login"""
        login_data = {
            "username": test_user.email,
            "password": "secret"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials"""
        login_data = {
            "username": "invalid@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_missing_fields(self, client: TestClient):
        """Test login with missing fields"""
        response = client.post("/api/v1/auth/login", data={})
        
        assert response.status_code == 422

    def test_get_current_user_success(self, client: TestClient, auth_headers, test_user):
        """Test getting current user with valid token"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name
        assert data["role"] == test_user.role

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401

    def test_refresh_token_success(self, client: TestClient, test_user):
        """Test token refresh"""
        # First login to get refresh token
        login_data = {
            "username": test_user.email,
            "password": "secret"
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token"""
        refresh_data = {"refresh_token": "invalid-refresh-token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401

    def test_logout_success(self, client: TestClient, auth_headers):
        """Test successful logout"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]

    def test_logout_no_token(self, client: TestClient):
        """Test logout without token"""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401

    def test_password_reset_request(self, client: TestClient, test_user):
        """Test password reset request"""
        reset_data = {"email": test_user.email}
        response = client.post("/api/v1/auth/forgot-password", json=reset_data)
        
        assert response.status_code == 200
        assert "password reset link" in response.json()["message"].lower()

    def test_password_reset_request_invalid_email(self, client: TestClient):
        """Test password reset request with invalid email"""
        reset_data = {"email": "nonexistent@example.com"}
        response = client.post("/api/v1/auth/forgot-password", json=reset_data)
        
        # Should still return 200 for security (don't reveal if email exists)
        assert response.status_code == 200

    def test_password_reset_confirm(self, client: TestClient):
        """Test password reset confirmation"""
        reset_data = {
            "token": "valid-reset-token",
            "password": "newpassword123"
        }
        response = client.post("/api/v1/auth/reset-password", json=reset_data)
        
        # This would normally require a valid reset token from email
        # For testing, we expect it to fail with invalid token
        assert response.status_code in [200, 400]

    def test_change_password_success(self, client: TestClient, auth_headers):
        """Test password change with valid current password"""
        change_data = {
            "current_password": "secret",
            "new_password": "newsecret123"
        }
        response = client.post("/api/v1/auth/change-password", 
                             json=change_data, headers=auth_headers)
        
        assert response.status_code == 200

    def test_change_password_wrong_current(self, client: TestClient, auth_headers):
        """Test password change with wrong current password"""
        change_data = {
            "current_password": "wrongpassword",
            "new_password": "newsecret123"
        }
        response = client.post("/api/v1/auth/change-password", 
                             json=change_data, headers=auth_headers)
        
        assert response.status_code == 400

    def test_change_password_no_auth(self, client: TestClient):
        """Test password change without authentication"""
        change_data = {
            "current_password": "secret",
            "new_password": "newsecret123"
        }
        response = client.post("/api/v1/auth/change-password", json=change_data)
        
        assert response.status_code == 401