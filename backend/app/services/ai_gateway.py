from __future__ import annotations

import asyncio
import json as _json
import logging
import httpx
import boto3
import os

from typing import Any

from app.core.config import settings

# Retry policy for transient OpenRouter failures. Backoffs are in seconds.
_CHAT_RETRY_BACKOFFS: tuple[float, ...] = (1.0, 3.0)
_CHAT_RETRY_STATUS: frozenset[int] = frozenset({408, 425, 429, 500, 502, 503, 504})

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Pin a specific OpenRouter model rather than the "openrouter/free" auto-router. auto-routing swaps providers per-request, which makes prompt tuning impossible.
OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"
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

AWS_BEDROCK_MODEL = "anthropic.claude-3-haiku-20240307-v1:0"

# ---------------------------------------------------------------------------
# Public embedding interface
# ---------------------------------------------------------------------------

async def get_embedding(
    text: str,
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[float]:
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

    body = _json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",

        # Explicitly request UTF-8 to prevent decode errors with
        # answers that contain math/Unicode symbols (∑, ∫, ≤, etc.)
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "HTTP-Referer": "https://project20.localhost",
        "X-Title": "Project 20 AI Oral Assessment",
    }

    max_attempts = len(_CHAT_RETRY_BACKOFFS) + 1

    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(OPENROUTER_CHAT_URL, headers=headers, content=body)

            if response.status_code in _CHAT_RETRY_STATUS and attempt < max_attempts:
                wait_s = _CHAT_RETRY_BACKOFFS[attempt - 1]
                logger.warning(
                    "[AI Gateway] OpenRouter HTTP %s (attempt %d/%d) — retrying in %.1fs",
                    response.status_code, attempt, max_attempts, wait_s,
                )
                await asyncio.sleep(wait_s)
                continue

            response.raise_for_status()

            # Explicitly decode as UTF-8 to avoid charset-detection failures when
            # response bodies contain Unicode math symbols or non-ASCII characters.
            data = _json.loads(response.content.decode("utf-8"))
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError(f"OpenRouter returned no choices: {data}")

            message = choices[0].get("message") or {}
            content = message.get("content")

            if content is None or not str(content).strip():
                raise RuntimeError(f"OpenRouter returned empty content: {data}")

            content = str(content).strip()

            logger.info(
                "[AI Gateway] OpenRouter chat: %d input tokens, reply=%d chars (attempt %d)",
                data.get("usage", {}).get("prompt_tokens", 0),
                len(content),
                attempt,
            )
            return content

        except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as exc:
            if attempt >= max_attempts:
                logger.error("[AI Gateway] OpenRouter transport error after %d attempts: %s", attempt, exc)
                raise RuntimeError(f"OpenRouter chat transport error: {exc}") from exc
            wait_s = _CHAT_RETRY_BACKOFFS[attempt - 1]
            logger.warning(
                "[AI Gateway] OpenRouter transport error %s (attempt %d/%d) — retrying in %.1fs",
                type(exc).__name__, attempt, max_attempts, wait_s,
            )
            await asyncio.sleep(wait_s)
            continue

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

    raise RuntimeError(f"OpenRouter chat failed after {max_attempts} attempts")

# ---------------------------------------------------------------------------
# AWS Bedrock chat
# ---------------------------------------------------------------------------

session = boto3.Session(profile_name=settings.aws_profile_name)
bedrock_client = session.client(
    service_name='bedrock-runtime', 
    region_name=settings.aws_region
)

async def chat_complete_bedrock(
        messages: list[dict[str, str]],
        system_prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 1500,
        ) -> str:
    
    if not settings.aws_bearer_token_bedrock:
        logger.warning("[AI Gateway] AWS_BEARER_TOKEN_BEDROCK not set — returning placeholder (dev mode)")
        return "[AI response placeholder — set AWS_BEARER_TOKEN_BEDROCK in .env to enable live AI]"
    
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system_prompt, # Claude 3 support independent system prompt
        "messages": messages
    }
    

    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(
            None, 
            lambda: bedrock_client.invoke_model(
                modelId=AWS_BEDROCK_MODEL,
                body=_json.dumps(payload)
            )
        )
        
        response_body = _json.loads(response.get('body').read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        logger.error(f"[AI Gateway] Bedrock error: {e}")
        raise RuntimeError(f"Bedrock call failed: {e}")
    
# ---------------------------------------------------------------------------
# Smart chat
# ---------------------------------------------------------------------------

async def smart_chat_complete(
    messages: list[dict[str, str]],
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> str:
    """
    Primary: AWS Bedrock; Fallback: OpenRouter
    """
    # 1. Attempt Bedrock first
    if settings.aws_profile_name:
        try:
            logger.info("[AI Gateway] Attempting Bedrock (Claude 3 Haiku)...")
            return await chat_complete_bedrock(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as exc:
            logger.warning(f"[AI Gateway] Bedrock failed: {exc}. Falling back to OpenRouter...")

    # 2. OpenRouter as a redundant backup
    try:
        logger.info("[AI Gateway] Using OpenRouter fallback...")
        return await chat_complete(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except Exception as exc:
        logger.error(f"[AI Gateway] Both AI providers failed: {exc}")
        raise RuntimeError("All AI providers exhausted.") from exc