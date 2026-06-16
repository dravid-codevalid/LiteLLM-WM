# File: router.py. Description: Workspace API endpoints. Consists of: FastAPI router handling workspace creation, deletion, member management, and model allowance.
import uuid

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.auth.models import User
from src.modules.workspaces import service
from src.modules.workspaces.schemas import (
    CreateWorkspaceRequest, AddMemberRequest, AddModelRequest,
    WorkspaceResponse, MemberResponse, ModelResponse,
)
from src.shared.db.engine import get_session
from src.shared.middleware.auth import get_current_user

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.post("")
async def create_workspace(
    data: CreateWorkspaceRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    ws = await service.create_workspace(session, data.name, data.model_ids, user)
    return {"success": True, "data": WorkspaceResponse.model_validate(ws)}


@router.get("/available-models")
async def list_available_models(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    models = await service.list_available_models(session)
    return {"success": True, "data": [ModelResponse.model_validate(m) for m in models]}


@router.get("")
async def list_workspaces(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    workspaces = await service.list_workspaces(session, user)
    return {"success": True, "data": [WorkspaceResponse.model_validate(w) for w in workspaces]}


@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    ws = await service.get_workspace(session, workspace_id, user)
    return {"success": True, "data": WorkspaceResponse.model_validate(ws)}


@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await service.delete_workspace(session, workspace_id, user)
    return {"success": True, "data": {"message": "Workspace deleted"}}


@router.post("/{workspace_id}/members")
async def add_member(
    workspace_id: uuid.UUID,
    data: AddMemberRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await service.add_member(session, workspace_id, data.username, user)
    return {"success": True, "data": {"message": "Member added"}}


@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await service.remove_member(session, workspace_id, user_id, user)
    return {"success": True, "data": {"message": "Member removed"}}


@router.get("/{workspace_id}/members")
async def list_members(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    members = await service.list_members(session, workspace_id, user)
    return {"success": True, "data": [MemberResponse.model_validate(m) for m in members]}


@router.get("/{workspace_id}/models")
async def list_models(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    models = await service.list_models(session, workspace_id, user)
    return {"success": True, "data": [ModelResponse.model_validate(m) for m in models]}


@router.post("/{workspace_id}/models")
async def add_model(
    workspace_id: uuid.UUID,
    data: AddModelRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await service.add_model(session, workspace_id, data.model_id, user)
    return {"success": True, "data": {"message": "Model added"}}


@router.delete("/{workspace_id}/models/{model_id}")
async def remove_model(
    workspace_id: uuid.UUID,
    model_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await service.remove_model(session, workspace_id, model_id, user)
    return {"success": True, "data": {"message": "Model removed"}}
