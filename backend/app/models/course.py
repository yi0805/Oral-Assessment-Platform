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
    course_code: Mapped[str] = mapped_column(
        String, nullable=False, comment="e.g. COMPSCI 399"
    )
    course_name: Mapped[str] = mapped_column(String, nullable=False)
    term: Mapped[str] = mapped_column(
        String, nullable=False, comment="e.g. 26S1"
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    enrollments = relationship("CourseEnrollment", back_populates="course", passive_deletes=True,)
    materials = relationship("Material", back_populates="course", passive_deletes=True,)
    assessment_configs = relationship("AssessmentConfig", back_populates="course", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Course {self.course_code}: {self.course_name}>"


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    upi: Mapped[str] = mapped_column(String, nullable=False)

    course = relationship("Course", back_populates="enrollments")
    user = relationship("User", back_populates="enrollments")

    def __repr__(self) -> str:
        return f"<Enrollment user={self.user_id} course={self.course_id}>"
