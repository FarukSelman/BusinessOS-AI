from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ExpenseCategoryCreate(BaseModel):
    name: str = Field(..., max_length=100)
    color: str = Field("#ef4444", max_length=7)
    icon: str | None = Field(None, max_length=50)

class ExpenseCategoryUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    color: str | None = Field(None, max_length=7)
    icon: str | None = Field(None, max_length=50)

class ExpenseCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    name: str
    color: str
    icon: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime
