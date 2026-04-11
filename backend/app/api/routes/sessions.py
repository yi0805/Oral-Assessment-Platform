from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_student
from app.models.assessment import AssessmentConfig, AssessmentSession
from app.models.course import CourseEnrollment, Course
from app.models.feedback import AISummary, SessionFeedback
from app.models.question import Question
from app.models.session_runtime import SessionQuestionItem, TranscriptMessage
from app.models.user import User
# from app.schemas.assessment import (
#     SessionOut,
#     SessionQuestionItemOut,
#     SessionStartResponse,
#     StudentResponseRequest,
#     StudentResponseResponse,
#     AssessmentConfigOut
# )
from app.schemas import *

from pydantic import BaseModel, ConfigDict, model_validator
# from app.schemas.feedback import AISummaryOut
# from app.schemas.user import UserOut
# from app.schemas.course import CourseOut
from app.schemas.enums import SessionStatus

router = APIRouter()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_code: str
    course_name: str 
    term: str
    description: str

class AISummaryOut(BaseModel):
    """
    AI-generated advisory analysis returned by GET /sessions/:id/ai-summary.
    Per the user flow (Phase 5), the summary must be:
    - Evidence-based (short quotes from transcript)
    - Rubric-linked (evaluates against the rubric)
    - Strengths and gaps clearly identified
    - Advisory only (suggested numeric score, never auto-assigned)
    """
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    session_id: UUID
    summary_text: str
    strengths: str | None
    gaps: str | None
    evidence_refs: list | None
    suggested_grade: int | None
    model_name: str
    advisory_only: bool
    status: str
    error_message: str | None
    generated_at: datetime


class AssessmentConfigBase(BaseModel):
    """
    Base model for assessments containing core fields and automated validation logic.
    
    Subclasses (Request/Response models) should inherit from this class to reuse 
    common fields and avoid code duplication.
    """
    title: str
    instructions: str | None = None
    assessment_mode: AssessmentMode = AssessmentMode.generic
    material_r_id: UUID | None = None
    total_time_minute: int = 15
    # per_question_time_limit_minutes: int | None = None
    main_questions_num: int = 3
    follow_up_num: int = 1
    open_at: datetime | None = None
    close_at: datetime | None = None

    @model_validator(mode="after")
    def validate_assessment_logic(self):
        # if self.per_question_time_limit_minutes is None:
        #     if self.main_question_num > 0:
        #         self.per_question_time_limit_minutes = max(
        #             3, # at least 3 minutes per question
        #             self.total_time_minutes // self.max_main_questions
        #         )
        #     else:
        #         self.per_question_time_limit_minutes = self.total_time_minutes

        if self.open_at and self.close_at and self.close_at <= self.open_at:
            raise ValueError("close_at must be after open_at")

        return self


class SessionOut(BaseModel):
    """Full session details for GET /sessions/:id (instructor review)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assessment_config_id: UUID
    course_id: UUID
    student_id: UUID
    status: SessionStatus
    started_at: datetime | None
    expires_at: datetime | None
    ended_at: datetime | None
    total_messages: int | None
    current_main_index: int | None
    current_followup_index: int | None
    transcript_locked: bool
    released_at: datetime | None
    created_at: datetime
    updated_at: datetime

class SessionQuestionItemOut(BaseModel):
    """A question that was actually asked during a live session."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    source_question_id: UUID | None
    parent_item_id: UUID | None
    asked_text: str
    question_kind: QuestionKind
    main_group_no: int | None
    followup_no: int | None
    generated_by: GeneratedBy
    asked_at: datetime
    is_answered: bool

class StudentResponseRequest(BaseModel):
    """POST /sessions/:id/respond — student submits their answer."""
    answer_text: str

class AssessmentConfigOut(AssessmentConfigBase):
    """Response shape for assessment configuration."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    question_pool_id: UUID | None
    title: str
    description: str | None
    assessment_mode: AssessmentMode
    material_r_id: UUID | None
    total_time_minutes: int
    per_question_time_limit_minutes: int | None
    main_question_num: int | None
    follow_up_num: int | None
    followup_enabled: bool
    open_at: datetime | None
    close_at: datetime | None
    status: AssessmentStatus
    published_by: UUID | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

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


class PendingReviewOut(BaseModel):
    session: SessionOut 
    assessment_config: AssessmentConfigOut
    # user:  UserOut
    course: CourseOut 
    aisummary: AISummaryOut | None
    session_feedback: SessionFeedbackOut | None

class StudentInfoOut(BaseModel):
    full_name: str
    email: str | None = None
    image: str | None = None

class AssessmentInfoOut(BaseModel):
    title: str

class AISummaryInfoOut(BaseModel):
    suggested_grade: int | None = None
    summary_text: str | None = None

class SessionFeedbackOut(BaseModel):
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
    session_feedback: SessionFeedbackOut | None = None
    transcript: list[TranscriptMessageOut]


class StudentCourseAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assessment_config_id: UUID
    session_id: UUID
    session_status: SessionStatus
    title: str
    description: str | None = None
    total_time_minutes: int
    main_questions_num: int | None = None
    follow_up_num: int | None = None
    release_time: datetime | None = None
    due_time: datetime | None = None

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
    main_question_num: int
    follow_up_num: int


class AssessmentHistoryItemOut(BaseModel):
    session_id: UUID
    assessment_config_id: UUID
    assessment_title: str
    submitted_at: datetime | None = None
    weight_percent: float | None = None
    final_grade: int
    instructor_name: str
    instructor_image: str | None = None
    instructor_department: str | None = None
    comments: str | None = None


class AssessmentHistoryOut(BaseModel):
    course_code: str | None = None
    course_name: str
    class_average_grade: float | None = None
    items: list[AssessmentHistoryItemOut]


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
        db.query(AssessmentSession, AssessmentConfig, User, Course, AISummary, SessionFeedback)
        .join(
            CourseEnrollment,
            CourseEnrollment.course_id == AssessmentSession.course_id,
        )
        .join(
            User,
            User.id == AssessmentSession.user_s_id,
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
        .outerjoin(SessionFeedback, SessionFeedback.session_id == AssessmentSession.id)
        .filter(CourseEnrollment.user_id == current_user.id)
        .filter(CourseEnrollment.course_role == "instructor")
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
            "instructor_feedback": instructor_feedback,
        }
        for session, assessment_config, user, course, ai_summary, instructor_feedback in pendingReviews
    ]

@router.get("/transcript/{session_id}", response_model=TranscriptDetailOut, summary="Integration",)
def get_transcript_detail(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    generalInfo = (
        db.query(AssessmentSession, User, AssessmentConfig, AISummary, SessionFeedback)
        .join(User, User.id == AssessmentSession.student_id)
        .join(AssessmentConfig, AssessmentConfig.id == AssessmentSession.assessment_config_id)
        .outerjoin(AISummary, AISummary.session_id == AssessmentSession.id)
        .outerjoin(SessionFeedback, SessionFeedback.session_id == AssessmentSession.id)
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
            AssessmentSession.user_s_id == current_user.id,
            AssessmentSession.status.in_(["not_started", "in_progress"]),
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
            AssessmentSession.course_id == course_id,
            AssessmentSession.student_id == current_user.id,
            AssessmentSession.status == "released",
            SessionFeedback.final_grade.isnot(None),
        )
        .order_by(
            func.coalesce(AssessmentSession.ended_at, SessionFeedback.released_at).desc()
        )
        .all()
    )

    items = [
        AssessmentHistoryItemOut(
            session_id=session.id,
            assessment_config_id=config.id,
            assessment_title=config.title,
            submitted_at=session.ended_at or feedback.released_at,
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
        .filter(
            AssessmentSession.course_id == course_id,
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
        # expires_at = now + timedelta(minutes=config.total_time_minutes)
        session.status = "in_progress"
        # session.started_at = now
        # session.expires_at = expires_at
        db.flush()

        first_question = (
            db.query(Question)
            .filter(
                Question.question_pool_id == config.question_pool_id,
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
            main_question_num=config.main_question_num,
            follow_up_num=config.follow_up_num,
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
            # expires_at=session.expires_at,
            current_question=(
                SessionQuestionItemOut.model_validate(current_item)
                if current_item
                else None
            ),
            can_complete=current_item is None,
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

    max_main = config.main_question_num if config else 0
    max_followups = config.follow_up_num if config else 0
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