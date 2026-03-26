"""
Course management routes.



Endpoints:
  POST /courses → create a new course (instructor only)
  GET /courses → list courses for current user
  GET /courses/:id → get course details
  POST /courses/:id/enroll → enroll user in course
  GET /courses/:id/students → list enrolled students

TODO:
- [ ] POST /courses with CourseCreate schema
- [ ] GET /courses filtered by current user's enrollments
- [ ] GET /courses/:id with enrollment check
- [ ] POST /courses/:id/enroll (instructor-only)
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.course import Course, CourseEnrollment
from app.models.user import User
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseOut, CourseBrief,
    EnrollmentCreate, EnrollmentOut, StudentListItem,
)
from app.schemas.user import UserBrief

router = APIRouter()


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    """Create a new course. Only instructors should call this."""
    # TODO: get current user from JWT and verify role == instructor
    course = Course(
        course_code=payload.course_code,
        course_name=payload.course_name,
        term=payload.term,
        description=payload.description,
        # created_by=current_user.id,  # TODO: uncomment when auth is wired
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("", response_model=list[CourseBrief])
def list_courses(db: Session = Depends(get_db)):
    """List all courses the current user is enrolled in."""
    # TODO: filter by current user's enrollments once auth is wired
    # For now, return all courses for development
    courses = db.query(Course).order_by(Course.created_at.desc()).all()
    return courses


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: UUID, db: Session = Depends(get_db)):
    """Get full details for a specific course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/{course_id}/enroll", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def enroll_user(course_id: UUID, payload: EnrollmentCreate, db: Session = Depends(get_db)):
    """Enroll a user in a course. Only instructors should call this."""
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify user exists
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check for duplicate enrollment
    existing = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course_id,
        CourseEnrollment.user_id == payload.user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already enrolled in this course")

    enrollment = CourseEnrollment(
        course_id=course_id,
        user_id=payload.user_id,
        course_role=payload.course_role,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.get("/{course_id}/students", response_model=list[StudentListItem])
def list_students(course_id: UUID, db: Session = Depends(get_db)):
    """List all students enrolled in a course."""
    enrollments = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.course_id == course_id)
        .all()
    )
    result = []
    for e in enrollments:
        user = db.query(User).filter(User.id == e.user_id).first()
        result.append(StudentListItem(
            enrollment_id=e.id,
            user=UserBrief.model_validate(user),
            course_role=e.course_role,
            is_active=e.is_active,
            enrolled_at=e.enrolled_at,
        ))
    return result

