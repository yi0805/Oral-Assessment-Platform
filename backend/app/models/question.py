import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


question_pool_materials = Table(
    "question_pool_materials",
    Base.metadata,
    Column(
        "question_pool_id",
        UUID(as_uuid=True),
        ForeignKey("question_pools.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "material_id",
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class QuestionPool(Base):
    __tablename__ = "question_pools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assessment_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_configs.id", ondelete="CASCADE"), nullable=False, unique=True,
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default="draft", comment="draft | published"
    )

    assessment_config = relationship("AssessmentConfig", back_populates="question_pool")
    questions = relationship("Question", back_populates="pool",  passive_deletes=True,)
    materials = relationship("Material", secondary=question_pool_materials, lazy="select")

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

    question_index: Mapped[int] = mapped_column(Integer, nullable=False)

    pool = relationship("QuestionPool", back_populates="questions")

    def __repr__(self) -> str:
        return f"<Question [{self.question_index}] {self.question_text[:50]}...>"
