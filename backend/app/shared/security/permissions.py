from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException

from app.db.session import get_db

from app.modules.membership.repository import MembershipRepository
from app.modules.user.models import User

from app.shared.auth.permissions import Permission
from app.shared.security.dependencies import get_current_user
from app.shared.security.permission_matrix import ROLE_PERMISSIONS


# ---------------------------------------------------------
# Require Permission
# ---------------------------------------------------------

def require_permission(
    permission: Permission,
):

    def permission_checker(
        business_id: UUID,

        current_user: User = Depends(
            get_current_user,
        ),

        db: Session = Depends(
            get_db,
        ),
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


        allowed_roles = [
            role
            for role, permissions in ROLE_PERMISSIONS.items()
            if permission in permissions
        ]


        if membership.role not in allowed_roles:

            raise ForbiddenException(
                "You do not have permission.",
            )


        return current_user


    return permission_checker

def require_superadmin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Yalnızca platform admini (is_superadmin=True) olan kullanıcıların
    erişebileceği endpoint'ler için kullanılır. Belirli bir işletmeye
    üyelik gerektirmez — tüm işletmeler üzerinde yetki verir.
    """
    if not current_user.is_superadmin:
        raise ForbiddenException(
            detail="Bu işlem için platform admin yetkisi gerekiyor.",
        )
    return current_user