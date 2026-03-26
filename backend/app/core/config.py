"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    openai_api_key: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""

    jwt_secret_key: str = "local-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
