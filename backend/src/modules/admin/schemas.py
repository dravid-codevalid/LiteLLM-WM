# File: schemas.py. Description: Admin data transfer objects. Consists of: Pydantic schemas for creating/updating GlobalModels and returning masked API keys.
import uuid
from typing import Optional
from pydantic import BaseModel, Field


class CreateGlobalModelRequest(BaseModel):
    llm_company_name: str
    model_type: str = "chat"
    model_name: str
    api_key: str
    requires_manual_pricing: bool = False
    fallback_input_cost_per_million: Optional[float] = None
    fallback_output_cost_per_million: Optional[float] = None


class UpdateGlobalModelRequest(BaseModel):
    llm_company_name: Optional[str] = None
    model_type: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    requires_manual_pricing: Optional[bool] = None
    fallback_input_cost_per_million: Optional[float] = None
    fallback_output_cost_per_million: Optional[float] = None


class GlobalModelResponse(BaseModel):
    id: uuid.UUID
    llm_company_name: str
    model_type: str
    model_name: str
    api_key_masked: str  # e.g. "sk-****abcd"
    requires_manual_pricing: bool
    fallback_input_cost_per_million: Optional[float]
    fallback_output_cost_per_million: Optional[float]
