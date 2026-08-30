from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# Question

class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_pool_id: UUID
    question_text: str
    question_index: int
    generation_provenance: dict | None = None


class SupportingContextItemOut(BaseModel):
    material_id: UUID
    material_filename: str
    chunk_id: UUID
    chunk_index: int
    text: str


class QuestionSupportingContextOut(BaseModel):
    source_material_ids: list[UUID]
    source_chunk_ids: list[UUID]
    model: str | None = None
    generated_at: str | None = None
    prompt_version: str | None = None
    contexts: list[SupportingContextItemOut]

class QuestionUpdate(BaseModel):
    question_text: str | None = None


class QuestionCreate(BaseModel):
    question_text: str = Field(min_length=1)


# Question generation

class QuestionGenerationRequest(BaseModel):
    material_ids: list[UUID] = Field(min_length=1, max_length=5)
    rubric_id: UUID
    assessment_title: str
    total_time_minutes: int
    buffer_time_minutes: int = Field(default=0, ge=0, le=30)
    num_main_questions: int
    max_followups_per_main: int = 1
    release_time: datetime | None = None
    due_time: datetime | None = None

class QuestionGenerationResponse(BaseModel):
    assessment_config: UUID
    questions: list[QuestionOut]

