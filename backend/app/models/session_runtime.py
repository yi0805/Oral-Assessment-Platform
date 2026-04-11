import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SessionQuestionItem(Base):

    __tablename__ = "session_question_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False
    )
    source_question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    question_kind: Mapped[str] = mapped_column(
        String, nullable=False, comment="main | followup"
    )
    main_group_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Runtime main-question position for the session.",
    )
    followup_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Runtime follow-up position within a main-question group.",
    )

    session = relationship("AssessmentSession", back_populates="question_items")

    def __repr__(self) -> str:
        return f"<SQI [{self.question_kind}] group={self.main_group_no} fu={self.followup_no}>"


class TranscriptMessage(Base):

    __tablename__ = "transcript_messages"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence_no", name="uq_transcript_session_seq"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=True, comment=" if not None, this is student answer"
    )
    session_question_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("session_question_items.id", ondelete="RESTRICT"),
        nullable=True,
        comment="if not None, this is question",
    )

    message_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="main_question | followup_question | student_answer", 
    )

    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    session = relationship("AssessmentSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message #{self.sequence_no} {self.content[:40]}...>"
