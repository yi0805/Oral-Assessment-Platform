"""Pydantic schemas for rubric management API."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RubricCreate(BaseModel):
    """POST /courses/:id/rubrics — create a rubric by text input or file upload."""
    title: str
    description: str | None = None
    rubric_text: str
    original_filename: str | None = None


class RubricUpdate(BaseModel):
    """PUT /rubrics/:id — update rubric content."""
    title: str | None = None
    description: str | None = None
    rubric_text: str | None = None


class RubricOut(BaseModel):
    """Full rubric details."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    title: str
    description: str | None
    rubric_text: str
    original_filename: str | None
    storage_key: str | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    material_id: UUID | None = None
    mime_type: str | None = None


class RubricBrief(BaseModel):
    """Minimal rubric info for lists and selection dropdowns."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    created_at: datetime
