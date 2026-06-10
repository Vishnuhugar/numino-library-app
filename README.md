# 📚 Neighborhood Library Management System

A full-stack library management application built with **Python (FastAPI)**, **PostgreSQL**, and **Next.js**.

---

## Architecture Overview

```
library-app/
├── backend/                  # Python FastAPI REST API
│   ├── app/
│   │   ├── api/routes/       # HTTP route handlers
│   │   │   ├── books.py
│   │   │   ├── members.py
│   │   │   └── loans.py
│   │   ├── core/
│   │   │   ├── config.py     # Pydantic settings (env vars)
│   │   │   └── exceptions.py # Domain exceptions
│   │   ├── db/
│   │   │   └── session.py    # Async SQLAlchemy engine + session
│   │   ├── models/
│   │   │   └── models.py     # ORM models (Member, Book, Loan)
│   │   ├── schemas/
│   │   │   └── schemas.py    # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── member_service.py
│   │   │   ├── book_service.py
│   │   │   └── loan_service.py
│   │   └── main.py           # FastAPI app, CORS, exception handlers
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # Next.js 14 App Router
│   ├── src/
│   │   ├── app/              # Next.js app directory
│   │   ├── components/
│   │   │   ├── books/
│   │   │   ├── members/
│   │   │   └── lending/
│   │   └── lib/
│   │       └── api.ts        # Typed API client
│   └── Dockerfile
├── scripts/
│   ├── schema.sql            # PostgreSQL DDL + seed data
│   └── test_api.py           # CLI smoke-test script
├── docker-compose.yml
└── .env.example
```

---

## Database Schema

### `members`
| Column            | Type           | Notes                          |
|-------------------|----------------|--------------------------------|
| id                | UUID (PK)      | Auto-generated                 |
| name              | VARCHAR(255)   | Required                       |
| email             | VARCHAR(255)   | Required, unique               |
| phone             | VARCHAR(30)    | Optional                       |
| address           | TEXT           | Optional                       |
| membership_date   | DATE           | Default: today                 |
| is_active         | BOOLEAN        | Default: true                  |
| created_at        | TIMESTAMPTZ    |                                |
| updated_at        | TIMESTAMPTZ    | Auto-updated via trigger       |

### `books`
| Column            | Type           | Notes                          |
|-------------------|----------------|--------------------------------|
| id                | UUID (PK)      |                                |
| title             | VARCHAR(500)   | Required                       |
| author            | VARCHAR(255)   | Required                       |
| isbn              | VARCHAR(20)    | Unique                         |
| genre             | VARCHAR(100)   |                                |
| publisher         | VARCHAR(255)   |                                |
| published_year    | SMALLINT       |                                |
| total_copies      | SMALLINT       | ≥ 1                            |
| available_copies  | SMALLINT       | 0 ≤ avail ≤ total              |
| description       | TEXT           |                                |

### `loans`
| Column            | Type           | Notes                          |
|-------------------|----------------|--------------------------------|
| id                | UUID (PK)      |                                |
| member_id         | UUID (FK)      | → members.id                   |
| book_id           | UUID (FK)      | → books.id                     |
| borrowed_at       | TIMESTAMPTZ    | Default: now                   |
| due_date          | DATE           | Default: today + 14 days       |
| returned_at       | TIMESTAMPTZ    | NULL while active              |
| fine_amount       | NUMERIC(8,2)   | Calculated on return           |
| fine_paid         | BOOLEAN        |                                |
| notes             | TEXT           |                                |

A **partial unique index** prevents the same member borrowing the same book twice (while active).

---

## REST API Endpoints

### Members — `/api/v1/members`
| Method   | Path                    | Description               |
|----------|-------------------------|---------------------------|
| `POST`   | `/members`              | Register a new member     |
| `GET`    | `/members`              | List members (paginated)  |
| `GET`    | `/members/{id}`         | Get member by ID          |
| `PATCH`  | `/members/{id}`         | Update member details     |
| `DELETE` | `/members/{id}`         | Remove member             |

### Books — `/api/v1/books`
| Method   | Path                    | Description               |
|----------|-------------------------|---------------------------|
| `POST`   | `/books`                | Add a book                |
| `GET`    | `/books`                | List books (paginated)    |
| `GET`    | `/books/{id}`           | Get book by ID            |
| `PATCH`  | `/books/{id}`           | Update book details       |
| `DELETE` | `/books/{id}`           | Remove book               |

### Loans — `/api/v1/loans`
| Method   | Path                        | Description                    |
|----------|-----------------------------|--------------------------------|
| `POST`   | `/loans`                    | Borrow a book                  |
| `GET`    | `/loans`                    | List loans (paginated, filter) |
| `GET`    | `/loans/stats`              | Library-wide statistics        |
| `GET`    | `/loans/{id}`               | Get loan by ID                 |
| `POST`   | `/loans/{id}/return`        | Return a book                  |
| `POST`   | `/loans/{id}/pay-fine`      | Mark fine as paid              |

**Query parameters for `GET /loans`:**
- `member_id` — filter by member
- `book_id` — filter by book
- `active_only=true` — currently out
- `overdue_only=true` — past due date, not returned

---

## Quick Start — Docker (Recommended)

### Prerequisites
- Docker ≥ 24 and Docker Compose ≥ 2.20

### Steps

```bash
# 1. Clone / unzip the project
cd library-app

# 2. Copy environment config
cp .env.example .env

# 3. Start everything
docker compose up --build

# Services:
#   PostgreSQL  → localhost:5432
#   API         → http://localhost:8000
#   Frontend    → http://localhost:3000
#   Swagger UI  → http://localhost:8000/docs
```

The schema and seed data are applied automatically on first run.

---

## Local Development (Without Docker)

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/librarydb"
export CORS_ORIGINS="http://localhost:3000"

# Apply schema (requires running PostgreSQL)
psql -U postgres -d librarydb -f ../scripts/schema.sql

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
# → http://localhost:3000
```

### PostgreSQL only (via Docker)

```bash
docker run -d \
  --name library_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=librarydb \
  -p 5432:5432 \
  postgres:16-alpine
```

---

## Running the Smoke Test

With the API running:

```bash
python scripts/test_api.py
```

This will:
1. Create a test member and book
2. Borrow the book
3. Attempt a duplicate borrow (should return 409)
4. Return the book
5. Check library stats
6. Clean up test data

---

## Interactive API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Business Rules

| Rule | Details |
|------|---------|
| Loan period | 14 days (configurable via `LOAN_PERIOD_DAYS`) |
| Fine rate | $1.00/day overdue (configurable via `FINE_RATE_PER_DAY`) |
| Duplicate loans | A member cannot borrow the same book twice (enforced at DB + API level) |
| Unavailable books | Borrowing fails if `available_copies == 0` |
| Inactive members | Inactive members cannot borrow books |
| Delete protection | Members with active loans and books on active loan cannot be deleted |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | (postgres URL) | Async SQLAlchemy connection string |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `FINE_RATE_PER_DAY` | `1.00` | USD fine per overdue day |
| `LOAN_PERIOD_DAYS` | `14` | Default loan period |
| `SECRET_KEY` | `changeme` | App secret (for future auth) |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API base URL for the frontend |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 |
| Validation | Pydantic v2 |
| ASGI server | Uvicorn |
| Frontend | Next.js 14 (App Router) |
| Styling | Tailwind CSS |
| Icons | Lucide React |
| Containerization | Docker + Docker Compose |
