"""
tests/test_unit.py
────────────────────────────────────────────────────────────────────────────
Pure unit tests — no database, no HTTP.

Tests that verify:
  • _calculate_fine() produces correct Decimal values
  • Domain exception hierarchy and http_status codes
  • Pydantic schema validation rules
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ConflictError, LibraryError, NotFoundError, ValidationError
from app.services.loan_service import _calculate_fine
from app.schemas.schemas import BookCreate, BookUpdate, MemberCreate, MemberUpdate


# ── Fine calculation ──────────────────────────────────────────────────────────


class TestCalculateFine:
    """_calculate_fine(due_date, returned_at) → Decimal."""

    def test_on_time_return_no_fine(self):
        due = date(2024, 6, 1)
        returned = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)
        assert _calculate_fine(due, returned) == Decimal("0.00")

    def test_one_day_overdue(self):
        due = date(2024, 6, 1)
        returned = datetime(2024, 6, 2, 10, 0, tzinfo=timezone.utc)
        # Default FINE_RATE_PER_DAY = 1.00
        assert _calculate_fine(due, returned) == Decimal("1.00")

    def test_multiple_days_overdue(self):
        due = date(2024, 6, 1)
        returned = datetime(2024, 6, 8, 0, 0, tzinfo=timezone.utc)
        assert _calculate_fine(due, returned) == Decimal("7.00")

    def test_returned_before_due_no_fine(self):
        due = date(2024, 6, 10)
        returned = datetime(2024, 6, 5, 0, 0, tzinfo=timezone.utc)
        assert _calculate_fine(due, returned) == Decimal("0.00")

    def test_fine_without_returned_at_uses_today(self):
        """Calling without returned_at measures against today."""
        past_due = date(2000, 1, 1)   # definitely in the past
        fine = _calculate_fine(past_due)
        assert fine > Decimal("0")


# ── Exception hierarchy ───────────────────────────────────────────────────────


class TestExceptions:
    def test_not_found_is_library_error(self):
        exc = NotFoundError("missing")
        assert isinstance(exc, LibraryError)
        assert exc.http_status == 404
        assert exc.detail == "missing"

    def test_conflict_error_status(self):
        exc = ConflictError("clash")
        assert exc.http_status == 409

    def test_validation_error_status(self):
        exc = ValidationError("bad input")
        assert exc.http_status == 422

    def test_str_returns_detail(self):
        assert str(NotFoundError("x")) == "x"


# ── Schema validation ─────────────────────────────────────────────────────────


class TestMemberSchemas:
    def test_valid_member_create(self):
        m = MemberCreate(name="Alice", email="alice@example.com")
        assert m.name == "Alice"

    def test_empty_name_rejected(self):
        with pytest.raises(PydanticValidationError):
            MemberCreate(name="", email="a@b.com")

    def test_invalid_email_rejected(self):
        with pytest.raises(PydanticValidationError):
            MemberCreate(name="Alice", email="not-an-email")

    def test_phone_max_length(self):
        with pytest.raises(PydanticValidationError):
            MemberCreate(name="Alice", email="a@b.com", phone="x" * 31)

    def test_member_update_partial(self):
        """MemberUpdate allows any subset of fields."""
        upd = MemberUpdate(name="Bob")
        assert upd.name == "Bob"
        assert upd.email is None


class TestBookSchemas:
    def test_valid_book_create(self):
        b = BookCreate(title="Dune", author="Herbert", total_copies=3)
        assert b.total_copies == 3

    def test_total_copies_must_be_at_least_1(self):
        with pytest.raises(PydanticValidationError):
            BookCreate(title="X", author="Y", total_copies=0)

    def test_published_year_lower_bound(self):
        with pytest.raises(PydanticValidationError):
            BookCreate(title="X", author="Y", published_year=999)

    def test_published_year_upper_bound(self):
        with pytest.raises(PydanticValidationError):
            BookCreate(title="X", author="Y", published_year=2101)

    def test_book_update_allows_empty(self):
        """An empty PATCH body is valid — nothing changes."""
        upd = BookUpdate()
        assert upd.title is None

    def test_title_max_length(self):
        with pytest.raises(PydanticValidationError):
            BookCreate(title="x" * 501, author="Y")
