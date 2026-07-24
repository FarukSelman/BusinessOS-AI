from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.shared.enums.document import DocumentStatus


# ---------------------------------------------------------
# Business Summary
# ---------------------------------------------------------

class BusinessSummary(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    name: str
    slug: str


# ---------------------------------------------------------
# Create
# ---------------------------------------------------------

class DocumentCreate(BaseModel):

    file_name: str

    storage_path: str

    mime_type: str

    file_size: int


# ---------------------------------------------------------
# Update
# ---------------------------------------------------------

class DocumentUpdate(BaseModel):

    status: DocumentStatus | None = None


# ---------------------------------------------------------
# Response
# ---------------------------------------------------------

class DocumentResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )


    id: UUID


    business_id: UUID


    uploaded_by: UUID


    file_name: str


    original_name: str


    mime_type: str


    file_size: int


    storage_path: str


    status: DocumentStatus


    created_at: datetime


    updated_at: datetime


    business: BusinessSummary