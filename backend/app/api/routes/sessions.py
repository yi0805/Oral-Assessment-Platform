from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_student
from app.models import (
    User, 
    AssessmentConfig, AssessmentSession, 
    CourseEnrollment, Course, AISummary, Question, 
    SessionQuestionItem, TranscriptMessage, SessionFeedback
)

from app.schemas import (
    AssessmentHistoryItemOut, AssessmentHistoryOut, 
    PendingReviewOut, TranscriptDetailOut, StudentCourseAssessmentOut, StudentSavedMessageOut, StudentNextQuestionOut,
    StudentResponseRequest, StudentResponseResponse, SessionStartResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _normalize_followup(text: str) -> str:
    text = " ".join(text.strip().split())
    text = re.sub(r"^['\"`\-\*\d\.\)\s]+", "", text)

    m = re.search(r".*?\?", text)
    if m:
        text = m.group(0)

    words = text.split()
    if len(words) > 25:
        text = " ".join(words[:25]).rstrip(",.;:") + "?"

    return text


def _get_main_question_by_order(
    db: Session,
    config: AssessmentConfig | None,
    order: int,
) -> Question | None:
    """Return the main question at the given position from the pool."""
    if not config or not config.question_pool:
        return None

    pool_id = config.question_pool.id

    questions = (
        db.query(Question)
        .filter(Question.question_pool_id == pool_id)
        .order_by(Question.question_index.asc())
        .all()
    )

    idx = order - 1
    return questions[idx] if 0 <= idx < len(questions) else None


async def _generate_ai_followup(
    db: Session,
    session: AssessmentSession,
    main_question_text: str | None,
    current_followup: int,
) -> str:
    """
    Generate a context-aware follow-up question using the AI Gateway.
    Falls back to a generic probing question on any AI error.
    """
    from app.services.ai_gateway import chat_complete

    latest_student_msg = (
        db.query(TranscriptMessage)
        .filter(
            TranscriptMessage.session_id == session.id,
            TranscriptMessage.message_type == "student_answer",
        )
        .order_by(TranscriptMessage.sequence_no.desc())
        .first()
    )

    student_answer = latest_student_msg.content if latest_student_msg else ""

    FOLLOWUP_SYSTEM_PROMPT = """
        You are an expert academic assessor conducting an oral exam.
        Your goal is to generate exactly one follow-up question to probe the student's understanding deeply but concisely.

        Rules:
        IDENTIFY: MUST pick one specific technical term or concept from the student's last answer and generate EXACTLY ONE follow-up question.
        NO REPETITION: Do not repeat the current main question or restate the student's answer.
        OUTPUT FORMAT: Output ONLY the question text. Strictly NO quotes, NO JSON, NO preamble and NO explanations.
        CONSTRAINT: The question must be under 25 words.
        """

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
            temperature=0.2,
            max_tokens=1800,
        )

        followup_text = _normalize_followup(result)
        return followup_text.strip().strip('"').strip("'")

    except RuntimeError as exc:
        logger.warning("Follow-up AI generation failed: %s — using fallback", exc)
        fallback_probes = [
            "Can you elaborate further on that point?",
            "What evidence or reasoning supports your answer?",
            "How would this apply in a real-world scenario?",
        ]
        return fallback_probes[current_followup % len(fallback_probes)]


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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/pendingReviews",
    response_model=list[PendingReviewOut],
    summary="Integration",
)
def pending_Reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(AssessmentSession, AssessmentConfig, User, Course, AISummary, SessionFeedback)
        .join(
            AssessmentConfig,
            AssessmentConfig.id == AssessmentSession.assessment_config_id,
        )
        .join(
            CourseEnrollment,
            CourseEnrollment.course_id == AssessmentConfig.course_id,
        )
        .join(
            User,
            User.id == AssessmentSession.user_s_id,
        )
        .join(
            Course,
            Course.id == AssessmentConfig.course_id,
        )
        .outerjoin(
            AISummary,
            AISummary.session_id == AssessmentSession.id,
        )
        .outerjoin(SessionFeedback, SessionFeedback.session_id == AssessmentSession.id)
        .filter(CourseEnrollment.user_id == current_user.id)
        .filter(AssessmentSession.status == "under_review")
        .distinct()
        .all()
    )

    return [
        {
            "session": session,
            "assessment_config": assessment_config,
            "course": course,
            "aisummary": {
                "suggested_grade": ai_summary.suggested_grade,
                "summary_text": ai_summary.summary_text,
            } if ai_summary else None,
            "session_feedback": {
                "final_grade": feedback.final_grade,
                "comments": feedback.comments,
            } if feedback else None,
        }
        for session, assessment_config, user, course, ai_summary, feedback in rows
    ]


@router.get("/transcript/{session_id}", response_model=TranscriptDetailOut, summary="Integration")
def get_transcript_detail(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    general_info = (
        db.query(AssessmentSession, User, AssessmentConfig, AISummary, SessionFeedback)
        .join(User, User.id == AssessmentSession.user_s_id)
        .join(AssessmentConfig, AssessmentConfig.id == AssessmentSession.assessment_config_id)
        .outerjoin(AISummary, AISummary.session_id == AssessmentSession.id)
        .outerjoin(SessionFeedback, SessionFeedback.session_id == AssessmentSession.id)
        .filter(AssessmentSession.id == session_id)
        .first()
    )

    if not general_info:
        raise HTTPException(status_code=404, detail="Transcript not found")

    session_obj, user_obj, assessment_obj, ai_obj, feedback_obj = general_info

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
        "session_feedback": None if not feedback_obj else {
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
            AssessmentConfig.course_id == course_id,
            AssessmentSession.user_s_id == current_user.id,
            AssessmentSession.status.in_(["not_started", "in_progress"]),
        )
        .order_by(AssessmentConfig.release_time.desc())
        .all()
    )

    items = [
        StudentCourseAssessmentOut(
            assessment_config_id=config.id,
            session_id=session.id,
            session_status=session.status,
            title=config.title,
            description=config.description,
            total_time_minute=config.total_time_minute,
            main_question_num=config.main_question_num,
            follow_up_num=config.follow_up_num,
            release_time=config.release_time,
            due_time=config.due_time,
        )
        for session, config in rows
    ]

    return items


@router.get(
    "/courses/{course_id}/my-assessment-history",
    response_model=AssessmentHistoryOut,
    summary="Integration",
)
def get_my_assessment_history(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course.",
        )

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    rows = (
        db.query(AssessmentSession, AssessmentConfig, SessionFeedback, User)
        .join(AssessmentConfig, AssessmentConfig.id == AssessmentSession.assessment_config_id)
        .join(SessionFeedback, SessionFeedback.session_id == AssessmentSession.id)
        .join(User, User.id == SessionFeedback.user_i_id)
        .filter(
            AssessmentConfig.course_id == course_id,
            AssessmentSession.user_s_id == current_user.id,
            AssessmentSession.status == "released",
            SessionFeedback.final_grade.isnot(None),
        )
        .all()
    )

    items = [
        AssessmentHistoryItemOut(
            session_id=session.id,
            assessment_config_id=config.id,
            assessment_title=config.title,
            final_grade=feedback.final_grade,
            instructor_name=instructor.full_name,
            instructor_image=instructor.image,
            comments=feedback.comments,
        )
        for session, config, feedback, instructor in rows
    ]

    class_avg = (
        db.query(func.avg(SessionFeedback.final_grade))
        .join(AssessmentSession, SessionFeedback.session_id == AssessmentSession.id)
        .join(AssessmentConfig, AssessmentConfig.id == AssessmentSession.assessment_config_id)
        .filter(
            AssessmentConfig.course_id == course_id,
            AssessmentSession.status == "released",
            SessionFeedback.final_grade.isnot(None),
        )
        .scalar()
    )

    return AssessmentHistoryOut(
        course_code=course.course_code,
        course_name=course.course_name,
        class_average_grade=round(float(class_avg), 2) if class_avg is not None else None,
        items=items,
    )


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
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in the course for this assessment.",
        )

    now = datetime.now(timezone.utc)

    if config.release_time and now < config.release_time:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Assessment opens at {config.release_time.isoformat()}.",
        )

    if config.due_time and now > config.due_time:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This assessment has closed.",
        )

    session = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.assessment_config_id == assessment_config_id,
            AssessmentSession.user_s_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No session found for this assessment. It may not have been released yet.",
        )

    pool = config.question_pool

    if session.status == "not_started":
        session.status = "in_progress"
        db.flush()

        first_question = None
        if pool:
            first_question = (
                db.query(Question)
                .filter(Question.question_pool_id == pool.id)
                .order_by(Question.question_index.asc())
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
            question_kind="main",
            main_group_no=1,
            followup_no=0,
        )
        db.add(item)
        db.flush()

        msg = TranscriptMessage(
            session_id=session.id,
            session_question_item_id=item.id,
            message_type="main_question",
            sequence_no=1,
            content=first_question.question_text,
        )
        db.add(msg)
        db.commit()

        return SessionStartResponse(
            session_id=session.id,
            assessment_title=config.title,
            total_time_minute=config.total_time_minute,
            main_question_num=config.main_question_num,
            follow_up_num=config.follow_up_num,
        )

    if session.status == "in_progress":
        return SessionStartResponse(
            session_id=session.id,
            assessment_title=config.title,
            total_time_minute=config.total_time_minute,
            main_question_num=config.main_question_num,
            follow_up_num=config.follow_up_num,
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

    if session.user_s_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session.",
        )

    if session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session is not in progress (current status: {session.status}).",
        )

    config = (
        db.query(AssessmentConfig)
        .filter(AssessmentConfig.id == session.assessment_config_id)
        .first()
    )

    last_msg = (
        db.query(TranscriptMessage)
        .filter(TranscriptMessage.session_id == session_id)
        .order_by(TranscriptMessage.sequence_no.desc())
        .first()
    )
    next_seq = (last_msg.sequence_no + 1) if last_msg else 1

    last_question_item = (
        db.query(SessionQuestionItem)
        .filter(SessionQuestionItem.session_id == session_id)
        .order_by(SessionQuestionItem.main_group_no.desc(), SessionQuestionItem.followup_no.desc())
        .first()
    )

    answer_msg = TranscriptMessage(
        session_id=session_id,
        session_question_item_id=last_question_item.id if last_question_item else None,
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
    next_question_text: str | None = None

    max_main = config.main_question_num if config else 0
    max_followups = config.follow_up_num if config else 0
    followup_enabled = max_followups > 0

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

    # Get the current main question text for follow-up context
    main_item = (
        db.query(SessionQuestionItem)
        .filter(
            SessionQuestionItem.session_id == session_id,
            SessionQuestionItem.question_kind == "main",
            SessionQuestionItem.main_group_no == current_main,
        )
        .first()
    )
    main_question_text: str | None = None
    if main_item:
        source_q = db.query(Question).filter(Question.id == main_item.source_question_id).first()
        if source_q:
            main_question_text = source_q.question_text

    if followup_enabled and current_followup < max_followups:
        followup_text = await _generate_ai_followup(
            db=db,
            session=session,
            main_question_text=main_question_text,
            current_followup=current_followup,
        )

        item = SessionQuestionItem(
            session_id=session_id,
            source_question_id=main_item.source_question_id if main_item else last_question_item.source_question_id,
            question_kind="followup",
            main_group_no=current_main,
            followup_no=current_followup + 1,
        )
        db.add(item)
        db.flush()

        followup_msg = TranscriptMessage(
            session_id=session_id,
            session_question_item_id=item.id,
            message_type="followup_question",
            sequence_no=next_seq,
            content=followup_text,
        )
        db.add(followup_msg)

        next_question_item = item
        next_question_text = followup_text

    elif current_main < max_main:
        next_main_no = current_main + 1
        next_q = _get_main_question_by_order(db, config, next_main_no)

        if next_q:
            item = SessionQuestionItem(
                session_id=session_id,
                source_question_id=next_q.id,
                question_kind="main",
                main_group_no=next_main_no,
                followup_no=0,
            )
            db.add(item)
            db.flush()

            main_msg = TranscriptMessage(
                session_id=session_id,
                session_question_item_id=item.id,
                message_type="main_question",
                sequence_no=next_seq,
                content=next_q.question_text,
            )
            db.add(main_msg)

            next_question_item = item
            next_question_text = next_q.question_text
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

    return StudentResponseResponse(
        message_saved=StudentSavedMessageOut(
            sequence_no=answer_msg.sequence_no,
            message_type=answer_msg.message_type,
            content=answer_msg.content,
        ),
        next_question=(
            StudentNextQuestionOut(
                id=next_question_item.id,
                question_text=next_question_text or "",
                question_kind=next_question_item.question_kind,
                main_group_no=next_question_item.main_group_no,
                followup_no=next_question_item.followup_no,
            )
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

    if session.user_s_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session.",
        )

    if session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session cannot be completed from status '{session.status}'.",
        )

    session.status = "under_review"
    db.commit()
    db.refresh(session)

    background_tasks.add_task(_run_ai_summary_background, session_id)

    return {"session_id": str(session.id), "status": session.status}
