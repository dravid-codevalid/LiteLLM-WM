# File: service.py. Description: Workspace business logic. Consists of: workspace lifecycle management and RBAC enforcement.
import uuid

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.auth.models import User
from src.modules.workspaces.models import Workspace, GlobalModel
from src.modules.workspaces import repository
from src.modules.auth.repository import get_user_by_username


def _require_admin(workspace: Workspace, user: User) -> None:
    if workspace.admin_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace admin access required")


async def _get_workspace_or_404(session: AsyncSession, workspace_id: uuid.UUID) -> Workspace:
    workspace = await repository.get_workspace_by_id(session, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


async def _require_membership(session: AsyncSession, workspace_id: uuid.UUID, user: User) -> None:
    if not await repository.is_member(session, workspace_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a workspace member")


async def create_workspace(session: AsyncSession, name: str, model_ids: list[uuid.UUID], user: User) -> Workspace:
    workspace = Workspace(name=name, admin_id=user.id)
    workspace = await repository.create_workspace(session, workspace)
    await repository.add_member(session, workspace.id, user.id)
    for model_id in model_ids:
        await repository.add_model_link(session, workspace.id, model_id)
    return workspace


async def list_available_models(session: AsyncSession) -> list[GlobalModel]:
    return await repository.get_all_global_models(session)


async def list_workspaces(session: AsyncSession, user: User) -> list[Workspace]:
    return await repository.get_user_workspaces(session, user.id)


async def get_workspace(session: AsyncSession, workspace_id: uuid.UUID, user: User) -> Workspace:
    workspace = await _get_workspace_or_404(session, workspace_id)
    await _require_membership(session, workspace_id, user)
    return workspace


async def delete_workspace(session: AsyncSession, workspace_id: uuid.UUID, user: User) -> None:
    workspace = await _get_workspace_or_404(session, workspace_id)
    _require_admin(workspace, user)
    await repository.delete_workspace(session, workspace)


async def add_member(session: AsyncSession, workspace_id: uuid.UUID, username: str, user: User) -> None:
    workspace = await _get_workspace_or_404(session, workspace_id)
    _require_admin(workspace, user)

    target = await get_user_by_username(session, username)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.is_owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owners cannot be added to workspaces")
    if target.id == workspace.admin_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace creator is already a member")
    if await repository.is_member(session, workspace_id, target.id):
        raise HTTPException(status_code=400, detail="User already a member")
    await repository.add_member(session, workspace_id, target.id)


async def remove_member(
    session: AsyncSession, workspace_id: uuid.UUID, target_user_id: uuid.UUID, user: User,
) -> None:
    workspace = await _get_workspace_or_404(session, workspace_id)
    _require_admin(workspace, user)
    if target_user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
    await repository.remove_member(session, workspace_id, target_user_id)


async def list_members(session: AsyncSession, workspace_id: uuid.UUID, user: User):
    await _get_workspace_or_404(session, workspace_id)
    await _require_membership(session, workspace_id, user)
    return await repository.get_members(session, workspace_id)


async def add_model(session: AsyncSession, workspace_id: uuid.UUID, model_id: uuid.UUID, user: User) -> None:
    workspace = await _get_workspace_or_404(session, workspace_id)
    _require_admin(workspace, user)
    await repository.add_model_link(session, workspace_id, model_id)


async def remove_model(
    session: AsyncSession, workspace_id: uuid.UUID, model_id: uuid.UUID, user: User,
) -> None:
    workspace = await _get_workspace_or_404(session, workspace_id)
    _require_admin(workspace, user)
    await repository.remove_model_link(session, workspace_id, model_id)


async def list_models(session: AsyncSession, workspace_id: uuid.UUID, user: User):
    await _get_workspace_or_404(session, workspace_id)
    await _require_membership(session, workspace_id, user)
    return await repository.get_allowed_models(session, workspace_id)
