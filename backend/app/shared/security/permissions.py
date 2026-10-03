from fastapi import Depends

from app.core.exceptions import ForbiddenException

from app.modules.membership.models import Membership
from app.modules.user.models import User

from app.shared.auth.permissions import Permission
from app.shared.security.business import get_business_membership
from app.shared.security.dependencies import get_current_user
from app.shared.security.permission_matrix import ROLE_PERMISSIONS


# ---------------------------------------------------------
# Require Permission
# ---------------------------------------------------------

def require_permission(
    permission: Permission,
):
    """
    Member of the business in the path whose role grants `permission`
    (ROLE_PERMISSIONS). Membership itself is checked by
    get_business_membership, the same dependency every business route uses.
    """

    def permission_checker(
        membership: Membership = Depends(
            get_business_membership,
        ),

        current_user: User = Depends(
            get_current_user,
        ),
    ) -> User:

        if permission not in ROLE_PERMISSIONS.get(membership.role, set()):

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