"""Pydantic schemas for question pool and individual question API."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.enums import QuestionKind, AnswerStyle, Difficulty, PoolStatus
from app.schemas.assessment import AssessmentConfigBase
from typing import Optional


class QuestionCreate(BaseModel):
    """POST /question-pools/:id/questions — add a custom question to a pool."""
    question_text: str
    question_kind: QuestionKind
    answer_style: AnswerStyle
    # NOTE: difficulty is not used in assessments — leave as None.
    difficulty: Difficulty | None = Field(
        default=None,
        description="Difficulty level — optional, not used in current assessments. Leave null.",
        examples=[None],
    )
    learning_objective: str | None = None
    display_order: int | None = None
    # NOTE: parent_question_id MUST be null for main questions.
    # Only set this when adding a pre-defined follow-up question (rare).
    parent_question_id: UUID | None = Field(
        default=None,
        description=(
            "Leave null for main questions. "
            "Only set when explicitly linking a pre-defined follow-up to its parent."
        ),
        examples=[None],
    )


class QuestionUpdate(BaseModel):
    """PUT /questions/:id — edit an existing question."""
    question_text: str | None = None
    question_kind: QuestionKind | None = None
    answer_style: AnswerStyle | None = None
    difficulty: Difficulty | None = None
    learning_objective: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


class QuestionOut(BaseModel):
    """Individual question response shape."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_pool_id: UUID
    parent_question_id: UUID | None
    question_text: str
    question_kind: QuestionKind
    answer_style: AnswerStyle
    difficulty: Difficulty | None
    learning_objective: str | None
    source_chunk_refs: list | None
    display_order: int | None
    is_active: bool
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class QuestionPoolCreate(BaseModel):
    """POST /courses/:id/question-pools — create a new question pool."""
    title: str
    description: str | None = None
    generation_method: str = "manual"


class QuestionPoolGenerateRequest(BaseModel):
    """POST /question-pools/:id/generate — trigger AI question generation.

    Only main questions are generated here. Follow-up questions are generated
    dynamically during the student's session based on their actual answers.
    """
    material_ids: list[UUID]
    rubric_id: UUID | None = None
    num_main_questions: int = 3


class QuestionPoolOut(BaseModel):
    """Full pool with nested list of questions."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    title: str
    description: str | None
    generated_from_materials: list | None
    generation_method: str
    created_by: UUID
    approved_by: UUID | None
    status: PoolStatus
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    questions: list[QuestionOut] = []


class QuestionPoolBrief(BaseModel):
    """Minimal pool info for selection lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    status: PoolStatus
    generation_method: str
    created_at: datetime

class PublishAsAssessmentRequest(AssessmentConfigBase):
    """POST /question-pools/{pool_id}/publish-as-assessment"""
    pass