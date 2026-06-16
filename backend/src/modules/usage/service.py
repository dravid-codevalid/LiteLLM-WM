# File: service.py. Description: Usage business logic. Consists of: token cost calculation logic, ledger record insertion, and visibility-rule query methods.
import uuid
from decimal import Decimal
import logging

import litellm
from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from src.modules.usage.models import UsageLedger
from src.modules.usage import repository
from src.modules.workspaces.models import GlobalModel
from src.modules.workspaces import repository as ws_repository
from src.modules.auth.models import User

logger = logging.getLogger(__name__)


def calculate_cost(
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    fallback_input_cost: Decimal | None = None,
    fallback_output_cost: Decimal | None = None,
) -> Decimal:
    """
    Step 1: Look up in litellm.model_cost
    Step 2: Fall back to GlobalModel's manual pricing
    Step 3: Calculate cost
    """
    model_info = litellm.model_cost.get(model_name)

    if model_info:
        input_cost_per_token = Decimal(str(model_info.get("input_cost_per_token", 0)))
        output_cost_per_token = Decimal(str(model_info.get("output_cost_per_token", 0)))
    elif fallback_input_cost is not None and fallback_output_cost is not None:
        input_cost_per_token = fallback_input_cost / Decimal("1000000")
        output_cost_per_token = fallback_output_cost / Decimal("1000000")
    else:
        logger.warning(f"No pricing for model {model_name}, cost will be 0")
        return Decimal("0.000000")

    cost = (Decimal(prompt_tokens) * input_cost_per_token) + (
        Decimal(completion_tokens) * output_cost_per_token
    )
    return cost.quantize(Decimal("0.000001"))


async def record_usage(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    message_id: uuid.UUID | None,
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    is_flagged_error: bool = False,
) -> UsageLedger:
    """Calculate cost and persist a ledger record."""
    # Look up fallback pricing from GlobalModel
    fallback_input: Decimal | None = None
    fallback_output: Decimal | None = None

    stmt = select(GlobalModel).where(GlobalModel.model_name == model_name)
    result = await session.exec(stmt)
    global_model = result.first()
    if global_model and global_model.requires_manual_pricing:
        fallback_input = global_model.fallback_input_cost_per_million
        fallback_output = global_model.fallback_output_cost_per_million

    cost = calculate_cost(
        model_name, prompt_tokens, completion_tokens, fallback_input, fallback_output
    )

    record = UsageLedger(
        workspace_id=workspace_id,
        user_id=user_id,
        message_id=message_id,
        model_name=model_name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        calculated_cost=cost,
        is_flagged_error=is_flagged_error,
    )
    return await repository.insert_ledger(session, record)


# --- Visibility-rule query methods (called by router via service layer) ---


async def get_my_usage(
    session: AsyncSession, workspace_id: uuid.UUID, user: User,
) -> dict:
    """Get current user's own usage summary. Enforces workspace membership."""
    if not await ws_repository.is_member(session, workspace_id, user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a workspace member"
        )
    return await repository.get_user_usage(session, workspace_id, user.id)


async def get_workspace_usage(
    session: AsyncSession, workspace_id: uuid.UUID, user: User,
) -> dict:
    """Get workspace-wide usage + per-user breakdown. Enforces workspace admin."""
    ws = await ws_repository.get_workspace_by_id(session, workspace_id)
    if not ws or ws.admin_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace admin access required",
        )
    return await repository.get_workspace_usage(session, workspace_id)
