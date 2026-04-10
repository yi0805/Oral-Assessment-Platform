"""
ORM models: courses + course_enrollments tables.
ORM:courses + course_enrollments.

Owner: Bess
One-sentence truth (courses): What courses exist
One-sentence truth (enrollments): Who belongs to which course
"""
import uuid

from sqlalchemy import String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_code: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="e.g. COMPSCI399"
    )
    course_name: Mapped[str] = mapped_column(String, nullable=False)
    term: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="e.g. 2026-S1"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Relationships ---
    enrollments = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    materials = relationship("Material", back_populates="course", cascade="all, delete-orphan")
    # rubrics = relationship("Rubric", back_populates="course", cascade="all, delete-orphan")
    assessment_configs = relationship("AssessmentConfig", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Course {self.course_code}: {self.course_name}>"


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    __table_args__ = (
        UniqueConstraint("course_id", "user_id", name="uq_enrollment_course_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # --- Relationships ---
    course = relationship("Course", back_populates="enrollments")
    user = relationship("User", back_populates="enrollments")

    def __repr__(self) -> str:
        return f"<Enrollment user={self.user_id} course={self.course_id}>"
