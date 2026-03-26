"""
Material upload & processing routes

Endpoints:
  POST /courses/:id/materials/upload → upload PDF to S3, create materials row
  GET /courses/:id/materials → list all materials for a course
  GET /materials/:id → get material details + processing status
  GET /materials/:id/status → poll processing status (SSE preferred)
  DELETE /materials/:id → soft-delete material + S3 object

Pipeline flow triggered by upload:
  upload → extracting → chunking → embedding → ready
  (see app/services/material_pipeline.py)
"""
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.course import Course
from app.models.material import Material
from app.schemas.material import MaterialListItem, MaterialOut, MaterialStatusOut, MaterialUploadResponse
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
)
async def upload_material(
    course_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Upload a course material file.
    1. Validate file type
    2. Upload bytes to configured storage backend
    3. Create materials row with status='uploaded'
    4. Trigger background processing pipeline
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    filename = file.filename or "unknown"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"File type '{extension}' not supported. Allowed: {sorted(ALLOWED_FILE_TYPES)}",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")

    material_id = uuid4()
    storage_key = s3_client.generate_key(course_id, material_id, filename)
    content_type = file.content_type or MIME_MAP.get(extension) or "application/octet-stream"

    try:
        s3_client.upload_file(
            file_bytes,
            storage_key,
            content_type=content_type,
            metadata={
                "course_id": str(course_id),
                "material_id": str(material_id),
                "title": title,
            },
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=f"Storage upload failed: {exc}") from exc

    material = Material(
        id=material_id,
        course_id=course_id,
        uploaded_by=UUID("a0000000-0000-0000-0000-000000000001"),  # TODO: replace with auth user
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
        raise HTTPException(status_code=500, detail="Material metadata could not be saved") from exc

    # Leave pipeline disabled until extraction/chunking is ready for every file type.
    # background_tasks.add_task(material_pipeline.run_pipeline, material.id)
    return material


@router.get("/courses/{course_id}/materials", response_model=list[MaterialListItem])
def list_materials(course_id: UUID, db: Session = Depends(get_db)):
    """List all materials for a course, ordered by upload date."""
    materials = (
        db.query(Material)
        .filter(Material.course_id == course_id)
        .order_by(Material.uploaded_at.desc())
        .all()
    )
    return materials


@router.get("/materials/{material_id}", response_model=MaterialOut)
def get_material(material_id: UUID, db: Session = Depends(get_db)):
    """Get full details for a specific material including processing state."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.get("/materials/{material_id}/status", response_model=MaterialStatusOut)
def get_material_status(material_id: UUID, db: Session = Depends(get_db)):
    """Lightweight polling endpoint for processing status."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(material_id: UUID, db: Session = Depends(get_db)):
    """Delete a material and remove the object from the configured storage backend."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    try:
        s3_client.delete_file(material.storage_key)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=f"Storage delete failed: {exc}") from exc

    db.delete(material)
    db.commit()
    return None
