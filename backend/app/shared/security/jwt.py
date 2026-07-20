from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedException



# ---------------------------------------------------------
# Create Token Helper
# ---------------------------------------------------------

def _create_token(
    payload: dict,
    expires_delta: timedelta,
) -> str:

    now = datetime.now(UTC)

    payload.update(
        {
            "iat": now,
            "exp": now + expires_delta,
        }
    )

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )



# ---------------------------------------------------------
# Access Token
# ---------------------------------------------------------

def create_access_token(
    subject: str,
) -> str:

    return _create_token(
        payload={
            "sub": subject,
            "type": "access",
        },
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
    )



# ---------------------------------------------------------
# Refresh Token
# ---------------------------------------------------------

def create_refresh_token(
    subject: str,
) -> str:

    return _create_token(
        payload={
            "sub": subject,
            "type": "refresh",
        },
        expires_delta=timedelta(
            days=30,
        ),
    )



# ---------------------------------------------------------
# Decode Token
# ---------------------------------------------------------

def _decode_token(
    token: str,
) -> dict:

    try:

        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[
                settings.ALGORITHM,
            ],
        )

    except JWTError:

        raise UnauthorizedException(
            "Invalid token."
        )



# ---------------------------------------------------------
# Verify Access Token
# ---------------------------------------------------------

def verify_access_token(
    token: str,
) -> dict:

    payload = _decode_token(
        token,
    )

    if payload.get("type") != "access":

        raise UnauthorizedException(
            "Invalid access token."
        )

    return payload



# ---------------------------------------------------------
# Verify Refresh Token
# ---------------------------------------------------------

def verify_refresh_token(
    token: str,
) -> dict:

    payload = _decode_token(
        token,
    )

    if payload.get("type") != "refresh":

        raise UnauthorizedException(
            "Invalid refresh token."
        )

    return payload