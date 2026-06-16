# File: repository.py. Description: Authentication database operations. Consists of: CRUD functions for User records.
import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.auth.models import User


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.exec(select(User).where(User.username == username))
    return result.first()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.exec(select(User).where(User.email == email))
    return result.first()


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await session.get(User, user_id)


async def create_user(session: AsyncSession, user: User) -> User:
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def search_users_by_prefix(
    session: AsyncSession, prefix: str, exclude_user_id: uuid.UUID = None, limit: int = 10
) -> list[User]:
    query = select(User).where(User.username.startswith(prefix)).where(User.is_owner == False)
    if exclude_user_id is not None:
        query = query.where(User.id != exclude_user_id)
    result = await session.exec(query.limit(limit))
    return list(result.all())
