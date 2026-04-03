"""Pydantic schemas for course management API."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.enums import CourseRole
from app.schemas.user import UserBrief


class CourseCreate(BaseModel):
    """POST /courses — create a new course."""
    course_code: str | None = None
    course_name: str
    term: str | None = None
    description: str | None = None


class CourseUpdate(BaseModel):
    """PUT /courses/:id — update course metadata."""
    course_code: str | None = None
    course_name: str | None = None
    term: str | None = None
    description: str | None = None


class CourseOut(BaseModel):
    """Response shape for GET /courses and GET /courses/:id."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_code: str | None
    course_name: str | None
    term: str | None
    description: str | None
    created_by: UUID | None
    created_at: datetime | None
    updated_at: datetime | None


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
    course_role: CourseRole

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
    course_role: CourseRole
    is_active: bool
    enrolled_at: datetime


class StudentListItem(BaseModel):
    """Single item in GET /courses/:id/students response."""
    model_config = ConfigDict(from_attributes=True)

    enrollment_id: UUID
    user: UserBrief
    course_role: CourseRole
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
