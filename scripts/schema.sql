-- ============================================================
-- Neighborhood Library Management System — Database Schema
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Members ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS members (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(255) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    phone         VARCHAR(30),
    address       TEXT,
    membership_date DATE       NOT NULL DEFAULT CURRENT_DATE,
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Books ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS books (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    title         VARCHAR(500) NOT NULL,
    author        VARCHAR(255) NOT NULL,
    isbn          VARCHAR(20)  UNIQUE,
    genre         VARCHAR(100),
    publisher     VARCHAR(255),
    published_year SMALLINT,
    total_copies  SMALLINT    NOT NULL DEFAULT 1 CHECK (total_copies >= 1),
    available_copies SMALLINT NOT NULL DEFAULT 1 CHECK (available_copies >= 0),
    description   TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT available_le_total CHECK (available_copies <= total_copies)
);

-- ── Loans ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS loans (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id     UUID        NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    book_id       UUID        NOT NULL REFERENCES books(id)   ON DELETE RESTRICT,
    borrowed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_date      DATE        NOT NULL DEFAULT (CURRENT_DATE + INTERVAL '14 days'),
    returned_at   TIMESTAMPTZ,
    fine_amount   NUMERIC(8,2) NOT NULL DEFAULT 0.00,
    fine_paid     BOOLEAN     NOT NULL DEFAULT FALSE,
    notes         TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- A member cannot have two active loans for the same book
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_loan
    ON loans (member_id, book_id)
    WHERE returned_at IS NULL;

-- ── Indexes ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_loans_member    ON loans (member_id);
CREATE INDEX IF NOT EXISTS idx_loans_book      ON loans (book_id);
CREATE INDEX IF NOT EXISTS idx_loans_returned  ON loans (returned_at) WHERE returned_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_books_isbn      ON books (isbn);
CREATE INDEX IF NOT EXISTS idx_members_email   ON members (email);

-- ── auto-update updated_at ───────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DO $$ BEGIN
    CREATE TRIGGER trg_members_updated_at
        BEFORE UPDATE ON members
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TRIGGER trg_books_updated_at
        BEFORE UPDATE ON books
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TRIGGER trg_loans_updated_at
        BEFORE UPDATE ON loans
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ── Seed Data ────────────────────────────────────────────────
INSERT INTO members (name, email, phone, address) VALUES
    ('Alice Johnson',  'alice@example.com',  '555-1001', '12 Maple Street'),
    ('Bob Martinez',   'bob@example.com',    '555-1002', '34 Oak Avenue'),
    ('Carol Williams', 'carol@example.com',  '555-1003', '56 Pine Road')
ON CONFLICT DO NOTHING;

INSERT INTO books (title, author, isbn, genre, publisher, published_year, total_copies, available_copies) VALUES
    ('The Great Gatsby',       'F. Scott Fitzgerald', '9780743273565', 'Fiction',   'Scribner',          1925, 3, 3),
    ('To Kill a Mockingbird',  'Harper Lee',          '9780061935466', 'Fiction',   'HarperCollins',     1960, 2, 2),
    ('1984',                   'George Orwell',       '9780451524935', 'Dystopian', 'Signet Classic',    1949, 4, 4),
    ('Pride and Prejudice',    'Jane Austen',         '9780141439518', 'Romance',   'Penguin Classics',  1813, 2, 2),
    ('The Hitchhiker''s Guide','Douglas Adams',       '9780345391803', 'Sci-Fi',    'Del Rey',           1979, 3, 3)
ON CONFLICT DO NOTHING;
