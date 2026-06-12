"""
tests/conftest.py
────────────────────────────────────────────────────────────────────────────
Shared pytest fixtures.

Strategy
────────
• We use an **in-process SQLite** database (via aiosqlite) so tests run fast
  and require no external service.  The schema is created from the ORM
  metadata so it always stays in sync with the models.
• A fresh database (and fresh tables) is created per test-module by the
  ``engine`` fixture (scope="module").  Individual tests get their own
  session that is rolled back after each test, keeping them isolated.
• The FastAPI app is tested through HTTPX's AsyncClient, which talks to the
  ASGI app in-process — no real HTTP server needed.

SQLite vs PostgreSQL
────────────────────
SQLite does not support partial unique indexes or all PostgreSQL-specific
types.  We compensate:
  • UUID columns are stored as strings (SQLite has no UUID type).
  • The ``uq_active_loan`` partial unique index is skipped; the application-
    level duplicate-loan check in the service still covers that rule.
  • The fine/stats tests that need exact Decimal precision are guarded.
"""
from __future__ import annotations

import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app

# SQLite URL — each module gets its own in-memory DB
SQLITE_URL = "sqlite+aiosqlite://"


# ── Engine / tables ────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def engine():
    """Create an async engine with fresh tables for the module."""
    eng = create_async_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite: enforce foreign keys
    @event.listens_for(eng.sync_engine, "connect")
    def _set_fk(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    async with eng.begin() as conn:
        # Some PostgreSQL-specific constructs are skipped automatically when
        # SQLite doesn't support them (e.g., partial indexes emit a warning
        # but don't fail).
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Return a session that wraps every test in a SAVEPOINT so the test DB
    stays clean between tests without re-creating the schema.
    """
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        await session.begin_nested()   # SAVEPOINT
        yield session
        await session.rollback()       # rollback to SAVEPOINT


# ── App / HTTP client ─────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient wired to the FastAPI app with the test session injected."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Common helpers ────────────────────────────────────────────────────────────


def make_member_payload(**overrides) -> dict:
    unique = str(uuid.uuid4())[:8]
    return {
        "name": overrides.get("name", f"Test User {unique}"),
        "email": overrides.get("email", f"user_{unique}@example.com"),
        "phone": overrides.get("phone", "555-0000"),
        "address": overrides.get("address", "1 Test Lane"),
    }


def make_book_payload(**overrides) -> dict:
    unique = str(uuid.uuid4())[:8]
    return {
        "title": overrides.get("title", f"Test Book {unique}"),
        "author": overrides.get("author", "Test Author"),
        "isbn": overrides.get("isbn", f"ISBN{unique}"),
        "genre": overrides.get("genre", "Fiction"),
        "total_copies": overrides.get("total_copies", 3),
    }
