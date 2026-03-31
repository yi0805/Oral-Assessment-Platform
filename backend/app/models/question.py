"""ORM models for question pools and approved bank questions."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuestionPool(Base):
    __tablename__ = "question_pools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_from_materials = mapped_column(JSONB, nullable=True, comment="Array of material UUIDs.")
    generation_method: Mapped[str] = mapped_column(
        String, nullable=False, comment="manual | ai_generated | hybrid"
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default="draft", comment="draft | reviewed | approved | archived"
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    course = relationship("Course", back_populates="question_pools")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    questions = relationship("Question", back_populates="pool", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<QuestionPool {self.title} [{self.status}]>"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_pools.id", ondelete="CASCADE"), nullable=False
    )
    parent_question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Null for a main question; set for a follow-up template.",
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_kind: Mapped[str] = mapped_column(String, nullable=False, comment="main | followup | probe")
    answer_style: Mapped[str] = mapped_column(String, nullable=False, comment="short | long | mixed")
    difficulty: Mapped[str | None] = mapped_column(String, nullable=True, comment="easy | medium | hard")
    learning_objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_chunk_refs = mapped_column(JSONB, nullable=True, comment="Chunk identifiers grounding the question.")
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    pool = relationship("QuestionPool", back_populates="questions")
    parent_question = relationship("Question", remote_side=[id], foreign_keys=[parent_question_id])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Question [{self.question_kind}] {self.question_text[:50]}...>"
