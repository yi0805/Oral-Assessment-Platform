from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# this settings will read from .env file and environment variables, providing a centralised configuration for the application.

class Settings(BaseSettings):
    database_url: str 

    storage_backend: str
    s3_bucket_name: str
    aws_region: str
    # Integration made this optional for prod deployments using an
    # instance role instead of a named profile. The streaming
    # resolver (audio_streamer._BotoProfileCredentialResolver) is
    # guarded behind `if profile_name`, so None falls through to the
    # SDK's default CRT credential chain — works in both cases.
    aws_profile_name: str | None = None

    # Issue #72: poll interval (seconds) for batch AWS Transcribe jobs.
    transcribe_poll_interval_seconds: int = 1

    # Master switch for every Amazon Transcribe route. Keep production
    # opt-in: disabling streaming alone does not disable batch jobs.
    transcribe_enabled: bool = False

    # Issue #72: feature flag for the WebSocket streaming-transcription
    # route (/sessions/{id}/transcribe/stream).
    stt_streaming_enabled: bool = True

    # Issue #72: hard cap (seconds) on a single streaming-transcribe
    # WebSocket session.
    stt_streaming_max_seconds: int = 300

    # BackgroundTasks are in-process. Only a processing row older than this
    # threshold is eligible for instructor-authorised recovery.
    material_processing_stale_seconds: int = Field(default=900, ge=60)

    gemini_api_key: str
    openrouter_api_key: str
    aws_bearer_token_bedrock: str | None = None

    google_instructor_domains: str
    google_instructor_allowlist: str
    google_allowed_login_domains: str

    jwt_secret_key: str 
    jwt_algorithm: str 
    jwt_expire_minutes: int
 
    rate_limit_default: int

    cors_origins: str

    cookie_secure: bool = False

    # Safe deployment metadata for diagnostics. These values deliberately
    # contain no infrastructure or credential details.
    app_version: str = "unknown"
    git_commit: str = "unknown"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

