from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ── Shared helpers ───────────────────────────────────────────────────────────

class OrmModel(BaseModel):
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# MEMBER
# ═══════════════════════════════════════════════════════════════════════════════

class MemberBase(BaseModel):
    name    : str            = Field(..., min_length=1, max_length=255)
    email   : EmailStr
    phone   : Optional[str] = Field(None, max_length=30)
    address : Optional[str] = None


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    name      : Optional[str]      = Field(None, min_length=1, max_length=255)
    email     : Optional[EmailStr] = None
    phone     : Optional[str]      = Field(None, max_length=30)
    address   : Optional[str]      = None
    is_active : Optional[bool]     = None


class MemberOut(OrmModel, MemberBase):
    id              : uuid.UUID
    membership_date : date
    is_active       : bool
    created_at      : datetime
    updated_at      : datetime
    active_loans    : int = 0   # populated by service


# ═══════════════════════════════════════════════════════════════════════════════
# BOOK
# ═══════════════════════════════════════════════════════════════════════════════

class BookBase(BaseModel):
    title          : str           = Field(..., min_length=1, max_length=500)
    author         : str           = Field(..., min_length=1, max_length=255)
    isbn           : Optional[str] = Field(None, max_length=20)
    genre          : Optional[str] = Field(None, max_length=100)
    publisher      : Optional[str] = Field(None, max_length=255)
    published_year : Optional[int] = Field(None, ge=1000, le=2100)
    description    : Optional[str] = None
    total_copies   : int           = Field(1, ge=1)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title          : Optional[str] = Field(None, min_length=1, max_length=500)
    author         : Optional[str] = Field(None, min_length=1, max_length=255)
    isbn           : Optional[str] = Field(None, max_length=20)
    genre          : Optional[str] = Field(None, max_length=100)
    publisher      : Optional[str] = Field(None, max_length=255)
    published_year : Optional[int] = Field(None, ge=1000, le=2100)
    description    : Optional[str] = None
    total_copies   : Optional[int] = Field(None, ge=1)


class BookOut(OrmModel, BookBase):
    id               : uuid.UUID
    available_copies : int
    created_at       : datetime
    updated_at       : datetime

    @property
    def is_available(self) -> bool:
        return self.available_copies > 0


# ═══════════════════════════════════════════════════════════════════════════════
# LOAN
# ═══════════════════════════════════════════════════════════════════════════════

class LoanCreate(BaseModel):
    member_id : uuid.UUID
    book_id   : uuid.UUID
    notes     : Optional[str] = None


class LoanReturn(BaseModel):
    notes : Optional[str] = None


class LoanOut(OrmModel):
    id          : uuid.UUID
    member_id   : uuid.UUID
    book_id     : uuid.UUID
    borrowed_at : datetime
    due_date    : date
    returned_at : Optional[datetime] = None
    fine_amount : Decimal
    fine_paid   : bool
    notes       : Optional[str]      = None
    created_at  : datetime
    updated_at  : datetime

    # Nested summary objects (populated by service)
    member_name : Optional[str] = None
    book_title  : Optional[str] = None
    book_author : Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self.returned_at is None

    @property
    def is_overdue(self) -> bool:
        return self.returned_at is None and date.today() > self.due_date


# ── Pagination wrapper ───────────────────────────────────────────────────────

class PagedResponse[T](BaseModel):
    items : list[T]
    total : int
    page  : int
    size  : int
    pages : int


# ── Stats ────────────────────────────────────────────────────────────────────

class LibraryStats(BaseModel):
    total_books    : int
    total_members  : int
    active_loans   : int
    overdue_loans  : int
    total_fines    : Decimal
