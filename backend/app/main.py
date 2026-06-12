"""
app/main.py
────────────────────────────────────────────────────────────────────────────
FastAPI application factory.

Startup order
─────────────
1. configure_logging()  — must be first so all subsequent imports log correctly
2. Build the FastAPI app
3. Register middleware (CORS, request-id/logging)
4. Register exception handlers for every domain exception
5. Mount routers
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.config import get_settings
from app.core.exceptions import ConflictError, LibraryError, NotFoundError, ValidationError
from app.core.logging import configure_logging
from app.core.middleware import RequestLoggingMiddleware
from app.api.routes import books, loans, members

# ── 1. Logging — before anything else ────────────────────────────────────────
settings = get_settings()
configure_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)

# ── 2. App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="REST API for the Neighborhood Library Management System",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── 3. Middleware (order matters: outermost first) ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# ── 4. Exception handlers ─────────────────────────────────────────────────────


def _error_body(detail: str, code: str | None = None) -> dict:
    body: dict = {"detail": detail}
    if code:
        body["code"] = code
    return body


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    logger.warning("NotFoundError: %s", exc.detail)
    return JSONResponse(status_code=404, content=_error_body(exc.detail, "NOT_FOUND"))


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    logger.warning("ConflictError: %s", exc.detail)
    return JSONResponse(status_code=409, content=_error_body(exc.detail, "CONFLICT"))


@app.exception_handler(ValidationError)
async def domain_validation_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Domain-level validation errors (raised by service code)."""
    logger.warning("ValidationError: %s", exc.detail)
    return JSONResponse(
        status_code=422,
        content=_error_body(exc.detail, "VALIDATION_ERROR"),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Pydantic / FastAPI request body / query-param validation failures."""
    errors = exc.errors()
    logger.warning("RequestValidationError on %s %s: %s", request.method, request.url.path, errors)
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed.",
            "code": "REQUEST_VALIDATION_ERROR",
            "errors": errors,
        },
    )


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Catch-all for Pydantic v2 ValidationErrors that escape route handlers."""
    logger.error("Unhandled PydanticValidationError: %s", exc)
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Data validation failed.",
            "code": "VALIDATION_ERROR",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(LibraryError)
async def generic_library_error_handler(
    request: Request, exc: LibraryError
) -> JSONResponse:
    """Safety net for any LibraryError subclass not caught above."""
    logger.error("Unhandled LibraryError type=%s: %s", type(exc).__name__, exc.detail)
    return JSONResponse(
        status_code=exc.http_status,
        content=_error_body(exc.detail),
    )


# ── 5. Routers ────────────────────────────────────────────────────────────────
app.include_router(members.router, prefix="/api/v1")
app.include_router(books.router, prefix="/api/v1")
app.include_router(loans.router, prefix="/api/v1")


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root() -> dict:
    return {
        "status": "ok",
        "service": settings.APP_TITLE,
        "version": settings.APP_VERSION,
    }


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "healthy"}


logger.info("Library API v%s ready", settings.APP_VERSION)
