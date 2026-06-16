# File: activities.py. Description: Temporal activities. Consists of: record_usage_activity wrapping the usage service for Temporal execution.
import uuid
from dataclasses import dataclass

from temporalio import activity

from src.shared.db.engine import async_session_factory
from src.modules.usage.service import record_usage


@dataclass
class UsageActivityInput:
    workspace_id: str
    user_id: str
    message_id: str | None
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    is_flagged_error: bool = False


@activity.defn
async def record_usage_activity(input: UsageActivityInput) -> str:
    async with async_session_factory() as session:
        record = await record_usage(
            session=session,
            workspace_id=uuid.UUID(input.workspace_id),
            user_id=uuid.UUID(input.user_id),
            message_id=uuid.UUID(input.message_id) if input.message_id else None,
            model_name=input.model_name,
            prompt_tokens=input.prompt_tokens,
            completion_tokens=input.completion_tokens,
            is_flagged_error=input.is_flagged_error,
        )
    return str(record.id)
