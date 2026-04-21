import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_instructor
from app.services import material_pipeline, s3_client

from app.models import Course, CourseEnrollment, Material, User
from app.schemas import GithubImportBody

router = APIRouter()
logger = logging.getLogger(__name__)

MIME_MAP = {
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}


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
    _require_course_instructor(db, course_id, current_user)

    filename = file.filename or "unknown"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    # Check for existing material
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

    # Read file bytes 
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is empty.",
        )

    # Upload to storage
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

    # Save material record
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

    # Kick off background pipeline
    background_tasks.add_task(material_pipeline.run_pipeline, material.id)

    return material.id


# Import GitHub repo as material

# @router.post(
#     "/courses/{course_id}/materials/github",
#     status_code=status.HTTP_201_CREATED,
#     summary="Import GitHub Repo as Material",
# )
# async def import_github_repo(
#     course_id: UUID,
#     body: GithubImportBody,
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_instructor),
# ):
#     _require_course_instructor(db, course_id, current_user)

#     text_bytes, filename = function that returns text_bytes and filename

#     existing_material = (
#         db.query(Material)
#         .filter(
#             Material.course_id == course_id,
#             Material.filename == filename,
#         )
#         .first()
#     )

#     if existing_material:
#         return existing_material.id

#     material_id = uuid4()
#     storage_key = s3_client.generate_key(course_id, material_id, filename)
#     content_type = "text/plain"

#     try:
#         s3_client.upload_file(
#             text_bytes,
#             storage_key,
#             content_type=content_type,
#             metadata={
#                 "course_id": str(course_id),
#                 "material_id": str(material_id),
#                 "title": filename,
#                 "source": "github",
#                 "source_url": body.url,
#             },
#         )

#     except RuntimeError as exc:
#         raise HTTPException(
#             status_code=status.HTTP_502_BAD_GATEWAY,
#             detail=f"Storage upload failed: {exc}",
#         ) from exc

#     material = Material(
#         id=material_id,
#         course_id=course_id,
#         filename=filename,
#         mime_type=content_type,
#         storage_key=storage_key,
#         material_category="course_material",
#     )

#     try:
#         db.add(material)
#         db.commit()
#         db.refresh(material)

#     except SQLAlchemyError as exc:
#         db.rollback()
#         try:
#             s3_client.delete_file(storage_key)

#         except Exception:
#             logger.exception("Rollback cleanup failed for storage key=%s", storage_key)

#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Material metadata could not be saved.",
#         ) from exc

#     background_tasks.add_task(material_pipeline.run_pipeline, material.id)

#     return material.id