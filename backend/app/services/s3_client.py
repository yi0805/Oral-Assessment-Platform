"""
AWS S3 client wrapper with local filesystem fallback for development.
Uses local storage when AWS credentials are not configured.
"""
import os
import logging
from pathlib import Path
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

LOCAL_STORAGE_DIR = Path("local_uploads")


def _use_local() -> bool:
    """Return True if AWS credentials are not configured (local dev mode)."""
    return not settings.aws_access_key_id

def _get_s3_client():
    """Create a boto3 S3 client from settings."""
    import os
    session_token = os.getenv("AWS_SESSION_TOKEN", "")
    kwargs = {
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
        "region_name": settings.aws_region,
    }
    if session_token:
        kwargs["aws_session_token"] = session_token
    return boto3.client("s3", **kwargs)


def upload_file(file_bytes: bytes, storage_key: str) -> str:
    """
    Upload a file to S3 or local filesystem.
    Returns the storage key on success.
    """
    if _use_local():
        local_path = LOCAL_STORAGE_DIR / storage_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(file_bytes)
        logger.info(f"[LOCAL] Saved {len(file_bytes)} bytes to {local_path}")
        return storage_key

    client = _get_s3_client()
    client.put_object(
        Bucket=settings.s3_bucket_name,
        Key=storage_key,
        Body=file_bytes,
    )
    logger.info(f"[S3] Uploaded {len(file_bytes)} bytes to s3://{settings.s3_bucket_name}/{storage_key}")
    return storage_key


def download_file(storage_key: str) -> bytes:
    """Download a file from S3 or local filesystem. Returns the file content as bytes."""
    if _use_local():
        local_path = LOCAL_STORAGE_DIR / storage_key
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")
        return local_path.read_bytes()

    client = _get_s3_client()
    try:
        response = client.get_object(Bucket=settings.s3_bucket_name, Key=storage_key)
        return response["Body"].read()
    except ClientError as e:
        raise FileNotFoundError(f"S3 object not found: {storage_key}") from e


def delete_file(storage_key: str) -> None:
    """Delete a file from S3 or local filesystem."""
    if _use_local():
        local_path = LOCAL_STORAGE_DIR / storage_key
        if local_path.exists():
            local_path.unlink()
            logger.info(f"[LOCAL] Deleted {local_path}")
        return

    client = _get_s3_client()
    client.delete_object(Bucket=settings.s3_bucket_name, Key=storage_key)
    logger.info(f"[S3] Deleted s3://{settings.s3_bucket_name}/{storage_key}")


def generate_key(course_id: UUID, material_id: UUID, filename: str) -> str:
    """Generate the S3 key following the project convention."""
    return f"courses/{course_id}/materials/{material_id}/{filename}"
