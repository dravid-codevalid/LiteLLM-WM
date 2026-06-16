# File: models.py. Description: Usage database models. Consists of: UsageLedger SQLModel table for immutable financial records.
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Numeric, DateTime
from sqlmodel import SQLModel, Field


class UsageLedger(SQLModel, table=True):
    __tablename__ = "usage_ledger"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="workspaces.id",
        ondelete="SET NULL",
        nullable=True,
        index=True,
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    model_name: str = Field(nullable=False)
    message_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="messages.id",
        ondelete="SET NULL",
        nullable=True,
    )
    prompt_tokens: int = Field(default=0, nullable=False)
    completion_tokens: int = Field(default=0, nullable=False)
    total_tokens: int = Field(default=0, nullable=False)
    calculated_cost: Decimal = Field(
        default=Decimal("0.000000"),
        sa_column=Column(Numeric(12, 6), nullable=False, default=0),
    )
    is_flagged_error: bool = Field(default=False, nullable=False)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
