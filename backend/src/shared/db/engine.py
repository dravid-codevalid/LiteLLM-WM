# File: engine.py. Description: Database connection setup. Consists of: async SQLAlchemy engine, SQLModel session factory, and get_session dependency.
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession
from sqlalchemy.orm import sessionmaker

from src.shared.config.settings import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

async_session_factory = sessionmaker(
    engine, class_=SQLModelAsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[SQLModelAsyncSession, None]:
    async with async_session_factory() as session:
        yield session
