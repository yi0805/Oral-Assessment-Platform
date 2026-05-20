from uuid import UUID

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.schemas import CourseInfoOut, AISummaryInfoOut


# Shared / common

class StudentInfoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str
    email: str | None = None
    image: str | None = None

class AssessmentTitleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str

class SessionFeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    final_grade: int | None = None
    comments: str | None = None


# Assessment config

class AssessmentConfigInfoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str


class AssessmentConfigDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    total_time_minute: int
    buffer_time_minute: int
    main_question_num: int
    release_time: datetime | None = None
    due_time: datetime | None = None
    status: str


class AssessmentConfigUpdate(BaseModel):
    title: str | None = None
    total_time_minute: int | None = None
    buffer_time_minute: int | None = Field(default=None, ge=0, le=30)
    main_question_num: int | None = None
    release_time: datetime | None = None
    due_time: datetime | None = None


class AssessmentConfigSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    status: str
    total_time_minute: int
    main_question_num: int
    release_time: datetime | None = None
    due_time: datetime | None = None


class ReleaseResponse(BaseModel):
    sessions_created: int


class AssessmentCopyRequest(BaseModel):
    target_course_id: UUID
    title: str | None = None


# Session

class SessionInfoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_s_id: UUID

class SessionStartResponse(BaseModel):
    session_id: UUID
    assessment_title: str
    main_question_num: int
    follow_up_num: int
    expires_at: datetime | None = None
    current_question: "StudentNextQuestionOut | None" = None
    can_complete: bool = False


# Student — assessment view

class StudentCourseAssessmentOut(BaseModel):
    assessment_config_id: UUID
    title: str
    description: str | None = None
    total_time_minute: int
    main_question_num: int | None = None
    follow_up_num: int | None = None
    due_time: datetime | None = None
    status: str
    completed_at: datetime | None = None

class StudentNextQuestionOut(BaseModel):
    question_text: str
    question_kind: str
    main_group_no: int
    followup_no: int

class StudentResponseRequest(BaseModel):
    answer_text: str

class StudentResponseResponse(BaseModel):
    next_question: StudentNextQuestionOut | None = None

class AudioTranscriptionResponse(BaseModel):
    """Issue #71 — transcript-only result for the edit-before-submit flow.

    Returned by the transcribe-audio endpoint. The transcript is NOT
    persisted to the database; the client populates it into the answer
    input and submits separately via the standard text response endpoint.
    """
    transcript: str

# Assessment history

class AssessmentHistoryItemOut(BaseModel):
    session_id: UUID
    assessment_title: str
    final_grade: int
    instructor_name: str
    instructor_image: str | None = None
    comments: str | None = None
    submitted_at: datetime | None = None

class AssessmentHistoryOut(BaseModel):
    class_average_grade: float | None = None
    items: list[AssessmentHistoryItemOut]


# Review / transcript (instructor-facing)

class PendingReviewOut(BaseModel):
    session: SessionInfoOut
    user: StudentInfoOut
    assessment_config: AssessmentConfigInfoOut
    course: CourseInfoOut
    aisummary: AISummaryInfoOut | None
    session_feedback: SessionFeedbackOut | None

class TranscriptMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sequence_no: int
    message_type: str
    content: str

class TranscriptDetailOut(BaseModel):
    student: StudentInfoOut
    assessment: AssessmentTitleOut
    ai_summary: AISummaryInfoOut | None = None
    session_feedback: SessionFeedbackOut | None = None
    blur_count: int | None = None
    disconnect_count: int | None = None
    resume_count: int | None = None
    transcript: list[TranscriptMessageOut]

class BlurNotificationRequest(BaseModel):
    blur_count: int

class ReconnectNotificationRequest(BaseModel):
    disconnect_count: int = Field(ge=0)

class InstructorNotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    session_id: UUID
    blur_count: int
    disconnect_count: int
    resume_count: int
    course_code: str
    course_name: str
    assessment_title: str
    student_name: str
