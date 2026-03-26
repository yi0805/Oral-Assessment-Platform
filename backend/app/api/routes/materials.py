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

TODO:
- POST upload endpoint with multipart/form-data
- S3 upload via boto3 (or local file storage for dev)
- Background task to trigger pipeline
- GET list and detail endpoints
- Status polling endpoint
"""
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.material import Material
from app.models.course import Course
from app.schemas.material import MaterialUploadResponse, MaterialOut, MaterialStatusOut, MaterialListItem

router = APIRouter()

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
    Upload a course material file (PDF for MVP).
    1. Validate file type
    2. Generate S3 key and upload to S3 (or local storage in dev)
    3. Create materials row with status='uploaded'
    4. Trigger background processing pipeline
    """
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Validate file type
    filename = file.filename or "unknown"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"File type '{extension}' not supported. Allowed: {ALLOWED_FILE_TYPES}",
        )

    # Read file content
    file_bytes = await file.read()
    material_id = uuid4()

    # S3 key convention: courses/{course_id}/materials/{material_id}/{filename}
    storage_key = f"courses/{course_id}/materials/{material_id}/{filename}"

    # TODO: Upload to S3 via app.services.s3_client
    # For local dev, save to a local directory instead
    # s3_client.upload_file(file_bytes, storage_key)

    # Create database record
    material = Material(
        id=material_id,
        course_id=course_id,
        # uploaded_by=current_user.id,  # TODO: wire auth
        uploaded_by=UUID("a0000000-0000-0000-0000-000000000001"),  # Temp: seed instructor
        title=title,
        original_filename=filename,
        file_type=extension,
        mime_type=MIME_MAP.get(extension),
        storage_key=storage_key,
        file_size_bytes=len(file_bytes),
        processing_status="uploaded",
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    # Trigger background processing pipeline
    # background_tasks.add_task(material_pipeline.run_pipeline, material.id)
    # TODO: uncomment when material_pipeline service is implemented

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
    """Soft-delete a material and its S3 object."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # TODO: Delete from S3 via s3_client.delete_file(material.storage_key)

    db.delete(material)
    db.commit()
    return None

