"""
Course management routes.

Endpoints
---------
POST   /courses                        Create a new course (instructor only)
GET    /courses                        List courses the current user is enrolled in
GET    /courses/{course_id}            Get course details (enrolled users only)
POST   /courses/{course_id}/enroll     Enroll a user in a course (instructor only)
GET    /courses/{course_id}/students   List all enrolled users (instructor only)
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor
from app.models.course import Course, CourseEnrollment
from app.models.user import User
from app.schemas.course import (
    CourseCreate,
    CourseOut,
    CourseBrief,
    EnrollmentCreate,
    EnrollmentOut,
    StudentListItem,
)
from app.schemas.user import UserBrief

router = APIRouter()


@router.post(
    "",
    response_model=CourseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course",
    description="Instructor-only. Creates a course and records the creator.",
)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = Course(
        course_code=payload.course_code,
        course_name=payload.course_name,
        term=payload.term,
        description=payload.description,
        created_by=current_user.id,
    )
    db.add(course)
    db.flush()

    # Auto-enroll the creator as instructor so they can manage it immediately.
    enrollment = CourseEnrollment(
        course_id=course.id,
        user_id=current_user.id,
        course_role="instructor",
    )
    db.add(enrollment)
    db.commit()
    db.refresh(course)
    return course


@router.get(
    "",
    response_model=list[CourseBrief],
    summary="List my courses",
    description="Returns all courses the authenticated user is actively enrolled in.",
)
def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Admins see every course; everyone else sees only their enrollments.
    if current_user.role == "admin":
        courses = db.query(Course).order_by(Course.created_at.desc()).all()
        return courses

    enrollments = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.is_active.is_(True),
        )
        .all()
    )
    course_ids = [e.course_id for e in enrollments]
    if not course_ids:
        return []

    courses = (
        db.query(Course)
        .filter(Course.id.in_(course_ids))
        .order_by(Course.created_at.desc())
        .all()
    )
    return courses


@router.get(
    "/{course_id}",
    response_model=CourseOut,
    summary="Get course details",
    description="Returns full course details. Requires active enrollment or admin role.",
)
def get_course(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Enforce enrollment check (admins bypass).
    if current_user.role != "admin":
        enrolled = (
            db.query(CourseEnrollment)
            .filter(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.user_id == current_user.id,
                CourseEnrollment.is_active.is_(True),
            )
            .first()
        )
        if not enrolled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this course.",
            )

    return course


@router.post(
    "/{course_id}/enroll",
    response_model=EnrollmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll a user in a course",
    description="Instructor-only. Enrols any existing user in this course with the given role.",
)
def enroll_user(
    course_id: UUID,
    payload: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == payload.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already enrolled in this course.",
        )

    enrollment = CourseEnrollment(
        course_id=course_id,
        user_id=payload.user_id,
        course_role=payload.course_role,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.get(
    "/{course_id}/students",
    response_model=list[StudentListItem],
    summary="List enrolled users",
    description="Instructor-only. Lists all users enrolled in the course with their roles.",
)
def list_students(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    enrollments = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.course_id == course_id)
        .order_by(CourseEnrollment.enrolled_at.asc())
        .all()
    )

    result = []
    for e in enrollments:
        user = db.query(User).filter(User.id == e.user_id).first()
        if user:
            result.append(
                StudentListItem(
                    enrollment_id=e.id,
                    user=UserBrief.model_validate(user),
                    course_role=e.course_role,
                    is_active=e.is_active,
                    enrolled_at=e.enrolled_at,
                )
            )
    return result
