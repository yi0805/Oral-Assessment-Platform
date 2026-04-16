from uuid import UUID
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_instructor

from app.models import AssessmentConfig, AssessmentSession, CourseEnrollment, User, QuestionPool
from app.schemas import ReleaseResponse, AssessmentConfigInfoOut

router = APIRouter()


# Release assessment

@router.post(
    "/courses/{course_id}/assessments/{assessment_config_id}/release",
    response_model=ReleaseResponse,
    summary="Release an assessment to students",
)
def release_assessment(
    course_id: UUID,
    assessment_config_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    # Verify instructor enrollment 
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor for this course.")

    # Validate assessment config
    config = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.id == assessment_config_id,
            AssessmentConfig.course_id == course_id,
        )
        .first()
    )

    if not config:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if config.status != "draft":
        raise HTTPException(status_code=409, detail="Assessment is already published or closed.")

    if config.main_question_num is None:
        raise HTTPException(status_code=422, detail="main_question_num must be set before publishing.")

    # Validate question pool
    question_pool = (
        db.query(QuestionPool)
        .filter(QuestionPool.assessment_config_id == config.id)
        .first()
    )

    if not question_pool:
        raise HTTPException(status_code=422, detail="No question pool found for this assessment.")
    
    if question_pool.status != "draft":
        raise HTTPException(status_code=422, detail="Question pool was already published.")

    # Publish config and question pool
    question_pool.status = "published"

    now = datetime.now(timezone.utc)
    config.release_time = now
    config.due_time = now + timedelta(days=30)
    config.status = "published"

    # Create sessions for all enrolled students
    student_enrollments = (
        db.query(CourseEnrollment)
        .join(User, CourseEnrollment.user_id == User.id)
        .filter(
            CourseEnrollment.course_id == course_id,
            User.role == "student",
        )
        .all()
    )

    sessions_created = 0

    for enr in student_enrollments:
        db.add(AssessmentSession(
            assessment_config_id=config.id,
            user_s_id=enr.user_id,
            status="not_started",
        ))
        sessions_created += 1

    try:
        db.commit()
        
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to release assessment due to a server error.")

    return ReleaseResponse(sessions_created=sessions_created)


# Get assessment config

@router.get(
    "/courses/{course_id}/assessments/{assessment_config_id}",
    response_model=AssessmentConfigInfoOut,
    summary="Get assessment config details",
)
def get_assessment(
    course_id: UUID,
    assessment_config_id: UUID,
    db: Session = Depends(get_db),
):
    config = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.id == assessment_config_id,
            AssessmentConfig.course_id == course_id,
        )
        .first()
    )

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    return config


# Update assessment config

@router.put(
    "/courses/{course_id}/assessments/{assessment_config_id}",
    response_model=AssessmentConfigInfoOut,
    summary="Update an assessment config",
)
def update_assessment(
    course_id: UUID,
    assessment_config_id: UUID,
    payload: AssessmentConfigInfoOut,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    config = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.id == assessment_config_id,
            AssessmentConfig.course_id == course_id,
        )
        .first()
    )

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    if config.status != "draft":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot update a published assessment.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    try:
        db.commit()
        db.refresh(config)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database update failed")

    return config


# Delete assessment config

@router.delete(
    "/courses/{course_id}/assessments/{assessment_config_id}",
    summary="Delete an assessment config",
)
def delete_assessment(
    course_id: UUID,
    assessment_config_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    config = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.id == assessment_config_id,
            AssessmentConfig.course_id == course_id,
        )
        .first()
    )

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    if config.status != "draft":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete a published assessment.")

    try:
        db.delete(config)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database deletion failed")

    return {"message": "Assessment deleted successfully."}