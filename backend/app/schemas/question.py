"""Pydantic schemas for question pool and individual question API."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class UpdateNowRequest(BaseModel):
    material_id: UUID
    material_r_id: UUID
    assessment_title: str
    total_time_minutes: int 
    num_main_questions: int
    max_followups_per_main: int = 3
    description : str | None = None
    open_at: datetime | None = None
    close_at: datetime | None = None

class QuestionUpdate(BaseModel):
    question_text: str | None = None


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_pool_id: UUID
    question_text: str
    question_index: int


class UpdateNowResponse(BaseModel):
    assessment_config: UUID
    questions: list[QuestionOut]