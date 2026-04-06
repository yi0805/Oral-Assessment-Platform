"""
ORM models: materials + material_chunks tables.
ORM:materials + material_chunks.

Owner: Bess (PRIMARY — this is your signature domain)
One-sentence truth (materials): What files were uploaded + processing state
One-sentence truth (chunks): RAG-ready text segments with vector embeddings

ARCHITECTURE NOTE:
  material_chunks.embedding uses pgvector's Vector(1536) type.
  This is "course memory" in the dual-memory architecture.
  embeddingpgvectorVector(1536).
  "".
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    String, Text, Integer, BigInteger, DateTime, ForeignKey,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(
        String, nullable=False, comment="pdf | pptx | docx | txt"
    )
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_key: Mapped[str] = mapped_column(
        String, unique=True, nullable=False,
        comment="S3 key: courses/{course_id}/materials/{material_id}/{filename}"
    )
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Extraction fields (merged into materials for MVP simplicity)
    # (MVPmaterials)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="pypdf | python-pptx | docx-parser | tika"
    )

    # Processing pipeline state machine
    #
    processing_status: Mapped[str] = mapped_column(
        String, nullable=False, server_default="uploaded",
        comment="uploaded | extracting | chunking | embedding | ready | failed"
    )
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_chunks: Mapped[int | None] = mapped_column(Integer, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    material_category: Mapped[str] = mapped_column(
        String, nullable=False, 
        server_default="course_material",
        comment="course_material | rubric"
    )

    # --- Relationships ---
    course = relationship("Course", back_populates="materials")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    chunks = relationship("MaterialChunk", back_populates="material", cascade="all, delete-orphan")
    rubric = relationship("Rubric", back_populates="material", uselist=False)

    def __repr__(self) -> str:
        return f"<Material {self.title} [{self.processing_status}]>"


class MaterialChunk(Base):
    """
    RAG course memory: chunked text with vector embeddings.
    RAG:.

    Each chunk is ~500 tokens of text from a parent material,
    with a vector(1536) embedding for cosine similarity search via pgvector HNSW.
    """
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
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # gemini-embedding-001 with outputDimensionality=768 (pgvector HNSW index limit is 2000)
    embedding = mapped_column(
        Vector(768), nullable=True, comment="Gemini gemini-embedding-001 768-dim vector (outputDimensionality=768), HNSW indexed"
    )
    source_page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # --- Relationships ---
    material = relationship("Material", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk {self.material_id}[{self.chunk_index}] ({self.token_count} tokens)>"
