from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.modules.membership.repository import MembershipRepository
from app.modules.user.models import User

from app.shared.security.dependencies import get_current_user

from app.core.exceptions import UnauthorizedException


def require_member(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:

    repository = MembershipRepository(db)

    membership = repository.get_by_user_and_business(
        current_user.id,
        business_id,
    )

    if membership is None:
        raise UnauthorizedException(
            "You are not a member of this business."
        )

    return current_user


def require_admin(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:

    repository = MembershipRepository(db)

    if not repository.is_admin(
        current_user.id,
        business_id,
    ):
        raise UnauthorizedException(
            "Only business admins can perform this action."
        )

    return current_user


def require_owner(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:

    repository = MembershipRepository(db)

    if not repository.is_owner(
        current_user.id,
        business_id,
    ):
        raise UnauthorizedException(
            "Only business owners can perform this action."
        )

    return current_user