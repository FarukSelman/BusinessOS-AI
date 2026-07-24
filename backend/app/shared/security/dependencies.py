from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException

from app.db.session import get_db

from app.modules.user.models import User
from app.modules.user.repository import UserRepository

from app.shared.enums.user import UserStatus
from app.shared.security.jwt import verify_access_token



oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)



# ---------------------------------------------------------
# Raw Token
# ---------------------------------------------------------

def get_current_token(
    token: str = Depends(oauth2_scheme),
) -> str:

    return token



# ---------------------------------------------------------
# Current User
# ---------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    payload = verify_access_token(
        token,
    )

    user_id = payload.get(
        "sub",
    )

    if user_id is None:

        raise UnauthorizedException(
            "Invalid access token.",
        )


    try:

        user_uuid = UUID(
            user_id,
        )

    except ValueError:

        raise UnauthorizedException(
            "Invalid user identifier.",
        )


    repository = UserRepository(
        db,
    )

    user = repository.get(
        user_uuid,
    )


    if user is None:

        raise UnauthorizedException(
            "User not found.",
        )


    if user.status != UserStatus.ACTIVE:

        raise UnauthorizedException(
            "User account is not active.",
        )


    return user 