# File: models.py. Description: Authentication database models. Consists of: User SQLModel table mapping.
import uuid
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING

from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship

# link_model requires the actual class at import time (not under TYPE_CHECKING)
from src.modules.workspaces.models import WorkspaceUserLink

if TYPE_CHECKING:
    from src.modules.workspaces.models import Workspace
    from src.modules.conversations.models import Message


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(max_length=15, unique=True, index=True, nullable=False)
    email: str = Field(unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    is_owner: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    # Relationships
    workspaces: List["Workspace"] = Relationship(
        back_populates="members",
        link_model=WorkspaceUserLink,
    )
    messages: List["Message"] = Relationship(back_populates="sender")
