"""
OpenAI embedding service — generates vector(1536) embeddings for RAG.
OpenAI — RAGvector(1536).

Owner: Bess (embedding storage) + Joanne (model selection)
Used by: material_pipeline.py (Stage 4: EMBED)

TODO (Week 5):
- [ ] embed_text(text: str) → list[float] (1536 dimensions)
- [ ] embed_batch(texts: list[str]) → list[list[float]] (batch API for efficiency)
- [ ] Error handling: retry on rate limit, fail gracefully on API errors
"""
pass
