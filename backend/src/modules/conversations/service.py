# File: service.py. Description: Conversation business logic. Consists of: model validation, chat history assembly, LLM streaming execution, and message persistence.
import uuid
import logging

from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.auth.models import User
from src.modules.conversations.models import Conversation, Message
from src.modules.conversations import repository
from src.modules.workspaces import repository as ws_repository
from src.modules.llm.ports import LLMProvider, LLMUsage

logger = logging.getLogger(__name__)


async def create_conversation(
    session: AsyncSession, workspace_id: uuid.UUID, title: str, user: User,
) -> Conversation:
    if not await ws_repository.is_member(session, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Not a workspace member")
    conv = Conversation(title=title, workspace_id=workspace_id, created_by=user.id)
    return await repository.create_conversation(session, conv)


async def list_conversations(
    session: AsyncSession, workspace_id: uuid.UUID, user: User,
) -> list[Conversation]:
    if not await ws_repository.is_member(session, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Not a workspace member")
    return await repository.get_conversations_by_workspace(session, workspace_id)


async def get_conversation(
    session: AsyncSession, conversation_id: uuid.UUID, user: User,
) -> Conversation:
    conv = await repository.get_conversation_by_id(session, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not await ws_repository.is_member(session, conv.workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Not a workspace member")
    return conv


async def delete_conversation(
    session: AsyncSession, conversation_id: uuid.UUID, user: User,
) -> None:
    conv = await repository.get_conversation_by_id(session, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not await ws_repository.is_member(session, conv.workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Not a workspace member")
    await repository.delete_conversation(session, conv)


def build_message_history(messages: list[Message]) -> list[dict]:
    """Convert stored messages into the format LiteLLM expects."""
    history = []
    for msg in messages:
        history.append({"role": "user", "content": msg.prompt_text})
        history.append({"role": "assistant", "content": msg.response_text})
    return history


async def handle_chat_message(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    model_name: str,
    prompt: str,
    user: User,
    llm_provider: LLMProvider,
):
    """
    Full streaming pipeline:
    1. Validate model against workspace-allowed list
    2. Build history
    3. Stream LLM response
    4. Persist message
    5. Return usage for billing dispatch

    Yields: (chunk: str | None, message: Message | None, usage: LLMUsage | None)
    - chunk: streamed text piece
    - message: final persisted message (on completion)
    - usage: token usage (on completion)
    """
    conv = await repository.get_conversation_by_id(session, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 1. Validate model
    allowed_model = await ws_repository.is_model_allowed(session, conv.workspace_id, model_name)
    if not allowed_model:
        raise HTTPException(status_code=400, detail=f"Model {model_name} is not allowed in this workspace")

    # 2. Build history
    existing_messages = await repository.get_messages_by_conversation(session, conversation_id)
    history = build_message_history(existing_messages)
    history.append({"role": "user", "content": prompt})

    # 3. Stream
    full_response = ""
    async for chunk in llm_provider.stream(model_name, history, allowed_model.api_key):
        full_response += chunk
        yield chunk, None, None

    # 4. Persist
    usage = llm_provider.get_usage()
    message = Message(
        conversation_id=conversation_id,
        sender_id=user.id,
        sender_name=user.username,
        prompt_text=prompt,
        response_text=full_response,
        model_used=model_name,
    )
    message = await repository.create_message(session, message)

    yield None, message, usage
