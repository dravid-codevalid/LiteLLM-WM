# File: repository.py. Description: Usage database operations. Consists of: queries aggregating token and cost metrics per user, workspace, and globally.
import uuid
from decimal import Decimal

from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.usage.models import UsageLedger
from src.modules.auth.models import User


async def insert_ledger(session: AsyncSession, record: UsageLedger) -> UsageLedger:
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def get_user_usage(
    session: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID,
) -> dict:
    stmt = select(
        func.coalesce(func.sum(UsageLedger.prompt_tokens), 0),
        func.coalesce(func.sum(UsageLedger.completion_tokens), 0),
        func.coalesce(func.sum(UsageLedger.total_tokens), 0),
        func.coalesce(func.sum(UsageLedger.calculated_cost), Decimal("0")),
        func.count(UsageLedger.id),
    ).where(
        UsageLedger.workspace_id == workspace_id,
        UsageLedger.user_id == user_id,
    )
    result = await session.exec(stmt)
    row = result.one()
    return {
        "total_prompt_tokens": row[0],
        "total_completion_tokens": row[1],
        "total_tokens": row[2],
        "total_cost": float(row[3]),
        "record_count": row[4],
    }


async def get_workspace_usage(session: AsyncSession, workspace_id: uuid.UUID) -> dict:
    # Total
    total_stmt = select(
        func.coalesce(func.sum(UsageLedger.prompt_tokens), 0),
        func.coalesce(func.sum(UsageLedger.completion_tokens), 0),
        func.coalesce(func.sum(UsageLedger.total_tokens), 0),
        func.coalesce(func.sum(UsageLedger.calculated_cost), Decimal("0")),
        func.count(UsageLedger.id),
    ).where(UsageLedger.workspace_id == workspace_id)
    total_result = await session.exec(total_stmt)
    total = total_result.one()

    # Per-user breakdown
    user_stmt = (
        select(
            UsageLedger.user_id,
            User.username,
            func.coalesce(func.sum(UsageLedger.prompt_tokens), 0),
            func.coalesce(func.sum(UsageLedger.completion_tokens), 0),
            func.coalesce(func.sum(UsageLedger.total_tokens), 0),
            func.coalesce(func.sum(UsageLedger.calculated_cost), Decimal("0")),
        )
        .join(User, User.id == UsageLedger.user_id)
        .where(UsageLedger.workspace_id == workspace_id)
        .group_by(UsageLedger.user_id, User.username)
    )
    user_result = await session.exec(user_stmt)
    users = user_result.all()

    return {
        "total": {
            "total_prompt_tokens": total[0],
            "total_completion_tokens": total[1],
            "total_tokens": total[2],
            "total_cost": float(total[3]),
            "record_count": total[4],
        },
        "per_user": [
            {
                "user_id": row[0],
                "username": row[1],
                "total_prompt_tokens": row[2],
                "total_completion_tokens": row[3],
                "total_tokens": row[4],
                "total_cost": float(row[5]),
            }
            for row in users
        ],
    }


async def get_all_workspaces_usage(session: AsyncSession) -> list[dict]:
    """For the Application Owner: aggregate usage across all workspaces."""
    stmt = (
        select(
            UsageLedger.workspace_id,
            func.coalesce(func.sum(UsageLedger.prompt_tokens), 0),
            func.coalesce(func.sum(UsageLedger.completion_tokens), 0),
            func.coalesce(func.sum(UsageLedger.total_tokens), 0),
            func.coalesce(func.sum(UsageLedger.calculated_cost), Decimal("0")),
            func.count(UsageLedger.id),
        )
        .group_by(UsageLedger.workspace_id)
    )
    result = await session.exec(stmt)
    return [
        {
            "workspace_id": row[0],
            "total_prompt_tokens": row[1],
            "total_completion_tokens": row[2],
            "total_tokens": row[3],
            "total_cost": float(row[4]),
            "record_count": row[5],
        }
        for row in result.all()
    ]
