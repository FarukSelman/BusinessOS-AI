from datetime import datetime, timedelta

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.enums.invitation import InvitationStatus
from app.shared.enums.membership import MembershipRole
from app.shared.models.base import BaseModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.business.models import Business


class Invitation(BaseModel):
    """
    Invitation sent to an email address to join a business.
    """

    __tablename__ = "invitations"

    business_id: Mapped[str] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        nullable=False,
    )

    role: Mapped[MembershipRole] = mapped_column(
        Enum(
            MembershipRole,
            name="membership_role",
        ),
        nullable=False,
    )

    token: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
    )

    status: Mapped[InvitationStatus] = mapped_column(
        Enum(
            InvitationStatus,
            name="invitation_status",
        ),
        default=InvitationStatus.PENDING,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.utcnow() + timedelta(days=7),
        nullable=False,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    business: Mapped["Business"] = relationship(
        back_populates="invitations",
    )