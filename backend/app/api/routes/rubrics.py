"""
Rubric management routes.

Endpoints
---------
POST   /courses/{course_id}/rubrics   Create a rubric (instructor only)
GET    /courses/{course_id}/rubrics   List all rubrics for a course
GET    /rubrics/{rubric_id}           Get full rubric including rubric_text
PUT    /rubrics/{rubric_id}           Update rubric content (instructor only)
DELETE /rubrics/{rubric_id}           Delete a rubric (instructor only)
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor
from app.models.course import Course
from app.models.rubric import Rubric
from app.models.user import User
from app.schemas.rubric import RubricBrief, RubricCreate, RubricOut, RubricUpdate

router = APIRouter()


@router.post(
    "/courses/{course_id}/rubrics",
    response_model=RubricOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a rubric",
    description=(
        "Instructor-only. The `rubric_text` is passed as context to the AI "
        "for question generation and session summarisation."
    ),
)
def create_rubric(
    course_id: UUID,
    payload: RubricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    rubric = Rubric(
        course_id=course_id,
        title=payload.title,
        description=payload.description,
        rubric_text=payload.rubric_text,
        original_filename=payload.original_filename,
        created_by=current_user.id,
    )
    db.add(rubric)
    db.commit()
    db.refresh(rubric)
    return rubric


@router.get(
    "/courses/{course_id}/rubrics",
    response_model=list[RubricBrief],
    summary="List course rubrics",
    description="Returns all rubrics for a course (title + metadata, no rubric_text).",
)
def list_rubrics(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    rubrics = (
        db.query(Rubric)
        .filter(Rubric.course_id == course_id)
        .order_by(Rubric.created_at.desc())
        .all()
    )
    return rubrics


@router.get(
    "/rubrics/{rubric_id}",
    response_model=RubricOut,
    summary="Get rubric details",
    description="Returns the full rubric including rubric_text content.",
)
def get_rubric(
    rubric_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rubric not found")
    return rubric


@router.put(
    "/rubrics/{rubric_id}",
    response_model=RubricOut,
    summary="Update a rubric",
    description="Instructor-only. Updates title, description, or rubric_text.",
)
def update_rubric(
    rubric_id: UUID,
    payload: RubricUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rubric not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rubric, field, value)

    db.commit()
    db.refresh(rubric)
    return rubric


@router.delete(
    "/rubrics/{rubric_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a rubric",
    description="Instructor-only. Permanently removes the rubric.",
)
def delete_rubric(
    rubric_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rubric not found")

    db.delete(rubric)
    db.commit()
    return None
