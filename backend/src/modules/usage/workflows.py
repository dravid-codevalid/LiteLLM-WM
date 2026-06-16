# File: workflows.py. Description: Temporal workflows. Consists of: BillingWorkflow definition for reliable usage processing.
import uuid
from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from src.modules.usage.activities import record_usage_activity, UsageActivityInput


@dataclass
class BillingWorkflowInput:
    workspace_id: str
    user_id: str
    message_id: str | None
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    is_flagged_error: bool = False


@workflow.defn
class BillingWorkflow:
    @workflow.run
    async def run(self, input: BillingWorkflowInput) -> str:
        activity_input = UsageActivityInput(
            workspace_id=input.workspace_id,
            user_id=input.user_id,
            message_id=input.message_id,
            model_name=input.model_name,
            prompt_tokens=input.prompt_tokens,
            completion_tokens=input.completion_tokens,
            is_flagged_error=input.is_flagged_error,
        )
        result = await workflow.execute_activity(
            record_usage_activity,
            activity_input,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return result
