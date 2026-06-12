"""
app/services/loan_service.py
────────────────────────────────────────────────────────────────────────────
Loan business logic — borrow / return / fine calculation / stats.
No SQLAlchemy imports; all DB access through LoanRepository.
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models.models import Loan
from app.repositories.loan_repository import LoanRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.book_repository import BookRepository
from app.schemas.schemas import LibraryStats, LoanCreate, LoanOut, LoanReturn, PagedResponse

logger = logging.getLogger(__name__)
settings = get_settings()


def _pages(total: int, size: int) -> int:
    return max(1, -(-total // size))


def _calculate_fine(due_date: date, returned_at: Optional[datetime] = None) -> Decimal:
    cutoff = returned_at.date() if returned_at else date.today()
    overdue_days = max(0, (cutoff - due_date).days)
    return Decimal(str(round(overdue_days * settings.FINE_RATE_PER_DAY, 2)))


def _enrich(loan: Loan) -> LoanOut:
    """Map ORM Loan → LoanOut, populating denormalised name fields."""
    out = LoanOut.model_validate(loan)
    if loan.member:
        out.member_name = loan.member.name
    if loan.book:
        out.book_title = loan.book.title
        out.book_author = loan.book.author
    return out


async def borrow_book(db: AsyncSession, data: LoanCreate) -> LoanOut:
    member_repo = MemberRepository(db)
    book_repo   = BookRepository(db)
    loan_repo   = LoanRepository(db)

    member = await member_repo.get_by_id(data.member_id)
    if not member:
        raise NotFoundError(f"Member {data.member_id} not found.")
    if not member.is_active:
        raise ConflictError("Member account is inactive.")

    book = await book_repo.get_by_id(data.book_id)
    if not book:
        raise NotFoundError(f"Book {data.book_id} not found.")
    if book.available_copies < 1:
        raise ConflictError(f"No available copies of '{book.title}'.")

    if await loan_repo.get_active_loan(data.member_id, data.book_id):
        raise ConflictError("Member already has an active loan for this book.")

    loan = Loan(
        member_id=data.member_id,
        book_id=data.book_id,
        due_date=date.today() + timedelta(days=settings.LOAN_PERIOD_DAYS),
        notes=data.notes,
    )
    book.available_copies -= 1
    loan = await loan_repo.add(loan)

    logger.info(
        "Loan created id=%s member=%s book=%s due=%s",
        loan.id, data.member_id, data.book_id, loan.due_date,
    )

    # Reload with joined relations for the response
    full = await loan_repo.get_with_relations(loan.id)
    return _enrich(full)  # type: ignore[arg-type]


async def return_book(db: AsyncSession, loan_id: uuid.UUID, data: LoanReturn) -> LoanOut:
    loan_repo = LoanRepository(db)
    loan = await loan_repo.get_with_relations(loan_id)
    if not loan:
        raise NotFoundError(f"Loan {loan_id} not found.")
    if loan.returned_at:
        raise ConflictError("This loan has already been returned.")

    now = datetime.now(timezone.utc)
    loan.returned_at = now
    loan.fine_amount = _calculate_fine(loan.due_date, now)
    if data.notes:
        loan.notes = data.notes
    loan.book.available_copies += 1  # type: ignore[union-attr]

    await loan_repo.flush_and_refresh(loan)
    full = await loan_repo.get_with_relations(loan_id)

    logger.info(
        "Loan returned id=%s fine=%.2f", loan_id, loan.fine_amount
    )
    return _enrich(full)  # type: ignore[arg-type]


async def pay_fine(db: AsyncSession, loan_id: uuid.UUID) -> LoanOut:
    loan_repo = LoanRepository(db)
    loan = await loan_repo.get_with_relations(loan_id)
    if not loan:
        raise NotFoundError(f"Loan {loan_id} not found.")
    if not loan.returned_at:
        raise ConflictError("Cannot pay fine on an active loan.")
    if loan.fine_paid:
        raise ConflictError("Fine already paid.")
    if loan.fine_amount == 0:
        raise ConflictError("No fine outstanding.")

    loan.fine_paid = True
    await loan_repo.flush_and_refresh(loan)
    logger.info("Fine paid for loan id=%s amount=%.2f", loan_id, loan.fine_amount)
    full = await loan_repo.get_with_relations(loan_id)
    return _enrich(full)  # type: ignore[arg-type]


async def get_loan(db: AsyncSession, loan_id: uuid.UUID) -> LoanOut:
    loan = await LoanRepository(db).get_with_relations(loan_id)
    if not loan:
        raise NotFoundError(f"Loan {loan_id} not found.")
    return _enrich(loan)


async def list_loans(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    member_id: Optional[uuid.UUID] = None,
    book_id: Optional[uuid.UUID] = None,
    active_only: bool = False,
    overdue_only: bool = False,
) -> PagedResponse[LoanOut]:
    rows, total = await LoanRepository(db).search(
        page, size, member_id, book_id, active_only, overdue_only
    )
    return PagedResponse(
        items=[_enrich(loan) for loan in rows],
        total=total,
        page=page,
        size=size,
        pages=_pages(total, size),
    )


async def get_stats(db: AsyncSession) -> LibraryStats:
    raw = await LoanRepository(db).stats()
    return LibraryStats(
        total_books=raw["total_books"],
        total_members=raw["total_members"],
        active_loans=raw["active_loans"],
        overdue_loans=raw["overdue_loans"],
        total_fines=Decimal(str(raw["total_fines"])),
    )
