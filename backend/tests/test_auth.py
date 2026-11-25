"""
Register, login, current user and token refresh through the real API.

These tests used to patch auth.router.get_service, which FastAPI never looks
up again once the route is declared, so the real service ran against a
MagicMock session. They now run against PostgreSQL like the other
integration tests (skipped when it is unreachable).

Wrong e-mail or password answers 400 ("invalid_grant" in the OAuth2 password
flow, RFC 6749 §5.2); the login page shows the same message for any failure.
"""
import uuid

import pytest

from tests.pg_support import API, make_client, make_engine, release_client

PASSWORD = "StrongPassword123!"


@pytest.fixture(scope="module")
def engine():
    from app.db.base import Base

    eng = make_engine()
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def client(engine):
    with make_client(engine) as c:
        yield c
    release_client()


@pytest.fixture
def test_user_data():
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
        "password": PASSWORD,
    }


def register(client, data):
    return client.post(f"{API}/auth/register", json=data)


def login(client, email, password):
    # OAuth2 password form, as the login page sends it
    return client.post(f"{API}/auth/login", data={"username": email, "password": password})


@pytest.fixture
def registered(client, test_user_data):
    assert register(client, test_user_data).status_code == 201
    return test_user_data


def test_register_success(client, test_user_data):
    """Register a new user with valid data."""
    response = register(client, test_user_data)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == test_user_data["email"]
    assert "password" not in body and "password_hash" not in body


def test_register_duplicate_email(client, registered):
    """Should fail with 409 Conflict if email exists."""
    response = register(client, registered)
    assert response.status_code == 409


def test_login_success(client, registered):
    """Login with valid credentials."""
    response = login(client, registered["email"], PASSWORD)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"] and body["refresh_token"] and body["token_type"] == "bearer"


def test_login_wrong_password(client, registered):
    """Wrong password: 400 invalid credentials, no token."""
    response = login(client, registered["email"], "WrongPassword1")
    assert response.status_code == 400
    assert "access_token" not in response.json()
    assert response.json()["message"] == "E-posta veya şifre hatalı."


def test_login_nonexistent_user(client):
    """Unknown e-mail: same 400 as a wrong password, so accounts cannot be probed."""
    response = login(client, f"nobody-{uuid.uuid4().hex[:8]}@example.com", PASSWORD)
    assert response.status_code == 400
    assert response.json()["message"] == "E-posta veya şifre hatalı."


def test_get_me_authenticated(client, registered):
    """Get current user profile."""
    token = login(client, registered["email"], PASSWORD).json()["access_token"]
    response = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    assert response.json()["email"] == registered["email"]
    assert response.json()["first_name"] == "Test"


def test_get_me_unauthenticated(client):
    """Should fail with 401 if unauthenticated."""
    assert client.get(f"{API}/auth/me").status_code == 401
    bad = client.get(f"{API}/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert bad.status_code == 401


def test_refresh_token(client, registered):
    """Refresh access token."""
    refresh = login(client, registered["email"], PASSWORD).json()["refresh_token"]
    response = client.post(f"{API}/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200, response.text
    new_access = response.json()["access_token"]
    me = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 200 and me.json()["email"] == registered["email"]


def test_refresh_rejects_an_access_token(client, registered):
    """An access token is not a refresh token."""
    access = login(client, registered["email"], PASSWORD).json()["access_token"]
    response = client.post(f"{API}/auth/refresh", json={"refresh_token": access})
    assert response.status_code in (400, 401)
