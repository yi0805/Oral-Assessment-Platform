"""
Question generation service — bridge between Bess's RAG and Joanne's AI.
 — BessRAGJoanneAI.

Owner: Joanne (prompt design) + Bess (data pipeline)
Flow:
  1. Instructor selects materials → Bess retrieves relevant chunks via RAG
  2. Chunks + rubric text → Joanne's prompt template
  3. LLM generates draft questions → saved to question_pools + questions tables

TODO (Week 5-6):
- [ ] generate_pool(course_id, material_ids, rubric_id) → QuestionPool with Questions
- [ ] This is a SHARED ownership file — coordinate with Joanne
"""
pass
