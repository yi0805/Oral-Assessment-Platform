from app.models.user import User

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services import  s3_client

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
    user = db.query(User).filter(User.id == user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.full_name = new_username
    db.commit()
    db.refresh(user)
    return {"message": "User updated", "user": {"id": user.id, "name": user.full_name}}


@router.put("/updatePicture", summary="Change the current users profile picture")
async def update_picture(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    exists = db.query(User).filter(User.id == user.id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="User not found")
    filename = file.filename or "unknown"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is empty.",
        )
    image_id = UUID.uuid4()
    storage_key = s3_client.generate_key(user.id, image_id, filename)
    content_type = file.content_type or MIME_MAP.get(extension, "application/octet-stream")
    try:
        s3_client.upload_file(
        file_bytes,
        storage_key,
        content_type,
        metadata={
                "user_id": str(user.id),
                "image_id": str(image_id),
                "filename": filename,
            }
    )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage upload failed: {exc}",
        ) from exc

    try:
        user.image = storage_key
        db.commit()
        db.refresh(user)
    
    except SQLAlchemyError as exc:
        db.rollback()
        s3_client.delete_file(storage_key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Material metadata could not be saved.",
        ) from exc

    return {
        "message": "Profile picture updated",
        "key": storage_key
    }