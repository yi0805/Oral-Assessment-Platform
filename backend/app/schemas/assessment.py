"""Pydantic schemas for assessment configuration and runtime session APIs."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import AssessmentMode, AssessmentStatus, SessionStatus


class AssessmentConfigBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    instructions: Optional[str] = None
    assessment_mode: AssessmentMode = AssessmentMode.generic
    rubric_id: Optional[UUID] = None
    question_pool_id: Optional[UUID] = None
    total_time_minutes: int = Field(default=15, ge=1)
    per_question_time_limit_seconds: Optional[int] = Field(default=None, ge=1)
    max_followups_per_main: int = Field(default=3, ge=0)
    followup_enabled: bool = True
    open_at: Optional[datetime] = None
    close_at: Optional[datetime] = None


class AssessmentConfigCreate(AssessmentConfigBase):
    pass


class AssessmentConfigUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    instructions: Optional[str] = None
    assessment_mode: Optional[AssessmentMode] = None
    rubric_id: Optional[UUID] = None
    question_pool_id: Optional[UUID] = None
    total_time_minutes: Optional[int] = Field(default=None, ge=1)
    per_question_time_limit_seconds: Optional[int] = Field(default=None, ge=1)
    max_followups_per_main: Optional[int] = Field(default=None, ge=0)
    followup_enabled: Optional[bool] = None
    open_at: Optional[datetime] = None
    close_at: Optional[datetime] = None
    status: Optional[AssessmentStatus] = None


class AssessmentConfigOut(AssessmentConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    status: AssessmentStatus
    published_by: Optional[UUID] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SessionStartResponse(BaseModel):
    session_id: UUID
    expires_at: Optional[datetime] = None
    first_question: Optional[str] = None
    status: SessionStatus = SessionStatus.in_progress


class StudentResponseRequest(BaseModel):
    answer_text: str = Field(..., min_length=1)


class StudentResponseResponse(BaseModel):
    message_saved: bool = True
    next_question: Optional[str] = None
    status: SessionStatus
    time_remaining_seconds: Optional[int] = None
