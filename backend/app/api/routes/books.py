import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import BookCreate, BookOut, BookUpdate, PagedResponse
from app.services import book_service

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("", response_model=BookOut, status_code=status.HTTP_201_CREATED)
async def create_book(body: BookCreate, db: AsyncSession = Depends(get_db)):
    """Add a new book to the library catalogue."""
    book = await book_service.create_book(db, body)
    return BookOut.model_validate(book)


@router.get("", response_model=PagedResponse[BookOut])
async def list_books(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search title or author"),
    genre: Optional[str] = Query(None),
    available_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """List books with optional search and filters."""
    return await book_service.list_books(db, page, size, search, genre, available_only)


@router.get("/{book_id}", response_model=BookOut)
async def get_book(book_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Fetch a single book by ID."""
    book = await book_service.get_book(db, book_id)
    return BookOut.model_validate(book)


@router.patch("/{book_id}", response_model=BookOut)
async def update_book(
    book_id: uuid.UUID,
    body: BookUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update book metadata."""
    book = await book_service.update_book(db, book_id, body)
    return BookOut.model_validate(book)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Remove a book (only if no active loans)."""
    await book_service.delete_book(db, book_id)
