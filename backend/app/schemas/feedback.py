from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


#  AI summary

class AISummaryInfoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    suggested_grade: int | None = None
    summary_text: str | None = None


# Grade / review updates

class GradeUpdate(BaseModel):
    grade: int = Field(ge=0, le=100)

class InstructorReviewUpdate(BaseModel):
    final_grade: int = Field(ge=0, le=100)
    comments: str | None = None


# Release review

class ReleaseReview(BaseModel):
    session_id: UUID
    student_id: UUID

class ReleaseAllReviews(BaseModel):
    assessments: list[ReleaseReview]


# Approve AI grade

class ApproveAiReview(BaseModel):
    session_id: UUID

class ApproveAllAiReviews(BaseModel):
    assessments: list[ApproveAiReview]