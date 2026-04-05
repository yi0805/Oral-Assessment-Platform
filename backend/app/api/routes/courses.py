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
from sqlalchemy import and_


from app.models.feedback import AISummary, InstructorFeedback
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor
from app.models.course import Course, CourseEnrollment
from app.models.user import User
from app.models.assessment import AssessmentConfig, AssessmentSession
from app.schemas.course import (
    BulkEnrollResult,
    CourseBrief,
    CourseOut,
    EnrollmentCreate,
    EnrollmentOut,
    StudentListItem,
    
)
from app.schemas.pagination import Page
from app.schemas.user import UserBrief

from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict
from typing import List

router = APIRouter()
logger = logging.getLogger(__name__)


# @router.post(
#     "",
#     response_model=CourseOut,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new course",
#     description="Instructor-only. Creates a course and records the creator.",
# )
# def create_course(
#     payload: CourseCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_instructor),
# ):
#     # Guard against duplicate courses created by accidental double-clicks.
#     # A course is considered a duplicate if the same instructor already owns
#     # a course with the same course_name AND term.
#     existing = (
#         db.query(Course)
#         .filter(
#             Course.course_name == payload.course_name,
#             Course.term == payload.term,
#             Course.created_by == current_user.id,
#         )
#         .first()
#     )
#     if existing:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail=(
#                 f"You already have a course named '{payload.course_name}' "
#                 f"for term '{payload.term}' (id: {existing.id}). "
#                 "Use a different name or term, or manage the existing course."
#             ),
#         )

#     course = Course(
#         course_code=payload.course_code,
#         course_name=payload.course_name,
#         term=payload.term,
#         description=payload.description,
#         created_by=current_user.id,
#     )
#     db.add(course)
#     db.flush()

#     # Auto-enroll the creator as instructor so they can manage it immediately.
#     enrollment = CourseEnrollment(
#         course_id=course.id,
#         user_id=current_user.id,
#         course_role="instructor",
#     )
#     db.add(enrollment)
#     db.commit()
#     db.refresh(course)
#     return course


# @router.get(
#     "",
#     response_model=Page[CourseBrief],
#     summary="List my courses",
#     description="Returns all courses the authenticated user is actively enrolled in (paginated).",
# )
# def list_courses(
#     page: int = Query(1, ge=1, description="Page number (1-based)"),
#     page_size: int = Query(20, ge=1, le=100, description="Items per page"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     # Admins see every course; everyone else sees only their enrollments.
#     if current_user.role == "admin":
#         q = db.query(Course).order_by(Course.created_at.desc())
#     else:
#         enrollments = (
#             db.query(CourseEnrollment)
#             .filter(
#                 CourseEnrollment.user_id == current_user.id,
#                 CourseEnrollment.is_active.is_(True),
#             )
#             .all()
#         )
#         course_ids = [e.course_id for e in enrollments]
#         if not course_ids:
#             return Page.create([], 0, page, page_size)
#         q = db.query(Course).filter(Course.id.in_(course_ids)).order_by(Course.created_at.desc())

#     total = q.count()
#     items = q.offset((page - 1) * page_size).limit(page_size).all()
#     return Page.create(items, total, page, page_size)


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



# Integration


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_code: str | None
    course_name: str | None
    term: str | None
    description: str | None
    created_by: UUID | None
    created_at: datetime | None
    updated_at: datetime | None

class CourseCreate(BaseModel):
    course_code: str 
    course_name: str
    description: str | None = None

class InstructorDashboardStudentRow(BaseModel):
    session_id: UUID
    student_id: UUID
    student_name: str
    student_email: str
    student_image: str | None = None
    ai_suggested_score: int | None = None
    ai_summary: str | None = None
    final_grade: int | None = None
    status: str


class InstructorDashboardAssessmentOut(BaseModel):
    course_code: str
    course_name: str
    assessment_config_id: UUID
    assessment_title: str
    published_average_score: float | None = None
    ai_average_score: float | None = None
    submitted_count: int
    total_students: int
    students: list[InstructorDashboardStudentRow]

def generate_term() -> str:
    now = datetime.now()
    year_short = str(now.year)[-2:]
    semester = "S1" if now.month <= 6 else "S2"
    return f"{year_short}{semester}"

def dashboard_status(session_status: str) -> str:
    if session_status == "released":
        return "published"
    if session_status == "under_review" or session_status == "submitted" or session_status == "time_expired":
        return "review"
    return "inprogress"

@router.get(
    "",
    response_model=list[CourseOut],
    summary="Integration",
)
def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    courses = (
        db.query(Course)
        .join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
        .filter(CourseEnrollment.user_id == current_user.id)
        .filter(CourseEnrollment.is_active == True)
        .order_by(Course.course_code)
        .distinct()
        .all()
    )
    return courses


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Integration",
)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    term = generate_term()

    existing = (
        db.query(Course)
        .filter(
            Course.course_code == payload.course_code,
            Course.created_by == current_user.id,
            Course.term == term,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"You already have a course with code '{payload.course_code}' "
                f"for term '{term}' (id: {existing.id}). "
                "Use a different course code."
            ),
        )

    course = Course(
        course_code=payload.course_code,
        course_name=payload.course_name,
        term=term,
        description=payload.description,
        created_by=current_user.id,
    )

    db.add(course)
    db.flush()

    enrollment = CourseEnrollment(
        course_id=course.id,
        user_id=current_user.id,
        course_role="instructor",
    )
    db.add(enrollment)

    db.commit()

    return {"message": f"Course '{payload.course_name}' created successfully with term '{term}'."}



@router.get(
    "/{course_id}/instructor/dashboard",
    response_model=list[InstructorDashboardAssessmentOut],
    summary="Integration",
)
def get_instructor_dashboard(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )


    total_students = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.course_role == "student",
            CourseEnrollment.is_active.is_(True),
        )
        .count()
    )

    rows = (
        db.query(
            AssessmentSession,
            AssessmentConfig,
            User,
            AISummary,
            InstructorFeedback,
            
        )
        .join(
            AssessmentConfig,
            AssessmentConfig.id == AssessmentSession.assessment_config_id,
        )
        .join(
            User,
            User.id == AssessmentSession.student_id,
        )
        .outerjoin(
            AISummary,
            AISummary.session_id == AssessmentSession.id,
        )
        .outerjoin(
            InstructorFeedback,
            and_(
                InstructorFeedback.session_id == AssessmentSession.id,
                InstructorFeedback.instructor_id == current_user.id,
            ),
        )
        .filter(
            AssessmentSession.course_id == course_id,
            AssessmentConfig.course_id == course_id,
        )
        .order_by(AssessmentConfig.created_at.asc(), User.full_name.asc())
        .all()
    )

    print(f"Total assessment sessions found: {len(rows)}")


    assessment_configs = (
        db.query(AssessmentConfig)
        .filter(AssessmentConfig.course_id == course_id)
        .order_by(AssessmentConfig.created_at.asc())
        .all()
    )

    grouped = {}

    for assessment_config in assessment_configs:
        grouped[str(assessment_config.id)] = {
            "course_code": course.course_code,
            "course_name": course.course_name,
            "assessment_config_id": assessment_config.id,
            "assessment_title": assessment_config.title,
            "published_scores": [],
            "ai_scores": [],
            "submitted_count": 0,
            "students": [],
        }
    print(f"Total assessment configs found: {len(assessment_configs)}")
    print(f"Initial grouped dict keys (assessment config IDs): {list(grouped.keys())}")

    for session, assessment_config, student, ai_summary, instructor_feedback in rows:
        group = grouped[str(assessment_config.id)]

        if session.status in {"submitted", "under_review", "released", "time_expired"}:
            group["submitted_count"] += 1

        if ai_summary and ai_summary.suggested_grade is not None:
            group["ai_scores"].append(ai_summary.suggested_grade)

        if (
            instructor_feedback
            and instructor_feedback.released_to_student is True
            and instructor_feedback.final_grade is not None
        ):
            group["published_scores"].append(instructor_feedback.final_grade)

        final_grade = (
            instructor_feedback.final_grade
            if instructor_feedback and instructor_feedback.final_grade is not None
            else None
        )

        student_row = InstructorDashboardStudentRow(
            session_id=session.id,
            student_id=student.id,
            student_name=student.full_name,
            student_email=student.email,
            student_image=student.image,
            ai_suggested_score=(
                ai_summary.suggested_grade
                if ai_summary and ai_summary.suggested_grade is not None
                else None
            ),
            ai_summary=(
                ai_summary.summary_text
                if ai_summary and ai_summary.summary_text
                else None
            ),
            final_grade=final_grade,
            status=dashboard_status(session.status),
        )

        group["students"].append(student_row)

    print(grouped)

    response = []

    for group in grouped.values():
        published_scores = group["published_scores"]
        ai_scores = group["ai_scores"]
        student_rows = group["students"]

        published_average_score = (
            round(sum(published_scores) / len(published_scores), 2)
            if published_scores
            else None
        )

        ai_average_score = (
            round(sum(ai_scores) / len(ai_scores), 2)
            if ai_scores
            else None
        )


        response.append(
            InstructorDashboardAssessmentOut(
                course_code=group["course_code"],
                course_name=group["course_name"],
                assessment_config_id=group["assessment_config_id"],
                assessment_title=group["assessment_title"],
                published_average_score=published_average_score,
                ai_average_score=ai_average_score,
                submitted_count=group["submitted_count"],
                total_students=total_students,
                students=student_rows,
            )
        )

    return response