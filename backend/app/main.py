from contextlib import asynccontextmanager

import logging
from fastapi import FastAPI, Request
from fastapi import HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from psycopg import errors as psycopg_errors
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.api.router import api_router
from app.core.config import settings
from app.core.rate_limiter import limiter
from app.db.session import SessionLocal, engine
from app.jobs.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Roles, permissions and the admin account are created by
    # `python -m app.db.seed`, run once at deployment (see docker-compose).
    scheduler = start_scheduler()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)
    engine.dispose()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# Uploaded files are private: vehicle documents and ticket QR codes are only
# served through authenticated endpoints, never as static files.
settings.uploads_dir.mkdir(parents=True, exist_ok=True)


@app.exception_handler(DBAPIError)
async def handle_database_refusal(request: Request, exc: DBAPIError) -> JSONResponse:
    """Business rules enforced by PostgreSQL become 409 answers instead of 500s."""
    original = getattr(exc, "orig", None)
    if isinstance(original, psycopg_errors.RaiseException):
        detail = str(getattr(original.diag, "message_primary", None) or original).strip()
        return JSONResponse(status_code=409, content={"detail": detail})
    if isinstance(original, psycopg_errors.ForeignKeyViolation):
        return JSONResponse(status_code=409, content={"detail": "Cet élément est utilisé par d'autres données et ne peut pas être supprimé."})
    if isinstance(original, psycopg_errors.UniqueViolation):
        return JSONResponse(status_code=409, content={"detail": "Cette donnée existe déjà."})
    if isinstance(original, (psycopg_errors.StringDataRightTruncation, psycopg_errors.NumericValueOutOfRange)):
        return JSONResponse(status_code=422, content={"detail": "Une valeur saisie est trop longue ou hors limites."})
    logging.getLogger("cooperative.api").exception("Erreur base de données sur %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Une erreur est survenue. Veuillez réessayer."})


@app.middleware("http")
async def handle_unexpected_error(request: Request, call_next):
    # Registered before CORS so the error answer still carries CORS headers
    # and the browser can read it.
    try:
        return await call_next(request)
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("cooperative.api").exception(
            "Erreur interne sur %s %s", request.method, request.url.path, exc_info=exc
        )
        return JSONResponse(status_code=500, content={"detail": "Une erreur est survenue. Veuillez réessayer."})

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        *settings.allowed_origins,
        "https://cooperative-opal.vercel.app",
    ],
    # Any local port is accepted only during development.
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?" if settings.is_development else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def readiness_check() -> dict[str, str]:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        logging.getLogger("cooperative.api").exception("Base PostgreSQL indisponible")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service est temporairement indisponible.",
        )
    return {"status": "ready"}
