"""Storage client wrapper with local filesystem fallback for development."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, ProfileNotFound

from app.core.config import settings

logger = logging.getLogger(__name__)

LOCAL_STORAGE_DIR = Path("local_uploads")


def _use_local() -> bool:
    """Return True when the app is configured to use local storage."""
    return settings.storage_backend.lower() != "s3"


def _get_session() -> boto3.session.Session:
    """Create a boto3 session that supports explicit creds, profile-based SSO, or the default chain."""
    if settings.aws_profile_name:
        logger.info("[S3] Using AWS profile '%s'", settings.aws_profile_name)
        return boto3.Session(
            profile_name=settings.aws_profile_name,
            region_name=settings.aws_region,
        )

    if settings.aws_access_key_id and settings.aws_secret_access_key:
        logger.info("[S3] Using explicit AWS credentials from settings")
        return boto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_session_token=settings.aws_session_token or None,
            region_name=settings.aws_region,
        )

    logger.info("[S3] Using default AWS credential chain")
    return boto3.Session(region_name=settings.aws_region)


def _get_s3_client():
    """Create an S3 client from the configured boto3 session."""
    if not settings.s3_bucket_name:
        raise RuntimeError("S3_BUCKET_NAME is required when STORAGE_BACKEND=s3")

    try:
        session = _get_session()
        kwargs = {"region_name": settings.aws_region}
        if settings.s3_endpoint_url:
            kwargs["endpoint_url"] = settings.s3_endpoint_url
        return session.client("s3", **kwargs)
    except ProfileNotFound as exc:
        raise RuntimeError(
            f"AWS profile '{settings.aws_profile_name}' was not found. Run aws configure sso or set AWS_PROFILE_NAME correctly."
        ) from exc


def upload_file(
    file_bytes: bytes,
    storage_key: str,
    *,
    content_type: Optional[str] = None,
    metadata: Optional[dict[str, str]] = None,
) -> str:
    """Upload a file to S3 or local filesystem and return the storage key."""
    if _use_local():
        local_path = LOCAL_STORAGE_DIR / storage_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(file_bytes)
        logger.info("[LOCAL] Saved %s bytes to %s", len(file_bytes), local_path)
        return storage_key

    client = _get_s3_client()
    put_kwargs = {
        "Bucket": settings.s3_bucket_name,
        "Key": storage_key,
        "Body": file_bytes,
    }
    if content_type:
        put_kwargs["ContentType"] = content_type
    if metadata:
        put_kwargs["Metadata"] = metadata

    try:
        client.put_object(**put_kwargs)
    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        logger.exception("[S3] Upload failed for key=%s", storage_key)
        raise RuntimeError(f"Could not upload file to S3: {exc}") from exc

    logger.info("[S3] Uploaded %s bytes to s3://%s/%s", len(file_bytes), settings.s3_bucket_name, storage_key)
    return storage_key


def download_file(storage_key: str) -> bytes:
    """Download a file from S3 or local filesystem."""
    if _use_local():
        local_path = LOCAL_STORAGE_DIR / storage_key
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")
        return local_path.read_bytes()

    client = _get_s3_client()
    try:
        response = client.get_object(Bucket=settings.s3_bucket_name, Key=storage_key)
        return response["Body"].read()
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
            raise FileNotFoundError(f"S3 object not found: {storage_key}") from exc
        raise RuntimeError(f"Could not download file from S3: {exc}") from exc


def delete_file(storage_key: str) -> None:
    """Delete a file from S3 or local filesystem."""
    if _use_local():
        local_path = LOCAL_STORAGE_DIR / storage_key
        if local_path.exists():
            local_path.unlink()
            logger.info("[LOCAL] Deleted %s", local_path)
        return

    client = _get_s3_client()
    try:
        client.delete_object(Bucket=settings.s3_bucket_name, Key=storage_key)
    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        logger.exception("[S3] Delete failed for key=%s", storage_key)
        raise RuntimeError(f"Could not delete file from S3: {exc}") from exc

    logger.info("[S3] Deleted s3://%s/%s", settings.s3_bucket_name, storage_key)


def generate_key(course_id: UUID, material_id: UUID, filename: str) -> str:
    """Generate the storage key following the project convention."""
    safe_filename = Path(filename).name
    return f"courses/{course_id}/materials/{material_id}/{safe_filename}"
