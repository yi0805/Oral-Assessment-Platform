"""
AI summary & instructor feedback routes.

Endpoints
---------
POST  /sessions/{session_id}/ai-summary/generate   Trigger AI summary generation
GET   /sessions/{session_id}/ai-summary            Get the AI summary
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
    AISummaryOut,
    FeedbackCreate,
    FeedbackOut,
    FeedbackUpdate,
    StudentResultsOut,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: load session or 404
# ---------------------------------------------------------------------------

def _get_session_or_404(db: Session, session_id: UUID) -> AssessmentSession:
    sess = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return sess


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

    if sess.status not in ("submitted", "time_expired", "under_review"):
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

    if sess.status not in ("under_review", "submitted", "time_expired"):
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
# Release workflow
# ---------------------------------------------------------------------------

@router.put(
    "/sessions/{session_id}/release",
    response_model=FeedbackOut,
    summary="Release results to student",
    description=(
        "Instructor-only. Marks the feedback as released, making it visible to the "
        "student via GET /sessions/{id}/results. Transitions the session to 'released'. "
        "Requires: final_grade must be set and student_visible_comments must not be empty."
    ),
)
def release_results(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    sess = _get_session_or_404(db, session_id)

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

    if not feedback.final_grade:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="final_grade must be set before releasing results to the student.",
        )

    now = datetime.now(timezone.utc)
    feedback.released_to_student = True
    feedback.released_at = now

    sess.status = "released"
    sess.released_at = now

    db.commit()
    db.refresh(feedback)
    return feedback


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

    ai_summary = db.query(AISummary).filter(AISummary.session_id == session_id).first()

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
        ai_summary=AISummaryOut.model_validate(ai_summary) if ai_summary else None,
        transcript_messages=[TranscriptMessageOut.model_validate(m) for m in transcript],
    )
