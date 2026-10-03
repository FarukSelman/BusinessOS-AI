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

        # Customers
        Permission.CUSTOMER_CREATE,
        Permission.CUSTOMER_READ,
        Permission.CUSTOMER_UPDATE,
        Permission.CUSTOMER_DELETE,

        # Services
        Permission.SERVICE_CREATE,
        Permission.SERVICE_READ,
        Permission.SERVICE_UPDATE,
        Permission.SERVICE_DELETE,

        # Appointments
        Permission.APPOINTMENT_CREATE,
        Permission.APPOINTMENT_READ,
        Permission.APPOINTMENT_UPDATE,
        Permission.APPOINTMENT_DELETE,
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

        # Customers
        Permission.CUSTOMER_CREATE,
        Permission.CUSTOMER_READ,
        Permission.CUSTOMER_UPDATE,
        Permission.CUSTOMER_DELETE,

        # Services
        Permission.SERVICE_CREATE,
        Permission.SERVICE_READ,
        Permission.SERVICE_UPDATE,
        Permission.SERVICE_DELETE,

        # Appointments
        Permission.APPOINTMENT_CREATE,
        Permission.APPOINTMENT_READ,
        Permission.APPOINTMENT_UPDATE,
        Permission.APPOINTMENT_DELETE,
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

        # Customers
        Permission.CUSTOMER_READ,
        Permission.CUSTOMER_CREATE,

        # Services
        Permission.SERVICE_READ,

        # Appointments
        Permission.APPOINTMENT_READ,
        Permission.APPOINTMENT_CREATE,
        Permission.APPOINTMENT_UPDATE,
    },

    # =====================================================
    # VIEWER
    # =====================================================

    MembershipRole.VIEWER: {

        Permission.BUSINESS_READ,

        Permission.MEMBERSHIP_READ,

        Permission.DOCUMENT_READ,

        Permission.CUSTOMER_READ,

        Permission.SERVICE_READ,

        Permission.APPOINTMENT_READ,
    },
}