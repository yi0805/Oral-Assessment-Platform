from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from app.core.config import settings
from app.services.aws_clients import get_s3_client

logger = logging.getLogger(__name__)


def _get_s3_client():
    if not settings.s3_bucket_name:
        raise RuntimeError("S3_BUCKET_NAME is required when STORAGE_BACKEND=s3")
    return get_s3_client()


def upload_file(
    file_bytes: bytes,
    storage_key: str,
    *,
    content_type: str,
    metadata: Optional[dict[str, str]] = None,
) -> str:

    client = _get_s3_client()

    put_kwargs = {
        "Bucket": settings.s3_bucket_name,
        "Key": storage_key,
        "Body": file_bytes,
        "ContentType": content_type,
    }

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

    client = _get_s3_client()

    try:
        response = client.get_object(Bucket=settings.s3_bucket_name, Key=storage_key)
        
        return response["Body"].read()
    
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
            raise FileNotFoundError(f"S3 object not found: {storage_key}") from exc
        raise RuntimeError(f"Could not download file from S3: {exc}") from exc


def copy_object(source_key: str, dest_key: str) -> str:

    client = _get_s3_client()

    try:
        client.copy_object(
            Bucket=settings.s3_bucket_name,
            Key=dest_key,
            CopySource={"Bucket": settings.s3_bucket_name, "Key": source_key},
        )

    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        logger.exception("[S3] Copy failed: %s -> %s", source_key, dest_key)
        raise RuntimeError(f"Could not copy file in S3: {exc}") from exc

    logger.info(
        "[S3] Copied s3://%s/%s -> s3://%s/%s",
        settings.s3_bucket_name, source_key,
        settings.s3_bucket_name, dest_key,
    )
    return dest_key


def delete_file(storage_key: str) -> None:

    client = _get_s3_client()

    try:
        client.delete_object(Bucket=settings.s3_bucket_name, Key=storage_key)

    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        logger.exception("[S3] Delete failed for key=%s", storage_key)
        raise RuntimeError(f"Could not delete file from S3: {exc}") from exc

    logger.info("[S3] Deleted s3://%s/%s", settings.s3_bucket_name, storage_key)


def generate_key(course_id: UUID, material_id: UUID, filename: str) -> str:

    safe_filename = Path(filename).name

    return f"courses/{course_id}/materials/{material_id}/{safe_filename}"
