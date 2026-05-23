from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import UserRole


# Course

# Term format: "YYYYS1" or "YYYYS2" (4-digit year + semester).
TERM_PATTERN = r"^20\d{2}S[12]$"


class CourseInfoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_code: str

class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_code: str
    course_name: str
    term: str
    description: str

class CourseCreate(BaseModel):
    course_code: str
    course_name: str
    term: str = Field(pattern=TERM_PATTERN)
    description: str


#  Instructor dashboard

class InstructorDashboardStudentRow(BaseModel):
    session_id: UUID
    student_id: UUID
    student_name: str
    student_email: str
    student_image: str | None = None
    ai_suggested_score: int | None = None
    ai_summary: str | None = None
    final_grade: int | None = None
    status: str

class InstructorDashboardAssessmentOut(BaseModel):
    course_code: str
    course_name: str
    assessment_config_id: UUID
    assessment_title: str
    published_average_score: float | None = None
    ai_average_score: float | None = None
    submitted_count: int
    total_students: int
    students: list[InstructorDashboardStudentRow]
    

class EnrolledUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str | None = None
    upi: str
    role: UserRole | None = None


# Course join requests

class JoinRequestOut(BaseModel):
    id: UUID
    course_id: UUID
    course_code: str
    course_name: str
    term: str
    status: str
    requester_full_name: str
    requester_upi: str
    created_at: datetime


class JoinRequestsListOut(BaseModel):
    pending_for_review: list[JoinRequestOut]
    my_pending: list[JoinRequestOut]
    my_results: list[JoinRequestOut]