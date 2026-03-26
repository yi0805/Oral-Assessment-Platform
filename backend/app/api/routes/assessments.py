"""
Assessment configuration routes.

Endpoints:
  POST /courses/:id/assessments → create assessment config
  GET /courses/:id/assessments → list assessments for course
  PUT /assessments/:id → update config
  PUT /assessments/:id/publish → publish assessment
  GET /assessments/:id/sessions → list all student sessions

- CRUD for assessment configs (including v5 fields)
- Publish workflow with validation (pool approved? rubric set? open/close dates?)
"""
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.assessment import AssessmentConfig
from app.models.question import QuestionPool
from app.models.course import Course
from app.schemas.assessment import (
    AssessmentConfigCreate, AssessmentConfigUpdate, AssessmentConfigOut, AssessmentConfigBrief,
)

router = APIRouter()


@router.post(
    "/courses/{course_id}/assessments",
    response_model=AssessmentConfigOut,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment(course_id: UUID, payload: AssessmentConfigCreate, db: Session = Depends(get_db)):
    """
    Create a new assessment configuration.
    The instructor must specify max_main_questions and max_followups_per_main
    (no hardcoded defaults — per the user flow, these are instructor-defined).
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify the question pool exists and is approved
    pool = db.query(QuestionPool).filter(QuestionPool.id == payload.question_pool_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Question pool not found")
    if pool.status != "approved":
        raise HTTPException(status_code=409, detail="Question pool must be approved before creating an assessment")

    config = AssessmentConfig(
        course_id=course_id,
        question_pool_id=payload.question_pool_id,
        title=payload.title,
        instructions=payload.instructions,
        assessment_mode=payload.assessment_mode,
        rubric_id=payload.rubric_id,
        total_time_minutes=payload.total_time_minutes,
        per_question_time_limit_seconds=payload.per_question_time_limit_seconds,
        max_main_questions=payload.max_main_questions,
        max_followups_per_main=payload.max_followups_per_main,
        followup_enabled=payload.followup_enabled,
        open_at=payload.open_at,
        close_at=payload.close_at,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.get("/courses/{course_id}/assessments", response_model=list[AssessmentConfigBrief])
def list_assessments(course_id: UUID, db: Session = Depends(get_db)):
    """List all assessments for a course."""
    configs = (
        db.query(AssessmentConfig)
        .filter(AssessmentConfig.course_id == course_id)
        .order_by(AssessmentConfig.created_at.desc())
        .all()
    )
    return configs


@router.get("/assessments/{assessment_id}", response_model=AssessmentConfigOut)
def get_assessment(assessment_id: UUID, db: Session = Depends(get_db)):
    """Get full assessment configuration details."""
    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == assessment_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return config


@router.put("/assessments/{assessment_id}", response_model=AssessmentConfigOut)
def update_assessment(assessment_id: UUID, payload: AssessmentConfigUpdate, db: Session = Depends(get_db)):
    """Update assessment settings. Only allowed while status is 'draft'."""
    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == assessment_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if config.status != "draft":
        raise HTTPException(status_code=409, detail="Cannot update a published assessment")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return config


@router.put("/assessments/{assessment_id}/publish", response_model=AssessmentConfigOut)
def publish_assessment(assessment_id: UUID, db: Session = Depends(get_db)):
    """
    Publish an assessment — makes it available to students.
    Validates that all required fields are set before publishing.
    """
    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == assessment_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if config.status != "draft":
        raise HTTPException(status_code=409, detail="Assessment is already published or closed")

    # Validate required fields before publishing
    if config.max_main_questions is None:
        raise HTTPException(status_code=422, detail="max_main_questions must be set before publishing")
    if config.max_followups_per_main is None and config.followup_enabled:
        raise HTTPException(status_code=422, detail="max_followups_per_main must be set when follow-ups are enabled")

    config.status = "published"
    config.published_at = datetime.now(timezone.utc)
    # config.published_by = current_user.id  # TODO: wire auth
    db.commit()
    db.refresh(config)
    return config

