"""
app/repositories/member_repository.py
────────────────────────────────────────────────────────────────────────────
All DB queries related to Member rows live here.
The service layer calls these methods and never imports SQLAlchemy directly.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Loan, Member
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class MemberRepository(BaseRepository[Member]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Member, session)

    # ── Lookups ───────────────────────────────────────────────────────────────

    async def get_by_email(self, email: str) -> Member | None:
        return await self.get_by_field("email", email)

    async def search(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        active_only: bool = False,
    ) -> tuple[Sequence[Member], int]:
        filters: list = []
        if search:
            filters.append(
                or_(
                    Member.name.ilike(f"%{search}%"),
                    Member.email.ilike(f"%{search}%"),
                )
            )
        if active_only:
            filters.append(Member.is_active.is_(True))
        return await self.list_paged(
            *filters, order_by=Member.name, page=page, size=size
        )

    # ── Aggregates ────────────────────────────────────────────────────────────

    async def active_loan_counts(
        self, member_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        """Return {member_id: active_loan_count} for a batch of member IDs."""
        if not member_ids:
            return {}
        q = (
            select(Loan.member_id, func.count().label("cnt"))
            .where(Loan.member_id.in_(member_ids), Loan.returned_at.is_(None))
            .group_by(Loan.member_id)
        )
        rows = (await self._db.execute(q)).all()
        return {mid: cnt for mid, cnt in rows}

    async def active_loan_count(self, member_id: uuid.UUID) -> int:
        return await self.count(
            Loan.member_id == member_id, Loan.returned_at.is_(None)
        )
