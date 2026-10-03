from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class TagCreate(BaseModel):
    name: str = Field(..., max_length=100)
    color: Optional[str] = Field(default="#6366f1", max_length=7)
    description: Optional[str] = None

class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=7)
    description: Optional[str] = None

class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    name: str
    color: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class TagAssignmentCreate(BaseModel):
    tag_id: UUID
