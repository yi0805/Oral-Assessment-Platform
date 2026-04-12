from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from course import CourseInfoOut
from feedback import AISummaryInfoOut


class ReleaseResponse(BaseModel):
    sessions_created: int

class AssessmentConfigInfoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    title: str
    description: str | None = None
    material_r_id: UUID
    total_time_minute: int
    main_question_num: int
    follow_up_num: int
    release_time: datetime | None = None
    due_time: datetime | None = None
    status: str


class AssessmentHistoryItemOut(BaseModel):
    session_id: UUID
    assessment_config_id: UUID
    assessment_title: str
    final_grade: int
    instructor_name: str
    instructor_image: str | None = None
    comments: str | None = None


class AssessmentHistoryOut(BaseModel):
    course_code: str | None = None
    course_name: str
    class_average_grade: float | None = None
    items: list[AssessmentHistoryItemOut]

class AssessmentTitleOut(BaseModel):
    title: str

class SessionFeedbackOut(BaseModel):
    final_grade: int | None = None
    comments: str | None = None

class SessionInfoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assessment_config_id: UUID
    user_s_id: UUID
    status: str

class PendingReviewOut(BaseModel):
    session: SessionInfoOut
    assessment_config: AssessmentConfigInfoOut
    course: CourseInfoOut
    aisummary: AISummaryInfoOut | None
    session_feedback: SessionFeedbackOut | None

class StudentInfoOut(BaseModel):
    full_name: str
    email: str | None = None
    image: str | None = None

class TranscriptMessageOut(BaseModel):
    sequence_no: int
    message_type: str
    content: str

class TranscriptDetailOut(BaseModel):
    session_id: UUID
    student: StudentInfoOut
    assessment: AssessmentTitleOut
    ai_summary: AISummaryInfoOut | None = None
    session_feedback: SessionFeedbackOut | None = None
    transcript: list[TranscriptMessageOut]

class StudentCourseAssessmentOut(BaseModel):
    assessment_config_id: UUID
    session_id: UUID
    session_status: str
    title: str
    description: str | None = None
    total_time_minute: int
    main_question_num: int | None = None
    follow_up_num: int | None = None
    release_time: datetime | None = None
    due_time: datetime | None = None

class StudentSavedMessageOut(BaseModel):
    sequence_no: int
    message_type: str
    content: str

class StudentNextQuestionOut(BaseModel):
    id: UUID
    question_text: str
    question_kind: str
    main_group_no: int
    followup_no: int

class StudentResponseRequest(BaseModel):
    answer_text: str

class StudentResponseResponse(BaseModel):
    message_saved: StudentSavedMessageOut
    next_question: StudentNextQuestionOut | None = None
    session_status: str

class SessionStartResponse(BaseModel):
    session_id: UUID
    assessment_title: str
    total_time_minute: int
    main_question_num: int
    follow_up_num: int
