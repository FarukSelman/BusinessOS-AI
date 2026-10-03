from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from app.shared.enums.service import ServiceStatus

class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    price: Decimal = Field(default=0, ge=0)
    duration_minutes: Optional[int] = Field(default=None, ge=1)
    category: Optional[str] = None
    status: ServiceStatus = ServiceStatus.ACTIVE

class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    duration_minutes: Optional[int] = Field(None, ge=1)
    category: Optional[str] = None
    status: Optional[ServiceStatus] = None

class ServiceResponse(BaseModel):
    id: UUID
    business_id: UUID
    name: str
    description: Optional[str] = None
    price: Decimal
    duration_minutes: Optional[int] = None
    category: Optional[str] = None
    status: ServiceStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
