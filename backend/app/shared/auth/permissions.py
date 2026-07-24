from enum import Enum


class Permission(str, Enum):

    # ---------------------------------------------------------
    # Business
    # ---------------------------------------------------------

    BUSINESS_CREATE = "BUSINESS_CREATE"
    BUSINESS_READ = "BUSINESS_READ"
    BUSINESS_UPDATE = "BUSINESS_UPDATE"
    BUSINESS_DELETE = "BUSINESS_DELETE"

    # ---------------------------------------------------------
    # Membership
    # ---------------------------------------------------------

    MEMBERSHIP_READ = "MEMBERSHIP_READ"
    MEMBERSHIP_CREATE = "MEMBERSHIP_CREATE"
    MEMBERSHIP_UPDATE = "MEMBERSHIP_UPDATE"
    MEMBERSHIP_DELETE = "MEMBERSHIP_DELETE"

    # ---------------------------------------------------------
    # Invitation
    # ---------------------------------------------------------

    INVITATION_CREATE = "INVITATION_CREATE"
    INVITATION_READ = "INVITATION_READ"
    INVITATION_ACCEPT = "INVITATION_ACCEPT"
    INVITATION_DELETE = "INVITATION_DELETE"

    # ---------------------------------------------------------
    # Documents
    # ---------------------------------------------------------

    DOCUMENT_CREATE = "DOCUMENT_CREATE"
    DOCUMENT_READ = "DOCUMENT_READ"
    DOCUMENT_UPDATE = "DOCUMENT_UPDATE"
    DOCUMENT_DELETE = "DOCUMENT_DELETE"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"

    # ---------------------------------------------------------
    # Users
    # ---------------------------------------------------------

    USER_READ = "USER_READ"
    USER_UPDATE = "USER_UPDATE"

    # ---------------------------------------------------------
    # Future Modules
    # ---------------------------------------------------------

    AI_AGENT_MANAGE = "AI_AGENT_MANAGE"
    CRM_MANAGE = "CRM_MANAGE"
    BILLING_MANAGE = "BILLING_MANAGE"

    
