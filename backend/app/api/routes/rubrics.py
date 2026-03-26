"""Rubric management routes."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.rubric import Rubric
from app.models.course import Course
from app.schemas.rubric import RubricCreate, RubricUpdate, RubricOut, RubricBrief

router = APIRouter()


@router.post(
    "/courses/{course_id}/rubrics",
    response_model=RubricOut,
    status_code=status.HTTP_201_CREATED,
)
def create_rubric(course_id: UUID, payload: RubricCreate, db: Session = Depends(get_db)):
    """Create a new rubric for a course. The rubric_text is fed to the AI as prompt context."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    rubric = Rubric(
        course_id=course_id,
        title=payload.title,
        description=payload.description,
        rubric_text=payload.rubric_text,
        original_filename=payload.original_filename,
        # created_by=current_user.id,  # TODO: wire auth
        created_by=UUID("a0000000-0000-0000-0000-000000000001"),  # Temp: seed instructor
    )
    db.add(rubric)
    db.commit()
    db.refresh(rubric)
    return rubric


@router.get("/courses/{course_id}/rubrics", response_model=list[RubricBrief])
def list_rubrics(course_id: UUID, db: Session = Depends(get_db)):
    """List all rubrics for a course."""
    rubrics = (
        db.query(Rubric)
        .filter(Rubric.course_id == course_id)
        .order_by(Rubric.created_at.desc())
        .all()
    )
    return rubrics


@router.get("/rubrics/{rubric_id}", response_model=RubricOut)
def get_rubric(rubric_id: UUID, db: Session = Depends(get_db)):
    """Get full rubric details including the rubric_text content."""
    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return rubric


@router.put("/rubrics/{rubric_id}", response_model=RubricOut)
def update_rubric(rubric_id: UUID, payload: RubricUpdate, db: Session = Depends(get_db)):
    """Update rubric title, description, or content."""
    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rubric, field, value)

    db.commit()
    db.refresh(rubric)
    return rubric


