"""
app/services/member_service.py
────────────────────────────────────────────────────────────────────────────
Member business logic.

This module contains ONLY domain rules — it never imports SQLAlchemy or
constructs SQL.  All persistence is delegated to MemberRepository.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.models import Member
from app.repositories.member_repository import MemberRepository
from app.schemas.schemas import MemberCreate, MemberOut, MemberUpdate, PagedResponse

logger = logging.getLogger(__name__)


def _pages(total: int, size: int) -> int:
    return max(1, -(-total // size))


async def create_member(db: AsyncSession, data: MemberCreate) -> Member:
    repo = MemberRepository(db)
    logger.info("Creating member email=%s", data.email)

    if await repo.get_by_email(data.email):
        raise ConflictError(f"Email '{data.email}' is already registered.")

    member = Member(**data.model_dump())
    return await repo.add(member)


async def get_member(db: AsyncSession, member_id: uuid.UUID) -> Member:
    repo = MemberRepository(db)
    member = await repo.get_by_id(member_id)
    if not member:
        raise NotFoundError(f"Member {member_id} not found.")
    return member


async def update_member(
    db: AsyncSession, member_id: uuid.UUID, data: MemberUpdate
) -> Member:
    repo = MemberRepository(db)
    member = await get_member(db, member_id)

    if data.email and data.email != member.email:
        if await repo.get_by_email(data.email):
            raise ConflictError(f"Email '{data.email}' is already registered.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(member, field, value)

    logger.info("Updated member id=%s", member_id)
    return await repo.flush_and_refresh(member)


async def list_members(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    active_only: bool = False,
) -> PagedResponse[MemberOut]:
    repo = MemberRepository(db)
    rows, total = await repo.search(page, size, search, active_only)

    active_counts = await repo.active_loan_counts([m.id for m in rows])

    items = []
    for m in rows:
        out = MemberOut.model_validate(m)
        out.active_loans = active_counts.get(m.id, 0)
        items.append(out)

    return PagedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=_pages(total, size),
    )


async def delete_member(db: AsyncSession, member_id: uuid.UUID) -> None:
    repo = MemberRepository(db)
    member = await get_member(db, member_id)

    if await repo.active_loan_count(member_id):
        raise ConflictError("Cannot delete a member with active loans.")

    logger.info("Deleting member id=%s", member_id)
    await repo.delete(member)
