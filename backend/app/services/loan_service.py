from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models.models import Book, Loan, Member
from app.schemas.schemas import LibraryStats, LoanCreate, LoanOut, LoanReturn, PagedResponse

settings = get_settings()


def _calculate_fine(due_date: date, returned_at: Optional[datetime] = None) -> Decimal:
    """Return fine accrued in USD based on overdue days."""
    cutoff = returned_at.date() if returned_at else date.today()
    overdue_days = max(0, (cutoff - due_date).days)
    return Decimal(str(round(overdue_days * settings.FINE_RATE_PER_DAY, 2)))


async def _enrich(loan: Loan) -> LoanOut:
    out = LoanOut.model_validate(loan)
    if loan.member:
        out.member_name = loan.member.name
    if loan.book:
        out.book_title  = loan.book.title
        out.book_author = loan.book.author
    return out


async def borrow_book(db: AsyncSession, data: LoanCreate) -> LoanOut:
    # Validate member & book exist
    member = await db.get(Member, data.member_id)
    if not member:
        raise NotFoundError(f"Member {data.member_id} not found.")
    if not member.is_active:
        raise ConflictError("Member account is inactive.")

    book = await db.get(Book, data.book_id)
    if not book:
        raise NotFoundError(f"Book {data.book_id} not found.")
    if book.available_copies < 1:
        raise ConflictError(f"No available copies of '{book.title}'.")

    # Check duplicate active loan
    existing = await db.scalar(
        select(Loan).where(
            Loan.member_id == data.member_id,
            Loan.book_id   == data.book_id,
            Loan.returned_at.is_(None),
        )
    )
    if existing:
        raise ConflictError("Member already has an active loan for this book.")

    due = date.today() + timedelta(days=settings.LOAN_PERIOD_DAYS)
    loan = Loan(
        member_id = data.member_id,
        book_id   = data.book_id,
        due_date  = due,
        notes     = data.notes,
    )
    book.available_copies -= 1
    db.add(loan)
    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(Loan)
        .where(Loan.id == loan.id)
        .options(selectinload(Loan.member), selectinload(Loan.book))
    )
    loan = result.scalar_one()
    return await _enrich(loan)


async def return_book(
    db: AsyncSession, loan_id: uuid.UUID, data: LoanReturn
) -> LoanOut:
    result = await db.execute(
        select(Loan)
        .where(Loan.id == loan_id)
        .options(selectinload(Loan.member), selectinload(Loan.book))
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise NotFoundError(f"Loan {loan_id} not found.")
    if loan.returned_at:
        raise ConflictError("This loan has already been returned.")

    now = datetime.now(timezone.utc)
    loan.returned_at = now
    loan.fine_amount = _calculate_fine(loan.due_date, now)
    if data.notes:
        loan.notes = data.notes

    loan.book.available_copies += 1
    await db.flush()
    await db.refresh(loan)

    # Re-fetch with relationships
    result = await db.execute(
        select(Loan)
        .where(Loan.id == loan_id)
        .options(selectinload(Loan.member), selectinload(Loan.book))
    )
    loan = result.scalar_one()
    return await _enrich(loan)


async def pay_fine(db: AsyncSession, loan_id: uuid.UUID) -> LoanOut:
    result = await db.execute(
        select(Loan)
        .where(Loan.id == loan_id)
        .options(selectinload(Loan.member), selectinload(Loan.book))
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise NotFoundError(f"Loan {loan_id} not found.")
    if not loan.returned_at:
        raise ConflictError("Cannot pay fine on an active loan.")
    if loan.fine_paid:
        raise ConflictError("Fine already paid.")
    if loan.fine_amount == 0:
        raise ConflictError("No fine outstanding.")

    loan.fine_paid = True
    await db.flush()
    await db.refresh(loan)
    return await _enrich(loan)


async def get_loan(db: AsyncSession, loan_id: uuid.UUID) -> LoanOut:
    result = await db.execute(
        select(Loan)
        .where(Loan.id == loan_id)
        .options(selectinload(Loan.member), selectinload(Loan.book))
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise NotFoundError(f"Loan {loan_id} not found.")
    return await _enrich(loan)


async def list_loans(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    member_id: Optional[uuid.UUID] = None,
    book_id: Optional[uuid.UUID] = None,
    active_only: bool = False,
    overdue_only: bool = False,
) -> PagedResponse[LoanOut]:
    q = select(Loan).options(selectinload(Loan.member), selectinload(Loan.book))

    if member_id:
        q = q.where(Loan.member_id == member_id)
    if book_id:
        q = q.where(Loan.book_id == book_id)
    if active_only:
        q = q.where(Loan.returned_at.is_(None))
    if overdue_only:
        q = q.where(Loan.returned_at.is_(None), Loan.due_date < date.today())

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (
        await db.execute(
            q.order_by(Loan.borrowed_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
    ).scalars().all()

    return PagedResponse(
        items=[await _enrich(loan) for loan in rows],
        total=total or 0,
        page=page,
        size=size,
        pages=max(1, -(-( total or 1) // size)),
    )


async def get_stats(db: AsyncSession) -> LibraryStats:
    total_books   = await db.scalar(select(func.count()).select_from(Book))
    total_members = await db.scalar(select(func.count()).select_from(Member))
    active_loans  = await db.scalar(
        select(func.count()).where(Loan.returned_at.is_(None))
    )
    overdue_loans = await db.scalar(
        select(func.count()).where(
            Loan.returned_at.is_(None), Loan.due_date < date.today()
        )
    )
    total_fines = await db.scalar(
        select(func.coalesce(func.sum(Loan.fine_amount), 0)).where(
            Loan.fine_paid.is_(False), Loan.returned_at.isnot(None)
        )
    )
    return LibraryStats(
        total_books   = total_books or 0,
        total_members = total_members or 0,
        active_loans  = active_loans or 0,
        overdue_loans = overdue_loans or 0,
        total_fines   = Decimal(str(total_fines or 0)),
    )
