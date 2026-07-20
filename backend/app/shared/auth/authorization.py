from app.shared.auth.permissions import Permission
from app.shared.enums.membership import MembershipRole


ROLE_PERMISSIONS = {

    MembershipRole.OWNER: {

        Permission.BUSINESS_CREATE,
        Permission.BUSINESS_READ,
        Permission.BUSINESS_UPDATE,
        Permission.BUSINESS_DELETE,

        Permission.MEMBERSHIP_CREATE,
        Permission.MEMBERSHIP_READ,
        Permission.MEMBERSHIP_UPDATE,
        Permission.MEMBERSHIP_DELETE,

        Permission.INVITATION_CREATE,
        Permission.INVITATION_READ,
        Permission.INVITATION_ACCEPT,
        Permission.INVITATION_DELETE,

        Permission.USER_READ,
        Permission.USER_UPDATE,

        Permission.AI_AGENT_MANAGE,
        Permission.CRM_MANAGE,
        Permission.BILLING_MANAGE,
    },

    MembershipRole.ADMIN: {

        Permission.BUSINESS_READ,
        Permission.BUSINESS_UPDATE,

        Permission.MEMBERSHIP_CREATE,
        Permission.MEMBERSHIP_READ,
        Permission.MEMBERSHIP_UPDATE,

        Permission.INVITATION_CREATE,
        Permission.INVITATION_READ,
        Permission.INVITATION_ACCEPT,

        Permission.USER_READ,
    },

    MembershipRole.EMPLOYEE: {

        Permission.BUSINESS_READ,

        Permission.MEMBERSHIP_READ,

        Permission.INVITATION_ACCEPT,

        Permission.USER_READ,
    },

    MembershipRole.VIEWER: {

        Permission.BUSINESS_READ,

        Permission.MEMBERSHIP_READ,

        Permission.USER_READ,
    },
}


def has_permission(
    role: MembershipRole,
    permission: Permission,
) -> bool:

    return permission in ROLE_PERMISSIONS.get(
        role,
        set(),
    )