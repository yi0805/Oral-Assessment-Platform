"""
Embedding service — thin wrapper over the AI Gateway.

All vector generation in the system (material pipeline, RAG search) calls
this module.  The actual provider logic lives in ai_gateway.py.

Embedding model:  gemini-embedding-001  (Google AI)
Embedding dims:   768
"""
import logging

from app.services.ai_gateway import (
    EMBEDDING_DIMENSIONS,
    get_embedding,
    get_embeddings_batch,
)

logger = logging.getLogger(__name__)

# Re-export constants so callers can use embedding_service.EMBEDDING_DIMENSIONS
# without importing from ai_gateway directly.
EMBEDDING_MODEL = "gemini-embedding-001"
__all__ = ["EMBEDDING_MODEL", "EMBEDDING_DIMENSIONS", "embed_text", "embed_batch"]


async def embed_text(text: str) -> list[float]:
    """
    Generate a single 768-dimensional embedding vector for *text*.

    Used by the RAG search service when embedding a query string.
    Uses RETRIEVAL_QUERY task type to optimise Gemini's representation.
    """
    logger.debug("embed_text: %d chars", len(text))
    return await get_embedding(text, task_type="RETRIEVAL_QUERY")


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in a single Gemini batch call.

    Used by the material pipeline when embedding all chunks after chunking.
    Uses RETRIEVAL_DOCUMENT task type so chunks are indexed correctly.

    Returns:
        A list of 768-float lists in the same order as *texts*.
    """
    if not texts:
        return []

    logger.info("embed_batch: %d texts", len(texts))
    return await get_embeddings_batch(texts, task_type="RETRIEVAL_DOCUMENT")
