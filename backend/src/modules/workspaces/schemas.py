# File: schemas.py. Description: Workspace data transfer objects. Consists of: Pydantic schemas for workspace, member, and model management requests/responses.
import uuid
from pydantic import BaseModel, Field


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    model_ids: list[uuid.UUID] = Field(default_factory=list)


class AddMemberRequest(BaseModel):
    username: str


class AddModelRequest(BaseModel):
    model_id: uuid.UUID


class MemberResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str

    model_config = {"from_attributes": True}


class ModelResponse(BaseModel):
    id: uuid.UUID
    llm_company_name: str
    model_name: str
    model_type: str

    model_config = {"from_attributes": True}


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    admin_id: uuid.UUID

    model_config = {"from_attributes": True}
