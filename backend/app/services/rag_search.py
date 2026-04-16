import logging
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.material import MaterialChunk, Material
from app.services.embedding_service import embed_text

logger = logging.getLogger(__name__)

# Minimum cosine similarity to consider a result meaningful.
_MIN_SCORE = 0.45


@dataclass
class RAGResult:
    chunk_id: UUID
    material_id: UUID
    chunk_text: str
    score: float


async def search(
    db: Session,
    query_text: str,
    material_id: UUID,
    top_k: int = 5,
    material_category: str | None = "course_material",
) -> list[RAGResult]:
    
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
            Material.id == material_id,
            MaterialChunk.embedding.isnot(None),
        )
    )

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
        "[RAG text-fallback] Loaded %d excerpts for material %s (%d chars total)",
        len(excerpts),
        material_id,
        max_chars - remaining,
    )
    
    return excerpts
