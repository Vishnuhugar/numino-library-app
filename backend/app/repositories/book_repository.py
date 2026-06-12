"""
app/repositories/book_repository.py
"""
from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Book, Loan
from app.repositories.base import BaseRepository


class BookRepository(BaseRepository[Book]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Book, session)

    async def get_by_isbn(self, isbn: str) -> Book | None:
        return await self.get_by_field("isbn", isbn)

    async def search(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        genre: Optional[str] = None,
        available_only: bool = False,
    ) -> tuple[Sequence[Book], int]:
        filters: list = []
        if search:
            filters.append(
                or_(
                    Book.title.ilike(f"%{search}%"),
                    Book.author.ilike(f"%{search}%"),
                )
            )
        if genre:
            filters.append(Book.genre.ilike(f"%{genre}%"))
        if available_only:
            filters.append(Book.available_copies > 0)
        return await self.list_paged(
            *filters, order_by=Book.title, page=page, size=size
        )

    async def active_loan_count(self, book_id: uuid.UUID) -> int:
        return await self.count(
            Loan.book_id == book_id, Loan.returned_at.is_(None)
        )
