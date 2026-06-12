"""
app/services/book_service.py
────────────────────────────────────────────────────────────────────────────
Book business logic — no SQLAlchemy imports, only repository calls.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.models import Book
from app.repositories.book_repository import BookRepository
from app.schemas.schemas import BookCreate, BookOut, BookUpdate, PagedResponse

logger = logging.getLogger(__name__)


def _pages(total: int, size: int) -> int:
    return max(1, -(-total // size))


async def create_book(db: AsyncSession, data: BookCreate) -> Book:
    repo = BookRepository(db)
    logger.info("Creating book title=%r isbn=%s", data.title, data.isbn)

    if data.isbn and await repo.get_by_isbn(data.isbn):
        raise ConflictError(f"ISBN '{data.isbn}' already exists.")

    payload = data.model_dump()
    book = Book(**payload, available_copies=payload["total_copies"])
    return await repo.add(book)


async def get_book(db: AsyncSession, book_id: uuid.UUID) -> Book:
    repo = BookRepository(db)
    book = await repo.get_by_id(book_id)
    if not book:
        raise NotFoundError(f"Book {book_id} not found.")
    return book


async def update_book(
    db: AsyncSession, book_id: uuid.UUID, data: BookUpdate
) -> Book:
    repo = BookRepository(db)
    book = await get_book(db, book_id)

    if data.isbn and data.isbn != book.isbn and await repo.get_by_isbn(data.isbn):
        raise ConflictError(f"ISBN '{data.isbn}' already in use.")

    updates = data.model_dump(exclude_unset=True)

    if "total_copies" in updates:
        delta = updates["total_copies"] - book.total_copies
        new_avail = book.available_copies + delta
        if new_avail < 0:
            raise ConflictError(
                "Cannot reduce total_copies below the number of active loans."
            )
        book.available_copies = new_avail

    for field, value in updates.items():
        setattr(book, field, value)

    logger.info("Updated book id=%s", book_id)
    return await repo.flush_and_refresh(book)


async def list_books(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    genre: Optional[str] = None,
    available_only: bool = False,
) -> PagedResponse[BookOut]:
    repo = BookRepository(db)
    rows, total = await repo.search(page, size, search, genre, available_only)
    return PagedResponse(
        items=[BookOut.model_validate(b) for b in rows],
        total=total,
        page=page,
        size=size,
        pages=_pages(total, size),
    )


async def delete_book(db: AsyncSession, book_id: uuid.UUID) -> None:
    repo = BookRepository(db)
    book = await get_book(db, book_id)

    if await repo.active_loan_count(book_id):
        raise ConflictError("Cannot delete a book that is currently on loan.")

    logger.info("Deleting book id=%s", book_id)
    await repo.delete(book)
