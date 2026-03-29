"""
Project 20 — AI Oral Assessment API  v0.4.0
Entry point: uvicorn app.main:app --reload --port 8000

AI providers:
  Embeddings  → Google Gemini  (gemini-embedding-001, 768-dim)
  Chat / LLM  → OpenRouter free tier  (openrouter/free)
"""
import json
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.core.config import settings
from app.core.limiter import limiter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Swagger UI description — shown at the top of /docs
# ---------------------------------------------------------------------------

_DESCRIPTION = """
## AI-Supported Oral Assessment Backend

### How to authenticate in Swagger

**Step 1 — Get a token (development)**

Scroll to **Auth (Dev)** → `POST /api/v1/auth/dev-token` → click **Try it out** → paste:

```json
{"email": "bzha150@aucklanduni.ac.nz", "role": "instructor"}
```

Execute. Copy the `access_token` string from the response (it looks like `eyJ...`).

**Step 2 — Authorize**

Click the **🔒 Authorize** button at the top-right of this page.
In the **BearerJWT** row, paste the token into the **Value** field.
Click **Authorize** then **Close**.

Every request you make from Swagger will now include your JWT automatically.

---

### AI provider configuration

| Provider | Purpose | Key var |
|----------|---------|---------|
| Google Gemini `gemini-embedding-001` | Material embedding & RAG search | `GEMINI_API_KEY` |
| OpenRouter `openrouter/free` | Question generation, AI summaries, follow-ups | `OPENROUTER_API_KEY` |

Both keys go in `backend/.env`. Without them the system runs in dev-fallback mode
(zero vectors for embeddings, placeholder text for AI responses).

---

### Typical instructor flow

1. **POST** `/api/v1/courses` — create a course
2. **POST** `/api/v1/courses/{id}/materials/upload` — upload lecture PDF
3. **POST** `/api/v1/courses/{id}/rubrics` — paste the marking rubric
4. **POST** `/api/v1/courses/{id}/question-pools` — create an empty pool
5. **POST** `/api/v1/question-pools/{id}/generate` — AI generates questions from materials
6. **PUT**  `/api/v1/question-pools/{id}/approve` — review and approve
7. **POST** `/api/v1/courses/{id}/assessments` — configure & publish
8. After a student session: **POST** `/api/v1/sessions/{id}/ai-summary/generate`
9. **POST** `/api/v1/sessions/{id}/feedback` → **PUT** `/api/v1/sessions/{id}/release`
"""

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Project 20 — AI Oral Assessment API",
    description=_DESCRIPTION,
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "persistAuthorization": True,   # keeps the token across page refreshes
        "displayRequestDuration": True,
        "filter": True,
    },
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

_cors_origins: list[str] = []
if settings.cors_origins:
    try:
        parsed = json.loads(settings.cors_origins)
        _cors_origins = parsed if isinstance(parsed, list) else [settings.cors_origins]
    except (json.JSONDecodeError, ValueError):
        _cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

# In debug mode always add common local dev ports; in production only use explicit origins.
if settings.debug:
    _DEFAULT_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    _allowed_origins = list(set(_cors_origins + _DEFAULT_ORIGINS))
else:
    # Production: only origins explicitly listed in CORS_ORIGINS
    _allowed_origins = _cors_origins if _cors_origins else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Rate limiter middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Startup logging — surfaces missing AI keys early
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def _log_ai_config() -> None:
    gemini_ok = bool(settings.gemini_api_key)
    openrouter_ok = bool(settings.openrouter_api_key)
    if not gemini_ok:
        logger.warning(
            "GEMINI_API_KEY not set — material embedding and RAG search will be "
            "non-functional. Set it in .env to enable full pipeline."
        )
    if not openrouter_ok:
        logger.warning(
            "OPENROUTER_API_KEY not set — question generation, AI summaries, and "
            "adaptive follow-ups will return placeholder text. "
            "Set it in .env to enable live AI."
        )
    if gemini_ok and openrouter_ok:
        logger.info("AI Gateway: all keys configured (Gemini + OpenRouter).")


# ---------------------------------------------------------------------------
# Health checks (unauthenticated)
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"], summary="Root health check")
def root():
    """Returns service name and version — used for load-balancer probes."""
    return {"status": "ok", "project": "Project 20", "version": "0.4.0"}


@app.get("/health/db", tags=["Health"], summary="Database connectivity check")
def health_db():
    """Verifies the database connection is alive."""
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
        return {"status": "ok", "database": "connected", "public_tables": table_count}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Database health check failed")
        return {"status": "error", "database": str(exc)}


@app.get("/health/ai", tags=["Health"], summary="AI provider configuration check")
def health_ai():
    """Reports whether AI provider keys are configured (no live API call made)."""
    return {
        "status": "ok",
        "providers": {
            "embedding": {
                "provider": "Google Gemini",
                "model": "gemini-embedding-001",
                "dimensions": 768,
                "key_configured": bool(settings.gemini_api_key),
            },
            "chat": {
                "provider": "OpenRouter",
                "model": "openrouter/free",
                "key_configured": bool(settings.openrouter_api_key),
            },
        },
    }


@app.get("/health/migrations", tags=["Health"], summary="Database migration status")
def health_migrations():
    """
    Checks which migrations have been applied by verifying expected DB objects.
    Use this to diagnose 'stuck at extracting' or 500 errors.
    """
    from app.core.database import engine
    from sqlalchemy import text
    checks: dict = {}
    try:
        with engine.connect() as conn:
            # Migration 001: foundation tables
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name IN "
                    "('users','courses','materials','material_chunks','rubrics',"
                    "'question_pools','questions')"
                )
            )
            checks["001_foundation_tables"] = result.scalar() == 7

            # Migration 002: pgvector extension + embedding column
            try:
                conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
                pgvector_ext = conn.execute(
                    text("SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'")
                ).scalar() > 0
            except Exception:
                pgvector_ext = False
            checks["002_pgvector_extension"] = pgvector_ext

            embedding_col = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.columns "
                    "WHERE table_name = 'material_chunks' AND column_name = 'embedding'"
                )
            ).scalar() > 0
            checks["002_embedding_column"] = embedding_col

            # Migration 003: assessment runtime tables
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name IN "
                    "('assessment_configs','assessment_sessions','transcript_messages',"
                    "'ai_summaries','instructor_feedback')"
                )
            )
            checks["003_assessment_runtime"] = result.scalar() == 5

            # Migration 004: vector(768) (only checkable if embedding column exists)
            if embedding_col:
                # Check UDT name contains the dimension info via pgvector catalog
                dim_result = conn.execute(
                    text(
                        "SELECT atttypmod FROM pg_attribute "
                        "JOIN pg_class ON pg_class.oid = pg_attribute.attrelid "
                        "WHERE pg_class.relname = 'material_chunks' "
                        "AND pg_attribute.attname = 'embedding'"
                    )
                )
                row = dim_result.fetchone()
                checks["004_vector_768"] = row is not None and row[0] == 768
            else:
                checks["004_vector_768"] = False

            # Overall status
            all_ok = all(checks.values())
            status = "ok" if all_ok else "incomplete"

            return {
                "status": status,
                "migrations": checks,
                "action_needed": (
                    None if all_ok
                    else "Run: psql <DB_URL> -f db/migrations/001_schema.sql"
                ),
            }
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
