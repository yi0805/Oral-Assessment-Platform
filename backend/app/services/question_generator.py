from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.services import rag_search
from app.services._prompt_safety import (
    extract_json_array,
    sanitize_untrusted,
    truncate_for_prompt,
)
from app.services.ai_gateway import OPENROUTER_MODEL, smart_chat_complete


from app.models import AssessmentConfig, Question, QuestionPool, Material, MaterialChunk, Rubric

logger = logging.getLogger(__name__)


class QuestionGenerationError(RuntimeError):
    """A safe, expected failure that must not create publishable questions."""

_SYSTEM_PROMPT = """\
You are an expert university educator designing oral assessment questions.
Your task is to generate main assessment questions that are grounded in the
provided course material and aligned with the grading rubric.

Rules:
- Questions must be directly answerable from the course material provided.
- Each main question tests a distinct concept or learning objective.
- Questions should require substantive answers that demonstrate understanding.
- Output must be valid JSON — do NOT include markdown code fences or extra text.
"""

_GENERATION_PROMPT_TEMPLATE = """\
Generate {num_main} oral assessment main questions.

=== GRADING RUBRIC ===
{rubric_section}

=== COURSE MATERIAL EXCERPTS ===
{chunks_section}

=== OUTPUT FORMAT (strict JSON) ===
Return a JSON array of objects. Each object has:
  "main_question": string        — the main question text
  "learning_objective": string   — one sentence describing what is being tested
  "difficulty": "easy" | "medium" | "hard"
  "answer_style": "short" | "long" | "mixed"

Example (do not copy verbatim):
[
  {{
    "main_question": "Explain the role of the mitochondria in energy production.",
    "learning_objective": "Understand cellular respiration",
    "difficulty": "medium",
    "answer_style": "long"
  }}
]
"""

async def generate_pool(
    db: Session,
    config_id: UUID,
    pool_id: UUID,
    material_ids: list[UUID],
    rubric_id: UUID,
    num_main_questions: int,
) -> QuestionPool:
    pool = db.query(QuestionPool).filter(QuestionPool.id == pool_id).first()

    if not pool:
        raise ValueError(f"Question pool {pool_id} not found")

    rubric_text = ""

    if rubric_id:
        rubric = db.query(Rubric).filter(
            Rubric.id == rubric_id,
        ).first()

        if rubric:
            for item in rubric.criteria_data:
                rubric_text += f"- {item['title']}: {item['description']} ({item['max_points']} points)\n"


    _COVERAGE_QUERIES = [
        "key concepts, definitions, and terminology",
        "important theories, models, and frameworks",
        "processes, procedures, and step-by-step methods",
        "examples, case studies, and applications",
        "learning objectives and core principles",
    ]

    all_chunks: list[rag_search.RAGResult] = []
    rag_error: str | None = None

    try:
        chunks_per_query = max(6, (20 // len(_COVERAGE_QUERIES)) + 2)

        for mid in material_ids:
            for query in _COVERAGE_QUERIES:
                hits = await rag_search.search(
                    db=db,
                    query_text=query,
                    top_k=chunks_per_query,
                    material_id=mid,
                )
                all_chunks.extend(hits)

    except Exception as exc:  # noqa: BLE001
        rag_error = f"{type(exc).__name__}: {exc}"
        logger.warning(
            "generate_pool %s: RAG vector search raised %s",
            pool_id, rag_error,
        )
        all_chunks = []

    # Deduplicate by chunk_id, keep highest-scoring copy, limit to top 25
    seen: dict[UUID, rag_search.RAGResult] = {}
    for c in all_chunks:
        if c.chunk_id not in seen or c.score > seen[c.chunk_id].score:
            seen[c.chunk_id] = c

    unique_chunks: list[rag_search.RAGResult] = sorted(
        seen.values(), key=lambda x: -x.score
    )[:25]

    logger.info(
        "generate_pool %s: %d unique RAG vector chunks across %d material(s)%s",
        pool_id,
        len(unique_chunks),
        len(material_ids),
        f" (RAG error: {rag_error})" if rag_error else "",
    )

    if not unique_chunks:
        logger.warning(
            "generate_pool %s: no usable retrieved chunks for selected materials",
            pool_id,
        )
        raise QuestionGenerationError(
            "Selected materials do not have usable retrieved context. Retry processing them before generating questions."
        )


    if rubric_text.strip():
        rubric_section = truncate_for_prompt(sanitize_untrusted(rubric_text))
    else:
        rubric_section = "No rubric provided — generate generally applicable questions."

    chunks_section = "\n\n---\n\n".join(
        f"[Excerpt {i+1} | relevance score {c.score:.2f}]\n{c.chunk_text}"
        for i, c in enumerate(unique_chunks)
    )
    context_source = f"vector RAG ({len(unique_chunks)} chunks)"

    logger.info("generate_pool %s: building prompt using %s", pool_id, context_source)

    user_prompt = _GENERATION_PROMPT_TEMPLATE.format(
        num_main=num_main_questions,
        rubric_section=rubric_section,
        chunks_section=chunks_section,
    )

    try:
        raw_response = await smart_chat_complete(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=2000,
        )
        questions_data = _parse_llm_response(raw_response, num_main_questions)

    except (RuntimeError, ValueError) as exc:
        logger.error("Question generation LLM call failed: %s", exc)

        raise QuestionGenerationError("Question generation provider failed. Please try again.") from exc


    provenance = {
        "source_material_ids": [str(material_id) for material_id in material_ids],
        "source_chunk_ids": [str(chunk.chunk_id) for chunk in unique_chunks],
        "model": OPENROUTER_MODEL,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prompt_version": "question-generation-v1",
    }

    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == config_id).first()

    if config:
        config.description = await _generate_description(questions_data, rubric_section)

    for order, qdata in enumerate(questions_data, start=1):
        main_q = Question(
            question_pool_id=pool_id,
            question_text=qdata["main_question"],
            question_index = order,
            generation_provenance=provenance,
        )
        db.add(main_q)

    logger.info(
        "generate_pool %s: %d main questions saved (follow-ups generated dynamically during sessions)",
        pool_id,
        len(questions_data),
    )
    return pool



async def _generate_description(
    questions_data: list[dict],
    rubric_section: str,
) -> str:
    questions_summary = "\n".join(
        f"  {i}. {q['main_question']} (difficulty: {q.get('difficulty', 'N/A')}, "
        f"objective: {q.get('learning_objective', 'N/A')})"
        for i, q in enumerate(questions_data, start=1)
    )

    prompt = (
        "Based on the following oral assessment questions and rubric, write a "
        "concise 2-3 sentence description of this assessment. The description "
        "should tell students what topics are covered and what skills will be "
        "evaluated. Do NOT include any JSON formatting — return plain text only.\n\n"
        f"=== RUBRIC ===\n{rubric_section}\n\n"
        f"=== QUESTIONS ===\n{questions_summary}"
    )

    try:
        return await smart_chat_complete(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=(
                "You are a university educator. Write a brief, clear assessment "
                "description in plain text (no markdown, no JSON)."
            ),
            temperature=0.5,
            max_tokens=300,
        )
    
    except (RuntimeError, ValueError) as exc:
        logger.warning("Description generation failed: %s — using fallback", exc)
        return "AI oral assessment covering key course topics."


def _parse_llm_response(
    raw: str,
    expected_main: int,
) -> list[dict]:
    try:
        data = extract_json_array(raw)

    except ValueError as exc:
        logger.error("LLM response JSON parse failed: %s\nRaw: %.500s", exc, raw)
        raise QuestionGenerationError("AI returned an invalid question format.") from exc

    if not isinstance(data, list) or not data:
        logger.warning("LLM returned non-list or empty JSON: %.200s", raw)
        raise QuestionGenerationError("AI returned no usable questions.")

    # Validate / normalise each item (main questions only)
    validated: list[dict] = []
    for item in data[:expected_main]:
        if not isinstance(item, dict) or not str(item.get("main_question", "")).strip():
            raise QuestionGenerationError("AI returned an incomplete question set.")

        validated.append({
            "main_question": str(item["main_question"]),
            "learning_objective": str(item.get("learning_objective", "")),
            "difficulty": str(item.get("difficulty", "medium")),
            "answer_style": str(item.get("answer_style", "long")),
        })

    if len(validated) != expected_main:
        raise QuestionGenerationError("AI returned an incomplete question set.")

    return validated
