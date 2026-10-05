"""
Google sign-in.

A fake Google (httpx.MockTransport) answers the token and userinfo calls, so
no request ever leaves the machine. Integration tests use PostgreSQL and are
skipped when it is not reachable.
"""
import uuid
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.modules.auth import google
from app.modules.auth.google import GoogleAuthError, GoogleClient, get_google_client, safe_redirect
from app.modules.user.models import User
from app.shared.enums.user import UserStatus
from app.shared.security.jwt import create_access_token
from tests.pg_support import API, make_client, make_engine, release_client

CALLBACK = f"{API}/auth/google/callback"


@pytest.fixture(autouse=True)
def google_settings(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "test-secret-not-real")
    monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://localhost:3000")


# ====================================================================== fake Google

class FakeGoogle:
    def __init__(self, profile=None, token_status=200, userinfo_status=200, fail_network=False):
        self.profile = profile or {}
        self.token_status = token_status
        self.userinfo_status = userinfo_status
        self.fail_network = fail_network
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.fail_network:
            raise httpx.ConnectError("boom", request=request)
        if request.url == httpx.URL(google.GOOGLE_TOKEN_URL):
            if self.token_status != 200:
                return httpx.Response(self.token_status, json={"error": "invalid_grant"})
            return httpx.Response(200, json={"access_token": "google-access-token", "token_type": "Bearer"})
        if request.url == httpx.URL(google.GOOGLE_USERINFO_URL):
            assert request.headers["Authorization"] == "Bearer google-access-token"
            if self.userinfo_status != 200:
                return httpx.Response(self.userinfo_status)
            return httpx.Response(200, json=self.profile)
        return httpx.Response(404)

    def client(self) -> GoogleClient:
        return GoogleClient(transport=httpx.MockTransport(self.handler))


def profile(email, verified=True, **extra):
    return {"email": email, "email_verified": verified, "given_name": "Ayşe", "family_name": "Kaya",
            "name": "Ayşe Kaya", "picture": "https://lh3.googleusercontent.com/a/photo", **extra}


# ====================================================================== unit

@pytest.mark.parametrize("path, expected", [
    ("/invitations/accept/abc", "/invitations/accept/abc"),
    ("/select-business?x=1", "/select-business?x=1"),
    (None, "/select-business"),
    ("", "/select-business"),
    ("https://evil.example/steal", "/select-business"),
    ("//evil.example", "/select-business"),
    ("/\\evil.example", "/select-business"),
    ("javascript:alert(1)", "/select-business"),
    ("/ok\r\nSet-Cookie: x", "/select-business"),
])
def test_safe_redirect_blocks_open_redirects(path, expected):
    assert safe_redirect(path) == expected


def test_state_round_trip_and_tampering():
    state, nonce = google.new_state("/invitations/accept/t1")
    assert google.check_state(state, nonce) == "/invitations/accept/t1"
    with pytest.raises(GoogleAuthError):
        google.check_state(state, "other-nonce")          # cookie from another browser
    with pytest.raises(GoogleAuthError):
        google.check_state(state + "x", nonce)            # tampered signature
    with pytest.raises(GoogleAuthError):
        google.check_state(None, nonce)
    access = create_access_token(subject=str(uuid.uuid4()))
    with pytest.raises(GoogleAuthError):
        google.check_state(access, nonce)                 # a normal JWT is not a state


def test_authorization_url_contents():
    url = urlparse(google.authorization_url("STATE"))
    q = parse_qs(url.query)
    assert f"{url.scheme}://{url.netloc}{url.path}" == google.GOOGLE_AUTH_URL
    assert q["client_id"] == [settings.GOOGLE_CLIENT_ID]
    assert q["redirect_uri"] == [settings.GOOGLE_REDIRECT_URI]
    assert q["scope"] == ["openid email profile"]
    assert q["state"] == ["STATE"] and q["response_type"] == ["code"]


def test_client_sends_secret_only_to_google_token_endpoint():
    fake = FakeGoogle(profile("a@example.com"))
    result = fake.client().fetch_profile("auth-code")
    assert result.email == "a@example.com" and result.email_verified
    token_req, info_req = fake.requests
    body = parse_qs(token_req.content.decode())
    assert body["code"] == ["auth-code"] and body["client_secret"] == ["test-secret-not-real"]
    assert body["grant_type"] == ["authorization_code"]
    assert "client_secret" not in str(info_req.url)


@pytest.mark.parametrize("fake, code", [
    (FakeGoogle(token_status=400), "exchange_failed"),
    (FakeGoogle(profile("a@example.com"), userinfo_status=401), "profile_failed"),
    (FakeGoogle(fail_network=True), "network"),
    (FakeGoogle({"email_verified": True}), "no_email"),
])
def test_client_errors(fake, code):
    with pytest.raises(GoogleAuthError) as exc:
        fake.client().fetch_profile("c")
    assert exc.value.code == code


def test_email_verified_string_is_parsed():
    assert FakeGoogle(profile("a@example.com", verified="true")).client().fetch_profile("c").email_verified
    assert not FakeGoogle(profile("a@example.com", verified="false")).client().fetch_profile("c").email_verified


# ====================================================================== integration

@pytest.fixture(scope="module")
def engine():
    eng = make_engine()
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()


@pytest.fixture
def fake():
    fake = FakeGoogle()
    app.dependency_overrides[get_google_client] = fake.client
    yield fake
    app.dependency_overrides.pop(get_google_client, None)


@pytest.fixture
def client(engine, fake):
    with make_client(engine) as c:
        yield c
    release_client()


def start(client, redirect=None):
    """Runs /google/login and returns (state, cookie nonce)."""
    params = {"redirect": redirect} if redirect else {}
    r = client.get(f"{API}/auth/google/login", params=params, follow_redirects=False)
    assert r.status_code == 302
    location = urlparse(r.headers["location"])
    assert location.netloc == "accounts.google.com"
    state = parse_qs(location.query)["state"][0]
    cookie = r.cookies.get(google.STATE_COOKIE)
    assert cookie and "HttpOnly" in r.headers["set-cookie"] and "SameSite=lax" in r.headers["set-cookie"]
    return state, cookie


def finish(client, state, cookie=None, **params):
    if cookie is not None:
        client.cookies.set(google.STATE_COOKIE, cookie)
    else:
        client.cookies.clear()
    return client.get(CALLBACK, params={"code": "auth-code", "state": state, **params}, follow_redirects=False)


def fragment(response) -> dict:
    url = urlparse(response.headers["location"])
    assert f"{url.scheme}://{url.netloc}{url.path}" == "http://localhost:3000/auth/google/callback"
    assert url.query == ""  # tokens only in the fragment
    return {k: v[0] for k, v in parse_qs(url.fragment).items()}


def error_of(response) -> str:
    url = urlparse(response.headers["location"])
    assert url.path == "/login"
    return parse_qs(url.query)["error"][0]


def me(client, access_token):
    return client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {access_token}"})


def unique_email(prefix="ayse"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_new_user_is_created_and_signed_in(client, fake, db):
    email = unique_email()
    fake.profile = profile(email)
    state, cookie = start(client)
    r = finish(client, state, cookie)
    assert r.status_code == 302
    data = fragment(r)
    assert data["redirect"] == "/select-business"

    info = me(client, data["access_token"]).json()
    assert info["email"] == email and info["first_name"] == "Ayşe" and info["last_name"] == "Kaya"
    assert info["has_password"] is False
    assert info["profile_image"].startswith("https://lh3.googleusercontent.com/")
    assert "google_oauth_state=" in r.headers["set-cookie"] and "Max-Age=0" in r.headers["set-cookie"]

    # refresh token works like a normal login
    rr = client.post(f"{API}/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert rr.status_code == 200, rr.text


def test_existing_account_is_linked_case_insensitively(client, fake, db):
    email = unique_email("mehmet")
    user = User(first_name="Mehmet", last_name="Demir", email=email, password_hash="$2b$12$abcdefghijklmnopqrstuv",
                status=UserStatus.ACTIVE)
    db.add(user)
    db.commit()
    fake.profile = profile(email.upper())
    state, cookie = start(client)
    data = fragment(finish(client, state, cookie))

    info = me(client, data["access_token"]).json()
    assert info["id"] == str(user.id)
    assert info["first_name"] == "Mehmet"          # existing name is kept
    assert info["has_password"] is True
    assert db.scalar(select(func.count()).select_from(User).where(func.lower(User.email) == email)) == 1


def test_redirect_path_survives_the_round_trip(client, fake):
    fake.profile = profile(unique_email())
    state, cookie = start(client, redirect="/invitations/accept/tok123")
    assert fragment(finish(client, state, cookie))["redirect"] == "/invitations/accept/tok123"


def test_open_redirect_is_neutralised(client, fake):
    fake.profile = profile(unique_email())
    state, cookie = start(client, redirect="https://evil.example/x")
    assert fragment(finish(client, state, cookie))["redirect"] == "/select-business"


def test_missing_or_wrong_state_cookie_is_rejected(client, fake):
    fake.profile = profile(unique_email())
    state, _ = start(client)
    assert error_of(finish(client, state, cookie=None)) == "google_state"
    assert error_of(finish(client, state, cookie="forged")) == "google_state"
    assert fake.requests == []  # Google was never called


def test_unverified_email_is_rejected(client, fake, db):
    email = unique_email()
    fake.profile = profile(email, verified=False)
    state, cookie = start(client)
    assert error_of(finish(client, state, cookie)) == "google_email_not_verified"
    assert db.scalar(select(User).where(User.email == email)) is None


@pytest.mark.parametrize("status, deleted", [(UserStatus.INACTIVE, False), (UserStatus.ACTIVE, True)])
def test_inactive_or_deleted_account_is_refused(client, fake, db, status, deleted):
    email = unique_email("pasif")
    db.add(User(first_name="P", last_name="S", email=email, password_hash="!x", status=status, is_deleted=deleted))
    db.commit()
    fake.profile = profile(email)
    state, cookie = start(client)
    assert error_of(finish(client, state, cookie)) == "google_account_inactive"


def test_user_cancel_on_google_screen(client, fake):
    state, cookie = start(client, redirect="/invitations/accept/t")
    r = finish(client, state, cookie, error="access_denied")
    assert error_of(r) == "google_cancelled"
    assert parse_qs(urlparse(r.headers["location"]).query)["redirect"] == ["/invitations/accept/t"]


def test_google_failure_redirects_with_error(client, fake):
    fake.token_status = 400
    state, cookie = start(client)
    assert error_of(finish(client, state, cookie)) == "google_exchange_failed"


def test_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    r = client.get(f"{API}/auth/google/login", follow_redirects=False)
    assert r.status_code == 302 and error_of(r) == "google_not_configured"


def test_google_only_account_password_login_and_set_password(client, fake):
    email = unique_email()
    fake.profile = profile(email)
    state, cookie = start(client)
    token = fragment(finish(client, state, cookie))["access_token"]

    r = client.post(f"{API}/auth/login", data={"username": email, "password": "!google-oauth"})
    assert r.status_code in (400, 401), r.text  # clean error, not 500

    headers = {"Authorization": f"Bearer {token}"}
    r = client.post(f"{API}/auth/change-password", json={"new_password": "YeniSifre123"}, headers=headers)
    assert r.status_code == 200, r.text
    assert me(client, token).json()["has_password"] is True
    r = client.post(f"{API}/auth/login", data={"username": email, "password": "YeniSifre123"})
    assert r.status_code == 200, r.text

    # once a password exists, the current one is required again
    r = client.post(f"{API}/auth/change-password", json={"new_password": "BaskaSifre123"}, headers=headers)
    assert r.status_code == 400
