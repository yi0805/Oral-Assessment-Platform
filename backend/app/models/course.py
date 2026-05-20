import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("course_code", "term", name="uq_courses_code_term"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_code: Mapped[str] = mapped_column(
        String, nullable=False, comment="e.g. COMPSCI 399"
    )
    course_name: Mapped[str] = mapped_column(String, nullable=False)
    term: Mapped[str] = mapped_column(
        String, nullable=False, comment="e.g. 2026S1 (4-digit year + S1/S2)"
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    enrollments = relationship("CourseEnrollment", back_populates="course", passive_deletes=True,)
    materials = relationship("Material", back_populates="course", passive_deletes=True,)
    assessment_configs = relationship("AssessmentConfig", back_populates="course", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Course {self.course_code}: {self.course_name}>"


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    __table_args__ = (
        UniqueConstraint("course_id", "user_id", name="uq_course_enrollments_course_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    upi: Mapped[str] = mapped_column(String, nullable=False)

    course = relationship("Course", back_populates="enrollments")
    user = relationship("User", back_populates="enrollments")

    def __repr__(self) -> str:
        return f"<Enrollment user={self.user_id} course={self.course_id}>"


class CourseJoinRequest(Base):
    __tablename__ = "course_join_requests"
    __table_args__ = (
        Index(
            "uq_one_pending_join_request",
            "course_id",
            "requester_user_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    requester_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default="pending",
        comment="pending | approved | rejected",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<JoinRequest course={self.course_id} requester={self.requester_user_id} [{self.status}]>"
