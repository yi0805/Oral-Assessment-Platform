from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator




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
    description: str



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



# delete 231`3`
class CourseUpdate(BaseModel):
    """PUT /courses/:id — update course metadata."""
    course_code: str | None = None
    course_name: str | None = None
    term: str | None = None
    description: str | None = None




class CourseBrief(BaseModel):
    """Minimal course info for lists and embedded references."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_code: str | None
    course_name: str
    term: str | None


class EnrollmentCreate(BaseModel):
    """POST /courses/:id/enroll — enroll a user in a course."""
    user_id: UUID = Field(..., description="UUID of the user to enroll. Required.")
    # course_role: CourseRole

    @field_validator("user_id", mode="before")
    @classmethod
    def user_id_required(cls, v):
        if v is None or v == "":
            raise ValueError("user_id is required.")
        return v


class EnrollmentOut(BaseModel):
    """Response shape for enrollment records."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    user_id: UUID
    # course_role: CourseRole
    is_active: bool
    enrolled_at: datetime


class StudentListItem(BaseModel):
    """Single item in GET /courses/:id/students response."""
    model_config = ConfigDict(from_attributes=True)

    enrollment_id: UUID
    # user: UserBrief
    # course_role: CourseRole
    is_active: bool
    enrolled_at: datetime


class BulkEnrollResult(BaseModel):
    """
    Summary returned by POST /courses/:id/students/import-csv.

    users_created:    New User records created (first time we've seen this email).
    users_found:      Emails already in the users table.
    enrolled:         Users newly enrolled in this course.
    already_enrolled: Users who were already enrolled (skipped, no duplicate).
    errors:           Rows that could not be processed, with a reason per row.
    """
    users_created: int
    users_found: int
    enrolled: int
    already_enrolled: int
    errors: list[dict]
