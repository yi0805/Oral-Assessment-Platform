from uuid import UUID
from pydantic import BaseModel, Field


class ReleaseReview(BaseModel):
    session_id: UUID
    student_id: UUID

class ReleaseAllReviews(BaseModel):
    assessments: list[ReleaseReview]

class GradeUpdate(BaseModel):
    grade: int = Field(ge=0, le=100)

class InstructorReviewUpdate(BaseModel):
    final_grade: int = Field(ge=0, le=100)
    comments: str | None = None

class AISummaryInfoOut(BaseModel):
    suggested_grade: int | None = None
    summary_text: str | None = None