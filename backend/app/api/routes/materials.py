import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_instructor
from app.core.limiter import limiter
from app.services import material_pipeline, s3_client
from app.services.github_importer import fetch_repo_as_text
from app.utils.upload_validation import read_pdf_upload

from app.models import Course, CourseEnrollment, Material, User
from app.schemas import GithubImportBody, MaterialStatusOut, MaterialUploadOut


router = APIRouter()
logger = logging.getLogger(__name__)


def _material_status_out(material: Material) -> MaterialStatusOut:
    return MaterialStatusOut(
        id=material.id,
        filename=material.filename,
        processing_status=material.processing_status,
        is_processing_stale=material_pipeline.is_material_processing_stale(material),
    )

def _require_course_instructor(db: Session, course_id: UUID, user: User) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == user.id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an instructor in this course.",
        )

    return course

# Upload material

@router.post(
    "/courses/{course_id}/materials/upload",
    response_model=MaterialUploadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Material",
)
@limiter.limit("10/minute")
async def upload_material(
    request: Request,
    course_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    _require_course_instructor(db, course_id, current_user)

    filename = file.filename or "unknown.pdf"

    # Check for existing material
    existing_material = (
        db.query(Material)
        .filter(
            Material.course_id == course_id,
            Material.filename == filename,
            Material.material_category == "course_material",
        )
        .first()
    )

    if existing_material:
        return MaterialUploadOut(
            id=existing_material.id,
            processing_status=existing_material.processing_status,
        )

    file_bytes = await read_pdf_upload(file)

    # Upload to storage
    material_id = uuid4()
    storage_key = s3_client.generate_key(course_id, material_id, filename)
    content_type = "application/pdf"

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
        logger.warning("Material storage upload failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Material storage is currently unavailable.",
        ) from exc

    # Save material record
    material = Material(
        id=material_id,
        course_id=course_id,
        filename=filename,
        mime_type=content_type,
        storage_key=storage_key,
        material_category="course_material",
        processing_status="processing",
        processing_started_at=datetime.now(timezone.utc),
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

    # Kick off background pipeline
    background_tasks.add_task(material_pipeline.run_pipeline, material.id)

    return MaterialUploadOut(id=material.id, processing_status=material.processing_status)


@router.get(
    "/courses/{course_id}/materials/{material_id}/status",
    response_model=MaterialStatusOut,
    summary="Get material processing status",
)
def get_material_status(
    course_id: UUID,
    material_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    _require_course_instructor(db, course_id, current_user)
    material = (
        db.query(Material)
        .filter(Material.id == material_id, Material.course_id == course_id)
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="Material not found for this course.")
    return _material_status_out(material)


@router.post(
    "/courses/{course_id}/materials/{material_id}/retry",
    response_model=MaterialStatusOut,
    summary="Retry failed or interrupted material processing",
)
def retry_material_processing(
    course_id: UUID,
    material_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    _require_course_instructor(db, course_id, current_user)
    material = (
        db.query(Material)
        .filter(Material.id == material_id, Material.course_id == course_id)
        .with_for_update()
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="Material not found for this course.")
    if not material_pipeline.can_retry_material_processing(material):
        raise HTTPException(
            status_code=409,
            detail="Only failed or interrupted materials can be retried.",
        )

    material_pipeline.mark_material_processing(material)
    db.commit()
    background_tasks.add_task(material_pipeline.run_pipeline, material.id)
    return _material_status_out(material)


# Import GitHub repo as material

@router.post(
    "/courses/{course_id}/materials/github",
    response_model=MaterialUploadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Import GitHub Repo as Material",
)
@limiter.limit("5/minute")
async def import_github_repo(
    request: Request,
    course_id: UUID,
    body: GithubImportBody,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    _require_course_instructor(db, course_id, current_user)

    text_bytes, filename = await fetch_repo_as_text(body.url, body.ref)

    existing_material = (
        db.query(Material)
        .filter(
            Material.course_id == course_id,
            Material.filename == filename,
            Material.material_category == "course_material",
        )
        .first()
    )

    if existing_material:
        return MaterialUploadOut(
            id=existing_material.id,
            processing_status=existing_material.processing_status,
        )

    material_id = uuid4()
    storage_key = s3_client.generate_key(course_id, material_id, filename)
    content_type = "text/plain"

    try:
        s3_client.upload_file(
            text_bytes,
            storage_key,
            content_type=content_type,
            metadata={
                "course_id": str(course_id),
                "material_id": str(material_id),
                "title": filename,
                "source": "github",
                "source_url": body.url,
            },
        )

    except RuntimeError as exc:
        logger.warning("GitHub material storage upload failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Material storage is currently unavailable.",
        ) from exc

    material = Material(
        id=material_id,
        course_id=course_id,
        filename=filename,
        mime_type=content_type,
        storage_key=storage_key,
        material_category="course_material",
        processing_status="processing",
        processing_started_at=datetime.now(timezone.utc),
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

    background_tasks.add_task(material_pipeline.run_pipeline, material.id)

    return MaterialUploadOut(id=material.id, processing_status=material.processing_status)
