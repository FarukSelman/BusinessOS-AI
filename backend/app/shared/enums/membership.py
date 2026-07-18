from enum import Enum

class MembershipRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"
    VIEWER = "VIEWER"