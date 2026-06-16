# File: models.py. Description: Workspace database models. Consists of: Workspace, WorkspaceUserLink, WorkspaceModelLink, and GlobalModel SQLModel tables.
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Column, Numeric, DateTime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from src.modules.auth.models import User
    from src.modules.conversations.models import Conversation


class WorkspaceUserLink(SQLModel, table=True):
    __tablename__ = "workspace_user_links"

    workspace_id: uuid.UUID = Field(foreign_key="workspaces.id", primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)


class WorkspaceModelLink(SQLModel, table=True):
    __tablename__ = "workspace_model_links"

    workspace_id: uuid.UUID = Field(foreign_key="workspaces.id", primary_key=True)
    model_id: uuid.UUID = Field(foreign_key="global_models.id", primary_key=True)


class Workspace(SQLModel, table=True):
    __tablename__ = "workspaces"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(nullable=False)
    admin_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    # Relationships
    members: List["User"] = Relationship(
        back_populates="workspaces",
        link_model=WorkspaceUserLink,
    )
    allowed_models: List["GlobalModel"] = Relationship(link_model=WorkspaceModelLink)
    conversations: List["Conversation"] = Relationship(
        back_populates="workspace",
        cascade_delete=True,
    )


class GlobalModel(SQLModel, table=True):
    __tablename__ = "global_models"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    llm_company_name: str = Field(nullable=False)
    model_type: str = Field(nullable=False)
    model_name: str = Field(unique=True, nullable=False, index=True)
    api_key: str = Field(nullable=False)
    requires_manual_pricing: bool = Field(default=False, nullable=False)
    fallback_input_cost_per_million: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(12, 6), nullable=True),
    )
    fallback_output_cost_per_million: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(12, 6), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
