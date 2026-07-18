from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.db.session import get_db
from app.modules.user.models import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/users/login",
)


def get_current_token(
    token: str = Depends(oauth2_scheme),
) -> str:
    return token


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise UnauthorizedException(
                "Invalid token."
            )

    except JWTError:

        raise UnauthorizedException(
            "Invalid token."
        )

    user = db.get(
        User,
        UUID(user_id),
    )

    if user is None:

        raise UnauthorizedException(
            "User not found."
        )

    return user