import uuid
from datetime import datetime

from sqlalchemy import (
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

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    rubric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rubrics.id", ondelete="RESTRICT"),
        nullable=False,
    )

    total_time_minute: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )
    main_question_num: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
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


    course = relationship("Course", back_populates="assessment_configs")
    sessions = relationship(
        "AssessmentSession", back_populates="config",  passive_deletes=True,
    )
    question_pool = relationship("QuestionPool", back_populates="assessment_config", passive_deletes=True, uselist=False)

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
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    config = relationship("AssessmentConfig", back_populates="sessions")
    student = relationship("User", back_populates="sessions")

    question_items = relationship(
        "SessionQuestionItem", back_populates="session",  passive_deletes=True,
    )

    messages = relationship(
        "TranscriptMessage", back_populates="session", passive_deletes=True,
    )

    ai_summary = relationship("AISummary", back_populates="session", passive_deletes=True, uselist=False)
    feedback = relationship("SessionFeedback", back_populates="session", passive_deletes=True, uselist=False)

    def __repr__(self) -> str:
        return f"<Session student={self.user_s_id} [{self.status}]>"
