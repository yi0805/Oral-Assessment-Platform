"""
AI API Gateway — Project 20 centralised AI client.

All AI calls in the system must go through this module. Never call
external AI APIs directly from service files.

Provider routing
----------------
  Embeddings  → Google Gemini  (gemini-embedding-001)
                Endpoint: generativelanguage.googleapis.com
                Dimension: 768 (RETRIEVAL_DOCUMENT task type)

  Chat / LLM  → OpenRouter free tier  (openrouter/free)
                Endpoint: openrouter.ai/api/v1/chat/completions
                OpenAI-compatible schema

Dev fallback
------------
When a key is not configured the gateway returns zero vectors (embeddings)
or a clearly labelled placeholder string (chat) so the rest of the pipeline
stays testable end-to-end without live API keys.

Configuration keys (set in .env)
---------------------------------
  GEMINI_API_KEY       - Google AI Studio key (Gemini embedding)
  OPENROUTER_API_KEY   - OpenRouter key (chat completions)
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OPENROUTER_MODEL = "openrouter/free"
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


GEMINI_EMBED_MODEL = "models/gemini-embedding-001"
GEMINI_EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-embedding-001:embedContent"
)
GEMINI_BATCH_EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-embedding-001:batchEmbedContents"
)

EMBEDDING_DIMENSIONS = 768    #(pgvector HNSW max is 2000)
_ZERO_VECTOR: list[float] = [0.0] * EMBEDDING_DIMENSIONS  # 768 zeros 


# ---------------------------------------------------------------------------
# Public embedding interface
# ---------------------------------------------------------------------------

async def get_embedding(
    text: str,
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[float]:
    """
    Return a 768-dimensional float vector for *text* using Gemini Embedding.

    Args:
        text:       The text to embed (keep under ~2 000 tokens for best results).
        task_type:  Gemini task hint — one of RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY,
                    SEMANTIC_SIMILARITY, CLASSIFICATION, CLUSTERING.
                    Use RETRIEVAL_DOCUMENT when indexing material chunks.
                    Use RETRIEVAL_QUERY when embedding a search query.

    Returns:
        A list of 768 floats.  Returns a zero vector when the key is absent (dev mode).
    """
    if not settings.gemini_api_key:
        logger.warning("[AI Gateway] GEMINI_API_KEY not set — returning zero vector (dev mode)")

        return list(_ZERO_VECTOR)

    payload: dict[str, Any] = {
        "model": GEMINI_EMBED_MODEL,
        "content": {"parts": [{"text": text}]},
        "taskType": task_type,
        "outputDimensionality": EMBEDDING_DIMENSIONS,  # 768 — pgvector HNSW hard limit is 2000
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                GEMINI_EMBED_URL,
                headers={
                    "x-goog-api-key": settings.gemini_api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            response.raise_for_status()

            data = response.json()
            values: list[float] = data["embedding"]["values"]

            logger.debug("[AI Gateway] Gemini embed: %d dims for %d chars", len(values), len(text))

            return values
        
        except httpx.HTTPStatusError as exc:
            logger.error("[AI Gateway] Gemini embed HTTP %s: %s", exc.response.status_code, exc.response.text)
            raise RuntimeError(f"Gemini embedding failed: {exc.response.text}") from exc
        
        except Exception as exc:
            logger.error("[AI Gateway] Gemini embed error: %s", exc)
            raise RuntimeError(f"Gemini embedding error: {exc}") from exc


async def get_embeddings_batch(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[list[float]]:
    """
    Batch embed multiple texts via Gemini batchEmbedContents.

    Automatically splits into sub-batches of at most BATCH_SIZE=100 because
    the Gemini batchEmbedContents API accepts a maximum of 100 requests per call.
    Falls back to sequential single-embed calls if the batch API errors.

    Returns a list of 768-float vectors in the same order as *texts*.
    Returns zero vectors when GEMINI_API_KEY is not set (dev mode).
    """
    BATCH_SIZE = 100  # Gemini batchEmbedContents hard limit

    if not texts:
        return []

    if not settings.gemini_api_key:
        logger.warning("[AI Gateway] GEMINI_API_KEY not set — returning zero vectors (dev mode)")
        return [list(_ZERO_VECTOR) for _ in texts]

    all_embeddings: list[list[float]] = []

    # Process in sub-batches so we never exceed the API limit
    for batch_start in range(0, len(texts), BATCH_SIZE):
        batch = texts[batch_start : batch_start + BATCH_SIZE]
        batch_no = batch_start // BATCH_SIZE + 1
        total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

        requests_payload = [
            {
                "model": GEMINI_EMBED_MODEL,
                "content": {"parts": [{"text": t}]},
                "taskType": task_type,
                "outputDimensionality": EMBEDDING_DIMENSIONS,  # 768 — pgvector HNSW hard limit is 2000
            }
            for t in batch
        ]

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    GEMINI_BATCH_EMBED_URL,
                    headers={
                        "x-goog-api-key": settings.gemini_api_key,
                        "Content-Type": "application/json",
                    },
                    json={"requests": requests_payload},
                )

                response.raise_for_status()
                data = response.json()

                batch_embeddings: list[list[float]] = [
                    item["values"] for item in data["embeddings"]
                ]
                all_embeddings.extend(batch_embeddings)

                logger.info(
                    "[AI Gateway] Gemini batch embed %d/%d: %d texts embedded",
                    batch_no, total_batches, len(batch_embeddings),
                )

            except httpx.HTTPStatusError as exc:
                logger.error(
                    "[AI Gateway] Gemini batch embed %d/%d HTTP %s: %s — falling back to sequential",
                    batch_no, total_batches, exc.response.status_code, exc.response.text,
                )

                # Graceful fallback: embed one by one for this sub-batch
                for text in batch:
                    try:
                        vec = await get_embedding(text, task_type=task_type)

                    except Exception:  # noqa: BLE001
                        vec = list(_ZERO_VECTOR)

                    all_embeddings.append(vec)

            except Exception as exc:
                logger.error(
                    "[AI Gateway] Gemini batch embed %d/%d error: %s",
                    batch_no, total_batches, exc,
                )
                raise RuntimeError(f"Gemini batch embedding error: {exc}") from exc

    logger.info("[AI Gateway] Gemini batch embed complete: %d total vectors", len(all_embeddings))

    return all_embeddings


# ---------------------------------------------------------------------------
# Public chat / LLM interface
# ---------------------------------------------------------------------------

async def chat_complete(
    messages: list[dict[str, str]],
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
    model: str | None = None,
) -> str:
    """
    Call OpenRouter's free-tier model and return the assistant message content.

    Args:
        messages:      A list of ``{"role": "user"|"assistant", "content": "..."}``
                       dicts in the order they should appear.  Do NOT include a
                       system message here — use *system_prompt* instead.
        system_prompt: Optional system instruction prepended to the conversation.
        temperature:   Sampling temperature (0 = deterministic, 1 = creative).
        max_tokens:    Maximum number of tokens in the completion.
        model:         Override the default OpenRouter model.  Defaults to
                       ``openrouter/free``.

    Returns:
        The assistant's reply as a plain string.
        Returns a clearly marked placeholder when OPENROUTER_API_KEY is absent.
    """
    if not settings.openrouter_api_key:
        logger.warning("[AI Gateway] OPENROUTER_API_KEY not set — returning placeholder (dev mode)")
        return "[AI response placeholder — set OPENROUTER_API_KEY in .env to enable live AI]"

    full_messages: list[dict[str, str]] = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    payload: dict[str, Any] = {
        "model": model or OPENROUTER_MODEL,
        "messages": full_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                OPENROUTER_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    # Explicitly request UTF-8 to prevent decode errors with
                    # answers that contain math/Unicode symbols (∑, ∫, ≤, etc.)
                    "Content-Type": "application/json; charset=utf-8",
                    "Accept": "application/json",
                    "HTTP-Referer": "https://project20.localhost",
                    "X-Title": "Project 20 AI Oral Assessment",
                },
                content=__import__("json").dumps(payload, ensure_ascii=False).encode("utf-8"),
            )
            response.raise_for_status()
            # Explicitly decode as UTF-8 to avoid charset-detection failures when
            # response bodies contain Unicode math symbols or non-ASCII characters.
            data = __import__("json").loads(response.content.decode("utf-8"))
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError(f"OpenRouter returned no choices: {data}")

            message = choices[0].get("message") or {}
            content = message.get("content")

            if content is None or not str(content).strip():
                raise RuntimeError(f"OpenRouter returned empty content: {data}")

            content = str(content).strip()

            logger.info(
                "[AI Gateway] OpenRouter chat: %d input tokens, reply=%d chars",
                data.get("usage", {}).get("prompt_tokens", 0),
                len(content),
            )
            return content
        
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[AI Gateway] OpenRouter HTTP %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise RuntimeError(f"OpenRouter chat failed: {exc.response.text}") from exc
        except Exception as exc:
            logger.error("[AI Gateway] OpenRouter error: %s", exc)
            raise RuntimeError(f"OpenRouter chat error: {exc}") from exc
