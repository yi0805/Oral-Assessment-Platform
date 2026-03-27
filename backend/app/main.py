"""
Project 20 — AI Oral Assessment API
Entry point: uvicorn app.main:app --reload --port 8000
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Project 20 — AI Oral Assessment API",
    description=(
        "Backend API for the AI-Supported Individualized Oral Assessment Tool.\n\n"
        "Authentication: all protected endpoints require a Bearer JWT obtained "
        "from `GET /api/v1/auth/google/login`."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — origins read from CORS_ORIGINS env var so nothing is hardcoded
# ---------------------------------------------------------------------------

_cors_origins: list[str] = []
if settings.cors_origins:
    import json
    try:
        parsed = json.loads(settings.cors_origins)
        _cors_origins = parsed if isinstance(parsed, list) else [settings.cors_origins]
    except (json.JSONDecodeError, ValueError):
        _cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"], summary="Root health check")
def root():
    """Returns service name and version — useful for load-balancer probes."""
    return {"status": "ok", "project": "Project 20", "version": "0.2.0"}


@app.get("/health/db", tags=["Health"], summary="Database connectivity check")
def health_db():
    """
    Connects to the database and counts public tables.
    Returns HTTP 200 with `status: ok` or `status: error`.
    """
    from app.core.database import engine
    from sqlalchemy import text

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
            )
            table_count = result.scalar()
        return {"status": "ok", "database": "connected", "tables": table_count}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Database health check failed")
        return {"status": "error", "database": str(exc)}
