from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.enums import UserRole


# Course

class CourseInfoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_code: str

class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_code: str
    course_name: str
    description: str

class CourseCreate(BaseModel):
    course_code: str
    course_name: str
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

    full_name: str
    upi: str
    role: UserRole