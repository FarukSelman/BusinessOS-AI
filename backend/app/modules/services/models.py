from sqlalchemy import Enum, String, Text, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.shared.models.base import BaseModel
from app.shared.enums.service import ServiceStatus

class Service(BaseModel):
    __tablename__ = "services"

    business_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("businesses.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[ServiceStatus] = mapped_column(
        Enum(ServiceStatus, name="servicestatus", create_type=False),
        default=ServiceStatus.ACTIVE,
        nullable=False
    )
