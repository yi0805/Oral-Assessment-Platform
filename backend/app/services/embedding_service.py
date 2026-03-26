"""
OpenAI embedding service — generates vector(1536) embeddings for RAG.
Used by the material pipeline (Stage 4: EMBED) and RAG search.
"""
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSIONS = 1536


async def embed_text(text: str) -> list[float]:
    """Generate a single embedding vector from text using OpenAI API."""
    import httpx

    if not settings.openai_api_key:
        logger.warning("OpenAI API key not set — returning zero vector for dev")
        return [0.0] * EMBEDDING_DIMENSIONS

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"input": text, "model": EMBEDDING_MODEL},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in a single API call.
    More efficient than calling embed_text() in a loop.
    OpenAI supports up to ~2048 inputs per batch call.
    """
    import httpx

    if not settings.openai_api_key:
        logger.warning("OpenAI API key not set — returning zero vectors for dev")
        return [[0.0] * EMBEDDING_DIMENSIONS for _ in texts]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"input": texts, "model": EMBEDDING_MODEL},
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        # Sort by index to maintain input order
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]
