from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from app.shared.enums.business import BusinessStatus


class BusinessCreate(BaseModel):
    """Schema for creating a business."""

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    industry: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    phone: str = Field(
        min_length=5,
        max_length=30,
    )

    website: HttpUrl | None = None

    logo_url: HttpUrl | None = None


class BusinessUpdate(BaseModel):
    """Schema for updating a business."""

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    industry: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        min_length=5,
        max_length=30,
    )

    website: HttpUrl | None = None

    logo_url: HttpUrl | None = None


class BusinessResponse(BaseModel):
    """Schema returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    name: str

    slug: str

    industry: str

    email: EmailStr

    phone: str

    website: HttpUrl | None

    logo_url: HttpUrl | None

    status: BusinessStatus

    created_at: datetime

    updated_at: datetime