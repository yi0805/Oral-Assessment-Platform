from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.dependencies import require_instructor
from app.services.question_generator import generate_pool

from app.models import AssessmentConfig, Course, CourseEnrollment, Question, QuestionPool, User, Material
from app.schemas import UpdateNowRequest, QuestionUpdate, QuestionOut, UpdateNowResponse

router = APIRouter()

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
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor in this course.")

    rubric = db.query(Material).filter(
        Material.id == payload.material_r_id,
        Material.material_category == "rubric",
    ).first()

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
        follow_up_num=payload.max_followups_per_main,
        status="draft",
    )

    db.add(config)
    db.flush()


    pool = QuestionPool(
        assessment_config_id=config.id,
        material_id=payload.material_id,
        status="draft",
    )
    
    db.add(pool)
    db.flush()
    
    try:
        pool = await generate_pool(
            db=db,
            pool_id=pool.id,
            material_id=payload.material_id,
            rubric_id=payload.material_r_id,
            num_main_questions=payload.num_main_questions,
            course_id=course_id,
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
        .filter(Question.question_pool_id == pool.id)
        .order_by(Question.question_index.asc())
        .all()
    )

    return UpdateNowResponse(
        assessment_config=config.id,
        questions=[QuestionOut.model_validate(q) for q in questions],
    )


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
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    db.delete(question)
    db.commit()
    return {"message": "Question deleted successfully."}



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
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")


    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return {"message": "Question updated successfully."}
