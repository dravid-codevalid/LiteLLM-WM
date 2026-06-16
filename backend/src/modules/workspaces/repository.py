# File: repository.py. Description: Workspace database operations. Consists of: CRUD functions for Workspaces, Members, and Allowed Models.
import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.workspaces.models import (
    Workspace, WorkspaceUserLink, WorkspaceModelLink, GlobalModel,
)
from src.modules.auth.models import User


async def create_workspace(session: AsyncSession, workspace: Workspace) -> Workspace:
    session.add(workspace)
    await session.commit()
    await session.refresh(workspace)
    return workspace


async def get_workspace_by_id(session: AsyncSession, workspace_id: uuid.UUID) -> Workspace | None:
    return await session.get(Workspace, workspace_id)


async def get_user_workspaces(session: AsyncSession, user_id: uuid.UUID) -> list[Workspace]:
    stmt = (
        select(Workspace)
        .join(WorkspaceUserLink)
        .where(WorkspaceUserLink.user_id == user_id)
    )
    result = await session.exec(stmt)
    return list(result.all())


async def delete_workspace(session: AsyncSession, workspace: Workspace) -> None:
    await session.delete(workspace)
    await session.commit()


async def add_member(session: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID) -> None:
    link = WorkspaceUserLink(workspace_id=workspace_id, user_id=user_id)
    session.add(link)
    await session.commit()


async def remove_member(session: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID) -> None:
    stmt = select(WorkspaceUserLink).where(
        WorkspaceUserLink.workspace_id == workspace_id,
        WorkspaceUserLink.user_id == user_id,
    )
    result = await session.exec(stmt)
    link = result.first()
    if link:
        await session.delete(link)
        await session.commit()


async def get_members(session: AsyncSession, workspace_id: uuid.UUID) -> list[User]:
    stmt = (
        select(User)
        .join(WorkspaceUserLink)
        .where(WorkspaceUserLink.workspace_id == workspace_id)
    )
    result = await session.exec(stmt)
    return list(result.all())


async def is_member(session: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    stmt = select(WorkspaceUserLink).where(
        WorkspaceUserLink.workspace_id == workspace_id,
        WorkspaceUserLink.user_id == user_id,
    )
    result = await session.exec(stmt)
    return result.first() is not None


async def add_model_link(session: AsyncSession, workspace_id: uuid.UUID, model_id: uuid.UUID) -> None:
    link = WorkspaceModelLink(workspace_id=workspace_id, model_id=model_id)
    session.add(link)
    await session.commit()


async def remove_model_link(session: AsyncSession, workspace_id: uuid.UUID, model_id: uuid.UUID) -> None:
    stmt = select(WorkspaceModelLink).where(
        WorkspaceModelLink.workspace_id == workspace_id,
        WorkspaceModelLink.model_id == model_id,
    )
    result = await session.exec(stmt)
    link = result.first()
    if link:
        await session.delete(link)
        await session.commit()


async def get_allowed_models(session: AsyncSession, workspace_id: uuid.UUID) -> list[GlobalModel]:
    stmt = (
        select(GlobalModel)
        .join(WorkspaceModelLink)
        .where(WorkspaceModelLink.workspace_id == workspace_id)
    )
    result = await session.exec(stmt)
    return list(result.all())


async def is_model_allowed(session: AsyncSession, workspace_id: uuid.UUID, model_name: str) -> GlobalModel | None:
    stmt = (
        select(GlobalModel)
        .join(WorkspaceModelLink)
        .where(
            WorkspaceModelLink.workspace_id == workspace_id,
            GlobalModel.model_name == model_name,
        )
    )
    result = await session.exec(stmt)
    return result.first()


async def get_all_global_models(session: AsyncSession) -> list[GlobalModel]:
    stmt = select(GlobalModel)
    result = await session.exec(stmt)
    return list(result.all())
