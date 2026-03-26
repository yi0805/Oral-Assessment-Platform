"""
Question pool & question CRUD routes.

Owner: Bess (storage) + Joanne (AI generation)
Endpoints:
  POST /courses/:id/question-pools → create a new pool
  POST /question-pools/:id/generate → trigger AI question generation
  GET /question-pools/:id → get pool with all questions
  PUT /question-pools/:id/approve → mark pool as approved
  POST /question-pools/:id/questions → add custom question
  PUT /questions/:id → edit a question
  DELETE /questions/:id → remove question

TODO:
- CRUD endpoints for pools and questions
- Integration point with Joanne's AI generation service
"""
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.question import QuestionPool, Question
from app.models.course import Course
from app.schemas.question import (
    QuestionPoolCreate, QuestionPoolGenerateRequest, QuestionPoolOut, QuestionPoolBrief,
    QuestionCreate, QuestionUpdate, QuestionOut,
)

router = APIRouter()


@router.post(
    "/courses/{course_id}/question-pools",
    response_model=QuestionPoolOut,
    status_code=status.HTTP_201_CREATED,
)
def create_question_pool(course_id: UUID, payload: QuestionPoolCreate, db: Session = Depends(get_db)):
    """Create a new empty question pool for a course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    pool = QuestionPool(
        course_id=course_id,
        title=payload.title,
        description=payload.description,
        generation_method=payload.generation_method,
        # created_by=current_user.id,  # TODO: wire auth
        created_by=UUID("a0000000-0000-0000-0000-000000000001"),
    )
    db.add(pool)
    db.commit()
    db.refresh(pool)
    return pool


@router.post("/question-pools/{pool_id}/generate", response_model=QuestionPoolOut)
def generate_questions(pool_id: UUID, payload: QuestionPoolGenerateRequest, db: Session = Depends(get_db)):
    """
    Trigger AI question generation from selected materials and rubric.
    This calls Joanne's question_generator service, which:
    1. Retrieves relevant chunks via RAG search
    2. Feeds chunks + rubric_text to the LLM
    3. Saves generated questions to this pool
    """
    pool = db.query(QuestionPool).filter(QuestionPool.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Question pool not found")
    if pool.status != "draft":
        raise HTTPException(status_code=409, detail="Can only generate questions for draft pools")

    # TODO: Call question_generator.generate_pool(pool_id, payload.material_ids, payload.rubric_id)
    # This is the integration point with Joanne's AI service

    pool.generated_from_materials = [str(mid) for mid in payload.material_ids]
    pool.generation_method = "ai_generated"
    db.commit()
    db.refresh(pool)
    return pool


@router.get("/question-pools/{pool_id}", response_model=QuestionPoolOut)
def get_question_pool(pool_id: UUID, db: Session = Depends(get_db)):
    """Get a question pool with all its questions."""
    pool = db.query(QuestionPool).filter(QuestionPool.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Question pool not found")
    return pool


@router.put("/question-pools/{pool_id}/approve", response_model=QuestionPoolOut)
def approve_question_pool(pool_id: UUID, db: Session = Depends(get_db)):
    """Mark a question pool as approved. Only approved pools can be used in assessments."""
    pool = db.query(QuestionPool).filter(QuestionPool.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Question pool not found")

    pool.status = "approved"
    pool.approved_at = datetime.now(timezone.utc)
    # pool.approved_by = current_user.id  # TODO: wire auth
    db.commit()
    db.refresh(pool)
    return pool


@router.post(
    "/question-pools/{pool_id}/questions",
    response_model=QuestionOut,
    status_code=status.HTTP_201_CREATED,
)
def add_question(pool_id: UUID, payload: QuestionCreate, db: Session = Depends(get_db)):
    """Add a custom question to a pool. The instructor reviews, edits, deletes, or adds questions."""
    pool = db.query(QuestionPool).filter(QuestionPool.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Question pool not found")

    question = Question(
        question_pool_id=pool_id,
        parent_question_id=payload.parent_question_id,
        question_text=payload.question_text,
        question_kind=payload.question_kind,
        answer_style=payload.answer_style,
        difficulty=payload.difficulty,
        learning_objective=payload.learning_objective,
        display_order=payload.display_order,
        # created_by=current_user.id,  # TODO: wire auth
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.put("/questions/{question_id}", response_model=QuestionOut)
def update_question(question_id: UUID, payload: QuestionUpdate, db: Session = Depends(get_db)):
    """Edit an existing question in the pool."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return question


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: UUID, db: Session = Depends(get_db)):
    """Remove a question from the pool."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    db.delete(question)
    db.commit()
    return None
