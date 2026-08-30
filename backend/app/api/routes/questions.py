import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.dependencies import require_instructor
from app.core.limiter import limiter
from app.services.question_generator import QuestionGenerationError, generate_pool

from app.models import AssessmentConfig, Course, CourseEnrollment, Question, QuestionPool, User, Material, MaterialChunk, Rubric
from app.schemas import (
    QuestionGenerationRequest,
    QuestionCreate,
    QuestionUpdate,
    QuestionOut,
    QuestionGenerationResponse, QuestionSupportingContextOut,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# Generate question pool

@router.post(
    "/courses/{course_id}/generate-question",
    response_model=QuestionGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate question pool from material and rubric",
)
@limiter.limit("5/minute")
async def generate_question(
    request: Request,
    course_id: UUID,
    payload: QuestionGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    # Validate course and instructor
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor in this course.")

    # Validate rubric and material 
    rubric = (
        db.query(Rubric)
        .filter(
            Rubric.id == payload.rubric_id,
            Rubric.course_id == course_id,
        )
        .first()
    )

    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    

    unique_material_ids = list(dict.fromkeys(payload.material_ids))

    materials = (
        db.query(Material)
        .filter(
            Material.id.in_(unique_material_ids),
            Material.course_id == course_id,
            Material.material_category == "course_material",
            Material.processing_status == "ready",
        )
        .all()
    )

    if len(materials) != len(unique_material_ids):
        raise HTTPException(
            status_code=409,
            detail="Selected materials are unavailable, belong to another course, or are not ready.",
        )

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
            detail=f"A published assessment titled '{payload.assessment_title}' already exists",
        )

    # Create assessment config and question pool
    now = datetime.now(timezone.utc)
    release_time = payload.release_time or now
    due_time = payload.due_time or (release_time + timedelta(days=30))

    config = AssessmentConfig(
        course_id=course_id,
        title=payload.assessment_title,
        rubric_id=payload.rubric_id,
        total_time_minute=payload.total_time_minutes,
        buffer_time_minute=payload.buffer_time_minutes,
        main_question_num=payload.num_main_questions,
        follow_up_num=payload.max_followups_per_main,
        status="draft",
        release_time=release_time,
        due_time=due_time,
    )

    db.add(config)
    db.flush()

    pool = QuestionPool(
        assessment_config_id=config.id,
        status="draft",
    )

    db.add(pool)
    db.flush()

    pool.materials = materials

    #  Run AI generation
    try:
        pool = await generate_pool(
            db=db,
            pool_id=pool.id,
            material_ids=unique_material_ids,
            rubric_id=payload.rubric_id,
            num_main_questions=payload.num_main_questions,
            config_id=config.id,
        )

    except QuestionGenerationError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail="Question generation request is invalid.") from exc
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Question generation service is currently unavailable.",
        ) from exc

    try:
        db.commit()
        
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save assessment.") from exc

    #  Return generated questions 
    questions = (
        db.query(Question)
        .filter(Question.question_pool_id == pool.id)
        .order_by(Question.question_index.asc())
        .all()
    )

    return QuestionGenerationResponse(
        assessment_config=config.id,
        questions=[QuestionOut.model_validate(q) for q in questions],
    )


@router.get(
    "/questions/{question_id}/supporting-context",
    response_model=QuestionSupportingContextOut,
    summary="View supporting context used for AI question generation",
)
def get_question_supporting_context(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    question, config = _get_question_with_config_or_403(db, question_id, current_user)
    provenance = question.generation_provenance
    if not provenance:
        raise HTTPException(
            status_code=404,
            detail="Supporting context is unavailable for this manually created question.",
        )

    try:
        source_material_ids = [UUID(value) for value in provenance.get("source_material_ids", [])]
        source_chunk_ids = [UUID(value) for value in provenance.get("source_chunk_ids", [])]
    except (TypeError, ValueError) as exc:
        logger.warning("Question %s has invalid provenance", question.id)
        raise HTTPException(status_code=404, detail="Supporting context is unavailable.") from exc

    rows = (
        db.query(Material, MaterialChunk)
        .join(MaterialChunk, MaterialChunk.material_id == Material.id)
        .filter(
            Material.course_id == config.course_id,
            Material.id.in_(source_material_ids),
            MaterialChunk.id.in_(source_chunk_ids),
        )
        .order_by(Material.filename, MaterialChunk.chunk_index)
        .all()
    )
    contexts = [
        {
            "material_id": material.id,
            "material_filename": material.filename,
            "chunk_id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "text": chunk.chunk_text,
        }
        for material, chunk in rows
    ]
    return QuestionSupportingContextOut(
        source_material_ids=source_material_ids,
        source_chunk_ids=source_chunk_ids,
        model=provenance.get("model"),
        generated_at=provenance.get("generated_at"),
        prompt_version=provenance.get("prompt_version"),
        contexts=contexts,
    )


def _get_question_with_config_or_403(
    db: Session,
    question_id: UUID,
    current_user: User,
) -> tuple[Question, AssessmentConfig]:
    row = (
        db.query(Question, AssessmentConfig)
        .join(QuestionPool, QuestionPool.id == Question.question_pool_id)
        .join(AssessmentConfig, AssessmentConfig.id == QuestionPool.assessment_config_id)
        .filter(Question.id == question_id)
        .first()
    )

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    question, config = row

    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == config.course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor for this course.")

    return question, config


def _require_draft_assessment(config: AssessmentConfig) -> None:
    if config.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This assessment is {config.status} — questions cannot be modified.",
        )


def _get_assessment_for_instructor(
    db: Session,
    assessment_config_id: UUID,
    current_user: User,
) -> AssessmentConfig:
    config = (
        db.query(AssessmentConfig)
        .filter(AssessmentConfig.id == assessment_config_id)
        .first()
    )

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == config.course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor for this course.")

    return config


# List questions

@router.get(
    "/assessments/{assessment_config_id}/questions",
    response_model=list[QuestionOut],
    summary="List all questions in an assessment's pool",
)
def list_questions(
    assessment_config_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    config = _get_assessment_for_instructor(db, assessment_config_id, current_user)

    if not config.question_pool:
        return []

    questions = (
        db.query(Question)
        .filter(Question.question_pool_id == config.question_pool.id)
        .order_by(Question.question_index.asc())
        .all()
    )

    return questions


# Add question

@router.post(
    "/assessments/{assessment_config_id}/questions",
    response_model=QuestionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a single question to a draft assessment's pool",
)
def add_question(
    assessment_config_id: UUID,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    config = _get_assessment_for_instructor(db, assessment_config_id, current_user)

    _require_draft_assessment(config)

    if not config.question_pool:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No question pool found for this assessment.",
        )

    pool_id = config.question_pool.id

    max_index = (
        db.query(Question.question_index)
        .filter(Question.question_pool_id == pool_id)
        .order_by(Question.question_index.desc())
        .first()
    )

    next_index = (max_index[0] + 1) if max_index else 1

    question = Question(
        question_pool_id=pool_id,
        question_text=payload.question_text,
        question_index=next_index,
    )

    db.add(question)

    try:
        db.commit()
        db.refresh(question)

    except SQLAlchemyError as exc:
        db.rollback()
        
        raise HTTPException(status_code=500, detail="Could not save question.") from exc

    return question


# Delete question

@router.delete(
    "/questions/{question_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a question",
)
def delete_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    question, config = _get_question_with_config_or_403(db, question_id, current_user)
    _require_draft_assessment(config)

    pool_count = (
        db.query(Question)
        .filter(Question.question_pool_id == question.question_pool_id)
        .count()
    )

    if pool_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An assessment must have at least one question.",
        )

    if pool_count - 1 < config.main_question_num:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Lower the assessment's question count first "
                f"(currently requires {config.main_question_num})."
            ),
        )

    db.delete(question)
    db.commit()

    return {"message": "Question deleted successfully."}


# Update question

@router.put(
    "/questions/{question_id}",
    summary="Update a question",
)
def update_question(
    question_id: UUID,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    question, config = _get_question_with_config_or_403(db, question_id, current_user)
    _require_draft_assessment(config)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)

    return {"message": "Question updated successfully."}
