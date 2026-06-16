# File: schemas.py. Description: Conversation data transfer objects. Consists of: Pydantic schemas for conversation requests, and detailed message responses.
import uuid
from pydantic import BaseModel, Field
from datetime import datetime


class CreateConversationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class MessageResponse(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    sender_name: str
    prompt_text: str
    response_text: str
    model_used: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    workspace_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    workspace_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    messages: list[MessageResponse] = []

    model_config = {"from_attributes": True}
