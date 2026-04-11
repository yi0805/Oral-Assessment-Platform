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
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor
from app.models.assessment import AssessmentConfig
from app.models.course import Course, CourseEnrollment
from app.models.question import Question, QuestionPool
from app.models.user import User
from app.models.material import Material
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

from app.schemas import UpdateNowRequest


from pydantic import BaseModel, ConfigDict
from app.services.question_generator import generate_pool
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()

class QuestionUpdate(BaseModel):
    question_text: str | None = None


class UpdateNowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    assessment_config: AssessmentConfigOut
    pool_id: UUID
    questions: list[QuestionOut]


@router.post(
    "/courses/{course_id}/update-now",
    response_model=UpdateNowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate question pool from materials",

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
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor in this course.")

    rubric = db.query(Material).filter(Material.id == payload.material_r_id).first()

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
            ),
        )
    

    config = AssessmentConfig(
        course_id=course_id,
        title=payload.assessment_title,
        description=payload.description,
        material_r_id=payload.material_r_id,
        total_time_minute=payload.total_time_minutes,
        main_question_num=payload.num_main_questions,
        follow_up_num=payload.follow_up_num,
        status = "draft",
    )

    db.add(config)
    db.fresh(config)


    pool = QuestionPool(
        assessment_config_id = config.id,
        material_id = payload.material_id,
        status = "draft",
        )
    
    db.add(pool)
    db.flush(pool)
    
    try:
        pool = await generate_pool(
            db=db,
            pool_id=pool.id,
            material_ids=payload.material_id,
            rubric_id=payload.material_r_id,
            num_main_questions=payload.main_question_num,
        )

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    
    except RuntimeError as exc:

        raise HTTPException(status_code=502, detail=f"AI generation service error: {exc}") from exc


    try:
        db.commit()

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
        assessment_config=AssessmentConfigOut.model_validate(config),
        pool_id=pool.id,
        questions=[QuestionOut.model_validate(q) for q in questions],
    )


@router.delete(
    "/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Integration",

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
    return {"message": "Question deleted successfully."}



@router.put(
    "/questions/{question_id}",
    summary="Integration",

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
    return {"message": "Question updated successfully."}