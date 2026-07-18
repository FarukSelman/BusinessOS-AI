from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from app.shared.enums.membership import MembershipRole
from app.shared.models.base import BaseModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.user.models import User
    from app.modules.business.models import Business


class Membership(BaseModel):
    """
    User ↔ Business relationship.
    """

    __tablename__ = "memberships"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    business_id: Mapped[str] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
    )

    role: Mapped[MembershipRole] = mapped_column(
        Enum(
            MembershipRole,
            name="membership_role",
        ),
        default=MembershipRole.EMPLOYEE,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="memberships",
    )

    business: Mapped["Business"] = relationship(
        back_populates="memberships",
    )