"""
RAG (Retrieval-Augmented Generation) search service.
RAG.

Owner: Bess (search implementation) + Joanne (consumes results for prompts)
Interface contract with Joanne:
  POST /internal/rag/search
  { query: str, course_id: UUID, top_k: int }
  → { chunks: [{ chunk_text, score, source_page }] }

Uses pgvector HNSW index on material_chunks.embedding for cosine similarity.

TODO (Week 5-6):
- [ ] search(query_text, course_id, top_k=5) → list of ranked chunks
- [ ] Uses embedding_service to embed the query, then pgvector <=> operator
"""
pass
