"""
Material upload & processing routes.

Endpoints
---------
POST   /courses/{course_id}/materials/upload   Upload a file to storage
GET    /courses/{course_id}/materials           List all materials for a course
GET    /materials/{material_id}                 Get material details + processing status
GET    /materials/{material_id}/status          Lightweight processing-status poll
DELETE /materials/{material_id}                 Delete material + storage object

Processing pipeline (triggered asynchronously after upload):
  uploaded → extracting → chunking → embedding → ready  (or failed)
"""
import logging
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor
from app.models.course import Course, CourseEnrollment
from app.models.material import Material
from app.models.user import User
from app.schemas.material import (
    MaterialListItem,
    MaterialOut,
    MaterialStatusOut,
    MaterialUploadResponse,
)
from app.services import s3_client

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_FILE_TYPES = {"pdf", "pptx", "docx", "txt"}
MIME_MAP = {
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}


@router.post(
    "/courses/{course_id}/materials/upload",
    response_model=MaterialUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a course material",
    description=(
        "Instructor-only. Validates the file type, uploads to the configured "
        "storage backend (local or S3), persists metadata, and triggers the "
        "async processing pipeline (extract → chunk → embed → ready)."
    ),
)
async def upload_material(
    course_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Verify the uploader is enrolled as instructor in this course (or is admin).
    if current_user.role != "admin":
        enrollment = (
            db.query(CourseEnrollment)
            .filter(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.user_id == current_user.id,
                CourseEnrollment.course_role.in_(["instructor", "ta"]),
                CourseEnrollment.is_active.is_(True),
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
    if extension not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File type '{extension}' is not supported. Allowed types: {sorted(ALLOWED_FILE_TYPES)}",
        )

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
                "title": title,
                "uploaded_by": str(current_user.id),
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
        uploaded_by=current_user.id,
        title=title,
        original_filename=filename,
        file_type=extension,
        mime_type=content_type,
        storage_key=storage_key,
        file_size_bytes=len(file_bytes),
        processing_status="uploaded",
    )

    try:
        db.add(material)
        db.commit()
        db.refresh(material)
    except SQLAlchemyError as exc:
        db.rollback()
        try:
            s3_client.delete_file(storage_key)
        except Exception:  # noqa: BLE001
            logger.exception("Rollback cleanup failed for storage key=%s", storage_key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Material metadata could not be saved.",
        ) from exc

    # Trigger background processing pipeline when ready.
    # background_tasks.add_task(material_pipeline.run_pipeline, material.id)

    return material


@router.get(
    "/courses/{course_id}/materials",
    response_model=list[MaterialListItem],
    summary="List course materials",
    description="Returns all materials for a course ordered by upload date (newest first).",
)
def list_materials(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    materials = (
        db.query(Material)
        .filter(Material.course_id == course_id)
        .order_by(Material.uploaded_at.desc())
        .all()
    )
    return materials


@router.get(
    "/materials/{material_id}",
    response_model=MaterialOut,
    summary="Get material details",
    description="Returns full material metadata including the current processing status.",
)
def get_material(
    material_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    return material


@router.get(
    "/materials/{material_id}/status",
    response_model=MaterialStatusOut,
    summary="Poll processing status",
    description=(
        "Lightweight endpoint for polling the material processing pipeline status. "
        "Expected transitions: uploaded → extracting → chunking → embedding → ready (or failed)."
    ),
)
def get_material_status(
    material_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    return material


@router.delete(
    "/materials/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a material",
    description="Instructor-only. Removes the storage object and the database record.",
)
def delete_material(
    material_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

    try:
        s3_client.delete_file(material.storage_key)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage delete failed: {exc}",
        ) from exc

    db.delete(material)
    db.commit()
    return None
