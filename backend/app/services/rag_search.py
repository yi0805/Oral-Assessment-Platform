"""
RAG (Retrieval-Augmented Generation) search service.
Uses pgvector HNSW cosine similarity to find relevant material chunks.

This is the interface between Bess's data layer and Joanne's AI layer:
  Input: a natural language query + course_id
  Output: top-k most relevant text chunks ranked by cosine similarity

Used by: question_generator (Phase 3) and ai_summary_service (Phase 5)
"""
import logging
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.material import MaterialChunk, Material
from app.services.embedding_service import embed_text

logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    chunk_id: UUID
    material_id: UUID
    chunk_text: str
    score: float
    source_page_start: int | None
    source_page_end: int | None


async def search(
    db: Session,
    query_text: str,
    course_id: UUID,
    top_k: int = 5,
) -> list[RAGResult]:
    """
    Search for the most relevant chunks matching a query within a course.

    1. Embed the query text using OpenAI
    2. Use pgvector's cosine distance operator (<=> ) to find nearest chunks
    3. Filter to only chunks belonging to materials in the specified course
    4. Return top_k results ranked by similarity
    """
    # Step 1: Embed the query
    query_embedding = await embed_text(query_text)

    # Step 2: pgvector cosine similarity search
    # The <=> operator returns cosine distance (0 = identical, 2 = opposite)
    # We convert to similarity score: 1 - distance
    results = (
        db.query(
            MaterialChunk,
            MaterialChunk.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .join(Material, MaterialChunk.material_id == Material.id)
        .filter(
            Material.course_id == course_id,
            Material.processing_status == "ready",
            MaterialChunk.embedding.isnot(None),
        )
        .order_by("distance")
        .limit(top_k)
        .all()
    )

    return [
        RAGResult(
            chunk_id=chunk.id,
            material_id=chunk.material_id,
            chunk_text=chunk.chunk_text,
            score=round(1.0 - distance, 4),  # Convert distance to similarity
            source_page_start=chunk.source_page_start,
            source_page_end=chunk.source_page_end,
        )
        for chunk, distance in results
    ]
