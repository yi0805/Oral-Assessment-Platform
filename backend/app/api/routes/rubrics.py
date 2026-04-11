"""
Rubric management routes.

Endpoints
---------
POST   /courses/{course_id}/rubrics   Create a rubric (instructor only)
GET    /courses/{course_id}/rubrics   List all rubrics for a course
GET    /rubrics/{rubric_id}           Get full rubric including rubric_text
PUT    /rubrics/{rubric_id}           Update rubric content (instructor only)
DELETE /rubrics/{rubric_id}           Delete a rubric (instructor only)
"""
from uuid import UUID, uuid4
import logging
from sqlalchemy.exc import SQLAlchemyError

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.services import s3_client, material_pipeline
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor
from app.models.course import Course, CourseEnrollment
from app.models.rubric import Rubric
from app.models.user import User
from app.models.material import Material
from app.schemas.pagination import Page
from app.schemas.rubric import RubricBrief, RubricCreate, RubricOut, RubricUpdate
from app.schemas.material import MaterialUploadResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/courses/{course_id}/rubrics/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Integration",

)
async def upload_rubric(
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

    # Guard against accidental double-uploads of the same file.
    # If a rubric with the same original_filename already exists in this course
    # (regardless of processing status), return 409 with its ID so the caller
    # can manage the existing record instead of creating a duplicate.
    existing_rubric = (
        db.query(Rubric)
        .filter(
            Rubric.course_id == course_id,
            Rubric.original_filename == filename,
            Rubric.title == title,
        )
        .first()
    )
    if existing_rubric:
        # raise HTTPException(
        #     status_code=status.HTTP_409_CONFLICT,
        #     detail=(
        #         f"A rubric named '{filename}' already exists in this course "
        #         f"(id: {existing_rubric.id}). "
        #         "Delete the existing rubric first if you want to re-upload."
        #     ),
        # )
        return existing_rubric.id

    if extension != "pdf":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rubric upload only supports PDF files.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is empty.",
        )

    material_id = uuid4()
    storage_key = s3_client.generate_key(course_id, material_id, filename)

    try:
        # 1) upload PDF
        s3_client.upload_file(
            file_bytes,
            storage_key,
            content_type="application/pdf",
            metadata={
                "course_id": str(course_id),
                "material_id": str(material_id),
                "title": title,
                "uploaded_by": str(current_user.id),
                "material_category": "rubric",
            },
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage upload failed: {exc}",
        ) from exc

    # 2) create Material
    material = Material(
        id=material_id,
        course_id=course_id,
        uploaded_by=current_user.id,
        title=title,
        original_filename=filename,
        file_type="pdf",
        mime_type="application/pdf",
        storage_key=storage_key,
        file_size_bytes=len(file_bytes),
        processing_status="uploaded",
        material_category="rubric",
    )

    # 3) extract rubric text immediately
    extracted_text = material_pipeline.extract_text_from_bytes(
        pdf_bytes=file_bytes,
    )
    if not extracted_text:
        raise HTTPException(status_code=422, detail="Could not extract rubric text from PDF.")
    
    db.add(material)
    db.flush()

    # 3) create Rubric
    rubric = Rubric(
        course_id=course_id,
        title=title,
        rubric_text=extracted_text.text,
        original_filename=filename,
        storage_key=storage_key,
        created_by=current_user.id,
        material_id=material.id,
    )

    # 4) commit
    try:
        db.add(rubric)
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

    # 5) async RAG processing
    # Trigger the 4-stage processing pipeline as a background task:
    # extracting → chunking → embedding (Gemini gemini-embedding-001) → ready
    background_tasks.add_task(material_pipeline.run_pipeline, material.id)

    db.refresh(rubric)
    return rubric.id