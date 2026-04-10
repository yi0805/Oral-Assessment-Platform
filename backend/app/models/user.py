"""
ORM model: users table.
ORM:users.

Owner: Bess
Schema truth: schema_5.dbml → 001_foundation_tables.sql → THIS FILE
One-sentence truth: Who can use the system
"""
import uuid

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    image : Mapped[str | None] = mapped_column(String, nullable=True, comment="URL to profile image")
    role: Mapped[str] = mapped_column(
        String, nullable=False, comment="student | instructor | admin"
    )

    # --- Relationships ---
    # A user can be enrolled in many courses
    #
    enrollments = relationship("CourseEnrollment", back_populates="user")
    assessment_configs = relationship(
        "AssessmentConfig",
        back_populates="student"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
