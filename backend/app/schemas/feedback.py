"""Pydantic schemas for AI summary and instructor feedback API."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ---- AI Summary ----

class AISummaryOut(BaseModel):
    """
    AI-generated advisory analysis returned by GET /sessions/:id/ai-summary.
    Per the user flow (Phase 5), the summary must be:
    - Evidence-based (short quotes from transcript)
    - Rubric-linked (evaluates against the rubric)
    - Strengths and gaps clearly identified
    - Advisory only (suggested grade, never auto-assigned)
    """
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    session_id: UUID
    summary_text: str
    strengths: str | None
    gaps: str | None
    evidence_refs: list | None
    suggested_grade: str | None
    model_name: str
    advisory_only: bool
    status: str
    error_message: str | None
    generated_at: datetime


# ---- Instructor Feedback ----

class FeedbackCreate(BaseModel):
    """POST /sessions/:id/feedback — instructor submits grade and comments."""
    comments: str | None = None
    grading_rationale: str | None = None
    provisional_grade: str | None = None
    final_grade: str | None = None
    student_visible_comments: str | None = None


class FeedbackUpdate(BaseModel):
    """PUT /sessions/:id/feedback — instructor revises feedback before release."""
    comments: str | None = None
    grading_rationale: str | None = None
    provisional_grade: str | None = None
    final_grade: str | None = None
    student_visible_comments: str | None = None


class FeedbackOut(BaseModel):
    """Full feedback details for instructor view."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    instructor_id: UUID
    comments: str | None
    grading_rationale: str | None
    provisional_grade: str | None
    final_grade: str | None
    student_visible_comments: str | None
    released_to_student: bool
    released_at: datetime | None
    created_at: datetime
    updated_at: datetime


# ---- Student Results (post-release) ----

class StudentResultsOut(BaseModel):
    """
    GET /sessions/:id/results — what the student sees after the instructor releases.
    Per the user flow (Phase 6), the student can view:
    - Their final confirmed grade/mark
    - The instructor's manual feedback
    - The full transcript
    """
    session_id: UUID
    final_grade: str | None
    student_visible_comments: str | None
    released_at: datetime | None
    ai_summary: AISummaryOut | None
    transcript_messages: list["TranscriptMessageOut"]


# Avoid circular import — use string reference resolved at runtime
from app.schemas.assessment import TranscriptMessageOut  # noqa: E402
StudentResultsOut.model_rebuild()
