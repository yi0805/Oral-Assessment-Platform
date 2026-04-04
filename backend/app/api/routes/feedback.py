"""
AI summary & instructor feedback routes.

Endpoints
---------
POST  /sessions/{session_id}/ai-summary/generate   Trigger AI summary generation
GET   /sessions/{session_id}/ai-summary            Get the AI summary
POST  /sessions/{session_id}/ai-summary/accept     Accept AI grade + release in one step (NEW)
POST  /sessions/{session_id}/feedback              Instructor submits grade + comments
PUT   /sessions/{session_id}/feedback              Instructor revises feedback
PUT   /sessions/{session_id}/release               Release results to student
GET   /sessions/{session_id}/results               Student views released results

Workflow
--------
  student submits session
      ↓
  POST /ai-summary/generate  (instructor triggers or auto-triggered)
      ↓
  GET  /ai-summary           (instructor reviews AI advisory analysis)
      ↓
  POST /feedback             (instructor writes final grade + comments)
      ↓
  PUT  /release              (instructor releases to student)
      ↓
  GET  /results              (student views grade + feedback + transcript)
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor, require_student
from app.models.assessment import AssessmentSession
from app.models.feedback import AISummary, InstructorFeedback
from app.models.session_runtime import TranscriptMessage
from app.models.user import User
from app.schemas.assessment import TranscriptMessageOut
from app.schemas.feedback import (
    AISummaryOut,  # still used by generate_ai_summary and get_ai_summary endpoints
    FeedbackCreate,
    FeedbackOut,
    FeedbackUpdate,
    StudentResultsOut,
)

from pydantic import BaseModel, Field

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper:
# ---------------------------------------------------------------------------

def _get_session_or_404(db: Session, session_id: UUID, student_id: UUID) -> AssessmentSession:
    sess = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).filter(AssessmentSession.student_id == student_id).first()
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return sess

def format_for_student(ai_summary: AISummary, final_grade: int) -> str:
    parts = []

    if ai_summary.summary_text:
        parts.append("Overall feedback:")
        parts.append(ai_summary.summary_text.strip())

    if ai_summary.strengths:
        parts.append("\nStrengths:")
        parts.append(ai_summary.strengths.strip())

    if ai_summary.gaps:
        parts.append("\nAreas for improvement:")
        parts.append(ai_summary.gaps.strip())

    parts.append(f"\nFinal grade: {final_grade}")

    return "\n".join(parts)

def format_for_instructor(ai_summary: AISummary) -> str | None:
    if not ai_summary.summary_text:
        return None

    parts = []

    parts.append("AI Summary:")
    parts.append(ai_summary.summary_text.strip())

    if ai_summary.strengths:
        parts.append("\nStrengths:")
        parts.append(ai_summary.strengths.strip())

    if ai_summary.gaps:
        parts.append("\nGaps:")
        parts.append(ai_summary.gaps.strip())

    return "\n".join(parts)

# ---------------------------------------------------------------------------
# AI Summary
# ---------------------------------------------------------------------------

@router.post(
    "/sessions/{session_id}/ai-summary/generate",
    response_model=AISummaryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI advisory summary",
    description=(
        "Instructor-only. Triggers the AI service to produce an advisory analysis "
        "of the student's transcript against the rubric. Idempotent — calling again "
        "replaces any existing summary for this session. "
        "Transitions the session status to 'under_review'."
    ),
)
async def generate_ai_summary(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    sess = _get_session_or_404(db, session_id)

    if sess.status not in ("submitted", "under_review"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"AI summary can only be generated for submitted sessions "
                f"(current status: {sess.status})."
            ),
        )

    from app.services.ai_summary_service import generate_summary

    try:
        summary = await generate_summary(db=db, session_id=session_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return summary


@router.get(
    "/sessions/{session_id}/ai-summary",
    response_model=AISummaryOut,
    summary="Get AI advisory summary",
    description=(
        "Instructor-only. Returns the AI-generated advisory analysis for a session. "
        "404 if the summary has not yet been generated."
    ),
)
def get_ai_summary(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    _get_session_or_404(db, session_id)

    summary = db.query(AISummary).filter(AISummary.session_id == session_id).first()
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI summary not yet generated. Call POST /ai-summary/generate first.",
        )
    return summary


# ---------------------------------------------------------------------------
# Instructor Feedback
# ---------------------------------------------------------------------------

@router.post(
    "/sessions/{session_id}/feedback",
    response_model=FeedbackOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit instructor feedback",
    description=(
        "Instructor-only. Creates the official feedback record with grade and comments. "
        "Only one feedback record is allowed per session — use PUT to revise."
    ),
)
def create_feedback(
    session_id: UUID,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    sess = _get_session_or_404(db, session_id)

    if sess.status not in ("under_review", "submitted"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Feedback cannot be added to a session with status '{sess.status}'.",
        )

    existing = db.query(InstructorFeedback).filter(
        InstructorFeedback.session_id == session_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback already exists for this session. Use PUT to update.",
        )

    feedback = InstructorFeedback(
        session_id=session_id,
        instructor_id=current_user.id,
        comments=payload.comments,
        grading_rationale=payload.grading_rationale,
        provisional_grade=payload.provisional_grade,
        final_grade=payload.final_grade,
        student_visible_comments=payload.student_visible_comments,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.put(
    "/sessions/{session_id}/feedback",
    response_model=FeedbackOut,
    summary="Update instructor feedback",
    description=(
        "Instructor-only. Revises the existing feedback record. "
        "Not allowed after the feedback has been released to the student."
    ),
)
def update_feedback(
    session_id: UUID,
    payload: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    _get_session_or_404(db, session_id)

    feedback = db.query(InstructorFeedback).filter(
        InstructorFeedback.session_id == session_id
    ).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No feedback found for this session. Use POST to create it first.",
        )

    if feedback.released_to_student:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback has already been released to the student and cannot be modified.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(feedback, field, value)

    db.commit()
    db.refresh(feedback)
    return feedback


# ---------------------------------------------------------------------------
# Accept AI suggestion and release in one step
# ---------------------------------------------------------------------------

@router.post(
    "/sessions/{session_id}/ai-summary/accept",
    response_model=FeedbackOut,
    status_code=status.HTTP_201_CREATED,
    summary="Accept AI grade and release to student in one step",
    description=(
        "Instructor-only. Convenience endpoint: if the instructor is satisfied with the "
        "AI-generated advisory grade and summary, they can accept it in a single call. "
        "This will: (1) create an InstructorFeedback record using the AI suggested_grade "
        "as final_grade, (2) use the AI summary as the student-visible feedback, and (3) "
        "immediately release the results to the student. "
        "Requires an AI summary to have been generated first "
        "(POST /sessions/{id}/ai-summary/generate). "
        "Equivalent to POST /feedback + PUT /release in one request."
    ),
)
def accept_ai_and_release(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    sess = _get_session_or_404(db, session_id)

    if sess.status not in ("under_review", "submitted"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot accept AI grade for session with status '{sess.status}'. "
                "Session must be in 'under_review', or 'submitted' state."
            ),
        )

    # Require an AI summary to exist
    ai_summary = db.query(AISummary).filter(AISummary.session_id == session_id).first()
    if not ai_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No AI summary found for this session. "
                "Call POST /sessions/{id}/ai-summary/generate first."
            ),
        )
    if ai_summary.status != "success" or ai_summary.suggested_grade is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "AI summary did not produce a valid suggested grade. "
                "Please review the transcript manually and use POST /feedback instead."
            ),
        )

    existing = db.query(InstructorFeedback).filter(
        InstructorFeedback.session_id == session_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback already exists for this session. Use PUT /feedback to update.",
        )

    # Use AI suggested grade as the final grade
    final_grade = ai_summary.suggested_grade
    student_visible_comments = format_for_student(ai_summary, final_grade)
    grading_rationale = format_for_instructor(ai_summary)

    now = datetime.now(timezone.utc)
    feedback = InstructorFeedback(
        session_id=session_id,
        instructor_id=current_user.id,
        comments=f"[AI grade accepted by {current_user.full_name or current_user.email}]",
        grading_rationale=grading_rationale,
        provisional_grade=ai_summary.suggested_grade,
        final_grade=final_grade,
        student_visible_comments=student_visible_comments,
        released_to_student=True,
        released_at=now,
    )
    db.add(feedback)

    sess.status = "released"
    sess.released_at = now

    db.commit()
    db.refresh(feedback)
    return feedback


# ---------------------------------------------------------------------------
# Release workflow
# ---------------------------------------------------------------------------

# @router.put(
#     "/sessions/{session_id}/release",
#     response_model=FeedbackOut,
#     summary="Release results to student",
#     description=(
#         "Instructor-only. Marks the feedback as released, making it visible to the "
#         "student via GET /sessions/{id}/results. Transitions the session to 'released'. "
#         "Requires: final_grade must be set and student_visible_comments must not be empty."
#     ),
# )
# def release_results(
#     session_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_instructor),
# ):
#     sess = _get_session_or_404(db, session_id)

#     feedback = db.query(InstructorFeedback).filter(
#         InstructorFeedback.session_id == session_id
#     ).first()
#     if not feedback:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="No feedback found. Submit instructor feedback before releasing.",
#         )

#     if feedback.released_to_student:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="Results have already been released to this student.",
#         )

#     if not feedback.final_grade:
#         raise HTTPException(
#             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#             detail="final_grade must be set before releasing results to the student.",
#         )

#     now = datetime.now(timezone.utc)
#     feedback.released_to_student = True
#     feedback.released_at = now

#     sess.status = "released"
#     sess.released_at = now

#     db.commit()
#     db.refresh(feedback)
#     return feedback


# ---------------------------------------------------------------------------
# Student results view
# ---------------------------------------------------------------------------

@router.get(
    "/sessions/{session_id}/results",
    response_model=StudentResultsOut,
    summary="Student views released results",
    description=(
        "Student-only. Returns the final grade, instructor feedback, AI summary, "
        "and the full transcript — but only after the instructor has released them. "
        "Returns HTTP 403 if results have not been released yet."
    ),
)
def get_student_results(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    sess = _get_session_or_404(db, session_id)

    # Ownership check — students can only view their own sessions
    if sess.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session.",
        )

    feedback = db.query(InstructorFeedback).filter(
        InstructorFeedback.session_id == session_id
    ).first()

    if not feedback or not feedback.released_to_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your results have not been released yet. Please check back later.",
        )

    # NOTE: AI summary is intentionally NOT fetched or returned here.
    # Per user flow Phase 6, students only see: final grade, instructor feedback,
    # and the full transcript. The AI summary is an instructor-only advisory tool.

    transcript = (
        db.query(TranscriptMessage)
        .filter(TranscriptMessage.session_id == session_id)
        .order_by(TranscriptMessage.sequence_no.asc())
        .all()
    )

    return StudentResultsOut(
        session_id=session_id,
        final_grade=feedback.final_grade,
        student_visible_comments=feedback.student_visible_comments,
        released_at=feedback.released_at,
        transcript_messages=[TranscriptMessageOut.model_validate(m) for m in transcript],
    )



# Integration

class ReleaseReview(BaseModel):
    session_id: UUID
    student_id: UUID

class ReleaseAllReviews(BaseModel):
    assessments: list[ReleaseReview]

class GradeUpdate(BaseModel):
    grade: int = Field(ge=0, le=100)

def _release_one_result(
    db: Session,
    session_id: UUID,
    student_id: UUID,
):
    sess = _get_session_or_404(db, session_id, student_id)

    feedback = db.query(InstructorFeedback).filter(
        InstructorFeedback.session_id == session_id
    ).first()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No feedback found. Submit instructor feedback before releasing.",
        )

    if feedback.released_to_student:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Results have already been released to this student.",
        )

    if feedback.final_grade is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="final_grade must be set before releasing results to the student.",
        )

    now = datetime.now(timezone.utc)
    feedback.released_to_student = True
    feedback.released_at = now

    sess.status = "released"
    sess.released_at = now


@router.put(
    "/sessions/{session_id}/{student_id}/release/session",
    summary="Integration",
)
def release_result(
    session_id: UUID,
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    _release_one_result(db, session_id, student_id)

    db.commit()
    

    return {"message": f"Results released to student {student_id} for session {session_id}."}


@router.put(
    "/sessions/release/allSessions",
    summary="Integration",
)
def release_all_results(
    payload: ReleaseAllReviews,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    if not payload.assessments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No sessions provided.",
        )

    for assessment in payload.assessments:
        _release_one_result(
            db=db,
            session_id=assessment.session_id,
            student_id=assessment.student_id,
        )

    db.commit()
    return {
        "message": "All results released successfully"
    }




@router.put(
    "/sessions/{session_id}/grade",
    summary="Integration",
)
def update_grade(
    session_id: UUID,
    payload: GradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    feedback = db.query(InstructorFeedback).filter(
        InstructorFeedback.session_id == session_id
    ).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No feedback found. Submit instructor feedback updating the grade.",
        )

    if feedback.released_to_student:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Results have already been released to this student.",
        )

    feedback.final_grade = payload.grade


    db.commit()
    db.refresh(feedback)

    return {"message": f"Grade updated for session {session_id}."}