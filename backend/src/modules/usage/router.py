# File: router.py. Description: Usage API endpoints. Consists of: FastAPI router serving usage analytics for members and admins.
import uuid

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.auth.models import User
from src.modules.usage import service
from src.modules.usage.schemas import UsageSummaryResponse, WorkspaceUsageResponse, UserUsageBreakdown
from src.shared.db.engine import get_session
from src.shared.middleware.auth import get_current_user

router = APIRouter(tags=["usage"])


@router.get("/api/workspaces/{workspace_id}/usage/me")
async def my_usage(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await service.get_my_usage(session, workspace_id, user)
    return {"success": True, "data": UsageSummaryResponse(**data)}


@router.get("/api/workspaces/{workspace_id}/usage")
async def workspace_usage(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await service.get_workspace_usage(session, workspace_id, user)
    return {
        "success": True,
        "data": WorkspaceUsageResponse(
            workspace_total=UsageSummaryResponse(**data["total"]),
            per_user=[UserUsageBreakdown(**u) for u in data["per_user"]],
        ),
    }
