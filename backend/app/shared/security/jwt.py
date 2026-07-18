from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import settings


def create_access_token(
    subject: str,
) -> str:
    """
    Generate JWT access token.
    """

    expire = datetime.now(UTC) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )