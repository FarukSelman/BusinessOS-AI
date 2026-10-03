from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.shared.enums.customer import CustomerStatus


class CustomerCreate(BaseModel):
    """Schema for creating a customer."""

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    notes: str | None = None


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    notes: str | None = None

    status: CustomerStatus | None = None


class CustomerResponse(BaseModel):
    """Schema returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    business_id: UUID

    name: str

    email: EmailStr | None

    phone: str | None

    notes: str | None

    status: CustomerStatus

    created_at: datetime

    updated_at: datetime
