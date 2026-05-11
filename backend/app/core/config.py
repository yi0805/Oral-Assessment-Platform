from pydantic_settings import BaseSettings, SettingsConfigDict

# this settings will read from .env file and environment variables, providing a centralised configuration for the application.

class Settings(BaseSettings):
    database_url: str 

    storage_backend: str
    s3_bucket_name: str
    aws_region: str
    aws_profile_name: str

    # Issue #72: poll interval (seconds) for batch AWS Transcribe jobs.
    # Lower values return results sooner; slightly more API calls. 1s is
    # a sensible default; values above ~5s materially hurt perceived
    # latency. Override per-deployment via TRANSCRIBE_POLL_INTERVAL_SECONDS.
    transcribe_poll_interval_seconds: int = 1

    # Issue #72: feature flag for the WebSocket streaming-transcription
    # route (/sessions/{id}/transcribe/stream). Default ON after the
    # rollout in commit 28 of the feature/audio-to-text branch — the
    # streaming path delivers partials within ~300 ms and the batch
    # path is retained as the automatic fallback (see
    # useStudentSpeechStream.js + audio_transcriber.py). Set
    # STT_STREAMING_ENABLED=0 to force the legacy batch-only behaviour
    # if a regression turns up post-merge.
    stt_streaming_enabled: bool = True

    # Issue #72: hard cap (seconds) on a single streaming-transcribe
    # WebSocket session. Mirrors the 25 MB upload cap on the batch
    # route — protects against a stuck mic stream / runaway client
    # holding an AWS Transcribe Streaming connection open indefinitely.
    # 300s (5 minutes) is roomy for any realistic single-question
    # answer; the assessment-wide time limit (config.total_time_minute)
    # is enforced separately by _validate_session_for_transcribe.
    stt_streaming_max_seconds: int = 300

    gemini_api_key: str
    openrouter_api_key: str
    aws_bearer_token_bedrock: str

    google_instructor_domains: str
    google_instructor_allowlist: str
    google_allowed_login_domains: str

    jwt_secret_key: str 
    jwt_algorithm: str 
    jwt_expire_minutes: int
 
    rate_limit_default: int  

    cors_origins: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

