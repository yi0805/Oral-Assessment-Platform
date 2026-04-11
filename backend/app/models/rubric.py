import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Rubric(Base):
    __tablename__ = "rubrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rubric_text: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Full rubric content as text — fed to AI as prompt context"
    )
    original_filename: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="Null if manually entered"
    )
    storage_key: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="S3 key if uploaded as PDF/CSV"
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    material_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="SET NULL"),
        nullable=True
    )

    # --- Relationships ---
    course = relationship("Course", back_populates="rubrics")
    creator = relationship("User", foreign_keys=[created_by])
    assessment_configs = relationship("AssessmentConfig", back_populates="rubric")

    def __repr__(self) -> str:
        return f"<Rubric {self.title}>"
