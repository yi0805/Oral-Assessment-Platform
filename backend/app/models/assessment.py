"""ORM models for assessment configuration and student assessment sessions."""
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssessmentConfig(Base):
    __tablename__ = "assessment_configs"
    __table_args__ = (
        CheckConstraint(
            "release_time IS NULL OR due_time IS NULL OR due_time > release_time",
            name="chk_schedule_order",
        ),
        CheckConstraint(
            "question_pool_id IS NOT NULL",
            name="chk_config_question_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    question_pool_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_pools.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Required for generic assessments; null for personalized assessments until runtime generation.",
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    material_r_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional during draft setup, recommended before publish.",
    )

    total_time_minute: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="15"
    )
    main_question_num: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Maximum number of main questions shown to a student per session. Must be set before publishing.",
    )
    follow_up_num: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1"
    )

    release_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When students can start the assessment.",
    )
    due_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Hard deadline after which no new sessions should start.",
    )

    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default="draft", comment="draft | published"
    )

    # --- Relationships ---

    course = relationship("Course", back_populates="assessment_configs")
    rubric_material = relationship("Material", back_populates="assessment_configs")
    sessions = relationship(
        "AssessmentSession", back_populates="config", cascade="all, delete-orphan"
    )
    question_pools = relationship("QuestionPool", back_populates="assessment_configs", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<AssessmentConfig {self.title} [{self.status}]>"


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assessment_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_configs.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_s_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default="not_started",
        comment="not_started | in_progress | under_review | released",
    )

    # --- Relationships ---

    config = relationship("AssessmentConfig", back_populates="sessions")
    student = relationship(
        "User",
        back_populates="assessment_configs",
        foreign_keys=[user_s_id],
    )
    question_items = relationship(
        "SessionQuestionItem", back_populates="session", cascade="all, delete-orphan"
    )
    messages = relationship(
        "TranscriptMessage", back_populates="session", cascade="all, delete-orphan"
    )
    ai_summary = relationship("AISummary", back_populates="session", uselist=False)
    feedback = relationship("SessionFeedback", back_populates="session", uselist=False)

    def __repr__(self) -> str:
        return f"<Session student={self.user_s_id} [{self.status}]>"
