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



# auto_error=False: a missing token is answered below with our own (Turkish)
# message instead of FastAPI's "Not authenticated".
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)

NOT_AUTHENTICATED = "Bu işlem için giriş yapmalısınız."



# ---------------------------------------------------------
# Raw Token
# ---------------------------------------------------------

def get_current_token(
    token: str | None = Depends(oauth2_scheme),
) -> str:

    if not token:
        raise UnauthorizedException(NOT_AUTHENTICATED)

    return token



# ---------------------------------------------------------
# Current User
# ---------------------------------------------------------

def get_current_user(
    token: str = Depends(get_current_token),
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
            "Oturumunuzun süresi doldu, lütfen tekrar giriş yapın.",
        )


    try:

        user_uuid = UUID(
            user_id,
        )

    except ValueError:

        raise UnauthorizedException(
            "Geçersiz oturum bilgisi.",
        )


    repository = UserRepository(
        db,
    )

    user = repository.get(
        user_uuid,
    )


    if user is None:

        raise UnauthorizedException(
            "Kullanıcı bulunamadı.",
        )


    if user.status != UserStatus.ACTIVE:

        raise UnauthorizedException(
            "Hesabınız aktif değil.",
        )


    return user 