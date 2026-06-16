# File: auth.py. Description: Authentication middleware. Consists of: dependencies for extracting current user from JWT cookie and enforcing owner access.
from fastapi import Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.auth.models import User
from src.modules.auth import service as auth_service
from src.shared.db.engine import get_session


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return await auth_service.get_current_user_from_token(session, token)


async def require_owner(user: User = Depends(get_current_user)) -> User:
    if not user.is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    return user
