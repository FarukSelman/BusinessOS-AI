from app.shared.auth.permissions import Permission
from app.shared.enums.membership import MembershipRole


ROLE_PERMISSIONS: dict[
    MembershipRole,
    set[Permission],
] = {

    # =====================================================
    # OWNER
    # =====================================================

    MembershipRole.OWNER: {

        # Business
        Permission.BUSINESS_CREATE,
        Permission.BUSINESS_READ,
        Permission.BUSINESS_UPDATE,
        Permission.BUSINESS_DELETE,

        # Membership
        Permission.MEMBERSHIP_CREATE,
        Permission.MEMBERSHIP_READ,
        Permission.MEMBERSHIP_UPDATE,
        Permission.MEMBERSHIP_DELETE,

        # Invitation
        Permission.INVITATION_CREATE,
        Permission.INVITATION_READ,
        Permission.INVITATION_ACCEPT,
        Permission.INVITATION_DELETE,

        # Documents
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE,
        Permission.DOCUMENT_DELETE,
        Permission.DOCUMENT_UPLOAD,
      

        # User
        Permission.USER_READ,
        Permission.USER_UPDATE,

        # Future Modules
        Permission.AI_AGENT_MANAGE,
        Permission.CRM_MANAGE,
        Permission.BILLING_MANAGE,
    },

    # =====================================================
    # ADMIN
    # =====================================================

    MembershipRole.ADMIN: {

        # Business
        Permission.BUSINESS_READ,
        Permission.BUSINESS_UPDATE,

        # Membership
        Permission.MEMBERSHIP_CREATE,
        Permission.MEMBERSHIP_READ,
        Permission.MEMBERSHIP_UPDATE,

        # Invitation
        Permission.INVITATION_CREATE,
        Permission.INVITATION_READ,
        Permission.INVITATION_ACCEPT,

        # Documents
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE,
        Permission.DOCUMENT_DELETE,
        Permission.DOCUMENT_UPLOAD,

        # User
        Permission.USER_READ,

        # Future Modules
        Permission.AI_AGENT_MANAGE,
        Permission.CRM_MANAGE,
    },

    # =====================================================
    # EMPLOYEE
    # =====================================================

    MembershipRole.EMPLOYEE: {

        Permission.BUSINESS_READ,

        Permission.MEMBERSHIP_READ,

        Permission.INVITATION_ACCEPT,

        Permission.DOCUMENT_READ,

        Permission.USER_READ,

        Permission.DOCUMENT_READ,
    },

    # =====================================================
    # VIEWER
    # =====================================================

    MembershipRole.VIEWER: {

        Permission.BUSINESS_READ,

        Permission.MEMBERSHIP_READ,

        Permission.DOCUMENT_READ,
        
    },
}