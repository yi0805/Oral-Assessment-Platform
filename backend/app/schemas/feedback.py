from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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

class _SummaryLLMOutput(BaseModel):
    summary_text: str = Field(min_length=1)
    suggested_grade: int = Field(ge=0, le=100)

    @field_validator("suggested_grade", mode="before")
    @classmethod
    def _coerce_grade(cls, v: object) -> int:
        if v is None:
            return 0
        
        try:
            grade = int(v)

        except (TypeError, ValueError):
            return 0
        
        return max(0, min(100, grade))