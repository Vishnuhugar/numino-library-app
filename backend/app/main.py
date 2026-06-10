from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError
from app.api.routes import members, books, loans

settings = get_settings()

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="REST API for the Neighborhood Library Management System",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(members.router, prefix="/api/v1")
app.include_router(books.router,   prefix="/api/v1")
app.include_router(loans.router,   prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": settings.APP_TITLE, "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
