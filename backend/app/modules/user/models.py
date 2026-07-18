from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.enums.user import UserStatus
from app.shared.models.base import BaseModel
from sqlalchemy.orm import relationship

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.membership.models import Membership


class User(BaseModel):
    """
    Platform user.
    """

    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    profile_image: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            name="user_status",
        ),
        default=UserStatus.PENDING,
        nullable=False,
    )

    memberships: Mapped[list["Membership"]] = relationship(
    back_populates="user",
    )