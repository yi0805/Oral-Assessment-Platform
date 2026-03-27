"""
Question pool & question CRUD routes.

Endpoints
---------
POST   /courses/{course_id}/question-pools          Create an empty question pool
GET    /courses/{course_id}/question-pools          List all pools for a course
POST   /question-pools/{pool_id}/generate           Trigger AI question generation
GET    /question-pools/{pool_id}                    Get pool with all questions
PUT    /question-pools/{pool_id}/approve            Mark pool as approved
POST   /question-pools/{pool_id}/questions          Add a custom question
PUT    /questions/{question_id}                     Edit a question
DELETE /questions/{question_id}                     Remove a question
"""
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor
from app.models.course import Course
from app.models.question import Question, QuestionPool
from app.models.user import User
from app.schemas.question import (
    QuestionCreate,
    QuestionOut,
    QuestionPoolBrief,
    QuestionPoolCreate,
    QuestionPoolGenerateRequest,
    QuestionPoolOut,
    QuestionUpdate,
)

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
    response_model=list[QuestionPoolBrief],
    summary="List question pools",
    description="Returns all question pools for a course (brief view, no questions list).",
)
def list_question_pools(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    pools = (
        db.query(QuestionPool)
        .filter(QuestionPool.course_id == course_id)
        .order_by(QuestionPool.created_at.desc())
        .all()
    )
    return pools


@router.post(
    "/question-pools/{pool_id}/generate",
    response_model=QuestionPoolOut,
    summary="Trigger AI question generation",
    description=(
        "Instructor-only. Marks the pool for AI generation from the selected "
        "materials and rubric. The actual generation is handled by the AI service "
        "(question_generator.py integration point)."
    ),
)
def generate_questions(
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

    # Integration point: call question_generator.generate_pool(pool_id, payload.material_ids, payload.rubric_id)
    pool.generated_from_materials = [str(mid) for mid in payload.material_ids]
    pool.generation_method = "ai_generated"
    db.commit()
    db.refresh(pool)
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
    description="Instructor-only. Updates the text or metadata of an existing question.",
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

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return question


@router.delete(
    "/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question",
    description="Instructor-only. Permanently removes a question from its pool.",
)
def delete_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    db.delete(question)
    db.commit()
    return None
