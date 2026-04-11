import logging
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_instructor

from app.services import material_pipeline, s3_client

from app.models import  Course, CourseEnrollment, Material, User

router = APIRouter()
logger = logging.getLogger(__name__)

MIME_MAP = {
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}


@router.post(
    "/courses/{course_id}/materials/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload Material",
)
async def upload_material(
    course_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_role.in_(["instructor"]),
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an instructor in this course.",
        )

    filename = file.filename or "unknown"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    existing_material = (
        db.query(Material)
        .filter(
            Material.course_id == course_id,
            Material.filename == filename,
        )
        .first()
    )

    if existing_material:
        return existing_material.id
    
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is empty.",
        )

    material_id = uuid4()
    storage_key = s3_client.generate_key(course_id, material_id, filename)
    content_type = file.content_type or MIME_MAP.get(extension, "application/octet-stream")

    try:
        s3_client.upload_file(
            file_bytes,
            storage_key,
            content_type=content_type,
            metadata={
                "course_id": str(course_id),
                "material_id": str(material_id),
                "title": filename,
            },
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage upload failed: {exc}",
        ) from exc

    material = Material(
        id=material_id,
        course_id=course_id,
        filename=filename,
        mime_type=content_type,
        storage_key=storage_key,
        material_category="course_material",
    )

    try:
        db.add(material)
        db.commit()
        db.refresh(material)

    except SQLAlchemyError as exc:
        db.rollback()
        try:
            s3_client.delete_file(storage_key)

        except Exception:  
            logger.exception("Rollback cleanup failed for storage key=%s", storage_key)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Material metadata could not be saved.",
        ) from exc

    # Trigger the 4-stage processing pipeline as a background task:
    # extracting → chunking → embedding (Gemini gemini-embedding-001) → ready
    background_tasks.add_task(material_pipeline.run_pipeline, material.id)

    return material.id