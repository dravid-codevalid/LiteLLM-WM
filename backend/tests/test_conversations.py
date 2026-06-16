# File: test_conversations.py. Description: Conversation module test stubs. Consists of: conversation CRUD and membership enforcement tests.
import pytest
from httpx import AsyncClient

from tests.conftest import make_user_data


async def _setup_workspace(client: AsyncClient):
    """Register user, login, and create a workspace."""
    data = make_user_data()
    await client.post("/api/auth/register", json=data)
    resp = await client.post("/api/auth/login", json={"username": data["username"], "password": data["password"]})
    client.cookies.set("access_token", resp.cookies.get("access_token"))
    ws_resp = await client.post("/api/workspaces", json={"name": "Chat WS"})
    return ws_resp.json()["data"]["id"]


@pytest.mark.asyncio
async def test_create_conversation(client: AsyncClient):
    """Workspace member can create a conversation."""
    ws_id = await _setup_workspace(client)
    resp = await client.post(f"/api/workspaces/{ws_id}/conversations", json={"title": "Research Chat"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Research Chat"


@pytest.mark.asyncio
async def test_list_conversations(client: AsyncClient):
    """Lists all conversations in a workspace."""
    ws_id = await _setup_workspace(client)
    await client.post(f"/api/workspaces/{ws_id}/conversations", json={"title": "Chat 1"})
    await client.post(f"/api/workspaces/{ws_id}/conversations", json={"title": "Chat 2"})
    resp = await client.get(f"/api/workspaces/{ws_id}/conversations")
    body = resp.json()
    assert body["success"] is True
    assert len(body["data"]) == 2


@pytest.mark.asyncio
async def test_get_conversation_with_messages(client: AsyncClient):
    """Getting a conversation includes its messages."""
    ws_id = await _setup_workspace(client)
    conv_resp = await client.post(f"/api/workspaces/{ws_id}/conversations", json={"title": "Detail Chat"})
    conv_id = conv_resp.json()["data"]["id"]
    resp = await client.get(f"/api/conversations/{conv_id}")
    body = resp.json()
    assert body["success"] is True
    assert "messages" in body["data"]


@pytest.mark.asyncio
async def test_delete_conversation(client: AsyncClient):
    """Workspace member can delete a conversation."""
    ws_id = await _setup_workspace(client)
    conv_resp = await client.post(f"/api/workspaces/{ws_id}/conversations", json={"title": "To Delete"})
    conv_id = conv_resp.json()["data"]["id"]
    resp = await client.delete(f"/api/conversations/{conv_id}")
    body = resp.json()
    assert body["success"] is True
