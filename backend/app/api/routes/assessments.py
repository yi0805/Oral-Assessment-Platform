"""
Assessment configuration routes.

Endpoints
---------
POST   /courses/{course_id}/assessments           Create an assessment config (instructor only)
GET    /courses/{course_id}/assessments           List assessments for a course
GET    /assessments/{assessment_id}               Get full assessment config
PUT    /assessments/{assessment_id}               Update config (draft only, instructor only)
PUT    /assessments/{assessment_id}/publish       Publish the assessment (instructor only)
GET    /assessments/{assessment_id}/sessions      List all student sessions (instructor only)
"""
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor
from app.models.assessment import AssessmentConfig,AssessmentSession
from app.models.course import Course,CourseEnrollment
from app.models.question import QuestionPool, Question
from app.models.material import Material, MaterialChunk
from app.models.user import User
from app.schemas.pagination import Page
from app.schemas.assessment import (
    AssessmentConfigBrief,
    AssessmentConfigCreate,
    AssessmentConfigOut,
    AssessmentConfigUpdate,
)


from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()


@router.post(
    "/courses/{course_id}/assessments",
    response_model=AssessmentConfigOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create an assessment configuration",
    description=(
        "Instructor-only. The question pool must already be in 'approved' status. "
        "The instructor sets main_question_num and follow_up_num."
    ),
)
def create_assessment(
    course_id: UUID,
    payload: AssessmentConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    pool = db.query(QuestionPool).filter(QuestionPool.id == payload.question_pool_id).first()
    if not pool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question pool not found")
    if pool.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The question pool must be approved before creating an assessment.",
        )

    rubric = db.query(Material).filter(Material.id == payload.material_r_id).first()
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rubric not found")

    # Validate business rules
    if payload.total_time_minute < 10:
        raise HTTPException(
            status_code=422,
            detail="total_time_minutes must be at least 10 minutes"
        )

    if payload.open_at and payload.close_at and payload.close_at <= payload.open_at:
        raise HTTPException(
            status_code=422,
            detail="close_at must be after open_at"
    )

    # Guard: duplicate title within same course
    existing_config = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.course_id == course_id,
            AssessmentConfig.title == payload.title,
        )
        .first()
    )
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"An assessment titled '{payload.title}' already exists in this course "
                f"(id: {existing_config.id}, status: {existing_config.status}). "
                "Use a different title or manage the existing assessment."
            ),
        )

    config = AssessmentConfig(
        course_id=course_id,
        question_pool_id=payload.question_pool_id,
        title=payload.title,
        description=payload.description,
        material_r_id=payload.material_r_id,
        total_time_minute=payload.total_time_minute,
        # per_question_time_limit_minutes=payload.per_question_time_limit_minutes,
        main_question_num=payload.main_question_num,
        follow_up_num=payload.follow_up_num,
        release_time=payload.release_time,
        due_time=payload.due_time,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.get(
    "/courses/{course_id}/assessments",
    response_model=Page[AssessmentConfigBrief],
    summary="List assessments for a course",
    description="Returns brief summaries of all assessments in a course (paginated).",
)
def list_assessments(
    course_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    q = (
        db.query(AssessmentConfig)
        .filter(AssessmentConfig.course_id == course_id)
        .order_by(AssessmentConfig.created_at.desc())
    )
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return Page.create(items, total, page, page_size)


@router.get(
    "/assessments/{assessment_id}",
    response_model=AssessmentConfigOut,
    summary="Get assessment config details",
    description="Returns the full assessment configuration.",
)
def get_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == assessment_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return config


@router.put(
    "/assessments/{assessment_id}",
    response_model=AssessmentConfigOut,
    summary="Update an assessment config",
    description="Instructor-only. Only allowed while the assessment is in 'draft' status.",
)
def update_assessment(
    assessment_id: UUID,
    payload: AssessmentConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == assessment_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    if config.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot update a published or closed assessment.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return config


@router.put(
    "/assessments/{assessment_id}/publish",
    response_model=AssessmentConfigOut,
    summary="Publish an assessment",
    description=(
        "Instructor-only. Makes the assessment available to enrolled students. "
        "Validates that required fields (main_question_num, etc.) are set before publishing."
    ),
)
def publish_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == assessment_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    if config.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessment is already published or closed.",
        )

    if config.main_question_num is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="main_question_num must be set before publishing.",
        )
    if config.followup_enabled and config.max_followups_per_main is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="max_followups_per_main must be set when follow-ups are enabled.",
        )

    config.status = "published"
    config.published_at = datetime.now(timezone.utc)
    config.published_by = current_user.id
    db.commit()
    db.refresh(config)
    return config





# //integration


class ReleaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assessment_config: AssessmentConfigOut
    sessions_created: int

@router.post(
    "/courses/{course_id}/assessments/{assessment_config_id}/release",
    response_model=ReleaseResponse,
    summary="Integration",
)
def release_assessment(
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
        raise HTTPException(status_code=404, detail="Assessment not found")
    if config.status != "draft":
        raise HTTPException(status_code=409, detail="Assessment is already published or closed.")

    if config.main_question_num is None:
        raise HTTPException(status_code=422, detail="main_question_num must be set before publishing.")

    now = datetime.now(timezone.utc)
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
        existing_session = (
            db.query(AssessmentSession)
            .filter(
                AssessmentSession.assessment_config_id == assessment_config_id,
                AssessmentSession.user_s_id == enrollment.user_id,
            )
            .first()
        )
        if not existing_session:
            db.add(AssessmentSession(
                assessment_config_id=config.id,
                course_id=course_id,
                user_s_id=enrollment.user_id,
                status="not_started",
            ))
            sessions_created += 1

    try:
        db.commit()
        db.refresh(config)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to publish assessment.") from exc

    return ReleaseResponse(
        assessment_config=AssessmentConfigOut.model_validate(config),
        sessions_created=sessions_created,
    )
