import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_instructor

from app.services import s3_client, material_pipeline
from app.models import Course, CourseEnrollment, Material, User, Rubric, AssessmentConfig
from app.schemas import RubricCreate, RubricOut

router = APIRouter()
logger = logging.getLogger(__name__)

MIME_MAP = {
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}


# Upload rubric

@router.post(
    "/courses/{course_id}/rubrics/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload a rubric",
)
async def upload_rubric(
    course_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    # Validate course and instructor 
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an instructor in this course.",
        )

    # Check for existing rubric 
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
                "material_category": "rubric",
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

    #  Kick off background pipeline 
    background_tasks.add_task(material_pipeline.run_pipeline, material.id)

    return material.id

# Create rubric via form (criteria, rating, points)

@router.post(
    "/courses/{course_id}/rubric",
    response_model=RubricOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a grading rubric for an assessment",
)
def create_rubric(
    course_id: UUID,
    payload: RubricCreate,
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
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an instructor in this course.",
        )
    
    # rubric_id = uuid4()

    # Check total points
    submitted_total = sum(item.max_points for item in payload.criteria_data)
    if submitted_total != payload.total_points:
        raise HTTPException(
            status_code=400, 
            detail=f"Total points mismatch. Expected {payload.total_points}, got {submitted_total}"
        )

    rubric = Rubric(
        # id=rubric_id
        course_id=course_id,
        total_points=payload.total_points,
        criteria_data=[item.model_dump() for item in payload.criteria_data]
    )

    db.add(rubric)

    try:        
        db.commit()
        db.refresh(rubric)
    except Exception as e:
        db.rollback()
        logger.error(f"Update failed: {e}")
        raise HTTPException(status_code=500, detail="Could not save rubric to database")
    
    return rubric

# Retrieve rubric
@router.get(
    "/assessments/{assessment_config_id}/rubric",
    response_model=RubricOut,
    summary="Get rubric details",
)
def get_rubric(
    assessment_config_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):

    rubric = (
            db.query(Rubric)
            .join(AssessmentConfig)
            .filter(
                Rubric.assessment_config_id == assessment_config_id,
            )
            .first()
        )

    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rubric not found")

    return rubric

# Update rubric
@router.put(
    "/assessments/{assessment_config_id}/rubric",
    response_model=RubricOut,
    summary="Update a rubric",
)
def update_rubric(
    assessment_config_id: UUID,
    payload: RubricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
   
    rubric = (
            db.query(Rubric)
            .join(AssessmentConfig)
            .filter(
                Rubric.assessment_config_id == assessment_config_id,
            )
            .first()
        )
   
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rubric not found")

    update_rubric = payload.model_dump(exclude_unset=True)
    for field, value in update_rubric.items():
        setattr(rubric, field, value)

    try:
        db.commit()
        db.refresh(rubric)
    except Exception as e:
        db.rollback()
        logger.error(f"Update failed: {e}")
        raise HTTPException(status_code=500, detail="Database update failed")

    return rubric