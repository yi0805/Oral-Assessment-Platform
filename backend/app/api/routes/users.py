from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services import s3_client

from app.models import User

logger = logging.getLogger(__name__)

MIME_MAP = {
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}

router = APIRouter()

@router.put("/updateUsername",
            summary = "Change the current users full name.")
def update_user_name(new_username: str,
                    user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    user.full_name = new_username

    db.commit()
    db.refresh(user)

    return {"message": "User updated successfully"}


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
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    S3_BASE_URL = "https://team8-project20-materials.s3.ap-southeast-2.amazonaws.com/"

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is empty.",
        )
    
    image_id = uuid4()

    safe_filename = Path(filename).name
    storage_key = f"users/{user.id}/images/{image_id}/{safe_filename}"
    public_url = f"{S3_BASE_URL}{storage_key}"
    content_type = file.content_type or MIME_MAP.get(extension, "application/octet-stream")

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

    return {
        "message": "Profile picture updated successfully",
    }