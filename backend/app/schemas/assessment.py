from uuid import UUID

from datetime import datetime
from pydantic import BaseModel, ConfigDict

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

class ReleaseResponse(BaseModel):
    sessions_created: int


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

class StudentNextQuestionOut(BaseModel):
    question_text: str
    question_kind: str
    main_group_no: int
    followup_no: int

class StudentResponseRequest(BaseModel):
    answer_text: str

class StudentResponseResponse(BaseModel):
    next_question: StudentNextQuestionOut | None = None

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
    transcript: list[TranscriptMessageOut]