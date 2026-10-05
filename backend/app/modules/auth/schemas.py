from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from app.shared.enums.user import UserStatus
from uuid import UUID


# ==========================================================
# Register
# ==========================================================

class RegisterRequest(BaseModel):

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


# ==========================================================
# Login
# ==========================================================

class LoginRequest(BaseModel):

    email: EmailStr

    password: str


# ==========================================================
# Refresh Token
# ==========================================================

class RefreshTokenRequest(BaseModel):

    refresh_token: str


# ==========================================================
# JWT Response
# ==========================================================

class TokenResponse(BaseModel):

    access_token: str

    refresh_token: str

    token_type: str = "bearer"


# ==========================================================
# Current User
# ==========================================================

class MeResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    first_name: str

    last_name: str

    email: EmailStr

    profile_image: HttpUrl | None

    status: UserStatus
    
    is_superadmin: bool

    # False for Google-only accounts: the profile page then offers "set password".
    has_password: bool = True


# ==========================================================
# Update Profile & Password
# ==========================================================

class UpdateProfilePayload(BaseModel):

    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=2,
        max_length=100,
    )


class ChangePasswordPayload(BaseModel):

    # Not required when the account has no password yet (Google sign-in).
    current_password: str | None = None

    new_password: str = Field(
        min_length=8,
        max_length=128,
    )
