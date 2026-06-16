# File: router.py. Description: Authentication API endpoints. Consists of: FastAPI router for /register, /login, /logout, and /me routes.
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.auth import service as auth_service
from src.modules.auth.schemas import RegisterRequest, LoginRequest, UserResponse
from src.modules.auth.models import User
from src.shared.db.engine import get_session
from src.shared.middleware.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24,
    )


@router.post("/register")
async def register(
    data: RegisterRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    user, token = await auth_service.register(session, data)
    _set_cookie(response, token)
    return {"success": True, "data": UserResponse.model_validate(user)}


@router.post("/login")
async def login(
    data: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    user, token = await auth_service.login(session, data)
    _set_cookie(response, token)
    return {"success": True, "data": UserResponse.model_validate(user)}


@router.post("/logout")
async def logout(response: Response, _: User = Depends(get_current_user)):
    response.delete_cookie("access_token")
    return {"success": True, "data": {"message": "Logged out"}}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"success": True, "data": UserResponse.model_validate(user)}


@router.get("/ws-token")
async def ws_token(request: Request):
    """Return the raw access_token for WebSocket authentication.
    This endpoint is called via the Next.js API proxy (same-origin),
    so the httponly cookie is sent. The frontend then passes this token
    as a query parameter when opening the cross-origin WebSocket."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"success": True, "data": {"token": token}}


@router.get("/users/search")
async def search_users(
    q: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    users = await auth_service.search_users(session, q, exclude_user_id=current_user.id)
    return {"success": True, "data": [UserResponse.model_validate(u) for u in users]}
