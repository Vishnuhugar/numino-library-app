from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Book, Loan
from app.schemas.schemas import BookCreate, BookOut, BookUpdate, PagedResponse
from app.core.exceptions import NotFoundError, ConflictError


async def create_book(db: AsyncSession, data: BookCreate) -> Book:
    if data.isbn:
        existing = await db.scalar(select(Book).where(Book.isbn == data.isbn))
        if existing:
            raise ConflictError(f"ISBN '{data.isbn}' already exists.")

    payload = data.model_dump()
    book = Book(**payload, available_copies=payload["total_copies"])
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


async def get_book(db: AsyncSession, book_id: uuid.UUID) -> Book:
    book = await db.get(Book, book_id)
    if not book:
        raise NotFoundError(f"Book {book_id} not found.")
    return book


async def update_book(
    db: AsyncSession, book_id: uuid.UUID, data: BookUpdate
) -> Book:
    book = await get_book(db, book_id)

    if data.isbn and data.isbn != book.isbn:
        clash = await db.scalar(select(Book).where(Book.isbn == data.isbn))
        if clash:
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

    await db.flush()
    await db.refresh(book)
    return book


async def list_books(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    genre: Optional[str] = None,
    available_only: bool = False,
) -> PagedResponse[BookOut]:
    q = select(Book)
    if search:
        q = q.where(
            Book.title.ilike(f"%{search}%") | Book.author.ilike(f"%{search}%")
        )
    if genre:
        q = q.where(Book.genre.ilike(f"%{genre}%"))
    if available_only:
        q = q.where(Book.available_copies > 0)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (
        await db.execute(q.order_by(Book.title).offset((page - 1) * size).limit(size))
    ).scalars().all()

    return PagedResponse(
        items=[BookOut.model_validate(b) for b in rows],
        total=total or 0,
        page=page,
        size=size,
        pages=max(1, -(-( total or 1) // size)),
    )


async def delete_book(db: AsyncSession, book_id: uuid.UUID) -> None:
    book = await get_book(db, book_id)
    active = await db.scalar(
        select(func.count()).where(
            Loan.book_id == book_id, Loan.returned_at.is_(None)
        )
    )
    if active:
        raise ConflictError("Cannot delete a book that is currently on loan.")
    await db.delete(book)
