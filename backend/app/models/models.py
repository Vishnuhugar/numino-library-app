import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime,
    ForeignKey, Index, Numeric, SmallInteger, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Member(Base):
    __tablename__ = "members"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name            = Column(String(255), nullable=False)
    email           = Column(String(255), nullable=False, unique=True)
    phone           = Column(String(30))
    address         = Column(Text)
    membership_date = Column(Date, nullable=False, default=date.today)
    is_active       = Column(Boolean, nullable=False, default=True)
    created_at      = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at      = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    loans = relationship("Loan", back_populates="member", lazy="select")


class Book(Base):
    __tablename__ = "books"

    __table_args__ = (
        CheckConstraint("total_copies >= 1", name="ck_books_total_ge_1"),
        CheckConstraint("available_copies >= 0", name="ck_books_avail_ge_0"),
        CheckConstraint("available_copies <= total_copies", name="ck_books_avail_le_total"),
    )

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title            = Column(String(500), nullable=False)
    author           = Column(String(255), nullable=False)
    isbn             = Column(String(20), unique=True)
    genre            = Column(String(100))
    publisher        = Column(String(255))
    published_year   = Column(SmallInteger)
    total_copies     = Column(SmallInteger, nullable=False, default=1)
    available_copies = Column(SmallInteger, nullable=False, default=1)
    description      = Column(Text)
    created_at       = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at       = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    loans = relationship("Loan", back_populates="book", lazy="select")


class Loan(Base):
    __tablename__ = "loans"

    __table_args__ = (
        # Only one active loan per member/book combination
        Index("uq_active_loan", "member_id", "book_id",
              unique=True, postgresql_where="returned_at IS NULL"),
    )

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id   = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="RESTRICT"), nullable=False)
    book_id     = Column(UUID(as_uuid=True), ForeignKey("books.id",   ondelete="RESTRICT"), nullable=False)
    borrowed_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    due_date    = Column(Date, nullable=False)
    returned_at = Column(DateTime(timezone=True))
    fine_amount = Column(Numeric(8, 2), nullable=False, default=0)
    fine_paid   = Column(Boolean, nullable=False, default=False)
    notes       = Column(Text)
    created_at  = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at  = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    member = relationship("Member", back_populates="loans")
    book   = relationship("Book",   back_populates="loans")
