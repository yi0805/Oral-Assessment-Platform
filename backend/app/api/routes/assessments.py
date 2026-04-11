from uuid import UUID
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_instructor

from app.models import AssessmentConfig, AssessmentSession, CourseEnrollment, User, QuestionPool
from app.schemas import ReleaseResponse

from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()


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
    
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_role == "instructor",
        )
        .first()
)

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor for this course.")

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
    
    question_pool = db.query(QuestionPool).filter(QuestionPool.assessment_config_id == config.id).first()
    question_pool.status = "published"

    now = datetime.now(timezone.utc)

    config.release_time = now
    config.due_time = now + timedelta(days=30) 
    config.status = "published"


    student_enrollments = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.course_role == "student",
        )
        .all()
    )

    sessions_created = 0

    for enrollment in student_enrollments:
        db.add(AssessmentSession(
            assessment_config_id=config.id,
            course_id=course_id,
            user_s_id=enrollment.user_id,
            status="not_started",
        ))
        sessions_created += 1

    try:
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to publish assessment.") from exc

    return {"sessions_created": sessions_created}
