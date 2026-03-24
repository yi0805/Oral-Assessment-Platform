"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://project20:localdev123@localhost:5432/project20_dev"

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-southeast-2"
    s3_bucket_name: str = "project20-materials"

    openai_api_key: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""

    jwt_secret_key: str = "local-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
