"""
Text chunking utility for the material processing pipeline.
Splits extracted text into ~500-token chunks with configurable overlap.
Uses a simple word-based approximation (1 token ~ 0.75 words).
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

APPROX_WORDS_PER_TOKEN = 0.75


@dataclass
class ChunkResult:
    chunk_text: str
    chunk_index: int
    token_count: int
    source_page_start: int | None = None
    source_page_end: int | None = None


def estimate_tokens(text: str) -> int:
    """Estimate token count from word count. Rough approximation: 1 token ~ 0.75 words."""
    word_count = len(text.split())
    return int(word_count / APPROX_WORDS_PER_TOKEN)


def chunk_text(
    text: str,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[ChunkResult]:
    """
    Split text into chunks of approximately max_tokens each, with overlap.
    Uses paragraph boundaries when possible for cleaner splits.
    """
    if not text.strip():
        return []

    # Split by double newlines (paragraphs) first, fall back to sentences
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_chunk_parts = []
    current_token_count = 0
    max_words = int(max_tokens * APPROX_WORDS_PER_TOKEN)
    overlap_words = int(overlap_tokens * APPROX_WORDS_PER_TOKEN)

    for para in paragraphs:
        para_words = len(para.split())
        para_tokens = int(para_words / APPROX_WORDS_PER_TOKEN)

        if current_token_count + para_tokens > max_tokens and current_chunk_parts:
            # Finalize current chunk
            chunk_text_str = "\n\n".join(current_chunk_parts)
            chunks.append(ChunkResult(
                chunk_text=chunk_text_str,
                chunk_index=len(chunks),
                token_count=estimate_tokens(chunk_text_str),
            ))

            # Keep overlap: take the last part(s) as seed for next chunk
            overlap_text = current_chunk_parts[-1] if current_chunk_parts else ""
            if estimate_tokens(overlap_text) <= overlap_tokens:
                current_chunk_parts = [overlap_text]
                current_token_count = estimate_tokens(overlap_text)
            else:
                current_chunk_parts = []
                current_token_count = 0

        current_chunk_parts.append(para)
        current_token_count += para_tokens

    # Don't forget the last chunk
    if current_chunk_parts:
        chunk_text_str = "\n\n".join(current_chunk_parts)
        chunks.append(ChunkResult(
            chunk_text=chunk_text_str,
            chunk_index=len(chunks),
            token_count=estimate_tokens(chunk_text_str),
        ))

    logger.info(f"Chunked text into {len(chunks)} chunks (max_tokens={max_tokens}, overlap={overlap_tokens})")
    return chunks
