"""
app/core/exceptions.py
────────────────────────────────────────────────────────────────────────────
Domain exception hierarchy.

All exceptions carry an optional ``detail`` string that is surfaced in the
HTTP response body.  The HTTP status code lives here (not in the handlers)
so that any layer of code can raise the right error without knowing about
FastAPI / HTTP.
"""
from __future__ import annotations


class LibraryError(Exception):
    """Base class for all domain errors.

    Attributes
    ----------
    detail : str
        Human-readable description forwarded to the HTTP response body.
    http_status : int
        Suggested HTTP status code.  Exception handlers read this so the
        mapping between domain errors and HTTP codes is in one place.
    """

    http_status: int = 500

    def __init__(self, detail: str = "An unexpected error occurred.") -> None:
        super().__init__(detail)
        self.detail = detail

    def __str__(self) -> str:          # pragma: no cover
        return self.detail


class NotFoundError(LibraryError):
    """Raised when a requested resource does not exist."""
    http_status = 404


class ConflictError(LibraryError):
    """Raised when an operation violates a uniqueness or state constraint."""
    http_status = 409


class ValidationError(LibraryError):
    """Raised when input fails domain-level validation beyond Pydantic."""
    http_status = 422
