# File: test_admin.py. Description: Admin module test stubs. Consists of: owner access enforcement, GlobalModel CRUD, and usage analytics tests.
import pytest
from httpx import AsyncClient

from tests.conftest import make_user_data
from src.modules.admin.service import mask_api_key


class TestMaskApiKey:
    """Unit tests for API key masking."""

    def test_normal_key(self):
        assert mask_api_key("sk-abc1234567890xyz") == "sk-****0xyz"

    def test_short_key(self):
        assert mask_api_key("short") == "****"

    def test_exactly_eight(self):
        assert mask_api_key("12345678") == "****"

    def test_nine_chars(self):
        assert mask_api_key("123456789") == "123****6789"


async def _login_as_owner(client: AsyncClient):
    """Register a user, then manually set is_owner (requires DB fixture)."""
    # In a real test, this would seed an owner via create_owner script or DB fixture
    data = make_user_data("owner", "owner@example.com")
    await client.post("/api/auth/register", json=data)
    resp = await client.post("/api/auth/login", json={"username": "owner", "password": data["password"]})
    client.cookies.set("access_token", resp.cookies.get("access_token"))


@pytest.mark.asyncio
async def test_owner_only_model_list(client: AsyncClient):
    """Non-owner users get 403 when accessing admin endpoints."""
    data = make_user_data()
    await client.post("/api/auth/register", json=data)
    resp = await client.post("/api/auth/login", json={"username": data["username"], "password": data["password"]})
    client.cookies.set("access_token", resp.cookies.get("access_token"))
    resp = await client.get("/api/admin/models")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_global_model():
    """Owner can create a global model with API key."""
    # Stub: requires owner DB fixture
    pass


@pytest.mark.asyncio
async def test_global_usage_analytics():
    """Owner can view cross-workspace usage analytics."""
    # Stub: requires owner + usage data fixtures
    pass


@pytest.mark.asyncio
async def test_list_litellm_models(client: AsyncClient, session):
    # 1. Register and login a user
    data = make_user_data("owneruser", "owner@example.com")
    await client.post("/api/auth/register", json=data)
    
    # 2. Directly set is_owner = True in DB
    from src.modules.auth.models import User
    from sqlmodel import select
    res = await session.exec(select(User).where(User.username == "owneruser"))
    user = res.one()
    user.is_owner = True
    session.add(user)
    await session.commit()
    
    login_resp = await client.post("/api/auth/login", json={"username": "owneruser", "password": data["password"]})
    client.cookies.set("access_token", login_resp.cookies.get("access_token"))
    
    # 3. Request litellm-models
    resp = await client.get("/api/admin/litellm-models")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert len(body["data"]) > 0
    first_model = body["data"][0]
    assert "model_name" in first_model
    assert "provider" in first_model
    assert "model_type" in first_model
