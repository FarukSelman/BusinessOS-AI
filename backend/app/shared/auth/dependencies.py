from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.dependencies import (
    Database,
    CurrentUser,
)

from app.core.exceptions import (
    ForbiddenException,
)

from app.modules.membership.models import Membership
from app.modules.membership.repository import MembershipRepository
from app.modules.user.models import User

from app.shared.auth.authorization import has_permission
from app.shared.auth.permissions import Permission


def require_permission(
    permission: Permission,
) -> Callable:

    def dependency(
        business_id: UUID,
        db: Session = Database,
        current_user: User = CurrentUser,
    ) -> Membership:

        repository = MembershipRepository(db)

        membership = repository.require_membership(
            current_user.id,
            business_id,
        )

        if not has_permission(
            membership.role,
            permission,
        ):
            raise ForbiddenException(
                "You do not have permission."
            )

        return membership

    return dependency