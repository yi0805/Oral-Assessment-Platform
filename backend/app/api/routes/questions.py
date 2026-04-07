"""
Question pool & question CRUD routes.

Endpoints
---------
POST   /courses/{course_id}/question-pools                  Create an empty question pool
GET    /courses/{course_id}/question-pools                  List all pools for a course
POST   /question-pools/{pool_id}/generate                   Trigger AI question generation
GET    /question-pools/{pool_id}                            Get pool with all questions
PUT    /question-pools/{pool_id}/approve                    Mark pool as approved
POST   /question-pools/{pool_id}/publish-as-assessment      One-step: approve + create + publish assessment
POST   /question-pools/{pool_id}/questions                  Add a custom question
PUT    /questions/{question_id}                             Edit a question
DELETE /questions/{question_id}                             Remove a question
"""
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor
from app.models.assessment import AssessmentConfig
from app.models.course import Course, CourseEnrollment
from app.models.question import Question, QuestionPool
from app.models.user import User
from app.models.rubric import Rubric
from app.core.limiter import limiter
from app.core.config import settings
from app.schemas.assessment import AssessmentConfigOut
from app.schemas.pagination import Page
from app.schemas.question import (
    QuestionCreate,
    QuestionOut,
    QuestionPoolBrief,
    QuestionPoolCreate,
    QuestionPoolGenerateRequest,
    QuestionPoolOut,
    QuestionUpdate,
    PublishAsAssessmentRequest
)




from pydantic import BaseModel, ConfigDict
from app.services.question_generator import generate_pool
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()


@router.post(
    "/courses/{course_id}/question-pools",
    response_model=QuestionPoolOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a question pool",
    description="Instructor-only. Creates an empty pool for a course.",
)
def create_question_pool(
    course_id: UUID,
    payload: QuestionPoolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    existing_pool = (
        db.query(QuestionPool)
        .filter(QuestionPool.course_id == course_id, QuestionPool.title == payload.title)
        .first()
    )
    if existing_pool:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A question pool titled '{payload.title}' already exists in this course "
                f"(id: {existing_pool.id}, status: {existing_pool.status}). "
                "Use the existing pool or choose a different title."
            ),
        )

    pool = QuestionPool(
        course_id=course_id,
        title=payload.title,
        description=payload.description,
        generation_method=payload.generation_method,
        created_by=current_user.id,
    )
    db.add(pool)
    db.commit()
    db.refresh(pool)
    return pool


@router.get(
    "/courses/{course_id}/question-pools",
    response_model=Page[QuestionPoolBrief],
    summary="List question pools",
    description="Returns all question pools for a course (brief view, no questions list) (paginated).",
)
def list_question_pools(
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
        db.query(QuestionPool)
        .filter(QuestionPool.course_id == course_id)
        .order_by(QuestionPool.created_at.desc())
    )
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return Page.create(items, total, page, page_size)


@router.post(
    "/question-pools/{pool_id}/generate",
    response_model=QuestionPoolOut,
    summary="Trigger AI question generation",
    description=(
        "Instructor-only. Uses the AI Gateway (OpenRouter free + RAG search) to "
        "generate grounded main questions from the selected materials and rubric. "
        "Only main questions are generated; follow-up questions are dynamically "
        "produced during the student's session based on their answers. "
        "Replaces any previously generated questions in the pool."
    ),
)
@limiter.limit(f"{settings.rate_limit_ai}/minute")
async def generate_questions(
    request: Request,
    pool_id: UUID,
    payload: QuestionPoolGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    pool = db.query(QuestionPool).filter(QuestionPool.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question pool not found")
    if pool.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="AI generation can only be triggered for pools in 'draft' status.",
        )

    from app.services.question_generator import generate_pool

    try:
        pool = await generate_pool(
            db=db,
            pool_id=pool_id,
            material_ids=payload.material_ids,
            rubric_id=payload.rubric_id,
            num_main_questions=payload.num_main_questions or 3,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI generation service error: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        # Catch unexpected DB errors (e.g. vector dimension mismatch if migration 004
        # not applied) and return a readable 500 instead of plain-text "Internal Server Error".
        import logging as _logging
        _logging.getLogger(__name__).exception(
            "Unexpected error in generate_questions for pool %s", pool_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Question generation failed: {type(exc).__name__}: {exc}",
        ) from exc

    return pool


@router.get(
    "/question-pools/{pool_id}",
    response_model=QuestionPoolOut,
    summary="Get a question pool",
    description="Returns the pool with all its questions.",
)
def get_question_pool(
    pool_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pool = db.query(QuestionPool).filter(QuestionPool.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question pool not found")
    return pool


@router.put(
    "/question-pools/{pool_id}/approve",
    response_model=QuestionPoolOut,
    summary="Approve a question pool",
    description=(
        "Instructor-only. Marks the pool as approved, making it eligible for use "
        "in assessment configurations."
    ),
)
def approve_question_pool(
    pool_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    pool = db.query(QuestionPool).filter(QuestionPool.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question pool not found")

    if pool.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Question pool is already approved.",
        )

    pool.status = "approved"
    pool.approved_at = datetime.now(timezone.utc)
    pool.approved_by = current_user.id
    db.commit()
    db.refresh(pool)
    return pool


# ---------------------------------------------------------------------------
# Publish pool as assessment (one-step shortcut)
# ---------------------------------------------------------------------------

class _PublishAsAssessmentRequest(QuestionPoolCreate.__class__):
    """
    Inline payload — we define it directly here to avoid a circular import
    with schemas/assessment.py.  Only the fields needed to create + publish
    an assessment are exposed; everything else uses sensible defaults.
    """
    pass

@router.post(
    "/question-pools/{pool_id}/publish-as-assessment",
    response_model=AssessmentConfigOut,
    status_code=status.HTTP_201_CREATED,
    summary="One-step: approve pool → create assessment → publish",
    description=(
        "Instructor-only. Convenience endpoint that combines three steps into one: "
        "(1) marks the pool as approved if it is not already, "
        "(2) creates an AssessmentConfig linked to the pool and its course, "
        "(3) immediately publishes that config. "
        "Equivalent to PUT /approve + POST /assessments + PUT /publish."
    ),
)
def publish_pool_as_assessment(
    pool_id: UUID,
    payload: PublishAsAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    pool = db.query(QuestionPool).filter(QuestionPool.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question pool not found")
    if pool.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot publish an archived question pool as an assessment.",
        )

    # Guard: prevent creating a second assessment from the same pool.
    existing_assessment = (
        db.query(AssessmentConfig)
        .filter(AssessmentConfig.question_pool_id == pool_id)
        .first()
    )
    if existing_assessment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"An assessment already exists for this question pool "
                f"(assessment id: {existing_assessment.id}, "
                f"title: '{existing_assessment.title}', "
                f"status: {existing_assessment.status}). "
                "Manage the existing assessment instead of creating a duplicate."
            ),
        )
    
    rubric = db.query(Rubric).filter(Rubric.id == payload.rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rubric not found")
    
    # Validate business rules
    if payload.total_time_minutes < 10:
        raise HTTPException(
            status_code=422,
            detail="total_time_minutes must be at least 10 minutes"
        )

    if payload.open_at and payload.close_at and payload.close_at <= payload.open_at:
        raise HTTPException(
            status_code=422,
            detail="close_at must be after open_at"
    )

    # Step 1: Auto-approve the pool if it is still in draft
    if pool.status == "draft":
        pool.status = "approved"
        pool.approved_at = datetime.now(timezone.utc)
        pool.approved_by = current_user.id
        db.flush()

    # Step 2: Create the AssessmentConfig
    config = AssessmentConfig(
        course_id=pool.course_id,
        question_pool_id=pool.id,
        title=payload.title,
        instructions=payload.instructions,
        assessment_mode="generic",
        rubric_id=payload.rubric_id,
        total_time_minutes=payload.total_time_minutes,
        per_question_time_limit_minutes=payload.per_question_time_limit_minutes,
        max_main_questions=payload.max_main_questions,
        max_followups_per_main=payload.max_followups_per_main,
        followup_enabled=payload.followup_enabled,
        open_at=payload.open_at,
        close_at=payload.close_at,
    )
    db.add(config)
    db.flush()

    # Step 3: Publish immediately
    now = datetime.now(timezone.utc)
    config.status = "published"
    config.published_at = now
    config.published_by = current_user.id

    db.commit()
    db.refresh(config)
    return config


@router.post(
    "/question-pools/{pool_id}/questions",
    response_model=QuestionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a question to a pool",
    description="Instructor-only. Manually adds a question to the pool.",
)
def add_question(
    pool_id: UUID,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    pool = db.query(QuestionPool).filter(QuestionPool.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question pool not found")

    question = Question(
        question_pool_id=pool_id,
        parent_question_id=payload.parent_question_id,
        question_text=payload.question_text,
        question_kind=payload.question_kind,
        answer_style=payload.answer_style,
        difficulty=payload.difficulty,
        learning_objective=payload.learning_objective,
        display_order=payload.display_order,
        created_by=current_user.id,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.put(
    "/questions/{question_id}",
    response_model=QuestionOut,
    summary="Edit a question",
    description=(
        "Instructor-only. Updates the text or metadata of an existing question. "
        "Allowed on pools in 'draft', 'approved', or 'published' status — "
        "blocked only when the pool is 'archived'."
    ),
)
def update_question(
    question_id: UUID,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    pool = db.query(QuestionPool).filter(QuestionPool.id == question.question_pool_id).first()
    if pool and pool.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot modify questions in an archived question pool.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return question


@router.delete(
    "/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question",
    description=(
        "Instructor-only. Permanently removes a question from its pool. "
        "Blocked only when the pool is 'archived'."
    ),
)
def delete_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    pool = db.query(QuestionPool).filter(QuestionPool.id == question.question_pool_id).first()
    if pool and pool.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete questions from an archived question pool.",
        )

    db.delete(question)
    db.commit()
    return None



































































# integration

class UpdateNowRequest(BaseModel):
    material_ids: list[UUID]
    rubric_id: UUID
    assessment_title: str
    num_main_questions: int = 3
    total_time_minutes: int = 15
    max_followups_per_main: int = 3
    followup_enabled: bool = True


class UpdateNowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    assessment: AssessmentConfigOut
    pool_id: UUID
    questions: list[QuestionOut]


@router.post(
    "/courses/{course_id}/update-now",
    response_model=UpdateNowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Integration",

)
async def update_now(
    course_id: UUID,
    payload: UpdateNowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_role.in_(["instructor"]),
            CourseEnrollment.is_active.is_(True),
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor in this course.")

    rubric = db.query(Rubric).filter(Rubric.id == payload.rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    published = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.course_id == course_id,
            AssessmentConfig.title == payload.assessment_title,
            AssessmentConfig.status == "published",
        )
        .first()
    )
    if published:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A published assessment titled '{payload.assessment_title}' already exists "
                f"(id: {published.id}). Delete or close it first."
            ),
        )


    pool = QuestionPool(
        course_id=course_id,
        title=payload.assessment_title,
        generation_method="ai_generated",
        created_by=current_user.id,
        )
    db.add(pool)
    db.flush()
    
    try:
        pool = await generate_pool(
            db=db,
            pool_id=pool.id,
            material_ids=payload.material_ids,
            rubric_id=payload.rubric_id,
            num_main_questions=payload.num_main_questions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=f"AI generation service error: {exc}") from exc

    now = datetime.now(timezone.utc)
    pool.status = "approved"
    pool.approved_at = now
    pool.approved_by = current_user.id
    db.flush()

    config = AssessmentConfig(
        course_id=course_id,
        question_pool_id=pool.id,
        title=payload.assessment_title,
        assessment_mode="generic",
        rubric_id=payload.rubric_id,
        total_time_minutes=payload.total_time_minutes,
        max_main_questions=payload.num_main_questions,
        max_followups_per_main=payload.max_followups_per_main,
        followup_enabled=payload.followup_enabled,
    )
    db.add(config)

    try:
        db.commit()
        db.refresh(config)
        db.refresh(pool)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save assessment.") from exc

    questions = (
        db.query(Question)
        .filter(Question.question_pool_id == pool.id, Question.is_active.is_(True))
        .order_by(Question.display_order.asc())
        .all()
    )

    return UpdateNowResponse(
        assessment=AssessmentConfigOut.model_validate(config),
        pool_id=pool.id,
        questions=[QuestionOut.model_validate(q) for q in questions],
    )


