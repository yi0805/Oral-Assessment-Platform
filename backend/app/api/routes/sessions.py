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
  respond → if now() > expires_at: auto-finalize with status='time_expired' and return next_question=None

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

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_instructor, require_student
from app.schemas.pagination import Page
from app.models.assessment import AssessmentConfig, AssessmentSession
from app.models.course import CourseEnrollment, Course
from app.models.feedback import AISummary, InstructorFeedback
from app.models.question import Question
from app.models.session_runtime import SessionQuestionItem, TranscriptMessage
from app.models.user import User
from app.schemas.assessment import (
    AssessmentStatsOut,
    FullTranscriptOut,
    SessionBrief,
    SessionBriefWithAIGrades, 
    SessionOut,
    SessionQuestionItemOut,
    SessionStartResponse,
    StudentResponseRequest,
    StudentResponseResponse,
    AssessmentConfigOut
)

from pydantic import BaseModel, ConfigDict
from app.schemas.feedback import AISummaryOut
from app.schemas.user import UserOut
from app.schemas.course import CourseOut
from app.schemas.enums import SessionStatus

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Start session
# ---------------------------------------------------------------------------

# @router.post(
#     "/assessments/{assessment_id}/sessions/start",
#     response_model=SessionStartResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Start an assessment session",
#     description=(
#         "Student-only. Creates a new session with a server-side expiry timer, "
#         "selects the first question from the approved pool, and records it in the transcript."
#     ),
# )
# def start_session(
#     assessment_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_student),
# ):
#     config = db.query(AssessmentConfig).filter(AssessmentConfig.id == assessment_id).first()
#     if not config:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
#     if config.status != "published":
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="This assessment is not currently published.",
#         )

#     # Verify the student is enrolled in this course
#     enrollment = (
#         db.query(CourseEnrollment)
#         .filter(
#             CourseEnrollment.course_id == config.course_id,
#             CourseEnrollment.user_id == current_user.id,
#             CourseEnrollment.is_active.is_(True),
#         )
#         .first()
#     )
#     if not enrollment:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You are not enrolled in the course for this assessment.",
#         )

#     now = datetime.now(timezone.utc)
#     if config.open_at and now < config.open_at:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail=f"Assessment opens at {config.open_at.isoformat()}.",
#         )
#     if config.close_at and now > config.close_at:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="This assessment has closed.",
#         )

#     # Prevent duplicate in-progress sessions
#     existing = (
#         db.query(AssessmentSession)
#         .filter(
#             AssessmentSession.assessment_config_id == assessment_id,
#             AssessmentSession.student_id == current_user.id,
#             AssessmentSession.status == "in_progress",
#         )
#         .first()
#     )
#     if existing:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="You already have an active session for this assessment.",
#         )

#     # Create session with server-side expiry timer
#     expires_at = now + timedelta(minutes=config.total_time_minutes)
#     session = AssessmentSession(
#         assessment_config_id=assessment_id,
#         course_id=config.course_id,
#         student_id=current_user.id,
#         status="in_progress",
#         started_at=now,
#         expires_at=expires_at,
#         current_main_index=1,
#         current_followup_index=0,
#     )
#     db.add(session)
#     db.flush()

#     # Pull the first approved main question
#     first_question = (
#         db.query(Question)
#         .filter(
#             Question.question_pool_id == config.question_pool_id,
#             Question.question_kind == "main",
#             Question.is_active.is_(True),
#         )
#         .order_by(Question.display_order.asc())
#         .first()
#     )
#     if not first_question:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="No active main questions found in the approved pool.",
#         )

#     # Record the question as a runtime item
#     item = SessionQuestionItem(
#         session_id=session.id,
#         source_question_id=first_question.id,
#         asked_text=first_question.question_text,
#         question_kind="main",
#         main_group_no=1,
#         followup_no=None,
#         generated_by="approved_pool",
#     )
#     db.add(item)
#     db.flush()

#     # Write the first transcript message
#     msg = TranscriptMessage(
#         session_id=session.id,
#         session_question_item_id=item.id,
#         sender_role="assistant",
#         message_type="main_question",
#         sequence_no=1,
#         content=first_question.question_text,
#     )
#     db.add(msg)
#     db.commit()
#     db.refresh(session)
#     db.refresh(item)

#     return SessionStartResponse(
#         session_id=session.id,
#         assessment_title=config.title,
#         total_time_minutes=config.total_time_minutes,
#         expires_at=expires_at,
#         first_question=SessionQuestionItemOut.model_validate(item),
#     )


# ---------------------------------------------------------------------------
# Submit response (+ AI follow-up generation)
# ---------------------------------------------------------------------------

# @router.post(
#     "/sessions/{session_id}/respond",
#     response_model=StudentResponseResponse,
#     summary="Submit a student answer",
#     description=(
#         "Student-only. Saves the answer, enforces the timer, then uses the AI "
#         "Gateway to decide the next question: AI follow-up → next main → complete."
#     ),
# )
# async def submit_response(
#     session_id: UUID,
#     payload: StudentResponseRequest,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_student),
# ):
#     session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
#     if not session:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

#     if session.student_id != current_user.id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You do not have access to this session.",
#         )

#     if session.status != "in_progress":
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail=f"Session is not in progress (current status: {session.status}).",
#         )

#     if session.transcript_locked:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="Transcript is locked — the session has ended.",
#         )

#     # Server-side timer enforcement — total session timer
#     now = datetime.now(timezone.utc)
#     if session.expires_at and now > session.expires_at:
#         # If expired now, auto-submit/finalize
#         session.status = "time_expired"
#         session.ended_at = now
#         session.transcript_locked = True
#         session.total_messages = (
#             db.query(TranscriptMessage)
#             .filter(TranscriptMessage.session_id == session_id)
#             .count()
#         )
#         db.commit()
#         db.refresh(session)

#         return StudentResponseResponse(
#             message_saved=None,
#             next_question=None,
#             session_status="time_expired",
#             time_remaining_seconds=0,
#         )

#     config = (
#         db.query(AssessmentConfig)
#         .filter(AssessmentConfig.id == session.assessment_config_id)
#         .first()
#     )

#     # Per-question time limit enforcement
#     # If per_question_time_limit_minutes is configured, check the time elapsed
#     # since the most recent assistant question was asked.
#     if config and config.per_question_time_limit_minutes:
#         time_limit_seconds = config.per_question_time_limit_minutes * 60

#         last_question_msg = (
#             db.query(TranscriptMessage)
#             .filter(
#                 TranscriptMessage.session_id == session_id,
#                 TranscriptMessage.sender_role == "assistant",
#             )
#             .order_by(TranscriptMessage.sequence_no.desc())
#             .first()
#         )

#         if last_question_msg:
#             elapsed = (now - last_question_msg.created_at.replace(tzinfo=timezone.utc)).total_seconds()
#             if elapsed > time_limit_seconds:
#                 raise HTTPException(
#                     status_code=status.HTTP_403_FORBIDDEN,
#                     detail=(
#                         f"Per-question time limit of {config.per_question_time_limit_minutes} minutes exceeded "
#                         f"({int(elapsed)} seconds elapsed). The question has been skipped."
#                     ),
#                 )

#     # Determine next sequence number
#     last_msg = (
#         db.query(TranscriptMessage)
#         .filter(TranscriptMessage.session_id == session_id)
#         .order_by(TranscriptMessage.sequence_no.desc())
#         .first()
#     )
#     next_seq = (last_msg.sequence_no + 1) if last_msg else 1

#     # Find the question item this answer responds to
#     last_question_item = (
#         db.query(SessionQuestionItem)
#         .filter(SessionQuestionItem.session_id == session_id)
#         .order_by(SessionQuestionItem.asked_at.desc())
#         .first()
#     )

#     # Persist the student's answer
#     answer_msg = TranscriptMessage(
#         session_id=session_id,
#         session_question_item_id=last_question_item.id if last_question_item else None,
#         sender_role="student",
#         message_type="student_answer",
#         sequence_no=next_seq,
#         content=payload.answer_text,
#     )
#     db.add(answer_msg)
#     db.flush()
#     next_seq += 1

#     # ------------------------------------------------------------------
#     # Decide next question
#     # ------------------------------------------------------------------
#     next_question_item: SessionQuestionItem | None = None
#     current_followup = session.current_followup_index or 0
#     current_main = session.current_main_index or 1
#     max_main = config.max_main_questions if config else None
#     max_followups = config.max_followups_per_main if config else 0
#     followup_enabled = config.followup_enabled if config else False

#     if followup_enabled and current_followup < max_followups:
#         # Generate an AI follow-up question for the current main question
#         followup_text = await _generate_ai_followup(
#             db=db,
#             session=session,
#             current_followup=current_followup,
#         )

#         item = SessionQuestionItem(
#             session_id=session_id,
#             source_question_id=None,          # fully AI-generated
#             asked_text=followup_text,
#             question_kind="followup",
#             main_group_no=current_main,
#             followup_no=current_followup + 1,
#             generated_by="adaptive_ai",
#         )
#         db.add(item)
#         db.flush()

#         followup_msg = TranscriptMessage(
#             session_id=session_id,
#             session_question_item_id=item.id,
#             sender_role="assistant",
#             message_type="followup_question",
#             sequence_no=next_seq,
#             content=followup_text,
#         )
#         db.add(followup_msg)

#         session.current_followup_index = current_followup + 1
#         next_question_item = item

#     elif max_main is None or current_main < max_main:
#         # Advance to the next main question from the approved pool
#         next_main_no = current_main + 1
#         next_q = _get_main_question_by_order(db, config, next_main_no)

#         if next_q:
#             item = SessionQuestionItem(
#                 session_id=session_id,
#                 source_question_id=next_q.id,
#                 asked_text=next_q.question_text,
#                 question_kind="main",
#                 main_group_no=next_main_no,
#                 followup_no=None,
#                 generated_by="approved_pool",
#             )
#             db.add(item)
#             db.flush()

#             main_msg = TranscriptMessage(
#                 session_id=session_id,
#                 session_question_item_id=item.id,
#                 sender_role="assistant",
#                 message_type="main_question",
#                 sequence_no=next_seq,
#                 content=next_q.question_text,
#             )
#             db.add(main_msg)

#             session.current_main_index = next_main_no
#             session.current_followup_index = 0
#             next_question_item = item
#         else:
#             # Pool exhausted — let the student submit
#             logger.info("Session %s: question pool exhausted at main %d", session_id, next_main_no)
#     else:
#         # All required main questions answered — student can submit
#         logger.info("Session %s: all %d main questions answered", session_id, max_main)

#     db.commit()
#     db.refresh(answer_msg)
#     db.refresh(session)
#     if next_question_item:
#         db.refresh(next_question_item)

#     time_remaining = (
#         max(0, int((session.expires_at - now).total_seconds()))
#         if session.expires_at else 0
#     )

#     return StudentResponseResponse(
#         message_saved=TranscriptMessageOut.model_validate(answer_msg),
#         next_question=(
#             SessionQuestionItemOut.model_validate(next_question_item)
#             if next_question_item else None
#         ),
#         session_status=session.status,
#         time_remaining_seconds=time_remaining,
#     )


# ---------------------------------------------------------------------------
# Complete session
# ---------------------------------------------------------------------------

# @router.post(
#     "/sessions/{session_id}/complete",
#     response_model=SessionOut,
#     summary="Complete a session",
#     description=(
#         "Student-only. Ends the session, locks the transcript, and records the "
#         "total message count. Can also be called automatically on timer expiry."
#     ),
# )
# def complete_session(
#     session_id: UUID,
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_student),
# ):
#     session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
#     if not session:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

#     if session.student_id != current_user.id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You do not have access to this session.",
#         )

#     if session.status != "in_progress":
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail=f"Session cannot be completed from status '{session.status}'.",
#         )

#     now = datetime.now(timezone.utc)
#     session.status = "submitted"
#     session.ended_at = now
#     session.transcript_locked = True
#     session.total_messages = (
#         db.query(TranscriptMessage)
#         .filter(TranscriptMessage.session_id == session_id)
#         .count()
#     )
#     db.commit()
#     db.refresh(session)

#     background_tasks.add_task(_run_ai_summary_background, session_id)

#     return session


# ---------------------------------------------------------------------------
# List my sessions (student) — MUST be defined before /sessions/{session_id}
# so FastAPI matches the literal path "mine" before the UUID path parameter.
# ---------------------------------------------------------------------------

# @router.get(
#     "/sessions/mine",
#     response_model=Page[SessionBrief],
#     summary="List my sessions",
#     description=(
#         "Student-only. Returns all sessions belonging to the authenticated student, "
#         "ordered most recent first (paginated)."
#     ),
# )
# def list_my_sessions(
#     page: int = Query(1, ge=1),
#     page_size: int = Query(20, ge=1, le=100),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_student),
# ):
#     q = (
#         db.query(AssessmentSession)
#         .filter(AssessmentSession.student_id == current_user.id)
#         .order_by(AssessmentSession.created_at.desc())
#     )
#     total = q.count()
#     items = q.offset((page - 1) * page_size).limit(page_size).all()
#     return Page.create(items, total, page, page_size)


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
    response_model=Page[SessionBriefWithAIGrades],
    summary="List student sessions for an assessment",
    description=(
        "Instructor-only. Returns brief summaries of all student sessions (paginated). "
        "Each item is enriched with student name, email, AI-suggested grade, and final grade "
        "for the instructor grading dashboard transcript list view."
    ),
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
    sessions = q.offset((page - 1) * page_size).limit(page_size).all()

    # Enrich each session brief with student info, AI suggested grade, and final grade
    enriched: list[SessionBriefWithAIGrades] = []
    for sess in sessions:
        brief = SessionBriefWithAIGrades.model_validate(sess)

        # Attach student name and email
        student = db.query(User).filter(User.id == sess.student_id).first()
        if student:
            brief.student_name = student.full_name
            brief.student_email = student.email

        # Attach AI suggested grade (advisory)
        ai_summary = db.query(AISummary).filter(
            AISummary.session_id == sess.id,
            AISummary.status == "success",
        ).first()
        if ai_summary:
            brief.ai_suggested_grade = ai_summary.suggested_grade

        # Attach instructor final grade if already graded
        feedback = db.query(InstructorFeedback).filter(
            InstructorFeedback.session_id == sess.id
        ).first()
        if feedback:
            brief.final_grade = feedback.final_grade

        enriched.append(brief)

    return Page.create(enriched, total, page, page_size)


@router.get(
    "/assessments/{assessment_id}/sessions/stats",
    response_model=AssessmentStatsOut,
    summary="Get class grade statistics",
    description=(
        "Instructor-only. Returns median, average, highest, and lowest final grades "
        "across all instructor-graded sessions for this assessment. "
        "Only sessions with a numeric final_grade are included in calculations. "
        "Matches the statistics panel shown on the instructor grading dashboard."
    ),
)
def get_assessment_stats(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == assessment_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    total_sessions = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.assessment_config_id == assessment_id)
        .count()
    )

    # Collect all numeric final grades for this assessment
    feedbacks = (
        db.query(InstructorFeedback)
        .join(AssessmentSession, InstructorFeedback.session_id == AssessmentSession.id)
        .filter(
            AssessmentSession.assessment_config_id == assessment_id,
            InstructorFeedback.final_grade.isnot(None),
        )
        .all()
    )

    # Parse final_grade values to floats
    numeric_grades: list[float] = [float(fb.final_grade) for fb in feedbacks]

    graded_count = len(numeric_grades)

    if graded_count == 0:
        return AssessmentStatsOut(
            assessment_id=assessment_id,
            total_sessions=total_sessions,
            graded_count=0,
            average_grade=None,
            median_grade=None,
            highest_grade=None,
            lowest_grade=None,
        )

    numeric_grades.sort()
    average = sum(numeric_grades) / graded_count
    n = graded_count
    if n % 2 == 1:
        median = numeric_grades[n // 2]
    else:
        median = (numeric_grades[n // 2 - 1] + numeric_grades[n // 2]) / 2.0

    return AssessmentStatsOut(
        assessment_id=assessment_id,
        total_sessions=total_sessions,
        graded_count=graded_count,
        average_grade=round(average, 2),
        median_grade=round(median, 2),
        highest_grade=max(numeric_grades),
        lowest_grade=min(numeric_grades),
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

import re

def _normalize_followup(text: str) -> str:
    text = " ".join(text.strip().split())
    text = re.sub(r"^['\"`\-\*\d\.\)\s]+", "", text)

    # only retrive the first question
    m = re.search(r".*?\?", text)
    if m:
        text = m.group(0)

    # only keep 25 words if question is too long
    words = text.split()
    if len(words) > 25:
        text = " ".join(words[:25]).rstrip(",.;:") + "?"

    return text

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

    Builds a compact conversation history from recent transcript messages,
    explicitly anchoring to the current main question so follow-ups stay
    on-topic (fixes: follow-up not relevant to the main question).

    Falls back to a generic probing question on any AI error.
    """
    from app.services.ai_gateway import chat_complete

    # Identify the current main question from session_question_items so the
    # follow-up is explicitly grounded in that question (not just recent chat).
    main_question_text: str | None = None
    current_main = session.current_main_index or 1
    main_item = (
        db.query(SessionQuestionItem)
        .filter(
            SessionQuestionItem.session_id == session.id,
            SessionQuestionItem.question_kind == "main",
            SessionQuestionItem.main_group_no == current_main,
        )
        .first()
    )
    if main_item:
        main_question_text = main_item.asked_text

    # Build recent conversation context (last 8 turns for breadth).
    # Limit to the current main question block by filtering on main_group_no
    # so follow-ups don't bleed context from previous main questions.
    # recent_msgs = (
    #     db.query(TranscriptMessage)
    #     .filter(TranscriptMessage.session_id == session.id)
    #     .order_by(TranscriptMessage.sequence_no.desc())
    #     .limit(8)
    #     .all()
    # )
    # recent_msgs.reverse()

    # history_lines = []
    # for m in recent_msgs:
    #     prefix = "Assessor" if m.sender_role == "assistant" else "Student"
    #     history_lines.append(f"{prefix}: {m.content}")
    # history = "\n".join(history_lines)

    # main_context = (
    #     f"\n\nThe main question being assessed is:\n\"{main_question_text}\"\n"
    #     if main_question_text else ""
    # )

    # Retrieve student's latest answer
    latest_student_msg = (
        db.query(TranscriptMessage)
        .filter(
            TranscriptMessage.session_id == session.id,
            TranscriptMessage.sender_role == "student",
            TranscriptMessage.message_type == "student_answer",
        )
        .order_by(TranscriptMessage.sequence_no.desc())
        .first()
    )

    student_answer = latest_student_msg.content if latest_student_msg else ""

    # FOLLOWUP_SYSTEM_PROMPT = """\
    #     You generate exactly one oral-assessment follow-up question.

    #     Rules:
    #     - Output exactly one single question.
    #     - No explanation.
    #     - No reasoning.
    #     - No preamble.
    #     - No quotes.
    #     - No JSON.
    #     - Maximum 25 words.
    #     - Must reference a specific idea from the student's most recent answer.
    #     """

    FOLLOWUP_SYSTEM_PROMPT = """
        You are an expert academic assessor conducting an oral exam.
        Your goal is to generate exactly one follow-up question to probe the student's understanding deeply but concisely.

        Rules:
        IDENTIFY: MUST pick one specific technical term or concept from the student's last answer and generate EXACTLY ONE follow-up question.
        NO REPETITION: Do not repeat the current main question or restate the student's answer.
        OUTPUT FORMAT: Output ONLY the question text. Strictly NO quotes, NO JSON, NO preamble and NO explanations.
        CONSTRAINT: The question must be under 25 words.
        """
    
    # user_prompt = (
    #     f"{main_question_text}"
    #     f"Conversation so far:\n{history}\n\n"
    #     f"This is follow-up #{current_followup + 1}. "
    #     "It must reference a specific part of the student's answer and must not be generic."
    #     "Generate a follow-up question that is directly related to the main question above "
    #     "and probes what the student just said more deeply:"
    # )

    user_prompt = f"""
        Main question:
        {main_question_text}

        Student's latest answer:
        {student_answer}

        Write exactly one concise follow-up question that probes one specific point.
        """

    try:
        result = await chat_complete(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=FOLLOWUP_SYSTEM_PROMPT,
            temperature=0.2,  # Slightly lower temperature for more focused, on-topic questions
            max_tokens=1800,
        )

        followup_text = _normalize_followup(result)
        # Clean any accidental quotation wrapping
        return followup_text.strip().strip('"').strip("'")
    
    except RuntimeError as exc:
        logger.warning("Follow-up AI generation failed: %s — using fallback", exc)
        fallback_probes = [
            "Can you elaborate further on that point?",
            "What evidence or reasoning supports your answer?",
            "How would this apply in a real-world scenario?",
        ]
        return fallback_probes[current_followup % len(fallback_probes)]











































































# integration

class PendingReviewOut(BaseModel):
    session: SessionOut 
    assessment_config: AssessmentConfigOut
    user:  UserOut
    course: CourseOut 
    aisummary: AISummaryOut | None

class StudentInfoOut(BaseModel):
    full_name: str
    email: str | None = None
    image: str | None = None

class AssessmentInfoOut(BaseModel):
    title: str

class AISummaryInfoOut(BaseModel):
    suggested_grade: int | None = None
    summary_text: str | None = None

class InstructorFeedbackOut(BaseModel):
    final_grade: int | None = None
    comments: str | None = None

class TranscriptMessageOut(BaseModel):
    sequence_no: int
    message_type: str
    content: str

class TranscriptDetailOut(BaseModel):
    session_id: UUID
    student: StudentInfoOut
    assessment: AssessmentInfoOut
    ai_summary: AISummaryInfoOut | None = None
    instructor_feedback: InstructorFeedbackOut | None = None
    transcript: list[TranscriptMessageOut]


class StudentCourseAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assessment_config_id: UUID
    session_id: UUID
    session_status: SessionStatus
    title: str
    instructions: str | None = None
    total_time_minutes: int
    max_main_questions: int | None = None
    max_followups_per_main: int | None = None
    open_at: datetime | None = None
    close_at: datetime | None = None

class StudentSavedMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sequence_no: int
    message_type: str
    content: str


class StudentNextQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asked_text: str
    question_kind: str
    main_group_no: int
    followup_no: int | None = None


class StudentResponseResponse(BaseModel):
    message_saved: StudentSavedMessageOut
    next_question: StudentNextQuestionOut | None = None
    session_status: str

class SessionStartResponse(BaseModel):
    session_id: UUID
    assessment_title: str
    total_time_minutes: int
    expires_at: datetime | None
    current_question: SessionQuestionItemOut | None
    can_complete: bool = False
    max_main_questions: int
    max_followups_per_main: int


async def _run_ai_summary_background(session_id: UUID) -> None:
    """Run AI summary generation in a background task with its own DB session."""
    from app.core.database import SessionLocal
    from app.services.ai_summary_service import generate_summary

    db = SessionLocal()
    try:
        await generate_summary(db=db, session_id=session_id)
    except Exception:
        logger.exception("Background AI summary failed for session %s", session_id)
    finally:
        db.close()

@router.get(
    "/pendingReviews",
    response_model=list[PendingReviewOut],
    summary="Integration",
)
def pending_Reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pendingReviews = (
        db.query(AssessmentSession, AssessmentConfig, User, Course, AISummary)
        .join(
            CourseEnrollment,
            CourseEnrollment.course_id == AssessmentSession.course_id,
        )
        .join(
            User,
            User.id == AssessmentSession.student_id,
        )
        .join(
            Course,
            Course.id == AssessmentSession.course_id,
        )
        .join(
            AssessmentConfig,
            AssessmentConfig.id == AssessmentSession.assessment_config_id,
        )
        .outerjoin(
            AISummary,
            AISummary.session_id == AssessmentSession.id,
        )
        .filter(CourseEnrollment.user_id == current_user.id)
        .filter(CourseEnrollment.course_role == "instructor")
        .filter(CourseEnrollment.is_active == True)
        .filter(AssessmentSession.status == "under_review")
        .distinct()
        .all()
    )

    return [
        {
            "session": session,
            "assessment_config": assessment_config,
            "user": user,
            "course": course,
            "aisummary": ai_summary,

        }
        for session, assessment_config, user, course, ai_summary in pendingReviews
    ]

@router.get("/transcript/{session_id}", response_model=TranscriptDetailOut, summary="Integration",)
def get_transcript_detail(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    generalInfo = (
        db.query(AssessmentSession, User, AssessmentConfig, AISummary, InstructorFeedback)
        .join(User, User.id == AssessmentSession.student_id)
        .join(AssessmentConfig, AssessmentConfig.id == AssessmentSession.assessment_config_id)
        .outerjoin(AISummary, AISummary.session_id == AssessmentSession.id)
        .outerjoin(InstructorFeedback, InstructorFeedback.session_id == AssessmentSession.id)
        .filter(AssessmentSession.id == session_id)
        .first()
    )

    if not generalInfo:
        raise HTTPException(status_code=404, detail="Transcript not found")

    session_obj, user_obj, assessment_obj, ai_obj, feedback_obj = generalInfo

    transcripts = (
        db.query(TranscriptMessage)
        .filter(TranscriptMessage.session_id == session_id)
        .order_by(TranscriptMessage.sequence_no.asc())
        .all()
    )

    return {
        "session_id": session_obj.id,
        "student": {
            "full_name": user_obj.full_name,
            "email": user_obj.email,
            "image": user_obj.image,
        },
        "assessment": {
            "title": assessment_obj.title,
        },
        "ai_summary": None if not ai_obj else {
            "suggested_grade": ai_obj.suggested_grade,
            "summary_text": ai_obj.summary_text,
        },
        "instructor_feedback": None if not feedback_obj else {
            "final_grade": feedback_obj.final_grade,
            "comments": feedback_obj.comments,
        },
        "transcript": [
            {
                "sequence_no": transcript.sequence_no,
                "message_type": transcript.message_type,
                "content": transcript.content,
            }
            for transcript in transcripts
        ],
    }






@router.get(
    "/courses/{course_id}/my-assessment-sessions",
    response_model=list[StudentCourseAssessmentOut],
    summary="Integration",

)
def list_my_course_assessments(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.is_active.is_(True),
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course.",
        )

    rows = (
        db.query(AssessmentSession, AssessmentConfig)
        .join(AssessmentConfig, AssessmentConfig.id == AssessmentSession.assessment_config_id)
        .filter(
            AssessmentSession.course_id == course_id,
            AssessmentSession.student_id == current_user.id,
        )
        .order_by(AssessmentConfig.created_at.desc())
        .all()
    )


    items = [
        StudentCourseAssessmentOut(
            assessment_config_id=config.id,
            session_id=session.id,
            session_status=session.status,
            title=config.title,
            instructions=config.instructions,
            total_time_minutes=config.total_time_minutes,
            max_main_questions=config.max_main_questions,
            max_followups_per_main=config.max_followups_per_main,
            open_at=config.open_at,
            close_at=config.close_at,
        )
        for session, config in rows
    ]

    return items



@router.post(
    "/assessments/{assessment_config_id}/sessions/start",
    response_model=SessionStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Integration",
)
def start_session(
    assessment_config_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == assessment_config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    if config.status != "published":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This assessment is not currently published.",
        )

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

    session = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.assessment_config_id == assessment_config_id,
            AssessmentSession.student_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No session found for this assessment. It may not have been released yet.",
        )
    

    if session.status == "not_started":
        expires_at = now + timedelta(minutes=config.total_time_minutes)
        session.status = "in_progress"
        session.started_at = now
        session.started_by = current_user.id
        session.expires_at = expires_at
        db.flush()

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
            expires_at=session.expires_at,
            first_question=SessionQuestionItemOut.model_validate(item),
            max_main_questions=config.max_main_questions,
            max_followups_per_main=config.max_followups_per_main,
        )
    
    if session.status == "in_progress":
        # if session.expires_at and now > session.expires_at:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Your session has expired.",
        #     )

        current_item = (
            db.query(SessionQuestionItem)
            .outerjoin(
                TranscriptMessage,
                and_(
                    TranscriptMessage.session_question_item_id == SessionQuestionItem.id,
                    TranscriptMessage.sender_role == "student",
                ),
            )
            .filter(SessionQuestionItem.session_id == session.id)
            .filter(TranscriptMessage.id.is_(None))
            .order_by(
                SessionQuestionItem.main_group_no.asc(),
                SessionQuestionItem.followup_no.asc().nullsfirst(),
            )
            .first()
        )

        return SessionStartResponse(
            session_id=session.id,
            assessment_title=config.title,
            total_time_minutes=config.total_time_minutes,
            expires_at=session.expires_at,
            current_question=(
                SessionQuestionItemOut.model_validate(current_item)
                if current_item
                else None
            ),
            can_complete=current_item is None,
            max_main_questions=config.max_main_questions,
            max_followups_per_main=config.max_followups_per_main,
        )
    
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This session has already been submitted or completed.",
    )


   




@router.post(
    "/sessions/{session_id}/respond",
    response_model=StudentResponseResponse,
    summary="Integration",
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
    # now = datetime.now(timezone.utc)
    # if session.expires_at and now > session.expires_at:
    #     # If expired now, auto-submit/finalize
    #     session.status = "time_expired"
    #     session.ended_at = now
    #     session.transcript_locked = True
    #     session.total_messages = (
    #         db.query(TranscriptMessage)
    #         .filter(TranscriptMessage.session_id == session_id)
    #         .count()
    #     )
    #     db.commit()
    #     db.refresh(session)

    #     return StudentResponseResponse(
    #         message_saved=None,
    #         next_question=None,
    #         session_status="time_expired",
    #         time_remaining_seconds=0,
    #     )

    config = (
        db.query(AssessmentConfig)
        .filter(AssessmentConfig.id == session.assessment_config_id)
        .first()
    )

    # Per-question time limit enforcement
    # If per_question_time_limit_minutes is configured, check the time elapsed
    # since the most recent assistant question was asked.
    # if config and config.per_question_time_limit_minutes:
    #     time_limit_seconds = config.per_question_time_limit_minutes * 60

    #     last_question_msg = (
    #         db.query(TranscriptMessage)
    #         .filter(
    #             TranscriptMessage.session_id == session_id,
    #             TranscriptMessage.sender_role == "assistant",
    #         )
    #         .order_by(TranscriptMessage.sequence_no.desc())
    #         .first()
    #     )

    #     if last_question_msg:
    #         elapsed = (now - last_question_msg.created_at.replace(tzinfo=timezone.utc)).total_seconds()
    #         if elapsed > time_limit_seconds:
    #             raise HTTPException(
    #                 status_code=status.HTTP_403_FORBIDDEN,
    #                 detail=(
    #                     f"Per-question time limit of {config.per_question_time_limit_minutes} minutes exceeded "
    #                     f"({int(elapsed)} seconds elapsed). The question has been skipped."
    #                 ),
    #             )

    # Determine next sequence number
    last_msg = (
        db.query(TranscriptMessage)
        .filter(TranscriptMessage.session_id == session_id)
        .order_by(TranscriptMessage.sequence_no.desc())
        .first()
    )
    next_seq = (last_msg.sequence_no + 1) if last_msg else 1

    # Find the question item this answer responds to
    last_question_item = (
        db.query(SessionQuestionItem)
        .filter(SessionQuestionItem.session_id == session_id)
        .order_by(SessionQuestionItem.asked_at.desc())
        .first()
    )

    # Persist the student's answer
    answer_msg = TranscriptMessage(
        session_id=session_id,
        session_question_item_id=last_question_item.id if last_question_item else None,
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

    last_question_item = (
        db.query(SessionQuestionItem)
        .filter(SessionQuestionItem.session_id == session_id)
        .order_by(SessionQuestionItem.asked_at.desc())
        .first()
    )

    max_main = config.max_main_questions if config else 0
    max_followups = config.max_followups_per_main if config else 0
    followup_enabled = config.followup_enabled if config else False

    if not last_question_item:
        current_main = 1
        current_followup = 0
    else:
        current_main = last_question_item.main_group_no or 1
        current_followup = (
            last_question_item.followup_no or 0
            if last_question_item.question_kind == "followup"
            else 0
        )

    if followup_enabled and current_followup < max_followups:
        followup_text = await _generate_ai_followup(
            db=db,
            session=session,
            current_followup=current_followup,
        )

        item = SessionQuestionItem(
            session_id=session_id,
            source_question_id=None,
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

        next_question_item = item

    elif current_main < max_main:
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

            next_question_item = item
        else:
            logger.info(
                "Session %s: question pool exhausted at main %d",
                session_id,
                next_main_no,
        )
    else:
        logger.info("Session %s: all %d main questions answered", session_id, max_main)

    db.commit()
    db.refresh(answer_msg)
    db.refresh(session)
    if next_question_item:
        db.refresh(next_question_item)

    # time_remaining = (
    #     max(0, int((session.expires_at - now).total_seconds()))
    #     if session.expires_at else 0
    # )

    return StudentResponseResponse(
        message_saved=StudentSavedMessageOut.model_validate(answer_msg),
        next_question=(
            StudentNextQuestionOut.model_validate(next_question_item)
            if next_question_item else None
        ),
        session_status=session.status,
    )




@router.post(
    "/sessions/{session_id}/complete",
    summary="Integration",

)
def complete_session(
    session_id: UUID,
    background_tasks: BackgroundTasks,
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

    background_tasks.add_task(_run_ai_summary_background, session_id)

    return session