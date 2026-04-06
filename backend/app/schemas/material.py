"""Pydantic schemas for material upload and processing API."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.enums import ProcessingStatus


class MaterialUploadResponse(BaseModel):
    """Returned by POST /courses/:id/materials/upload after S3 upload completes."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    original_filename: str
    file_type: str
    storage_key: str
    file_size_bytes: int | None
    processing_status: ProcessingStatus
    uploaded_at: datetime
    material_category: str


class MaterialOut(BaseModel):
    """Full material details returned by GET /materials/:id."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    uploaded_by: UUID
    title: str
    original_filename: str
    file_type: str
    mime_type: str | None
    storage_key: str
    file_size_bytes: int | None
    page_count: int | None
    extraction_method: str | None
    processing_status: ProcessingStatus
    processing_error: str | None
    total_chunks: int | None
    uploaded_at: datetime
    processed_at: datetime | None
    updated_at: datetime
    material_category: str

class MaterialStatusOut(BaseModel):
    """Lightweight polling response for GET /materials/:id/status."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    processing_status: ProcessingStatus
    processing_error: str | None
    total_chunks: int | None
    processed_at: datetime | None


class MaterialListItem(BaseModel):
    """Single item in GET /courses/:id/materials response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    original_filename: str
    file_type: str
    processing_status: ProcessingStatus
    total_chunks: int | None
    uploaded_at: datetime
    material_category: str


class ChunkOut(BaseModel):
    """Single chunk returned by RAG search results."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    material_id: UUID
    chunk_index: int
    chunk_text: str
    token_count: int | None
    source_page_start: int | None
    source_page_end: int | None


class RAGSearchRequest(BaseModel):
    """POST /internal/rag/search — used by Joanne's AI service."""
    query: str
    course_id: UUID
    top_k: int = 5


class RAGSearchResult(BaseModel):
    """Single result from RAG search."""
    chunk_text: str
    score: float
    source_page_start: int | None
    source_page_end: int | None
    material_id: UUID
    chunk_id: UUID


class RAGSearchResponse(BaseModel):
    """Response for POST /internal/rag/search."""
    chunks: list[RAGSearchResult]
