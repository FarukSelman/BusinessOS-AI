import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_auth_service():
    with patch("app.modules.auth.router.get_service") as mock_get_service:
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        yield mock_service

def test_register_success(test_client, test_user_data, mock_auth_service):
    """Register a new user with valid data."""
    mock_auth_service.register.return_value = {"id": "uuid", "email": "test@example.com"}
    # The endpoint paths assume standard CRUD. Adjust if necessary.
    response = test_client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code in [200, 201]

def test_register_duplicate_email(test_client, test_user_data, mock_auth_service):
    """Should fail with 409 Conflict if email exists."""
    from fastapi import HTTPException
    mock_auth_service.register.side_effect = HTTPException(status_code=409, detail="Email already registered")
    response = test_client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 409

def test_login_success(test_client, mock_auth_service):
    """Login with valid credentials."""
    mock_auth_service.login.return_value = {"access_token": "token", "refresh_token": "rtoken", "token_type": "bearer"}
    response = test_client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "Password123!"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(test_client, mock_auth_service):
    """Should fail with 401 on wrong password."""
    from fastapi import HTTPException
    mock_auth_service.login.side_effect = HTTPException(status_code=401, detail="Invalid credentials")
    response = test_client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "WrongPassword"})
    assert response.status_code == 401

def test_login_nonexistent_user(test_client, mock_auth_service):
    """Should fail with 401 if user doesn't exist."""
    from fastapi import HTTPException
    mock_auth_service.login.side_effect = HTTPException(status_code=401, detail="Invalid credentials")
    response = test_client.post("/api/v1/auth/login", data={"username": "nonexistent@example.com", "password": "Password123!"})
    assert response.status_code == 401

def test_get_me_authenticated(test_client, auth_headers, mock_auth_service):
    """Get current user profile."""
    mock_auth_service.me.return_value = {"id": "uuid", "email": "test@example.com"}
    response = test_client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200

def test_get_me_unauthenticated(test_client):
    """Should fail with 401 if unauthenticated."""
    # Temporarily remove auth dependency override
    from app.shared.security.dependencies import get_current_user
    from app.main import app
    app.dependency_overrides.pop(get_current_user, None)
    
    response = test_client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_refresh_token(test_client, mock_auth_service):
    """Refresh access token."""
    mock_auth_service.refresh_token.return_value = {"access_token": "new_token", "refresh_token": "rtoken", "token_type": "bearer"}
    response = test_client.post("/api/v1/auth/refresh", json={"refresh_token": "valid_refresh_token"})
    assert response.status_code == 200
