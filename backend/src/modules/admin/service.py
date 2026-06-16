# File: service.py. Description: Admin business logic. Consists of: GlobalModel CRUD operations and cross-workspace usage analytics.
import uuid

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.admin import repository
from src.modules.admin.schemas import CreateGlobalModelRequest, UpdateGlobalModelRequest
from src.modules.workspaces.models import GlobalModel
from src.modules.usage import repository as usage_repository


def mask_api_key(key: str) -> str:
    """Mask an API key for display, showing only first 3 and last 4 characters."""
    if len(key) <= 8:
        return "****"
    return key[:3] + "****" + key[-4:]


async def list_models(session: AsyncSession) -> list[GlobalModel]:
    return await repository.get_all_models(session)


async def create_model(
    session: AsyncSession, data: CreateGlobalModelRequest,
) -> GlobalModel:
    model = GlobalModel(**data.model_dump())
    return await repository.create_model(session, model)


async def update_model(
    session: AsyncSession, model_id: uuid.UUID, data: UpdateGlobalModelRequest,
) -> GlobalModel:
    model = await repository.get_model_by_id(session, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(model, key, value)

    return await repository.update_model(session, model)


async def delete_model(session: AsyncSession, model_id: uuid.UUID) -> None:
    model = await repository.get_model_by_id(session, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    await repository.delete_model(session, model)


async def get_global_usage(session: AsyncSession) -> list[dict]:
    """Cross-workspace financial analytics for the Application Owner."""
    return await usage_repository.get_all_workspaces_usage(session)


async def get_workspace_usage(session: AsyncSession, workspace_id: uuid.UUID) -> dict:
    """Single workspace financial breakdown for the Application Owner."""
    return await usage_repository.get_workspace_usage(session, workspace_id)
