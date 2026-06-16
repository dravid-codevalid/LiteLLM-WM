# File: create_owner.py. Description: CLI script for initial setup. Consists of: logic to seed the primary Application Owner account directly in the database.
"""Seed the Application Owner user via CLI."""
import argparse
import asyncio
import os
import sys

# Add parent directory of scripts/ (backend root) to sys.path to allow src imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel.ext.asyncio.session import AsyncSession

# Import all models to register them with SQLModel/SQLAlchemy registry
from src.modules.auth.models import User  # noqa: F401
from src.modules.workspaces.models import (  # noqa: F401
    Workspace, WorkspaceUserLink, WorkspaceModelLink, GlobalModel,
)
from src.modules.conversations.models import Conversation, Message  # noqa: F401
from src.modules.usage.models import UsageLedger  # noqa: F401

from src.shared.db.engine import async_session_factory
from src.modules.auth.service import hash_password
from src.modules.auth import repository


async def create_owner(username: str, email: str, password: str) -> None:
    async with async_session_factory() as session:
        if await repository.get_user_by_username(session, username):
            print(f"User '{username}' already exists.")
            return

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_owner=True,
        )
        await repository.create_user(session, user)
        print(f"Application Owner '{username}' created successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create Application Owner")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    asyncio.run(create_owner(args.username, args.email, args.password))
