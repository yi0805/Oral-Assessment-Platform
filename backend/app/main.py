import json
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.core.config import settings
from app.core.limiter import limiter

# [STT Instrumentation - issue #72]
# Surface app.* loggers (e.g. logger = logging.getLogger(__name__) inside
# app.utils.audio_transcriber) at INFO level so the [STT timings] lines
# show up in uvicorn's stdout. Without this the root logger sits at
# WARNING by default and INFO calls get dropped silently.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


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

app.include_router(api_router, prefix="/api")
