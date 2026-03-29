"""Application configuration loaded from environment variables."""
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_INSECURE_DEFAULT_SECRET = "local-dev-secret-change-in-production"


class Settings(BaseSettings):
    database_url: str = "postgresql://project20:localdev123@localhost:5432/project20_dev"

    # Storage
    storage_backend: str = "local"  # local | s3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""
    aws_region: str = "ap-southeast-2"
    aws_profile_name: str = ""
    s3_bucket_name: str = "team8-project20-materials"
    s3_endpoint_url: str = ""

    # ---------------------------------------------------------------------------
    # AI API Keys
    # ---------------------------------------------------------------------------
    # Google AI Studio key — used for Gemini embedding (gemini-embedding-001).
    # Get one at: https://aistudio.google.com/app/apikey
    gemini_api_key: str = ""

    # OpenRouter key — used for all chat/LLM completions (openrouter/free tier).
    # Get one at: https://openrouter.ai/keys
    openrouter_api_key: str = ""

    # ---------------------------------------------------------------------------
    # Google OAuth 2.0
    # ---------------------------------------------------------------------------
    google_client_id: str = ""
    google_client_secret: str = ""
    # Full URL Google will redirect back to after the consent screen.
    # Must exactly match one of the Authorized Redirect URIs in your
    # Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client.
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # -------------------------------------------------------------------
    # Domain / role rules for NEW accounts (existing rows keep their role)
    # Values can be bare comma-separated or JSON-array style, e.g.:
    #   GOOGLE_INSTRUCTOR_DOMAINS=auckland.ac.nz
    #   GOOGLE_INSTRUCTOR_DOMAINS=[auckland.ac.nz,staff.uni.edu]
    # -------------------------------------------------------------------

    # Emails from these domains → instructor
    google_instructor_domains: str = ""
    # Specific email addresses → instructor (overrides domain check)
    google_instructor_allowlist: str = ""
    # Emails from these domains → student (informational; anything not
    # matched by the instructor rules defaults to student anyway)
    google_student_domains: str = ""
    # If non-empty, ONLY emails whose domain is in this list may log in.
    # Anyone else gets a 403.  Leave blank to allow any Google account.
    google_allowed_login_domains: str = ""

    # ---------------------------------------------------------------------------
    # JWT
    # ---------------------------------------------------------------------------
    jwt_secret_key: str = _INSECURE_DEFAULT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # ---------------------------------------------------------------------------
    # Rate limiting (requests per minute, per IP)
    # ---------------------------------------------------------------------------
    rate_limit_auth: int = 10       # /auth endpoints
    rate_limit_ai: int = 5          # AI generation endpoints (question gen, summaries)
    rate_limit_default: int = 60    # all other endpoints

    # ---------------------------------------------------------------------------
    # Application
    # ---------------------------------------------------------------------------
    # Where the SPA lives. After a successful OAuth callback the backend will
    # redirect to  {frontend_url}/auth/callback?token=<jwt>&role=<role>
    # Leave blank to return JSON instead of redirecting (useful for API testing).
    frontend_url: str = ""

    # JSON array or comma-separated list of allowed CORS origins.
    # e.g. CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
    cors_origins: str = ""

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# ---------------------------------------------------------------------------
# Start-up security warnings
# ---------------------------------------------------------------------------

if settings.jwt_secret_key == _INSECURE_DEFAULT_SECRET and not settings.debug:
    raise RuntimeError(
        "JWT_SECRET_KEY is set to the insecure development default. "
        "Set a strong random secret in your .env before running in production. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

if settings.jwt_secret_key == _INSECURE_DEFAULT_SECRET:
    logger.warning(
        "JWT_SECRET_KEY is using the insecure development default. "
        "Set JWT_SECRET_KEY in .env before deploying to production."
    )
