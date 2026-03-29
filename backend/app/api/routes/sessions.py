"""
Assessment session routes (student-facing + instructor review).

Endpoints
---------
POST   /assessments/{assessment_id}/sessions/start   Start a student session
POST   /sessions/{session_id}/respond                Submit a student answer + get next question
POST   /sessions/{session_id}/complete               End a session (student or auto-timeout)
GET    /sessions/{session_id}                        Full transcript (instructor review)
GET    /assessments/{assessment_id}/sessions         List all sessions (instructor dashboard)

Server-side timer enforcement
------------------------------
  start   → expires_at = now() + total_time_minutes
  respond → if now() > expires_at: auto-complete with status='time_expired', raise 403

AI follow-up generation (respond endpoint)
------------------------------------------
After saving a student's answer, the system decides the next step:
  1. If follow-ups are enabled AND current follow-up count < max_followups_per_main:
       → Generate an AI follow-up question via the AI Gateway (OpenRouter free)
       → Append to transcript as (assistant, followup_question)
  2. Else if more main questions remain:
       → Advance to next main question from the approved pool
       → Append to transcript as (assistant, main_question)
  3. Else:
       → Mark the session status as 'all_questions_complete' (still in_progress, timer running)
       → next_question = None signals to the frontend that the student can submit
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor, require_student
from app.schemas.pagination import Page
from app.models.assessment import AssessmentConfig, AssessmentSession
from app.models.course import CourseEnrollment
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
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Start session
# ---------------------------------------------------------------------------

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

    # Verify the student is enrolled in this course
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == config.course_id,
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.is_active.is_(True),
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in the course for this assessment.",
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

    # Prevent duplicate in-progress sessions
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

    # Create session with server-side expiry timer
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

    # Pull the first approved main question
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

    # Record the question as a runtime item
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

    # Write the first transcript message
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


# ---------------------------------------------------------------------------
# Submit response (+ AI follow-up generation)
# ---------------------------------------------------------------------------

@router.post(
    "/sessions/{session_id}/respond",
    response_model=StudentResponseResponse,
    summary="Submit a student answer",
    description=(
        "Student-only. Saves the answer, enforces the timer, then uses the AI "
        "Gateway to decide the next question: AI follow-up → next main → complete."
    ),
)
async def submit_response(
    session_id: UUID,
    payload: StudentResponseRequest,
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

    # Server-side timer enforcement — total session timer
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

    config = (
        db.query(AssessmentConfig)
        .filter(AssessmentConfig.id == session.assessment_config_id)
        .first()
    )

    # Per-question time limit enforcement
    # If per_question_time_limit_seconds is configured, check the time elapsed
    # since the most recent assistant question was asked.
    if config and config.per_question_time_limit_seconds:
        last_question_msg = (
            db.query(TranscriptMessage)
            .filter(
                TranscriptMessage.session_id == session_id,
                TranscriptMessage.sender_role == "assistant",
            )
            .order_by(TranscriptMessage.sequence_no.desc())
            .first()
        )
        if last_question_msg:
            elapsed = (now - last_question_msg.created_at.replace(tzinfo=timezone.utc)).total_seconds()
            if elapsed > config.per_question_time_limit_seconds:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        f"Per-question time limit of {config.per_question_time_limit_seconds}s exceeded "
                        f"({int(elapsed)}s elapsed). The question has been skipped."
                    ),
                )

    # Determine next sequence number
    last_msg = (
        db.query(TranscriptMessage)
        .filter(TranscriptMessage.session_id == session_id)
        .order_by(TranscriptMessage.sequence_no.desc())
        .first()
    )
    next_seq = (last_msg.sequence_no + 1) if last_msg else 1

    # Persist the student's answer
    answer_msg = TranscriptMessage(
        session_id=session_id,
        sender_role="student",
        message_type="student_answer",
        sequence_no=next_seq,
        content=payload.answer_text,
    )
    db.add(answer_msg)
    db.flush()
    next_seq += 1

    # ------------------------------------------------------------------
    # Decide next question
    # ------------------------------------------------------------------
    next_question_item: SessionQuestionItem | None = None
    current_followup = session.current_followup_index or 0
    current_main = session.current_main_index or 1
    max_main = config.max_main_questions if config else None
    max_followups = config.max_followups_per_main if config else 0
    followup_enabled = config.followup_enabled if config else False

    if followup_enabled and current_followup < max_followups:
        # Generate an AI follow-up question for the current main question
        followup_text = await _generate_ai_followup(
            db=db,
            session=session,
            current_followup=current_followup,
        )

        item = SessionQuestionItem(
            session_id=session_id,
            source_question_id=None,          # fully AI-generated
            asked_text=followup_text,
            question_kind="followup",
            main_group_no=current_main,
            followup_no=current_followup + 1,
            generated_by="adaptive_ai",
        )
        db.add(item)
        db.flush()

        followup_msg = TranscriptMessage(
            session_id=session_id,
            session_question_item_id=item.id,
            sender_role="assistant",
            message_type="followup_question",
            sequence_no=next_seq,
            content=followup_text,
        )
        db.add(followup_msg)

        session.current_followup_index = current_followup + 1
        next_question_item = item

    elif max_main is None or current_main < max_main:
        # Advance to the next main question from the approved pool
        next_main_no = current_main + 1
        next_q = _get_main_question_by_order(db, config, next_main_no)

        if next_q:
            item = SessionQuestionItem(
                session_id=session_id,
                source_question_id=next_q.id,
                asked_text=next_q.question_text,
                question_kind="main",
                main_group_no=next_main_no,
                followup_no=None,
                generated_by="approved_pool",
            )
            db.add(item)
            db.flush()

            main_msg = TranscriptMessage(
                session_id=session_id,
                session_question_item_id=item.id,
                sender_role="assistant",
                message_type="main_question",
                sequence_no=next_seq,
                content=next_q.question_text,
            )
            db.add(main_msg)

            session.current_main_index = next_main_no
            session.current_followup_index = 0
            next_question_item = item
        else:
            # Pool exhausted — let the student submit
            logger.info("Session %s: question pool exhausted at main %d", session_id, next_main_no)
    else:
        # All required main questions answered — student can submit
        logger.info("Session %s: all %d main questions answered", session_id, max_main)

    db.commit()
    db.refresh(answer_msg)
    db.refresh(session)
    if next_question_item:
        db.refresh(next_question_item)

    time_remaining = (
        max(0, int((session.expires_at - now).total_seconds()))
        if session.expires_at else 0
    )

    return StudentResponseResponse(
        message_saved=TranscriptMessageOut.model_validate(answer_msg),
        next_question=(
            SessionQuestionItemOut.model_validate(next_question_item)
            if next_question_item else None
        ),
        session_status=session.status,
        time_remaining_seconds=time_remaining,
    )


# ---------------------------------------------------------------------------
# Complete session
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Transcript view (instructor)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# List sessions (instructor dashboard)
# ---------------------------------------------------------------------------

@router.get(
    "/assessments/{assessment_id}/sessions",
    response_model=Page[SessionBrief],
    summary="List student sessions for an assessment",
    description="Instructor-only. Returns brief summaries of all student sessions (paginated).",
)
def list_sessions(
    assessment_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == assessment_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    q = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.assessment_config_id == assessment_id)
        .order_by(AssessmentSession.created_at.desc())
    )
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return Page.create(items, total, page, page_size)


@router.get(
    "/sessions/mine",
    response_model=Page[SessionBrief],
    summary="List my sessions",
    description=(
        "Student-only. Returns all sessions belonging to the authenticated student, "
        "ordered most recent first (paginated)."
    ),
)
def list_my_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    q = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.student_id == current_user.id)
        .order_by(AssessmentSession.created_at.desc())
    )
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return Page.create(items, total, page, page_size)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_main_question_by_order(
    db: Session,
    config: AssessmentConfig | None,
    order: int,
) -> Question | None:
    """Return the main question at the given display_order from the pool."""
    if not config or not config.question_pool_id:
        return None

    questions = (
        db.query(Question)
        .filter(
            Question.question_pool_id == config.question_pool_id,
            Question.question_kind == "main",
            Question.is_active.is_(True),
        )
        .order_by(Question.display_order.asc())
        .all()
    )

    idx = order - 1   # order is 1-based
    return questions[idx] if 0 <= idx < len(questions) else None


async def _generate_ai_followup(
    db: Session,
    session: AssessmentSession,
    current_followup: int,
) -> str:
    """
    Generate a context-aware follow-up question using the AI Gateway.

    Builds a compact conversation history from recent transcript messages
    and asks the LLM to generate the next follow-up.

    Falls back to a generic probing question on any AI error.
    """
    from app.services.ai_gateway import chat_complete

    # Build recent conversation context (last 6 turns for brevity)
    recent_msgs = (
        db.query(TranscriptMessage)
        .filter(TranscriptMessage.session_id == session.id)
        .order_by(TranscriptMessage.sequence_no.desc())
        .limit(6)
        .all()
    )
    recent_msgs.reverse()

    history_lines = []
    for m in recent_msgs:
        prefix = "Assessor" if m.sender_role == "assistant" else "Student"
        history_lines.append(f"{prefix}: {m.content}")
    history = "\n".join(history_lines)

    system_prompt = (
        "You are an academic assessor conducting an oral assessment. "
        "Generate a single, concise follow-up question that probes the student's "
        "understanding more deeply. The follow-up must be directly related to what "
        "the student just said. Output ONLY the question text — no preamble."
    )
    user_prompt = (
        f"Conversation so far:\n{history}\n\n"
        f"This is follow-up #{current_followup + 1}. "
        "Generate the next follow-up question:"
    )

    try:
        result = await chat_complete(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=150,
        )
        # Clean any accidental quotation wrapping
        return result.strip().strip('"').strip("'")
    except RuntimeError as exc:
        logger.warning("Follow-up AI generation failed: %s — using fallback", exc)
        fallback_probes = [
            "Can you elaborate further on that point?",
            "What evidence or reasoning supports your answer?",
            "How would this apply in a real-world scenario?",
        ]
        return fallback_probes[current_followup % len(fallback_probes)]
