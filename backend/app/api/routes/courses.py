from uuid import UUID
from io import StringIO
from datetime import datetime, timezone
import csv
from charset_normalizer import from_bytes
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor

from app.models import Course, CourseEnrollment, AISummary, SessionFeedback, User, AssessmentConfig, AssessmentSession
from app.schemas import CourseOut, CourseCreate, InstructorDashboardStudentRow, InstructorDashboardAssessmentOut, Userupi, UserRole

router = APIRouter()


# Helpers

def generate_term() -> str:
    now = datetime.now()
    year_short = str(now.year)[-2:]
    semester = "S1" if now.month <= 6 else "S2"
    return f"{year_short}{semester}"


def dashboard_status(session_status: str, due_time: datetime) -> str:
    if session_status == "released":
        return "published"
    if session_status == "under_review":
        return "review"
    now = datetime.now(timezone.utc)
    if now > due_time:
        return "overdue"
    return "inprogress"

# Add student/instructor individually
@router.post(
    "/{course_id}/enroluser",
    status_code=status.HTTP_200_OK,
    summary="Individually add users (student or instructor to course)",
)
def enrol_user(
    course_id: UUID,
    payload: Userupi,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    caller_enrolment = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course_id,
        CourseEnrollment.user_id == current_user.id
    ).first()

    if not caller_enrolment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an instructor of this course.",
        )

    role = (payload.role or UserRole.student.value).strip().lower()

    if role not in {UserRole.student.value, UserRole.instructor.value}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role must be 'student' or 'instructor'.",
        )

    new_user = db.query(User).filter(User.upi == payload.upi).first()
    if new_user:
        existing = db.query(CourseEnrollment).filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == new_user.id
        ).first()

        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already enrolled")

        if role == UserRole.instructor.value and new_user.role != UserRole.instructor.value:
            new_user.role = UserRole.instructor.value

        db.add(CourseEnrollment(course_id=course_id, user_id=new_user.id, upi=payload.upi))

    else:
        existing = db.query(CourseEnrollment).filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.upi == payload.upi
        ).first()

        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already enrolled")
        
        db.add(CourseEnrollment(course_id=course_id, upi=payload.upi))

    db.commit()

    return {"message": "Enrolled successfully."}


# Import students via CSV

@router.post(
    "/{course_id}/students/import-csv",
    status_code=status.HTTP_200_OK,
    summary="Bulk-enroll students from a CSV file",
)
def import_students_csv(
    course_id: UUID,
    file: UploadFile = File(..., description="CSV file with a single 'UPI' column."),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    owns = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )
    if not owns:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an instructor of this course.",
        )

    raw_bytes = file.file.read()

    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        result = from_bytes(raw_bytes).best()

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to detect file encoding. Please save the CSV as UTF-8.",
            )
        
        raw = str(result)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {exc}",
        ) from exc

    try:
        df = pd.read_csv(StringIO(raw))

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse CSV: {exc}",
        ) from exc
    
    df.columns = df.columns.str.strip().str.upper()

    if "UPI" not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is missing 'UPI' column.",
        )

    existing_upis = {
        upi for (upi,) in db.query(CourseEnrollment.upi)
        .filter(CourseEnrollment.course_id == course_id)
        .all()
    }

    newly_enrolled = 0
    for upi in df["UPI"].dropna().astype(str).str.strip():
        if not upi or upi in existing_upis:
            continue
        db.add(CourseEnrollment(course_id=course_id, upi=upi))
        existing_upis.add(upi)
        newly_enrolled += 1

    db.commit()

    return {"newly_enrolled": newly_enrolled}


# List courses

@router.get(
    "",
    response_model=list[CourseOut],
    summary="List courses the current user is enrolled in",
)
def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    term = generate_term()

    courses = (
        db.query(Course)
        .join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
        .filter(CourseEnrollment.user_id == current_user.id)
        .filter(Course.term == term)
        .order_by(Course.course_code)
        .all()
    )

    return courses


# Create course

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course",
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
            ),
        )

    course = Course(
        course_code=payload.course_code,
        course_name=payload.course_name,
        term=term,
        description=payload.description,
    )

    db.add(course)
    db.flush()

    enrollment = CourseEnrollment(
        course_id=course.id,
        user_id=current_user.id,
        upi=current_user.upi,
    )
    db.add(enrollment)
    db.commit()

    return {"message": f"Course '{payload.course_name}' created successfully with term '{term}'."}


# Instructor dashboard

@router.get(
    "/{course_id}/instructor/dashboard",
    response_model=list[InstructorDashboardAssessmentOut],
    summary="Get Students in a course",
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
        .join(User, CourseEnrollment.user_id == User.id)
        .filter(
            CourseEnrollment.course_id == course_id,
            User.role == "student",
        )
        .count()
    )

    rows = (
        db.query(
            AssessmentSession,
            AssessmentConfig,
            User,
            AISummary,
            SessionFeedback,
        )
        .join(AssessmentConfig, AssessmentConfig.id == AssessmentSession.assessment_config_id)
        .join(User, User.id == AssessmentSession.user_s_id)
        .outerjoin(AISummary, AISummary.session_id == AssessmentSession.id)
        .outerjoin(SessionFeedback, SessionFeedback.session_id == AssessmentSession.id)
        .filter(AssessmentConfig.course_id == course_id)
        .filter(AssessmentConfig.status == "published")
        .order_by(User.full_name.asc())
        .all()
    )

    assessment_configs = (
        db.query(AssessmentConfig)
        .filter(AssessmentConfig.course_id == course_id)
        .filter(AssessmentConfig.status == "published")
        .order_by(AssessmentConfig.release_time.asc())
        .all()
    )

    # Build grouped structure keyed by assessment config id
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

    for session, assessment_config, student, ai_summary, instructor_feedback in rows:
        group = grouped[str(assessment_config.id)]

        if session.status in {"under_review", "released"}:
            group["submitted_count"] += 1

        if ai_summary and ai_summary.suggested_grade is not None:
            group["ai_scores"].append(ai_summary.suggested_grade)

        if (
            instructor_feedback
            and instructor_feedback.status == "published"
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
            status=dashboard_status(session.status, assessment_config.due_time),
        )

        group["students"].append(student_row)

    # Assemble response
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


# Export published results as CSV

@router.get(
    "/{course_id}/assessments/{assessment_config_id}/export-results",
    summary="Export published assessment results as CSV",
)
def export_results_csv(
    course_id: UUID,
    assessment_config_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    owns = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )
    if not owns:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an instructor of this course.",
        )

    assessment_config = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.id == assessment_config_id,
            AssessmentConfig.course_id == course_id,
        )
        .first()
    )
    if not assessment_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found for this course.",
        )

    rows = (
        db.query(User.upi, SessionFeedback.comments, SessionFeedback.final_grade, AISummary.suggested_grade)
        .select_from(User)
        .join(AssessmentSession, AssessmentSession.user_s_id == User.id)
        .join(SessionFeedback, SessionFeedback.session_id == AssessmentSession.id)
        .join(AISummary, AISummary.session_id == AssessmentSession.id)
        .filter(
            AssessmentSession.assessment_config_id == assessment_config_id,
            AssessmentSession.status == "released",
            SessionFeedback.status == "published",
        )
        .order_by(User.upi)
        .all()
    )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["UPI", "Comments", "Final_Grade", "AI_grade"])

    for upi, comments, final_grade, AI_grade in rows:
        writer.writerow([upi, comments or "", final_grade, AI_grade])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=results_{assessment_config.title.replace(' ', '_')}.csv"
        },
    )

# Unenrol user from the course
@router.delete(
    "/{course_id}/delete-enrolment",
    summary="Delete student enrolment"
)
def delete_enrolment(
    course_id: UUID,
    payload: Userupi,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor)
):
    caller_enrolment = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course_id,
        CourseEnrollment.user_id == current_user.id
    ).first()

    if not caller_enrolment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an instructor of this course.",
        )

    target_enrolment = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course_id,
        CourseEnrollment.upi == payload.upi,
    ).first()

    if not target_enrolment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User enrolment not found")
    
    if target_enrolment.user_id == current_user.id:
      raise HTTPException(409, detail="Cannot remove your own enrolment.")

    try:
        db.delete(target_enrolment)
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database deletion failed")

    return {"message": "Enrolment deleted successfully."}