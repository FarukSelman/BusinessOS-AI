"""
Google sign-in (OAuth 2.0 authorization code flow, server side).

Flow
1. GET /auth/google/login?redirect=/path
   -> random nonce in an httpOnly cookie + signed `state` (nonce, redirect, 10 min)
   -> 302 to Google's consent screen.
2. GET /auth/google/callback?code=...&state=...
   -> state signature + expiry + nonce == cookie (CSRF / login-CSRF protection)
   -> code exchanged for a token with the client secret, profile read from
      Google's userinfo endpoint (over TLS, straight from Google, so no ID token
      signature check is needed)
   -> our own access/refresh tokens are handed to the frontend in the URL
      fragment (#...), which browsers never send to servers or put in logs.

The redirect target is only ever a same-site relative path (no open redirect).
"""
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt

from app.core.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

STATE_COOKIE = "google_oauth_state"
STATE_TTL = timedelta(minutes=10)
STATE_TYPE = "google_oauth_state"

# Stored in password_hash for Google-only accounts. Not a valid bcrypt hash,
# so password login fails cleanly (verify_password returns False).
GOOGLE_PASSWORD_MARKER = "!google-oauth"

DEFAULT_REDIRECT = "/select-business"


class GoogleAuthError(Exception):
    """Carries a short error code shown to the user on the login page."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(slots=True)
class GoogleProfile:
    email: str
    email_verified: bool
    given_name: str | None = None
    family_name: str | None = None
    name: str | None = None
    picture: str | None = None


def is_configured() -> bool:
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def safe_redirect(path: str | None) -> str:
    """Only same-site relative paths ('/x'); anything else falls back to the default."""
    if not path or not path.startswith("/") or path.startswith("//") or "\\" in path:
        return DEFAULT_REDIRECT
    if any(ch in path for ch in "\r\n\t") or "://" in path.split("?")[0]:
        return DEFAULT_REDIRECT
    return path[:500]


def new_state(redirect: str | None) -> tuple[str, str]:
    """Returns (signed_state, nonce). The nonce goes into the cookie."""
    nonce = secrets.token_urlsafe(32)
    payload = {
        "type": STATE_TYPE,
        "nonce": nonce,
        "redirect": safe_redirect(redirect),
        "exp": datetime.now(UTC) + STATE_TTL,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM), nonce


def check_state(state: str | None, cookie_nonce: str | None) -> str:
    """Validates the state against the cookie; returns the redirect path."""
    if not state or not cookie_nonce:
        raise GoogleAuthError("state")
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise GoogleAuthError("state") from None
    if payload.get("type") != STATE_TYPE or not hmac.compare_digest(str(payload.get("nonce", "")), cookie_nonce):
        raise GoogleAuthError("state")
    return safe_redirect(payload.get("redirect"))


def authorization_url(state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
        "access_type": "online",
        "include_granted_scopes": "true",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


class GoogleClient:
    """Talks to Google's token and userinfo endpoints. `transport` lets tests plug in a fake server."""

    def __init__(self, transport: httpx.BaseTransport | None = None, timeout: float = 10.0):
        self._transport = transport
        self._timeout = timeout

    def fetch_profile(self, code: str) -> GoogleProfile:
        try:
            with httpx.Client(transport=self._transport, timeout=self._timeout) as client:
                token = client.post(GOOGLE_TOKEN_URL, data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                })
                if token.status_code != 200:
                    raise GoogleAuthError("exchange_failed")
                access_token = token.json().get("access_token")
                if not access_token:
                    raise GoogleAuthError("exchange_failed")

                info = client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
                if info.status_code != 200:
                    raise GoogleAuthError("profile_failed")
                data = info.json()
        except httpx.HTTPError:
            raise GoogleAuthError("network") from None

        email = (data.get("email") or "").strip()
        if not email:
            raise GoogleAuthError("no_email")
        verified = data.get("email_verified")
        return GoogleProfile(
            email=email,
            email_verified=verified is True or str(verified).lower() == "true",
            given_name=data.get("given_name"),
            family_name=data.get("family_name"),
            name=data.get("name"),
            picture=data.get("picture"),
        )


def get_google_client() -> GoogleClient:
    """FastAPI dependency (overridden in tests)."""
    return GoogleClient()


def frontend_success_url(access_token: str, refresh_token: str, redirect: str) -> str:
    fragment = urlencode({"access_token": access_token, "refresh_token": refresh_token, "redirect": redirect})
    return f"{settings.FRONTEND_URL.rstrip('/')}/auth/google/callback#{fragment}"


def frontend_error_url(code: str, redirect: str | None = None) -> str:
    params = {"error": f"google_{code}"}
    if redirect and redirect != DEFAULT_REDIRECT:
        params["redirect"] = redirect
    return f"{settings.FRONTEND_URL.rstrip('/')}/login?{urlencode(params)}"
