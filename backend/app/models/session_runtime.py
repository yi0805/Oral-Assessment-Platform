"""ORM models for runtime question items and transcript messages."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SessionQuestionItem(Base):
    """A question actually asked during a live session."""

    __tablename__ = "session_question_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False
    )
    source_question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Null for fully dynamic AI-generated follow-ups.",
    )
    parent_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("session_question_items.id", ondelete="SET NULL"),
        nullable=True,
        comment="Self-reference for follow-up questions.",
    )
    asked_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_kind: Mapped[str] = mapped_column(
        String, nullable=False, comment="main | followup | probe"
    )
    main_group_no: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Runtime main-question position for the session.",
    )
    followup_no: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Runtime follow-up position within a main-question group.",
    )
    generated_by: Mapped[str] = mapped_column(
        String, nullable=False, comment="approved_pool | adaptive_ai | instructor_override"
    )
    rag_chunk_refs = mapped_column(
        JSONB, nullable=True, comment="Chunk identifiers used to ground generation."
    )
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_answered: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    session = relationship("AssessmentSession", back_populates="question_items")
    source_question = relationship("Question", foreign_keys=[source_question_id])
    parent_item = relationship("SessionQuestionItem", remote_side=[id], foreign_keys=[parent_item_id])
    messages = relationship("TranscriptMessage", back_populates="question_item")

    def __repr__(self) -> str:
        return f"<SQI [{self.question_kind}] group={self.main_group_no} fu={self.followup_no}>"


class TranscriptMessage(Base):
    """A single message turn in an assessment transcript."""

    __tablename__ = "transcript_messages"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence_no", name="uq_transcript_session_seq"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False
    )
    session_question_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("session_question_items.id", ondelete="SET NULL"),
        nullable=True,
        comment="Null for system notices unrelated to a specific question.",
    )
    sender_role: Mapped[str] = mapped_column(
        String, nullable=False, comment="system | assistant | student | instructor"
    )
    message_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="main_question | followup_question | student_answer | system_notice | summary_notice",
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session = relationship("AssessmentSession", back_populates="messages")
    question_item = relationship("SessionQuestionItem", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message #{self.sequence_no} [{self.sender_role}] {self.content[:40]}...>"
