"""
Schemas for the public (no login) booking page.

Everything here is visible to anyone on the internet, so each response lists
its fields explicitly: business contact info, services, opening hours and
staff display names only. Never customer data, staff phone/e-mail, user ids
or internal timestamps.
"""
import re
from datetime import date, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class PublicServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: Optional[str] = None
    price: float
    duration: int


class PublicOpeningHours(BaseModel):
    day_of_week: int  # 0 = Monday
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    is_closed: bool = False


class PublicBusinessInfo(BaseModel):
    id: UUID
    name: str
    slug: str
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    opening_hours: List[PublicOpeningHours] = []
    services: List[PublicServiceResponse] = []


class PublicBranchResponse(BaseModel):
    id: UUID
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    is_main: bool = False


class PublicStaffService(BaseModel):
    id: UUID
    name: str


class PublicStaffResponse(BaseModel):
    """Display data only: no phone, e-mail, user account or timestamps."""
    id: UUID
    full_name: str
    title: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    branch_id: Optional[UUID] = None
    services: List[PublicStaffService] = []


class PublicAvailableSlots(BaseModel):
    date: date
    service_id: UUID
    available_slots: List[time]


PHONE_HELP = "Geçerli bir telefon numarası girin (ör. 0532 123 45 67)."


def normalize_phone(raw: str) -> str:
    """'0532 123 45 67', '+90 532 1234567', '5321234567' -> '05321234567'."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("90") and len(digits) == 12:
        digits = "0" + digits[2:]
    elif len(digits) == 10 and not digits.startswith("0"):
        digits = "0" + digits
    if not re.fullmatch(r"0[2-5]\d{9}", digits):
        raise ValueError(PHONE_HELP)
    return digits


class PublicBookingCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    customer_phone: str = Field(max_length=30)
    customer_email: Optional[EmailStr] = None
    service_id: UUID
    branch_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    date: date
    start_time: time
    # Honeypot: hidden on the page, so people leave it empty and bots fill it.
    website: Optional[str] = Field(default=None, max_length=200)

    @field_validator("customer_name", mode="before")
    @classmethod
    def _clean_name(cls, value):
        if isinstance(value, str):
            value = re.sub(r"\s+", " ", value).strip()
            if len(value) < 2 or not re.search(r"[^\W\d_]", value):
                raise ValueError("Lütfen adınızı ve soyadınızı girin.")
        return value

    @field_validator("customer_phone")
    @classmethod
    def _clean_phone(cls, value: str) -> str:
        return normalize_phone(value)

    @field_validator("customer_email", mode="before")
    @classmethod
    def _clean_email(cls, value):
        if isinstance(value, str):
            value = value.strip().lower()
            if not value:
                return None
            # "ayşe@..." passes EmailStr, but most mail servers cannot deliver to it.
            if not value.isascii():
                raise ValueError("E-posta adresinde Türkçe karakter (ç, ğ, ı, ö, ş, ü) kullanılamaz.")
        return value


class PublicBookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    service_id: UUID
    branch_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    staff_name: Optional[str] = None
    customer_id: UUID
    date: date
    start_time: time
    end_time: time
    status: str
