# 📚 Neighborhood Library Management System

A full-stack library management application built with **Python (FastAPI)**, **PostgreSQL**, and **Next.js**.

---

## Architecture Overview

```
library-app/
├── backend/
│   ├── alembic/                    # Migrations — single schema source of truth
│   │   ├── env.py                  # Async-aware Alembic env (reads ORM metadata)
│   │   └── versions/
│   │       └── 0001_initial_schema.py
│   ├── app/
│   │   ├── api/routes/             # HTTP route handlers (thin — delegate to services)
│   │   │   ├── books.py
│   │   │   ├── loans.py
│   │   │   └── members.py
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic settings (env vars)
│   │   │   ├── exceptions.py       # Domain exceptions with http_status codes
│   │   │   ├── logging.py          # configure_logging(), _RequestIdFilter
│   │   │   └── middleware.py       # RequestLoggingMiddleware (request-id, timing)
│   │   ├── db/
│   │   │   └── session.py          # Async SQLAlchemy engine + session + Base
│   │   ├── models/
│   │   │   └── models.py           # ORM models (authoritative schema definition)
│   │   ├── repositories/           # ← NEW: persistence layer
│   │   │   ├── base.py             # Generic BaseRepository[T]
│   │   │   ├── book_repository.py
│   │   │   ├── loan_repository.py
│   │   │   └── member_repository.py
│   │   ├── schemas/
│   │   │   └── schemas.py          # Pydantic request/response schemas
│   │   ├── services/               # Business logic only — no SQLAlchemy imports
│   │   │   ├── book_service.py
│   │   │   ├── loan_service.py
│   │   │   └── member_service.py
│   │   └── main.py                 # App factory, middleware, exception handlers
│   ├── tests/
│   │   ├── conftest.py             # Fixtures: in-memory SQLite DB, AsyncClient
│   │   ├── test_books.py           # Book endpoint integration tests
│   │   ├── test_loans.py           # Loan endpoint integration tests
│   │   ├── test_members.py         # Member endpoint integration tests
│   │   └── test_unit.py            # Pure unit tests (fine calc, schemas, exceptions)
│   ├── alembic.ini
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/                       # Next.js 14 App Router
├── scripts/
│   ├── schema.sql                  # REFERENCE ONLY — see note below
│   └── test_api.py
└── docker-compose.yml
```

---

## Key Design Decisions (Review Feedback)

### 1. Logging & Error Handling

- **`app/core/logging.py`** — `configure_logging()` is called once at startup
  (before any import that logs). All modules use `logging.getLogger(__name__)`.
- **`app/core/middleware.py`** — `RequestLoggingMiddleware` mints a UUID4
  request-id, stores it in a `ContextVar`, and injects it into every log line
  emitted during that request via `_RequestIdFilter`. The ID is also echoed in
  the `X-Request-Id` response header for distributed tracing.
- **All domain exceptions** now have an `http_status` attribute so the HTTP
  mapping lives in one place (the exception class), not in the handler.
- **`ValidationError` is now fully registered** alongside `NotFoundError`,
  `ConflictError`, `RequestValidationError` (FastAPI), and `PydanticValidationError`.
  A generic `LibraryError` catch-all handles any future subclass automatically.

### 2. Single Schema Source of Truth

The previous codebase had three competing definitions of the schema:
- `scripts/schema.sql` (raw DDL)
- `app/models/models.py` (ORM)
- `alembic/` was present in requirements but never wired up

**Resolution:**
- **ORM models** are the authoritative schema definition.
- **Alembic** reads `Base.metadata` via `env.py` and generates migrations from
  it — so `autogenerate` will always detect ORM↔DB drift.
- `scripts/schema.sql` is now a reference-only file with a clear warning header.
  It must never be used to `CREATE TABLE` directly.

### 3. Repository Layer

Services previously mixed business logic with raw SQLAlchemy queries. Now:

| Layer | Responsibility | Imports |
|-------|---------------|---------|
| **Routes** | HTTP binding, request/response mapping | FastAPI, schemas |
| **Services** | Domain rules, orchestration, validation | repositories, exceptions |
| **Repositories** | SQL queries, ORM interactions | SQLAlchemy, models |

This means services can be tested by injecting a mock repository (no DB needed),
and all query changes are localised to one file per entity.

### 4. Tests

Tests use **pytest-asyncio** + **HTTPX AsyncClient** + **in-memory SQLite** via
`aiosqlite`. No external services are required.

```
tests/test_unit.py      Pure unit tests (no DB, no HTTP)
tests/test_members.py   Members CRUD integration tests
tests/test_books.py     Books CRUD integration tests
tests/test_loans.py     Full borrow/return/fine lifecycle tests
```

---

## Quick Start — Docker (Recommended)

```bash
cp .env.example .env
docker compose up --build
# API docs  → http://localhost:8000/docs
# Frontend  → http://localhost:3000
```

Schema is applied via `alembic upgrade head` (runs inside the container on
startup — see `Dockerfile CMD`).

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/librarydb"
export CORS_ORIGINS="http://localhost:3000"

# Apply schema (single source of truth)
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Run Tests

```bash
cd backend

# All tests (uses in-memory SQLite — no Postgres needed)
pytest

# With coverage
pytest --cov=app --cov-report=term-missing
```

### Generate a New Migration

After changing `app/models/models.py`:

```bash
cd backend
alembic revision --autogenerate -m "describe what changed"
alembic upgrade head
```

---

## REST API Endpoints

### Members `/api/v1/members`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/members` | Register member |
| GET | `/members` | List (search, active_only, paginated) |
| GET | `/members/{id}` | Get by ID |
| PATCH | `/members/{id}` | Update |
| DELETE | `/members/{id}` | Delete (no active loans) |

### Books `/api/v1/books`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/books` | Add book |
| GET | `/books` | List (search, genre, available_only) |
| GET | `/books/{id}` | Get by ID |
| PATCH | `/books/{id}` | Update |
| DELETE | `/books/{id}` | Delete (no active loans) |

### Loans `/api/v1/loans`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/loans` | Borrow a book |
| GET | `/loans` | List (member_id, book_id, active_only, overdue_only) |
| GET | `/loans/stats` | Library statistics |
| GET | `/loans/{id}` | Get by ID |
| POST | `/loans/{id}/return` | Return book + calculate fine |
| POST | `/loans/{id}/pay-fine` | Mark fine paid |

---

## Error Response Format

All errors return a consistent JSON body:

```json
{
  "detail": "Human-readable message",
  "code": "NOT_FOUND | CONFLICT | VALIDATION_ERROR | REQUEST_VALIDATION_ERROR",
  "errors": [...]   // present for validation errors only
}
```

The `X-Request-Id` header is always present in responses for log correlation.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgres URL | Async SQLAlchemy URL |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `FINE_RATE_PER_DAY` | `1.00` | USD fine per overdue day |
| `LOAN_PERIOD_DAYS` | `14` | Loan duration in days |
| `DEBUG` | `false` | Enables DEBUG log level + SQLAlchemy echo |
| `SECRET_KEY` | `changeme` | Reserved for future auth |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend API base URL |
