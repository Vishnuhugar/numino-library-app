"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01T00:00:00+00:00

This migration is the authoritative schema definition.
It was generated from the ORM models (app/models/models.py) and supersedes
the legacy scripts/schema.sql file.  All future schema changes must be
expressed as new Alembic revisions — never by editing the raw SQL file.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── pgcrypto (for gen_random_uuid fallback on older PG) ──────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # ── members ───────────────────────────────────────────────────────────────
    op.create_table(
        "members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("membership_date", sa.Date, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("email", name="uq_members_email"),
    )
    op.create_index("idx_members_email", "members", ["email"])

    # ── books ─────────────────────────────────────────────────────────────────
    op.create_table(
        "books",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("isbn", sa.String(20), nullable=True),
        sa.Column("genre", sa.String(100), nullable=True),
        sa.Column("publisher", sa.String(255), nullable=True),
        sa.Column("published_year", sa.SmallInteger, nullable=True),
        sa.Column(
            "total_copies",
            sa.SmallInteger,
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "available_copies",
            sa.SmallInteger,
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("isbn", name="uq_books_isbn"),
        sa.CheckConstraint("total_copies >= 1", name="ck_books_total_ge_1"),
        sa.CheckConstraint("available_copies >= 0", name="ck_books_avail_ge_0"),
        sa.CheckConstraint(
            "available_copies <= total_copies", name="ck_books_avail_le_total"
        ),
    )
    op.create_index("idx_books_isbn", "books", ["isbn"])

    # ── loans ─────────────────────────────────────────────────────────────────
    op.create_table(
        "loans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("members.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "book_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "borrowed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "fine_amount",
            sa.Numeric(8, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "fine_paid",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_loans_member", "loans", ["member_id"])
    op.create_index("idx_loans_book", "loans", ["book_id"])
    op.create_index(
        "idx_loans_active",
        "loans",
        ["returned_at"],
        postgresql_where=sa.text("returned_at IS NULL"),
    )
    # Partial unique index: one active loan per member+book
    op.create_index(
        "uq_active_loan",
        "loans",
        ["member_id", "book_id"],
        unique=True,
        postgresql_where=sa.text("returned_at IS NULL"),
    )

    # ── updated_at triggers ───────────────────────────────────────────────────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$
        """
    )
    for table in ("members", "books", "loans"):
        op.execute(
            f"""
            DO $$ BEGIN
                CREATE TRIGGER trg_{table}_updated_at
                    BEFORE UPDATE ON {table}
                    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
            EXCEPTION WHEN duplicate_object THEN NULL; END $$
            """
        )


def downgrade() -> None:
    for table in ("loans", "books", "members"):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at CASCADE")
