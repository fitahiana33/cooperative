from contextlib import asynccontextmanager

import logging
from fastapi import FastAPI, Request
from fastapi import HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.rate_limiter import limiter
from app.db.seed import seed_default_admin
from app.db.session import SessionLocal, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    with SessionLocal() as db:
        seed_default_admin(db)
    yield
    engine.dispose()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logging.getLogger("cooperative.api").exception(
        "Erreur interne sur %s %s", request.method, request.url.path, exc_info=exc
    )
    return JSONResponse(
        status_code=500,
        content={"message": "Une erreur est survenue. Veuillez réessayer."},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
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
