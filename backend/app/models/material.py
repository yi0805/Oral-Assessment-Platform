import uuid

from sqlalchemy import (
    String, Text, Integer, ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    storage_key: Mapped[str] = mapped_column(
        String, unique=True, nullable=False,
        comment="S3 key: courses/{course_id}/materials/{material_id}/{filename}"
    )
    material_category: Mapped[str] = mapped_column(
        String, nullable=False, 
        server_default="course_material",
        comment="course_material | rubric"
    )

    course = relationship("Course", back_populates="materials")
    chunks = relationship("MaterialChunk", back_populates="material", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Material {self.filename} [{self.material_category}]>"


class MaterialChunk(Base):
    __tablename__ = "material_chunks"
    __table_args__ = (
        UniqueConstraint("material_id", "chunk_index", name="uq_chunk_material_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="0-based position within material"
    )
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    embedding = mapped_column(
        Vector(768), nullable=True, comment="Gemini gemini-embedding-001, 768-dim vector (outputDimensionality=768), HNSW indexed"
    )

    material = relationship("Material", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk {self.material_id}[{self.chunk_index}]>"
