"""
Course management routes.

Endpoints
---------
POST   /courses                                    Create a new course (instructor only)
GET    /courses                                    List courses the current user is enrolled in
GET    /courses/{course_id}                        Get course details (enrolled users only)
POST   /courses/{course_id}/enroll                 Enroll a user in a course (instructor only)
GET    /courses/{course_id}/students               List all enrolled users (instructor only)
POST   /courses/{course_id}/students/import-csv    Bulk-enroll students from a CSV file (instructor only)
"""
import csv
import io
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor
from app.models.course import Course, CourseEnrollment
from app.models.user import User
from app.schemas.course import (
    BulkEnrollResult,
    CourseBrief,
    CourseCreate,
    CourseOut,
    EnrollmentCreate,
    EnrollmentOut,
    StudentListItem,
)
from app.schemas.pagination import Page
from app.schemas.user import UserBrief

router = APIRouter()
logger = logging.getLogger(__name__)


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
    # Guard against duplicate courses created by accidental double-clicks.
    # A course is considered a duplicate if the same instructor already owns
    # a course with the same course_name AND term.
    existing = (
        db.query(Course)
        .filter(
            Course.course_name == payload.course_name,
            Course.term == payload.term,
            Course.created_by == current_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"You already have a course named '{payload.course_name}' "
                f"for term '{payload.term}' (id: {existing.id}). "
                "Use a different name or term, or manage the existing course."
            ),
        )

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
    response_model=Page[CourseBrief],
    summary="List my courses",
    description="Returns all courses the authenticated user is actively enrolled in (paginated).",
)
def list_courses(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Admins see every course; everyone else sees only their enrollments.
    if current_user.role == "admin":
        q = db.query(Course).order_by(Course.created_at.desc())
    else:
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
            return Page.create([], 0, page, page_size)
        q = db.query(Course).filter(Course.id.in_(course_ids)).order_by(Course.created_at.desc())

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return Page.create(items, total, page, page_size)


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
        if existing.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already enrolled in this course.",
            )
        # Re-enroll a previously de-enrolled user: reactivate the existing row
        existing.is_active = True
        existing.course_role = payload.course_role
        db.commit()
        db.refresh(existing)
        return existing

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
    response_model=Page[StudentListItem],
    summary="List enrolled users",
    description="Instructor-only. Lists all users enrolled in the course with their roles (paginated).",
)
def list_students(
    course_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    q = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.course_id == course_id)
        .order_by(CourseEnrollment.enrolled_at.asc())
    )
    total = q.count()
    enrollments = q.offset((page - 1) * page_size).limit(page_size).all()

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
    return Page.create(result, total, page, page_size)


@router.post(
    "/{course_id}/students/import-csv",
    response_model=BulkEnrollResult,
    status_code=status.HTTP_200_OK,
    summary="Bulk-enroll students from a CSV file",
    description=(
        "Instructor-only. Upload a CSV file with columns: email (required), "
        "full_name (optional), role (optional, default 'student'). "
        "Creates missing user accounts, then enrols each user in this course. "
        "Returns a summary of what was created/skipped plus any per-row errors."
    ),
)
def import_students_csv(
    course_id: UUID,
    file: UploadFile = File(..., description="CSV file with columns: email, full_name, role"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Read and parse the CSV bytes
    try:
        raw = file.file.read().decode("utf-8-sig")  # utf-8-sig strips BOM if present
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {exc}",
        ) from exc

    reader = csv.DictReader(io.StringIO(raw))
    if reader.fieldnames is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file appears to be empty or has no header row.",
        )

    # Normalize column names to lowercase with no extra whitespace
    fieldnames_lower = [f.strip().lower() for f in reader.fieldnames]
    if "email" not in fieldnames_lower:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV must contain an 'email' column.",
        )

    users_created = 0
    users_found = 0
    enrolled = 0
    already_enrolled = 0
    errors: list[dict] = []

    for row_no, raw_row in enumerate(reader, start=2):  # row 1 is the header
        # Normalize keys
        row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items()}

        email = row.get("email", "").lower()
        if not email:
            errors.append({"row": row_no, "error": "Missing email address"})
            continue

        full_name: str | None = row.get("full_name") or row.get("name") or None
        role_raw = (row.get("role") or "student").lower()
        course_role = role_raw if role_raw in ("student", "instructor") else "student"

        try:
            # Upsert user — find by email or create a stub account
            user = db.query(User).filter(User.email == email).first()
            if user:
                users_found += 1
            else:
                user = User(
                    email=email,
                    full_name=full_name or email.split("@")[0],
                    role="student",  # system-level role; can log in via Google OAuth later
                )
                db.add(user)
                db.flush()  # get user.id without committing yet
                users_created += 1
                logger.info("CSV import: created user %s", email)

            # Enroll in course
            existing_enrollment = (
                db.query(CourseEnrollment)
                .filter(
                    CourseEnrollment.course_id == course_id,
                    CourseEnrollment.user_id == user.id,
                )
                .first()
            )
            if existing_enrollment:
                already_enrolled += 1
                # Reactivate if previously de-enrolled
                if not existing_enrollment.is_active:
                    existing_enrollment.is_active = True
            else:
                enrollment = CourseEnrollment(
                    course_id=course_id,
                    user_id=user.id,
                    course_role=course_role,
                )
                db.add(enrollment)
                enrolled += 1

        except Exception as exc:  # noqa: BLE001
            db.rollback()
            errors.append({"row": row_no, "email": email, "error": str(exc)})
            logger.warning("CSV import: row %d (%s) failed: %s", row_no, email, exc)
            continue

    db.commit()
    logger.info(
        "CSV import for course %s: created=%d found=%d enrolled=%d already=%d errors=%d",
        course_id,
        users_created,
        users_found,
        enrolled,
        already_enrolled,
        len(errors),
    )

    return BulkEnrollResult(
        users_created=users_created,
        users_found=users_found,
        enrolled=enrolled,
        already_enrolled=already_enrolled,
        errors=errors,
    )
