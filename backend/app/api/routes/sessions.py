"""
Assessment session routes (student-facing + instructor review).

Endpoints:
  POST /assessments/:id/sessions/start → start a student session
  POST /sessions/:id/respond → submit student answer
  POST /sessions/:id/complete → end session (manual or timeout)
  GET /sessions/:id → get full session with transcript

CRITICAL: Server-side timer enforcement.
  When session starts: expires_at = now() + total_time_minutes
  Every POST /respond checks: if now() > expires_at → 403 + auto-complete

TODO:
- Session start with timer calculation
- Student response persistence (transcript_messages)
- Integration with James's chat orchestrator
- Server-side expiry enforcement
"""
from uuid import UUID
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.assessment import AssessmentConfig, AssessmentSession
from app.models.session_runtime import SessionQuestionItem, TranscriptMessage
from app.models.question import Question
from app.schemas.assessment import (
    SessionStartResponse, StudentResponseRequest, StudentResponseResponse,
    SessionOut, SessionBrief, SessionQuestionItemOut, TranscriptMessageOut, FullTranscriptOut,
)

router = APIRouter()


@router.post("/assessments/{assessment_id}/sessions/start", response_model=SessionStartResponse)
def start_session(assessment_id: UUID, db: Session = Depends(get_db)):
    """
    Start a new assessment session for the current student.
    Sets expires_at = now() + total_time_minutes for server-side timer enforcement.
    Pulls the first main question from the approved pool.
    """
    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == assessment_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if config.status != "published":
        raise HTTPException(status_code=409, detail="Assessment is not published")

    # Check scheduling window
    now = datetime.now(timezone.utc)
    if config.open_at and now < config.open_at:
        raise HTTPException(status_code=403, detail="Assessment has not opened yet")
    if config.close_at and now > config.close_at:
        raise HTTPException(status_code=403, detail="Assessment has closed")

    # TODO: Check if student already has a session for this assessment
    # TODO: Get current user from JWT

    # Create session with server-side timer
    expires_at = now + timedelta(minutes=config.total_time_minutes)
    session = AssessmentSession(
        assessment_config_id=assessment_id,
        course_id=config.course_id,
        # student_id=current_user.id,  # TODO: wire auth
        student_id=UUID("a0000000-0000-0000-0000-000000000002"),  # Temp: seed student
        status="in_progress",
        started_at=now,
        expires_at=expires_at,
        current_main_index=1,
        current_followup_index=0,
    )
    db.add(session)
    db.flush()

    # Pull first main question from the approved pool
    first_question = (
        db.query(Question)
        .filter(
            Question.question_pool_id == config.question_pool_id,
            Question.question_kind == "main",
            Question.is_active == True,
        )
        .order_by(Question.display_order.asc())
        .first()
    )
    if not first_question:
        raise HTTPException(status_code=500, detail="No main questions found in the approved pool")

    # Create runtime question item
    item = SessionQuestionItem(
        session_id=session.id,
        source_question_id=first_question.id,
        asked_text=first_question.question_text,
        question_kind="main",
        main_group_no=1,
        followup_no=None,
        generated_by="approved_pool",
    )
    db.add(item)
    db.flush()

    # Create transcript message for the first question
    msg = TranscriptMessage(
        session_id=session.id,
        session_question_item_id=item.id,
        sender_role="assistant",
        message_type="main_question",
        sequence_no=1,
        content=first_question.question_text,
    )
    db.add(msg)
    db.commit()
    db.refresh(session)
    db.refresh(item)

    return SessionStartResponse(
        session_id=session.id,
        assessment_title=config.title,
        total_time_minutes=config.total_time_minutes,
        expires_at=expires_at,
        first_question=SessionQuestionItemOut.model_validate(item),
    )


@router.post("/sessions/{session_id}/respond", response_model=StudentResponseResponse)
def submit_response(session_id: UUID, payload: StudentResponseRequest, db: Session = Depends(get_db)):
    """
    Student submits an answer. Server enforces the time limit.
    1. Check if session has expired (server-side timer enforcement)
    2. Save the student's answer as a transcript message
    3. Return the saved message + session state + time remaining
    The next question (AI follow-up or next main) is handled by James's orchestrator.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="Session is not in progress")
    if session.transcript_locked:
        raise HTTPException(status_code=409, detail="Transcript is locked")

    # Server-side timer enforcement
    now = datetime.now(timezone.utc)
    if session.expires_at and now > session.expires_at:
        session.status = "time_expired"
        session.ended_at = now
        session.transcript_locked = True
        db.commit()
        raise HTTPException(status_code=403, detail="Session has expired due to time limit")

    # Get the next sequence number
    last_msg = (
        db.query(TranscriptMessage)
        .filter(TranscriptMessage.session_id == session_id)
        .order_by(TranscriptMessage.sequence_no.desc())
        .first()
    )
    next_seq = (last_msg.sequence_no + 1) if last_msg else 1

    # Save the student's answer
    msg = TranscriptMessage(
        session_id=session_id,
        sender_role="student",
        message_type="student_answer",
        sequence_no=next_seq,
        content=payload.answer_text,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # Calculate time remaining
    time_remaining = 0
    if session.expires_at:
        remaining = (session.expires_at - now).total_seconds()
        time_remaining = max(0, int(remaining))

    # TODO: James's orchestrator decides the next question here
    # For now, return None for next_question — the orchestrator will handle it
    return StudentResponseResponse(
        message_saved=TranscriptMessageOut.model_validate(msg),
        next_question=None,
        session_status=session.status,
        time_remaining_seconds=time_remaining,
    )


@router.post("/sessions/{session_id}/complete", response_model=SessionOut)
def complete_session(session_id: UUID, db: Session = Depends(get_db)):
    """
    End a session — called manually by the student or automatically on timeout.
    Locks the transcript so no further messages can be written.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status not in ("in_progress",):
        raise HTTPException(status_code=409, detail="Session cannot be completed from current status")

    now = datetime.now(timezone.utc)
    session.status = "submitted"
    session.ended_at = now
    session.transcript_locked = True
    session.total_messages = (
        db.query(TranscriptMessage)
        .filter(TranscriptMessage.session_id == session_id)
        .count()
    )
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions/{session_id}", response_model=FullTranscriptOut)
def get_session_transcript(session_id: UUID, db: Session = Depends(get_db)):
    """Get the full session with transcript for instructor review."""
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    question_items = (
        db.query(SessionQuestionItem)
        .filter(SessionQuestionItem.session_id == session_id)
        .order_by(SessionQuestionItem.asked_at.asc())
        .all()
    )
    messages = (
        db.query(TranscriptMessage)
        .filter(TranscriptMessage.session_id == session_id)
        .order_by(TranscriptMessage.sequence_no.asc())
        .all()
    )

    return FullTranscriptOut(
        session=SessionOut.model_validate(session),
        question_items=[SessionQuestionItemOut.model_validate(qi) for qi in question_items],
        messages=[TranscriptMessageOut.model_validate(m) for m in messages],
    )


@router.get("/assessments/{assessment_id}/sessions", response_model=list[SessionBrief])
def list_sessions(assessment_id: UUID, db: Session = Depends(get_db)):
    """List all student sessions for an assessment (instructor dashboard)."""
    sessions = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.assessment_config_id == assessment_id)
        .order_by(AssessmentSession.created_at.desc())
        .all()
    )
    return sessions

