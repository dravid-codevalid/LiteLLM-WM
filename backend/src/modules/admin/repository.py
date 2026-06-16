# File: repository.py. Description: Admin database operations. Consists of: CRUD functions for GlobalModel records.
import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.workspaces.models import GlobalModel


async def get_all_models(session: AsyncSession) -> list[GlobalModel]:
    result = await session.exec(select(GlobalModel))
    return list(result.all())


async def get_model_by_id(session: AsyncSession, model_id: uuid.UUID) -> GlobalModel | None:
    return await session.get(GlobalModel, model_id)


async def create_model(session: AsyncSession, model: GlobalModel) -> GlobalModel:
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return model


async def update_model(session: AsyncSession, model: GlobalModel) -> GlobalModel:
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return model


async def delete_model(session: AsyncSession, model: GlobalModel) -> None:
    await session.delete(model)
    await session.commit()
