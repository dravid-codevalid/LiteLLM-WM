# File: router.py. Description: Admin API endpoints. Consists of: FastAPI router for GlobalModel CRUD operations and cross-workspace usage analytics.
import uuid

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.admin.schemas import (
    CreateGlobalModelRequest, UpdateGlobalModelRequest, GlobalModelResponse,
)
from src.modules.admin import service
from src.modules.auth.models import User
from src.shared.db.engine import get_session
from src.shared.middleware.auth import require_owner

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _to_response(model) -> GlobalModelResponse:
    return GlobalModelResponse(
        id=model.id,
        llm_company_name=model.llm_company_name,
        model_type=model.model_type,
        model_name=model.model_name,
        api_key_masked=service.mask_api_key(model.api_key),
        requires_manual_pricing=model.requires_manual_pricing,
        fallback_input_cost_per_million=(
            float(model.fallback_input_cost_per_million)
            if model.fallback_input_cost_per_million is not None
            else None
        ),
        fallback_output_cost_per_million=(
            float(model.fallback_output_cost_per_million)
            if model.fallback_output_cost_per_million is not None
            else None
        ),
    )


@router.get("/models")
async def list_models(
    _: User = Depends(require_owner),
    session: AsyncSession = Depends(get_session),
):
    models = await service.list_models(session)
    return {"success": True, "data": [_to_response(m) for m in models]}


@router.post("/models")
async def create_model(
    data: CreateGlobalModelRequest,
    _: User = Depends(require_owner),
    session: AsyncSession = Depends(get_session),
):
    model = await service.create_model(session, data)
    return {"success": True, "data": _to_response(model)}


@router.put("/models/{model_id}")
async def update_model(
    model_id: uuid.UUID,
    data: UpdateGlobalModelRequest,
    _: User = Depends(require_owner),
    session: AsyncSession = Depends(get_session),
):
    model = await service.update_model(session, model_id, data)
    return {"success": True, "data": _to_response(model)}


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: uuid.UUID,
    _: User = Depends(require_owner),
    session: AsyncSession = Depends(get_session),
):
    await service.delete_model(session, model_id)
    return {"success": True, "data": {"message": "Model deleted"}}


@router.get("/litellm-models")
async def list_litellm_models(
    _: User = Depends(require_owner),
):
    import litellm
    models_data = []
    for model_name, info in litellm.model_cost.items():
        if not isinstance(info, dict):
            continue
        provider = info.get("litellm_provider", "other")
        mode = info.get("mode", "chat")
        models_data.append({
            "model_name": model_name,
            "provider": provider,
            "model_type": mode
        })
    models_data.sort(key=lambda x: (x["provider"], x["model_name"]))
    return {"success": True, "data": models_data}


@router.get("/usage")
async def global_usage(
    _: User = Depends(require_owner),
    session: AsyncSession = Depends(get_session),
):
    data = await service.get_global_usage(session)
    return {"success": True, "data": data}


@router.get("/usage/{workspace_id}")
async def workspace_usage(
    workspace_id: uuid.UUID,
    _: User = Depends(require_owner),
    session: AsyncSession = Depends(get_session),
):
    data = await service.get_workspace_usage(session, workspace_id)
    return {"success": True, "data": data}
