from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Question

class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_pool_id: UUID
    question_text: str
    question_index: int

class QuestionUpdate(BaseModel):
    question_text: str | None = None


# Question generation

class QuestionGenerationRequest(BaseModel):
    material_id: UUID
    rubric_id: UUID
    assessment_title: str
    total_time_minutes: int
    num_main_questions: int
    max_followups_per_main: int = 1

class QuestionGenerationResponse(BaseModel):
    assessment_config: UUID
    questions: list[QuestionOut]