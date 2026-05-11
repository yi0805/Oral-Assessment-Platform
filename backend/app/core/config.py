from pydantic_settings import BaseSettings, SettingsConfigDict

# this settings will read from .env file and environment variables, providing a centralised configuration for the application.

class Settings(BaseSettings):
    database_url: str 

    storage_backend: str
    s3_bucket_name: str
    aws_region: str
    aws_profile_name: str | None = None

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

