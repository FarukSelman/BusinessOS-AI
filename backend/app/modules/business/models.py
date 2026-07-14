from sqlalchemy import Enum, String

from sqlalchemy.orm import Mapped, mapped_column

from app.shared.enums.business import BusinessStatus
from app.shared.models.base import BaseModel


class Business(BaseModel):
    """
    Business entity.

    Represents a company registered in the BusinessOS AI platform.
    """

    __tablename__ = "businesses"

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )

    industry: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    website: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[BusinessStatus] = mapped_column(
        Enum(
            BusinessStatus,
            name="business_status",
        ),
        default=BusinessStatus.ACTIVE,
        nullable=False,
    )