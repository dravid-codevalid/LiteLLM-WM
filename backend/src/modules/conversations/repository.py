# File: repository.py. Description: Conversation database operations. Consists of: CRUD functions for conversations and messages.
import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.conversations.models import Conversation, Message


async def create_conversation(session: AsyncSession, conversation: Conversation) -> Conversation:
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def get_conversations_by_workspace(session: AsyncSession, workspace_id: uuid.UUID) -> list[Conversation]:
    result = await session.exec(
        select(Conversation).where(Conversation.workspace_id == workspace_id)
    )
    return list(result.all())


async def get_conversation_by_id(session: AsyncSession, conversation_id: uuid.UUID) -> Conversation | None:
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    result = await session.exec(stmt)
    return result.first()


async def delete_conversation(session: AsyncSession, conversation: Conversation) -> None:
    await session.delete(conversation)
    await session.commit()


async def create_message(session: AsyncSession, message: Message) -> Message:
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def get_messages_by_conversation(session: AsyncSession, conversation_id: uuid.UUID) -> list[Message]:
    result = await session.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp)
    )
    return list(result.all())
