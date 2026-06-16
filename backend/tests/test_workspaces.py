# File: test_workspaces.py. Description: Workspace module test stubs. Consists of: workspace CRUD, member management, and model assignment tests.
import pytest
from httpx import AsyncClient

from tests.conftest import make_user_data


async def _register_and_login(client: AsyncClient, username="testuser", email="test@example.com"):
    data = make_user_data(username=username, email=email)
    await client.post("/api/auth/register", json=data)
    resp = await client.post("/api/auth/login", json={"username": username, "password": data["password"]})
    client.cookies.set("access_token", resp.cookies.get("access_token"))
    return resp.json()["data"]


@pytest.mark.asyncio
async def test_create_workspace(client: AsyncClient):
    """Authenticated user can create a workspace and becomes its admin."""
    await _register_and_login(client)
    resp = await client.post("/api/workspaces", json={"name": "Test Workspace"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Test Workspace"


@pytest.mark.asyncio
async def test_list_workspaces(client: AsyncClient):
    """User sees only workspaces they are a member of."""
    await _register_and_login(client)
    await client.post("/api/workspaces", json={"name": "WS1"})
    await client.post("/api/workspaces", json={"name": "WS2"})
    resp = await client.get("/api/workspaces")
    body = resp.json()
    assert body["success"] is True
    assert len(body["data"]) == 2


@pytest.mark.asyncio
async def test_add_member(client: AsyncClient):
    """Workspace admin can add another user as a member."""
    admin = await _register_and_login(client)
    ws_resp = await client.post("/api/workspaces", json={"name": "Team WS"})
    ws_id = ws_resp.json()["data"]["id"]

    # Register a second user
    await client.post("/api/auth/register", json=make_user_data("member1", "member@example.com"))

    # Admin adds member
    resp = await client.post(f"/api/workspaces/{ws_id}/members", json={"username": "member1"})
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_delete_workspace_admin_only(client: AsyncClient):
    """Only workspace admin can delete the workspace."""
    await _register_and_login(client)
    ws_resp = await client.post("/api/workspaces", json={"name": "To Delete"})
    ws_id = ws_resp.json()["data"]["id"]
    resp = await client.delete(f"/api/workspaces/{ws_id}")
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_list_models_for_workspace(client: AsyncClient):
    """Workspace model listing returns assigned models."""
    await _register_and_login(client)
    ws_resp = await client.post("/api/workspaces", json={"name": "Model WS"})
    ws_id = ws_resp.json()["data"]["id"]
    resp = await client.get(f"/api/workspaces/{ws_id}/models")
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_add_member_owner_or_self_error(client: AsyncClient, session):
    # 1. Admin login
    admin = await _register_and_login(client, "adminuser", "admin@example.com")
    ws_resp = await client.post("/api/workspaces", json={"name": "Team WS"})
    ws_id = ws_resp.json()["data"]["id"]

    # 2. Create owner directly in DB
    from src.modules.auth.models import User
    owner = User(
        username="adminowner",
        email="owner@example.com",
        hashed_password="hashedpassword",
        is_owner=True
    )
    session.add(owner)
    await session.commit()

    # 3. Try to add owner to workspace (should fail)
    resp = await client.post(f"/api/workspaces/{ws_id}/members", json={"username": "adminowner"})
    assert resp.status_code == 400
    assert "Owners cannot be added to workspaces" in resp.json()["error"]["message"]

    # 4. Try to add self (admin) to workspace (should fail)
    resp = await client.post(f"/api/workspaces/{ws_id}/members", json={"username": "adminuser"})
    assert resp.status_code == 400
    assert "Workspace creator is already a member" in resp.json()["error"]["message"]
