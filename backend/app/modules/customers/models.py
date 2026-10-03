from sqlalchemy import Enum, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.enums.customer import CustomerStatus
from app.shared.models.base import BaseModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.business.models import Business


class Customer(BaseModel):
    """
    Customer entity.

    Represents a customer of a business in the BusinessOS AI platform.
    """

    __tablename__ = "customers"

    business_id: Mapped[PG_UUID] = mapped_column(
        ForeignKey(
            "businesses.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[CustomerStatus] = mapped_column(
        Enum(
            CustomerStatus,
            name="customer_status",
        ),
        default=CustomerStatus.ACTIVE,
        nullable=False,
    )
