from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import quote, unquote
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services import s3_client

from app.models import User

logger = logging.getLogger(__name__)

MAX_PICTURE_BYTES = 5 * 1024 * 1024

router = APIRouter()


def _s3_base_url() -> str:
    """Return the public, virtual-hosted S3 endpoint for this deployment."""
    return f"https://{settings.s3_bucket_name}.s3.{settings.aws_region}.amazonaws.com/"


def _public_s3_url(storage_key: str) -> str:
    """Build a browser-safe public URL while retaining S3 key separators."""
    return f"{_s3_base_url()}{quote(storage_key, safe='/')}"


@router.put("/updateUsername",
            summary = "Change the current users full name.")
def update_user_name(
    new_username: str = Query(..., min_length=1, max_length=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cleaned = new_username.strip()

    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Display name cannot be empty.",
        )

    user.full_name = cleaned

    db.commit()
    db.refresh(user)

    return {"message": "Name updated successfully"}


@router.put("/updatePicture", 
            summary="Change the current users profile picture")
async def update_picture(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    filename = file.filename or "unknown"

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is empty.",
        )

    if len(file_bytes) > MAX_PICTURE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Profile picture must be 5 MB or smaller.",
        )

    image_id = uuid4()

    safe_filename = Path(filename).name
    storage_key = f"users/{user.id}/images/{image_id}/{safe_filename}"
    public_url = _public_s3_url(storage_key)
    content_type = file.content_type
    previous_image_url = user.image

    try:
        s3_client.upload_file(
            file_bytes,
            storage_key,
            content_type=content_type,
            metadata={
                "user_id": str(user.id),
                "image_id": str(image_id),
                "filename": filename,
            },
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage upload failed: {e}",
        ) from e

    try:
        user.image = public_url
        db.commit()
        db.refresh(user)

    except SQLAlchemyError as e:
        db.rollback()

        try:
            s3_client.delete_file(storage_key)

        except RuntimeError:
            logger.exception(
                "Failed to clean up S3 object %s after DB error", storage_key
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile picture could not be saved.",
        ) from e

    s3_base_url = _s3_base_url()
    if previous_image_url and previous_image_url.startswith(s3_base_url):
        previous_key = unquote(previous_image_url[len(s3_base_url):])

        if previous_key and previous_key != storage_key:
            try:
                s3_client.delete_file(previous_key)
                
            except RuntimeError:
                logger.exception(
                    "Failed to delete previous profile picture %s", previous_key
                )

    return {
        "message": "Profile picture updated successfully",
    }
