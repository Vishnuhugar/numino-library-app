import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import LibraryStats, LoanCreate, LoanOut, LoanReturn, PagedResponse
from app.services import loan_service

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("", response_model=LoanOut, status_code=status.HTTP_201_CREATED)
async def borrow_book(body: LoanCreate, db: AsyncSession = Depends(get_db)):
    """Record a member borrowing a book."""
    return await loan_service.borrow_book(db, body)


@router.get("", response_model=PagedResponse[LoanOut])
async def list_loans(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    member_id: Optional[uuid.UUID] = Query(None),
    book_id: Optional[uuid.UUID] = Query(None),
    active_only: bool = Query(False),
    overdue_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Query loans. Filter by member, book, active status, or overdue."""
    return await loan_service.list_loans(db, page, size, member_id, book_id, active_only, overdue_only)


@router.get("/stats", response_model=LibraryStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Library-wide statistics."""
    return await loan_service.get_stats(db)


@router.get("/{loan_id}", response_model=LoanOut)
async def get_loan(loan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Fetch a single loan by ID."""
    return await loan_service.get_loan(db, loan_id)


@router.post("/{loan_id}/return", response_model=LoanOut)
async def return_book(
    loan_id: uuid.UUID,
    body: LoanReturn = LoanReturn(),
    db: AsyncSession = Depends(get_db),
):
    """Record a book return and calculate any fine."""
    return await loan_service.return_book(db, loan_id, body)


@router.post("/{loan_id}/pay-fine", response_model=LoanOut)
async def pay_fine(loan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Mark the fine on a returned loan as paid."""
    return await loan_service.pay_fine(db, loan_id)
