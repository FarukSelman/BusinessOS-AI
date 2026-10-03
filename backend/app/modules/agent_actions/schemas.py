from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentActionResponse(BaseModel):
    id: UUID
    business_id: UUID
    requested_by: UUID
    approved_by: UUID | None
    action_type: str
    status: str
    payload: dict
    result: dict | None
    rejection_reason: str | None
    executed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RejectAgentActionRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
