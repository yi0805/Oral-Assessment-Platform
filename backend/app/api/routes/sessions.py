"""
Assessment session routes (student-facing + instructor review).

Endpoints
---------
POST   /assessments/{assessment_id}/sessions/start   Start a student session
POST   /sessions/{session_id}/respond                Submit a student answer
POST   /sessions/{session_id}/complete               End a session (student or auto-timeout)
GET    /sessions/{session_id}                        Full transcript (instructor review)
GET    /assessments/{assessment_id}/sessions         List all sessions (instructor dashboard)

Server-side timer enforcement
------------------------------
  start  → expires_at = now() + total_time_minutes
  respond → if now() > expires_at: auto-complete with status='time_expired', raise 403
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor, require_student
from app.models.assessment import AssessmentConfig, AssessmentSession
from app.models.question import Question
from app.models.session_runtime import SessionQuestionItem, TranscriptMessage
from app.models.user import User
from app.schemas.assessment import (
    FullTranscriptOut,
    SessionBrief,
    SessionOut,
    SessionQuestionItemOut,
    SessionStartResponse,
    StudentResponseRequest,
    StudentResponseResponse,
    TranscriptMessageOut,
)

router = APIRouter()


@router.post(
    "/assessments/{assessment_id}/sessions/start",
    response_model=SessionStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start an assessment session",
    description=(
        "Student-only. Creates a new session with a server-side expiry timer, "
        "selects the first question from the approved pool, and records it in the transcript."
    ),
)
def start_session(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == assessment_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    if config.status != "published":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This assessment is not currently published.",
        )

    now = datetime.now(timezone.utc)
    if config.open_at and now < config.open_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Assessment opens at {config.open_at.isoformat()}.",
        )
    if config.close_at and now > config.close_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This assessment has closed.",
        )

    # Prevent duplicate in-progress sessions for the same student + assessment.
    existing = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.assessment_config_id == assessment_id,
            AssessmentSession.student_id == current_user.id,
            AssessmentSession.status == "in_progress",
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active session for this assessment.",
        )

    # Create session with server-side expiry timer.
    expires_at = now + timedelta(minutes=config.total_time_minutes)
    session = AssessmentSession(
        assessment_config_id=assessment_id,
        course_id=config.course_id,
        student_id=current_user.id,
        status="in_progress",
        started_at=now,
        expires_at=expires_at,
        current_main_index=1,
        current_followup_index=0,
    )
    db.add(session)
    db.flush()

    # Pull the first approved main question.
    first_question = (
        db.query(Question)
        .filter(
            Question.question_pool_id == config.question_pool_id,
            Question.question_kind == "main",
            Question.is_active.is_(True),
        )
        .order_by(Question.display_order.asc())
        .first()
    )
    if not first_question:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No active main questions found in the approved pool.",
        )

    # Record the question as a runtime item.
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

    # Write the first transcript message.
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


@router.post(
    "/sessions/{session_id}/respond",
    response_model=StudentResponseResponse,
    summary="Submit a student answer",
    description=(
        "Student-only. Saves the answer as a transcript message and enforces the "
        "server-side timer. Returns time remaining and the next question placeholder "
        "(populated by the AI orchestrator integration point)."
    ),
)
def submit_response(
    session_id: UUID,
    payload: StudentResponseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Ownership check — students can only respond to their own sessions.
    if session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session.",
        )

    if session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session is not in progress (current status: {session.status}).",
        )
    if session.transcript_locked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transcript is locked — the session has ended.",
        )

    # Server-side timer enforcement.
    now = datetime.now(timezone.utc)
    if session.expires_at and now > session.expires_at:
        session.status = "time_expired"
        session.ended_at = now
        session.transcript_locked = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your session has expired. The transcript has been locked.",
        )

    # Determine next sequence number.
    last_msg = (
        db.query(TranscriptMessage)
        .filter(TranscriptMessage.session_id == session_id)
        .order_by(TranscriptMessage.sequence_no.desc())
        .first()
    )
    next_seq = (last_msg.sequence_no + 1) if last_msg else 1

    # Persist the student's answer.
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

    time_remaining = max(0, int((session.expires_at - now).total_seconds())) if session.expires_at else 0

    # next_question is populated by the AI orchestrator (integration point).
    return StudentResponseResponse(
        message_saved=TranscriptMessageOut.model_validate(msg),
        next_question=None,
        session_status=session.status,
        time_remaining_seconds=time_remaining,
    )


@router.post(
    "/sessions/{session_id}/complete",
    response_model=SessionOut,
    summary="Complete a session",
    description=(
        "Student-only. Ends the session, locks the transcript, and records the "
        "total message count. Can also be called automatically on timer expiry."
    ),
)
def complete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session.",
        )

    if session.status not in ("in_progress",):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session cannot be completed from status '{session.status}'.",
        )

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


@router.get(
    "/sessions/{session_id}",
    response_model=FullTranscriptOut,
    summary="Get full session transcript",
    description=(
        "Instructor-only. Returns the complete session including all transcript "
        "messages and runtime question items, for grading review."
    ),
)
def get_session_transcript(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

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
