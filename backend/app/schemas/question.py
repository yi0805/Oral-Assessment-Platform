"""Pydantic schemas for question pool and individual question API."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.enums import QuestionKind, AnswerStyle, Difficulty, PoolStatus


class QuestionCreate(BaseModel):
    """POST /question-pools/:id/questions — add a custom question to a pool."""
    question_text: str
    question_kind: QuestionKind
    answer_style: AnswerStyle
    difficulty: Difficulty | None = None
    learning_objective: str | None = None
    display_order: int | None = None
    parent_question_id: UUID | None = None


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
    """POST /question-pools/:id/generate — trigger AI question generation."""
    material_ids: list[UUID]
    rubric_id: UUID | None = None
    num_main_questions: int = 3
    num_followups_per_main: int = 2


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
