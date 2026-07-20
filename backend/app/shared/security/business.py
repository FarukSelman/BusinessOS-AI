from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException

from app.db.session import get_db

from app.modules.membership.repository import MembershipRepository
from app.modules.user.models import User

from app.shared.security.dependencies import get_current_user



# ---------------------------------------------------------
# Require Member
# ---------------------------------------------------------

def require_member(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:

    repository = MembershipRepository(
        db,
    )

    membership = repository.get_by_user_and_business(
        user_id=current_user.id,
        business_id=business_id,
    )

    if membership is None:

        raise ForbiddenException(
            "You are not a member of this business.",
        )

    return current_user



# ---------------------------------------------------------
# Require Admin
# ---------------------------------------------------------

def require_admin(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:

    repository = MembershipRepository(
        db,
    )

    if not repository.is_admin(
        user_id=current_user.id,
        business_id=business_id,
    ):

        raise ForbiddenException(
            "Only business admins can perform this action.",
        )

    return current_user



# ---------------------------------------------------------
# Require Owner
# ---------------------------------------------------------

def require_owner(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:

    repository = MembershipRepository(
        db,
    )

    if not repository.is_owner(
        user_id=current_user.id,
        business_id=business_id,
    ):

        raise ForbiddenException(
            "Only business owners can perform this action.",
        )

    return current_user