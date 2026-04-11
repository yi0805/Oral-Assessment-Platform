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

from app.models.material import MaterialChunk, Material
from app.services.embedding_service import embed_text

logger = logging.getLogger(__name__)

# Minimum cosine similarity to consider a result meaningful.
# Zero-vector embeddings (stored as fallback when Gemini key is absent or
# embedding fails) produce cosine distance ≈ 1.0 → similarity ≈ 0.0.
# Any real embedding will score higher than this threshold.
_MIN_SCORE = 0.05


@dataclass
class RAGResult:
    chunk_id: UUID
    material_id: UUID
    chunk_text: str
    score: float


async def search(
    db: Session,
    query_text: str,
    course_id: UUID,
    top_k: int = 5,
    material_id: UUID | None = None,
    material_category: str | None = "course_material",
) -> list[RAGResult]:
    """
    Search for the most relevant chunks matching a query within a course.

    1. Embed the query text
    2. Use pgvector's cosine distance operator (<=>) to find nearest chunks
    3. Filter to only chunks belonging to materials in the specified course
       (optionally restricted to a specific subset of material_ids)
    4. Return top_k results ranked by similarity, excluding zero-vector chunks
       (those stored as a fallback when Gemini embedding was unavailable)

    Args:
        material_ids: If provided, restricts search to these specific materials.
                      If None, searches across all ready materials in the course.

    Returns:
        List of RAGResult sorted by descending similarity score.
        Returns an empty list (not raises) when no meaningful results are found.
    """
    # Step 1: Embed the query
    query_embedding = await embed_text(query_text)

    # Detect zero query vector (happens when GEMINI_API_KEY is absent).
    # A zero query vector makes cosine distance meaningless for every chunk —
    # skip the DB round-trip entirely and return empty.
    if all(v == 0.0 for v in query_embedding):
        logger.warning(
            "[RAG] Query embedding is a zero vector (GEMINI_API_KEY not set or "
            "embed_text failed). Returning empty results — question_generator will "
            "fall back to direct extracted_text."
        )
        return []

    # Step 2: pgvector cosine similarity search
    # The <=> operator returns cosine distance (0 = identical, 2 = opposite)
    # We convert to similarity score: 1 - distance
    # We also exclude chunks whose stored embedding is a zero vector by
    # requiring distance < 1.0 (zero-vector cosine distance = 1.0).
    q = (
        db.query(
            MaterialChunk,
            MaterialChunk.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .join(Material, MaterialChunk.material_id == Material.id)
        .filter(
            Material.course_id == course_id,
            MaterialChunk.embedding.isnot(None),
        )
    )

    if material_id:
        q = q.filter(Material.id == material_id)

    if material_category:
        q = q.filter(Material.material_category == material_category)

    results = q.order_by("distance").limit(top_k * 2).all()  # fetch extra, filter below

    meaningful = []
    for chunk, distance in results:
        score = round(1.0 - float(distance), 4)
        if score >= _MIN_SCORE:
            meaningful.append(RAGResult(
                chunk_id=chunk.id,
                material_id=chunk.material_id,
                chunk_text=chunk.chunk_text,
                score=score,
            ))
        if len(meaningful) >= top_k:
            break

    if not meaningful:
        logger.warning(
            "[RAG] All %d results scored below %.2f — embeddings are likely zero vectors. "
            "Re-upload material after setting GEMINI_API_KEY to get real embeddings.",
            len(results), _MIN_SCORE,
        )

    return meaningful


def get_extracted_text_chunks(
    db: Session,
    material_id: UUID | None,
    max_chars: int = 12000,
    material_category: str | None = "course_material",
) -> list[dict]:
    """
    Text-only fallback: directly read extracted_text from the materials table
    and split into excerpts.  Used by question_generator when vector RAG
    returns no results (e.g. zero-vector embeddings, missing Gemini key).

    Returns a list of dicts: [{"material_id": UUID, "text": str}, ...]
    Total characters across all excerpts capped at max_chars.
    """
    if not material_id:
        return []

    q = (
        db.query(Material.id, Material.filename, MaterialChunk.chunk_text)
        .join(MaterialChunk, MaterialChunk.material_id == Material.id)
        .filter(Material.id == material_id)
    )

    if material_category:
        q = q.filter(Material.material_category == material_category)

    rows = q.order_by(Material.id, MaterialChunk.chunk_index).all()

    excerpts: list[dict] = []
    remaining = max_chars

    for mid, fname, text in rows:
        if remaining <= 0:
            break

        if not text or not text.strip():
            continue
        
        chunk = text.strip()[:remaining]
        excerpts.append({
            "material_id": mid,
            "file_name": fname,
            "text": chunk,
        })
        remaining -= len(chunk)

    logger.info(
        "[RAG text-fallback] Loaded %d excerpts from %d materials (%d chars total)",
        len(excerpts),
        len(material_id),
        max_chars - remaining,
    )
    return excerpts
