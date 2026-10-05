from sqlalchemy import Enum, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.enums.user import UserStatus
from app.shared.models.base import BaseModel
from sqlalchemy.orm import relationship

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.membership.models import Membership
    from app.modules.document.models import Document


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

    is_superadmin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )


    @property
    def has_password(self) -> bool:
        """False for accounts created through Google sign-in that never set a password."""
        return not (self.password_hash or "").startswith("!")

    memberships: Mapped[list["Membership"]] = relationship(
    back_populates="user",
    )

    documents: Mapped[list["Document"]] = relationship(
    back_populates="uploader",
    )