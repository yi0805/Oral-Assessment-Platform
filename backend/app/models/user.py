import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    upi: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    image : Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(
        String, nullable=False, comment="student | instructor"
    )

    sessions = relationship("AssessmentSession", back_populates="student", passive_deletes=True)
    enrollments = relationship("CourseEnrollment", back_populates="user",  passive_deletes=True,)

    def __repr__(self) -> str:
        return f"<User {self.upi} {self.email} ({self.role})>"
