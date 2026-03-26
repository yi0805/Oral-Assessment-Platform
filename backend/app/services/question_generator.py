"""
Question generation service — bridge between RAG search and LLM.
Owned jointly by Bess (data pipeline) and Joanne (prompt design).

Flow:
  1. Instructor selects materials + rubric -> this service is called
  2. RAG search retrieves relevant chunks from selected materials
  3. Chunks + rubric_text are fed to the LLM via Joanne's prompt template
  4. LLM output is parsed into Question objects and saved to the pool
"""
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.question import QuestionPool, Question
from app.models.rubric import Rubric
from app.services import rag_search

logger = logging.getLogger(__name__)


async def generate_pool(
    db: Session,
    pool_id: UUID,
    material_ids: list[UUID],
    rubric_id: UUID | None = None,
    num_main_questions: int = 3,
    num_followups_per_main: int = 2,
) -> QuestionPool:
    """
    Generate questions for a pool using RAG + LLM.

    This is a shared integration point:
    - Bess provides: RAG search, chunk retrieval, database persistence
    - Joanne provides: prompt template, LLM call, output parsing

    For now, this creates placeholder questions.
    Joanne will replace the LLM call with her prompt engineering.
    """
    pool = db.query(QuestionPool).filter(QuestionPool.id == pool_id).first()
    if not pool:
        raise ValueError(f"Question pool {pool_id} not found")

    # Get rubric text if provided
    rubric_text = ""
    if rubric_id:
        rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
        if rubric:
            rubric_text = rubric.rubric_text

    # RAG search: get relevant chunks from selected materials
    # For each material, search for broad topic coverage
    all_chunks = []
    for mid in material_ids:
        chunks = await rag_search.search(
            db=db,
            query_text=f"key concepts and learning objectives from material {mid}",
            course_id=pool.course_id,
            top_k=10,
        )
        all_chunks.extend(chunks)

    # TODO: Joanne replaces this section with actual LLM call
    # The prompt should include:
    #   - rubric_text (grading criteria)
    #   - chunk texts (source material)
    #   - num_main_questions, num_followups_per_main (structure requirements)
    #
    # For now, create placeholder questions so the pipeline is testable end-to-end
    logger.info(f"Generating {num_main_questions} main questions with {len(all_chunks)} context chunks")

    for i in range(num_main_questions):
        main_q = Question(
            question_pool_id=pool_id,
            question_text=f"[AI-generated main question {i+1} — pending Joanne's LLM integration]",
            question_kind="main",
            answer_style="long",
            display_order=i + 1,
        )
        db.add(main_q)
        db.flush()  # Get the ID for follow-up references

        for j in range(num_followups_per_main):
            followup = Question(
                question_pool_id=pool_id,
                parent_question_id=main_q.id,
                question_text=f"[AI-generated follow-up {j+1} for Q{i+1} — pending LLM integration]",
                question_kind="followup",
                answer_style="mixed",
                display_order=None,
            )
            db.add(followup)

    pool.generated_from_materials = [str(mid) for mid in material_ids]
    pool.generation_method = "ai_generated"
    db.commit()
    db.refresh(pool)

    logger.info(f"Generated {num_main_questions} main + {num_main_questions * num_followups_per_main} follow-up questions for pool {pool_id}")
    return pool
