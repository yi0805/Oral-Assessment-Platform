from uuid import UUID

from pydantic import BaseModel, RootModel, ConfigDict, Field, field_validator
from typing import Dict


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

class CriterionFeedback(BaseModel):
    feedback: str = Field(min_length=1)
    suggested_points: int = Field(ge=0, le=100)

    @field_validator("suggested_points", mode="before")
    @classmethod
    def _coerce_grade(cls, v: object) -> int:
        if v is None:
            return 0
        
        try:
            grade = int(v)

        except (TypeError, ValueError):
            return 0
        
        return max(0, min(100, grade))

class _SummaryLLMOutput(RootModel):
    root: Dict[str, CriterionFeedback]

#  AI summary

class AISummaryInfoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    suggested_grade: int | None = None
    detailed_feedback: Dict[str, CriterionFeedback]