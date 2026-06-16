# File: schemas.py. Description: Usage data transfer objects. Consists of: Pydantic schemas for member, admin, and owner usage analytics responses.
import uuid
from pydantic import BaseModel
from datetime import datetime


class UsageSummaryResponse(BaseModel):
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost: float
    record_count: int


class UserUsageBreakdown(BaseModel):
    user_id: uuid.UUID
    username: str
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost: float


class WorkspaceUsageResponse(BaseModel):
    workspace_total: UsageSummaryResponse
    per_user: list[UserUsageBreakdown]


class LedgerRecordResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    user_id: uuid.UUID
    model_name: str
    message_id: uuid.UUID | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    calculated_cost: float
    is_flagged_error: bool
    timestamp: datetime

    model_config = {"from_attributes": True}
