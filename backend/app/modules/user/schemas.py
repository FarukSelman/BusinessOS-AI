from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from app.shared.enums.user import UserStatus


class UserCreate(BaseModel):
    """
    Schema for user registration.
    """

    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    profile_image: HttpUrl | None = None


class UserUpdate(BaseModel):
    """
    Schema for updating a user.
    """

    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    profile_image: HttpUrl | None = None


class UserResponse(BaseModel):
    """
    Schema returned by the API.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    first_name: str

    last_name: str

    email: EmailStr

    profile_image: HttpUrl | None

    status: UserStatus

    created_at: datetime

    updated_at: datetime

class TokenResponse(BaseModel):
    """
    JWT token response.
    """

    access_token: str

    token_type: str = "bearer"