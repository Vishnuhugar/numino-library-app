"""
alembic/env.py
────────────────────────────────────────────────────────────────────────────
Async-capable Alembic environment.

Key behaviours
──────────────
• ``target_metadata`` is set to ``Base.metadata`` so autogenerate compares
  the live database against the ORM models — making the ORM the single
  authoritative schema definition.
• The DATABASE_URL is read from the same ``Settings`` object used by the
  application, so there is exactly one place to change connection details.
• asyncpg (the async driver) is used at runtime; Alembic still uses a
  *synchronous* connection wrapper (``run_sync``) as recommended by
  SQLAlchemy docs for offline/online migration runs.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Pull in ORM metadata (single schema source of truth) ─────────────────────
# Importing models ensures they are registered on Base.metadata before
# autogenerate inspects it.  Do NOT replace this with the raw SQL file.
from app.db.session import Base  # noqa: F401 — registers Base
import app.models.models  # noqa: F401 — registers all ORM tables

from app.core.config import get_settings

# ── Alembic Config ────────────────────────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override sqlalchemy.url with the value from pydantic-settings so there is
# only one source of connection config.
settings = get_settings()
# asyncpg URL → replace with psycopg2-style for alembic synchronous operations
_sync_url = settings.DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
)
config.set_main_option("sqlalchemy.url", _sync_url)

_async_url = settings.DATABASE_URL
config.set_main_option("sqlalchemy.url", _async_url)

# ── Offline migration (no live DB connection required) ───────────────────────
def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting to the DB."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migration (connects to the live DB) ───────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations via run_sync."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
