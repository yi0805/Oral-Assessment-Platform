"""
Pydantic schemas for assessment configuration, session lifecycle, and chat interaction.

User flow alignment:
- main_question_num and follow_up_num are REQUIRED in ConfigCreate
  because the instructor must set these per the user flow (Phase 3: Configure Settings).
  There is no hardcoded default — the "e.g. 3 Main Questions" in the user flow
  is an example, not a fixed value.
"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator
from app.schemas.enums import (
    AssessmentMode, AssessmentStatus, SessionStatus,
    QuestionKind, GeneratedBy, SenderRole, MessageType,
)
    
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


# ---- Assessment Config ----

class AssessmentConfigCreate(AssessmentConfigBase):
    """POST /courses/:id/assessments — instructor creates a new assessment."""
    question_pool_id: UUID | None = None
    assessment_mode: AssessmentMode = AssessmentMode.generic

    @model_validator(mode="after")
    def validate_create_logic(self):
        if self.assessment_mode == AssessmentMode.generic and self.question_pool_id is None:
            raise ValueError("question_pool_id is required for generic mode")
        return self


class AssessmentConfigUpdate(BaseModel):
    """PUT /assessments/:id — update assessment settings before publishing."""
    title: str | None = None
    instructions: str | None = None
    assessment_mode: AssessmentMode | None = None
    material_r_id: UUID | None = None
    total_time_minutes: int | None = None
    per_question_time_limit_minutes: int | None = None
    main_question_num: int | None = None
    follow_up_num: int | None = None
    followup_enabled: bool | None = None
    open_at: datetime | None = None
    close_at: datetime | None = None


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


class AssessmentConfigBrief(BaseModel):
    """Minimal assessment info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    assessment_mode: AssessmentMode
    status: AssessmentStatus
    total_time_minutes: int
    main_question_num: int | None
    open_at: datetime | None
    close_at: datetime | None


# ---- Session Lifecycle ----

class SessionStartResponse(BaseModel):
    """Returned by POST /assessments/:id/sessions/start when a student begins."""
    session_id: UUID
    assessment_title: str
    total_time_minutes: int
    expires_at: datetime
    first_question: "SessionQuestionItemOut"
    main_question_num: int
    follow_up_num: int
    


class StudentResponseRequest(BaseModel):
    """POST /sessions/:id/respond — student submits their answer."""
    answer_text: str


class StudentResponseResponse(BaseModel):
    """Returned after a student submits an answer."""
    message_saved: "TranscriptMessageOut | None"
    next_question: "SessionQuestionItemOut | None"
    session_status: SessionStatus
    # time_remaining_seconds: int


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


class SessionBrief(BaseModel):
    """Single item in session lists (instructor dashboard)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    status: SessionStatus
    started_at: datetime | None
    ended_at: datetime | None
    total_messages: int | None
    # Enriched fields for the instructor grading dashboard (populated by the list endpoint)
    student_name: str | None = None
    student_email: str | None = None
    final_grade: int | None = None          # instructor-assigned final grade (if already graded)

class SessionBriefWithAIGrades(SessionBrief):
    ai_suggested_grade: int | None = None

class AssessmentStatsOut(BaseModel):
    """
    GET /assessments/{id}/sessions/stats
    Class-level grade statistics calculated from instructor-assigned final grades.
    Only graded (released) sessions with a numeric final_grade are included.
    Matches the statistics panel shown on the instructor grading dashboard
    (median, average, highest, lowest).
    """
    assessment_id: UUID
    total_sessions: int           # all sessions for the assessment
    graded_count: int             # sessions with a numeric final_grade
    average_grade: float | None   # arithmetic mean
    median_grade: float | None    # median
    highest_grade: float | None   # maximum
    lowest_grade: float | None    # minimum


# ---- Runtime items ----

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


class TranscriptMessageOut(BaseModel):
    """Single message turn in the conversation transcript."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    session_question_item_id: UUID | None
    sender_role: SenderRole
    message_type: MessageType
    sequence_no: int
    content: str
    token_count: int | None
    created_at: datetime


class FullTranscriptOut(BaseModel):
    """Complete session transcript for instructor review or student post-assessment view."""
    session: SessionOut
    question_items: list[SessionQuestionItemOut]
    messages: list[TranscriptMessageOut]
