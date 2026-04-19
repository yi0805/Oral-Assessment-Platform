import uuid

from sqlalchemy import ForeignKey, String, Text, Integer
from sqlalchemy.dialects.postgresql import  UUID
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
    suggested_grade: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Advisory numeric score suggested by the AI (0-100). Never auto-assigned.",
    )

    session = relationship("AssessmentSession", back_populates="ai_summary")

    def __repr__(self) -> str:
        return f"<AISummary session={self.session_id}>"


class SessionFeedback(Base):
    __tablename__ = "session_feedback"

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
    user_i_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Internal instructor notes.")
    final_grade: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default="draft", comment="draft | published"
    )

    session = relationship("AssessmentSession", back_populates="feedback")

    def __repr__(self) -> str:
        return f"<Feedback session={self.session_id} status={self.status}>"
