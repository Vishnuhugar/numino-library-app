"""
app/repositories/loan_repository.py
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Book, Loan, Member
from app.repositories.base import BaseRepository


class LoanRepository(BaseRepository[Loan]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Loan, session)

    # ── Single-row fetches ────────────────────────────────────────────────────

    async def get_with_relations(self, loan_id: uuid.UUID) -> Loan | None:
        """Fetch a loan with member and book eagerly loaded."""
        result = await self._db.execute(
            select(Loan)
            .where(Loan.id == loan_id)
            .options(selectinload(Loan.member), selectinload(Loan.book))
        )
        return result.scalar_one_or_none()

    async def get_active_loan(
        self, member_id: uuid.UUID, book_id: uuid.UUID
    ) -> Loan | None:
        """Return the currently active loan for this member+book, or None."""
        return await self._db.scalar(
            select(Loan).where(
                Loan.member_id == member_id,
                Loan.book_id == book_id,
                Loan.returned_at.is_(None),
            )
        )

    # ── List / filter ─────────────────────────────────────────────────────────

    async def search(
        self,
        page: int = 1,
        size: int = 20,
        member_id: Optional[uuid.UUID] = None,
        book_id: Optional[uuid.UUID] = None,
        active_only: bool = False,
        overdue_only: bool = False,
    ) -> tuple[Sequence[Loan], int]:
        filters: list = []
        if member_id:
            filters.append(Loan.member_id == member_id)
        if book_id:
            filters.append(Loan.book_id == book_id)
        if active_only:
            filters.append(Loan.returned_at.is_(None))
        if overdue_only:
            filters.append(Loan.returned_at.is_(None))
            filters.append(Loan.due_date < date.today())

        return await self.list_paged(
            *filters,
            order_by=Loan.borrowed_at.desc(),
            page=page,
            size=size,
            options=[selectinload(Loan.member), selectinload(Loan.book)],
        )

    # ── Aggregates ────────────────────────────────────────────────────────────

    async def stats(self) -> dict:
        total_books = await self._db.scalar(
            select(func.count()).select_from(Book)
        )
        total_members = await self._db.scalar(
            select(func.count()).select_from(Member)
        )
        active_loans = await self._db.scalar(
            select(func.count()).where(Loan.returned_at.is_(None))
        )
        overdue_loans = await self._db.scalar(
            select(func.count()).where(
                Loan.returned_at.is_(None), Loan.due_date < date.today()
            )
        )
        total_fines = await self._db.scalar(
            select(func.coalesce(func.sum(Loan.fine_amount), 0)).where(
                Loan.fine_paid.is_(False), Loan.returned_at.isnot(None)
            )
        )
        return {
            "total_books": total_books or 0,
            "total_members": total_members or 0,
            "active_loans": active_loans or 0,
            "overdue_loans": overdue_loans or 0,
            "total_fines": total_fines or 0,
        }
