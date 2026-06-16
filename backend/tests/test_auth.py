# File: test_auth.py. Description: Auth module test stubs. Consists of: registration, login, and session validation tests.
import pytest
from httpx import AsyncClient

from tests.conftest import make_user_data


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """New user registration returns user data and sets cookie."""
    data = make_user_data()
    resp = await client.post("/api/auth/register", json=data)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["username"] == data["username"]
    assert body["data"]["email"] == data["email"]


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """Duplicate username registration returns an error."""
    data = make_user_data()
    await client.post("/api/auth/register", json=data)
    resp = await client.post("/api/auth/register", json=data)
    assert resp.status_code == 400
    body = resp.json()
    assert body["success"] is False


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Valid credentials return user data with JWT cookie."""
    data = make_user_data()
    await client.post("/api/auth/register", json=data)
    resp = await client.post("/api/auth/login", json={"username": data["username"], "password": data["password"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "access_token" in resp.cookies


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Invalid credentials return authentication error."""
    resp = await client.post("/api/auth/login", json={"username": "nouser", "password": "wrong"})
    body = resp.json()
    assert body["success"] is False


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient):
    """Authenticated user can retrieve their profile via /me."""
    data = make_user_data()
    await client.post("/api/auth/register", json=data)
    login_resp = await client.post("/api/auth/login", json={"username": data["username"], "password": data["password"]})
    client.cookies.set("access_token", login_resp.cookies.get("access_token"))
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["username"] == data["username"]


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """Unauthenticated request to /me returns 401."""
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_search_users_filter(client: AsyncClient, session):
    # 1. Register and login User 1
    u1_data = make_user_data("userone", "u1@example.com")
    await client.post("/api/auth/register", json=u1_data)
    login_resp = await client.post("/api/auth/login", json={"username": u1_data["username"], "password": u1_data["password"]})
    client.cookies.set("access_token", login_resp.cookies.get("access_token"))

    # 2. Register User 2 (normal user)
    u2_data = make_user_data("usertwo", "u2@example.com")
    await client.post("/api/auth/register", json=u2_data)

    # 3. Create an owner user directly in DB
    from src.modules.auth.models import User
    owner = User(
        username="adminowner",
        email="owner@example.com",
        hashed_password="hashedpassword",
        is_owner=True
    )
    session.add(owner)
    await session.commit()

    # 4. Search for "user"
    resp = await client.get("/api/auth/users/search?q=user")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    usernames = [u["username"] for u in body["data"]]
    
    # User 1 (self) should not be visible
    assert "userone" not in usernames
    # Owner should not be visible
    assert "adminowner" not in usernames
    # User 2 should be visible
    assert "usertwo" in usernames
