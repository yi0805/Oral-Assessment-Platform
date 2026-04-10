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
    assessment_configs_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_configs.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default="draft", comment="draft | reviewed | approved | archived"
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False
    )
    # --- Relationships ---
    assessment_configs = relationship("AssessmentConfig", back_populates="question_pools")
    questions = relationship("Question", back_populates="pool", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<QuestionPool {self.id} [{self.status}]>"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_pools.id", ondelete="CASCADE"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)

    # display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    question_index: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # --- Relationships ---
    pool = relationship("QuestionPool", back_populates="questions")

    def __repr__(self) -> str:
        return f"<Question [{self.question_index}] {self.question_text[:50]}...>"
