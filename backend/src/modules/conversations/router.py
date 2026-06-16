# File: router.py. Description: Conversation API endpoints. Consists of: FastAPI router for REST CRUD operations and the main WebSocket streaming endpoint.
import uuid
import json
import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlmodel.ext.asyncio.session import AsyncSession
from temporalio.client import Client

from src.modules.auth.models import User
from src.modules.conversations import service
from src.modules.conversations.schemas import (
    CreateConversationRequest, ConversationResponse, ConversationDetailResponse,
    MessageResponse,
)
from src.modules.conversations.connection_manager import manager
from src.modules.llm.adapters.litellm_adapter import LiteLLMAdapter
from src.modules.auth.service import get_current_user_from_token
from src.modules.usage.workflows import BillingWorkflow, BillingWorkflowInput
from src.shared.config.settings import settings
from src.shared.db.engine import get_session, async_session_factory
from src.shared.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["conversations"])


@router.post("/api/workspaces/{workspace_id}/conversations")
async def create_conversation(
    workspace_id: uuid.UUID,
    data: CreateConversationRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    conv = await service.create_conversation(session, workspace_id, data.title, user)
    return {"success": True, "data": ConversationResponse.model_validate(conv)}


@router.get("/api/workspaces/{workspace_id}/conversations")
async def list_conversations(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    convs = await service.list_conversations(session, workspace_id, user)
    return {"success": True, "data": [ConversationResponse.model_validate(c) for c in convs]}


@router.get("/api/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    conv = await service.get_conversation(session, conversation_id, user)
    return {"success": True, "data": ConversationDetailResponse.model_validate(conv)}


@router.delete("/api/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await service.delete_conversation(session, conversation_id, user)
    return {"success": True, "data": {"message": "Conversation deleted"}}


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(ws: WebSocket, conversation_id: uuid.UUID):
    # Auth via query param (preferred) or cookie fallback
    token = ws.query_params.get("token") or ws.cookies.get("access_token")
    if not token:
        await ws.close(code=4001, reason="Not authenticated")
        return

    async with async_session_factory() as session:
        try:
            user = await get_current_user_from_token(session, token)
        except Exception:
            await ws.close(code=4001, reason="Invalid token")
            return

        # Get conversation to find workspace_id
        conv = await service.get_conversation(session, conversation_id, user)
        workspace_id = conv.workspace_id

    await manager.connect(ws, workspace_id, user.id, user.username)

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)

            if data.get("type") != "send_message":
                await ws.send_json({"type": "error", "detail": "Unknown message type"})
                continue

            model = data.get("model", "")
            prompt = data.get("prompt", "")

            if not model or not prompt:
                await ws.send_json({"type": "error", "detail": "model and prompt are required"})
                continue

            llm_provider = LiteLLMAdapter()

            async with async_session_factory() as session:
                try:
                    async for chunk, message, usage in service.handle_chat_message(
                        session, conversation_id, model, prompt, user, llm_provider,
                    ):
                        if chunk is not None:
                            await ws.send_json({"type": "message_chunk", "content": chunk})
                        if message is not None and usage is not None:
                            await ws.send_json({
                                "type": "message_complete",
                                "message_id": str(message.id),
                                "model_used": message.model_used,
                            })
                            # Dispatch Temporal billing workflow
                            try:
                                tc = await Client.connect(settings.TEMPORAL_HOST)
                                await tc.start_workflow(
                                    BillingWorkflow.run,
                                    BillingWorkflowInput(
                                        workspace_id=str(workspace_id),
                                        user_id=str(user.id),
                                        message_id=str(message.id),
                                        model_name=model,
                                        prompt_tokens=usage.prompt_tokens,
                                        completion_tokens=usage.completion_tokens,
                                    ),
                                    id=f"billing-{message.id}",
                                    task_queue=settings.TEMPORAL_TASK_QUEUE,
                                )
                            except Exception as billing_err:
                                logger.warning(f"Billing dispatch failed: {billing_err}")

                except Exception as e:
                    logger.error(f"LLM stream error: {e}")
                    await ws.send_json({"type": "error", "detail": str(e)})
                    # Crash circuit-breaker: log 0-token error record
                    try:
                        tc = await Client.connect(settings.TEMPORAL_HOST)
                        await tc.start_workflow(
                            BillingWorkflow.run,
                            BillingWorkflowInput(
                                workspace_id=str(workspace_id),
                                user_id=str(user.id),
                                message_id=None,
                                model_name=model,
                                prompt_tokens=0,
                                completion_tokens=0,
                                is_flagged_error=True,
                            ),
                            id=f"billing-error-{uuid.uuid4()}",
                            task_queue=settings.TEMPORAL_TASK_QUEUE,
                        )
                    except Exception as billing_err:
                        logger.warning(f"Crash billing dispatch failed: {billing_err}")

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(workspace_id, user.id)
