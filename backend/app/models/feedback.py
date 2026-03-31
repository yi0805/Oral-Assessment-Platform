"""ORM models for AI summaries and instructor feedback."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AISummary(Base):
    __tablename__ = "ai_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="One AI summary per assessment session.",
    )
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    gaps: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_refs = mapped_column(JSONB, nullable=True, comment="Transcript message IDs used as evidence.")
    model_name: Mapped[str] = mapped_column(String, nullable=False, comment="Model used to generate the advisory summary.")
    advisory_only: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Always true because the AI summary is advisory only.",
    )
    suggested_grade: Mapped[str | None] = mapped_column(
        String, nullable=True,
        comment="Advisory grade suggested by the AI (e.g. A, B+, Pass). Never auto-assigned.",
    )
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="success", comment="success | failed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session = relationship("AssessmentSession", back_populates="ai_summary")

    def __repr__(self) -> str:
        return f"<AISummary session={self.session_id} [{self.status}]>"


class InstructorFeedback(Base):
    __tablename__ = "instructor_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="One instructor feedback record per assessment session.",
    )
    instructor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Internal instructor notes.")
    grading_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    provisional_grade: Mapped[str | None] = mapped_column(String, nullable=True)
    final_grade: Mapped[str | None] = mapped_column(String, nullable=True)
    student_visible_comments: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Feedback shown to the student after release."
    )
    released_to_student: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    session = relationship("AssessmentSession", back_populates="feedback")
    instructor = relationship("User", foreign_keys=[instructor_id])

    def __repr__(self) -> str:
        return f"<Feedback session={self.session_id} released={self.released_to_student}>"
