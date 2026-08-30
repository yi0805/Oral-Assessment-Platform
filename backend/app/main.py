import json
import logging

from sqlalchemy import text
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.limiter import limiter

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logging.getLogger("app").setLevel(logging.INFO)


# application entry point, FastAPI app instance, and global middleware setup.

app = FastAPI(
    title="Project 20 — AI Oral Assessment API",
    docs_url="/docs",
)

_cors_origins: list[str] = []
if settings.cors_origins:
    try:
        parsed = json.loads(settings.cors_origins)
        _cors_origins = parsed if isinstance(parsed, list) else [settings.cors_origins]
    except (json.JSONDecodeError, ValueError):
        _cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(api_router, prefix="/api")


@app.get("/health/live", include_in_schema=False)
def health_live():
    """Report only that this application process can serve requests."""
    return {"status": "ok"}


@app.get("/health/ready", include_in_schema=False)
def health_ready(response: Response):
    """Verify the database connection without exposing connection details."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:  # Dependency configuration and driver errors are also not ready.
        logging.getLogger(__name__).warning("Readiness check failed", exc_info=True)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ok"}


@app.get("/version", include_in_schema=False)
def version():
    return {
        "version": settings.app_version,
        "git_commit": settings.git_commit,
    }
