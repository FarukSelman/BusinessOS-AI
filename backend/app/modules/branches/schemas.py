from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class BranchCreate(BaseModel):
    name: str = Field(..., max_length=150)
    address: str | None = None
    phone: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=255)
    is_main: bool = False
    is_active: bool = True
    working_hours: dict[str, Any] | None = None

class BranchUpdate(BaseModel):
    name: str | None = Field(None, max_length=150)
    address: str | None = None
    phone: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=255)
    is_main: bool | None = None
    is_active: bool | None = None
    working_hours: dict[str, Any] | None = None

class BranchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    business_id: UUID
    name: str
    address: str | None
    phone: str | None
    email: str | None
    is_main: bool
    is_active: bool
    working_hours: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
