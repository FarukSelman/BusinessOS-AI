from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.shared.enums.business import BusinessStatus


class BusinessCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)

    industry: str = Field(min_length=2, max_length=100)

    email: EmailStr

    phone: str = Field(min_length=5, max_length=30)

    website: str | None = None

    logo_url: str | None = None


class BusinessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str

    name: str

    slug: str

    industry: str

    email: EmailStr

    phone: str

    website: str | None

    logo_url: str | None

    status: BusinessStatus