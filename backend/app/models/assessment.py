"""ORM models for assessment configuration and student assessment sessions."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssessmentConfig(Base):
    __tablename__ = "assessment_configs"
    __table_args__ = (
        CheckConstraint(
            "open_at IS NULL OR close_at IS NULL OR close_at > open_at",
            name="chk_schedule_order",
        ),
        CheckConstraint(
            "(assessment_mode = 'generic' AND question_pool_id IS NOT NULL) OR assessment_mode = 'personalized'",
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
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    assessment_mode: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default="generic",
        comment="generic = question pool based MVP, personalized = student submission based future mode",
    )
    rubric_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rubrics.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional during draft setup, recommended before publish.",
    )

    total_time_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="15"
    )
    per_question_time_limit_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Null means the overall session timer is the only enforced limit.",
    )
    max_main_questions: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Maximum number of main questions shown to a student per session. Must be set before publishing.",
    )
    max_followups_per_main: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="3"
    )
    followup_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    open_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When students can start the assessment.",
    )
    close_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Hard deadline after which no new sessions should start.",
    )

    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default="draft", comment="draft | published | closed"
    )
    published_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    course = relationship("Course", back_populates="assessment_configs")
    question_pool = relationship("QuestionPool")
    rubric = relationship("Rubric", back_populates="assessment_configs")
    publisher = relationship("User", foreign_keys=[published_by])
    sessions = relationship(
        "AssessmentSession", back_populates="config", cascade="all, delete-orphan"
    )

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
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="Denormalized for instructor dashboard queries.",
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    started_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default="not_started",
        comment="not_started | in_progress | submitted | time_expired | under_review | released",
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_messages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_main_index: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Tracks runtime progress through the ordered main-question sequence.",
    )
    current_followup_index: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Tracks runtime progress within the current main question.",
    )
    transcript_locked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Set to true when the session ends to prevent further transcript writes.",
    )
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    config = relationship("AssessmentConfig", back_populates="sessions")
    student = relationship("User", foreign_keys=[student_id])
    starter = relationship("User", foreign_keys=[started_by])
    question_items = relationship(
        "SessionQuestionItem", back_populates="session", cascade="all, delete-orphan"
    )
    messages = relationship(
        "TranscriptMessage", back_populates="session", cascade="all, delete-orphan"
    )
    ai_summary = relationship("AISummary", back_populates="session", uselist=False)
    feedback = relationship("InstructorFeedback", back_populates="session", uselist=False)

    def __repr__(self) -> str:
        return f"<Session student={self.student_id} [{self.status}]>"
