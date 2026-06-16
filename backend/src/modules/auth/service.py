# File: service.py. Description: Authentication business logic. Consists of: password hashing, JWT token generation/validation, and register/login flows.
import uuid
from datetime import datetime, timezone, timedelta

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.auth.models import User
from src.modules.auth import repository
from src.modules.auth.schemas import RegisterRequest, LoginRequest, UserResponse
from src.shared.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


async def register(session: AsyncSession, data: RegisterRequest) -> tuple[User, str]:
    if await repository.get_user_by_username(session, data.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    if await repository.get_user_by_email(session, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    user = await repository.create_user(session, user)
    token = create_access_token(user.id)
    return user, token


async def login(session: AsyncSession, data: LoginRequest) -> tuple[User, str]:
    user = await repository.get_user_by_username(session, data.username)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return user, token


async def get_current_user_from_token(session: AsyncSession, token: str) -> User:
    user_id = decode_access_token(token)
    user = await repository.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def search_users(session: AsyncSession, prefix: str, exclude_user_id: uuid.UUID = None) -> list[User]:
    if not prefix:
        return []
    return await repository.search_users_by_prefix(session, prefix, exclude_user_id)
