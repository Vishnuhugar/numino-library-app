from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Loan, Member
from app.schemas.schemas import MemberCreate, MemberOut, MemberUpdate, PagedResponse
from app.core.exceptions import NotFoundError, ConflictError


async def create_member(db: AsyncSession, data: MemberCreate) -> Member:
    # Check email uniqueness
    existing = await db.scalar(select(Member).where(Member.email == data.email))
    if existing:
        raise ConflictError(f"Email '{data.email}' is already registered.")

    member = Member(**data.model_dump())
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member


async def get_member(db: AsyncSession, member_id: uuid.UUID) -> Member:
    member = await db.get(Member, member_id)
    if not member:
        raise NotFoundError(f"Member {member_id} not found.")
    return member


async def update_member(
    db: AsyncSession, member_id: uuid.UUID, data: MemberUpdate
) -> Member:
    member = await get_member(db, member_id)

    if data.email and data.email != member.email:
        clash = await db.scalar(select(Member).where(Member.email == data.email))
        if clash:
            raise ConflictError(f"Email '{data.email}' is already registered.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(member, field, value)

    await db.flush()
    await db.refresh(member)
    return member


async def list_members(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    active_only: bool = False,
) -> PagedResponse[MemberOut]:
    q = select(Member)
    if search:
        q = q.where(
            Member.name.ilike(f"%{search}%") | Member.email.ilike(f"%{search}%")
        )
    if active_only:
        q = q.where(Member.is_active.is_(True))

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (
        await db.execute(q.order_by(Member.name).offset((page - 1) * size).limit(size))
    ).scalars().all()

    # Count active loans per member
    active_counts: dict[uuid.UUID, int] = {}
    if rows:
        ids = [m.id for m in rows]
        counts_q = (
            select(Loan.member_id, func.count().label("cnt"))
            .where(Loan.member_id.in_(ids), Loan.returned_at.is_(None))
            .group_by(Loan.member_id)
        )
        for mid, cnt in (await db.execute(counts_q)).all():
            active_counts[mid] = cnt

    items = []
    for m in rows:
        out = MemberOut.model_validate(m)
        out.active_loans = active_counts.get(m.id, 0)
        items.append(out)

    return PagedResponse(
        items=items,
        total=total or 0,
        page=page,
        size=size,
        pages=max(1, -(-( total or 1) // size)),
    )


async def delete_member(db: AsyncSession, member_id: uuid.UUID) -> None:
    member = await get_member(db, member_id)
    active = await db.scalar(
        select(func.count()).where(
            Loan.member_id == member_id, Loan.returned_at.is_(None)
        )
    )
    if active:
        raise ConflictError("Cannot delete a member with active loans.")
    await db.delete(member)
