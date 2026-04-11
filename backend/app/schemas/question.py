"""Pydantic schemas for question pool and individual question API."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.enums import QuestionKind, AnswerStyle, Difficulty, PoolStatus

from typing import Optional


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