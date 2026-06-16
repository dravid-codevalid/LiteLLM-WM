# File: models.py. Description: Conversation database models. Consists of: Conversation and Message SQLModel tables.
import uuid
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING

from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from src.modules.workspaces.models import Workspace
    from src.modules.auth.models import User


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(nullable=False)
    workspace_id: uuid.UUID = Field(
        foreign_key="workspaces.id", ondelete="CASCADE", nullable=False
    )
    created_by: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    # Relationships
    workspace: "Workspace" = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(
        back_populates="conversation",
        cascade_delete=True,
    )


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(
        foreign_key="conversations.id", ondelete="CASCADE", nullable=False
    )
    sender_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    sender_name: str = Field(nullable=False)
    prompt_text: str = Field(nullable=False)
    response_text: str = Field(nullable=False)
    model_used: str = Field(nullable=False)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")
    sender: "User" = Relationship(back_populates="messages")
