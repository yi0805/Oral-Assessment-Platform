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
from app.core.dependencies import require_instructor


from app.models import Course, CourseEnrollment, Material, User

router = APIRouter()
logger = logging.getLogger(__name__)

MIME_MAP = {
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}



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


    existing_rubric = (
        db.query(Material)
        .filter(
                Material.course_id == course_id,
                Material.filename == filename,
                Material.material_category == "rubric",
        )
        .first()
    )

    if existing_rubric:
        return existing_rubric.id

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
                "material_category": "rubric",
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
        material_category="rubric",
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

    return material.id