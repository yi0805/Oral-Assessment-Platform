"""
Question generation service — RAG-grounded AI question generation.

Flow:
  1. Instructor selects materials + rubric and specifies num_main_questions
  2. RAG search retrieves the most relevant chunks from selected materials
  3. Chunks + rubric_text are assembled into a structured prompt
  4. Prompt is sent to the LLM via the AI Gateway (OpenRouter free tier)
  5. LLM output is parsed into main question objects
  6. Main questions are saved to the pool in the database

Note: Only MAIN questions are generated here. Follow-up questions are NOT
pre-generated. They are dynamically generated during the student's assessment
session based on the student's actual answer to each main question — see
app/api/routes/sessions.py:_generate_ai_followup().

AI provider: OpenRouter free  (openrouter/free)
Gateway:      app.services.ai_gateway.chat_complete
"""
from __future__ import annotations

import json
import logging
import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.question import Question, QuestionPool
from app.models.material import Material, MaterialChunk
from app.services import rag_search
from app.services.ai_gateway import chat_complete

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_pool(
    db: Session,
    pool_id: UUID,
    course_id: UUID,
    material_id: UUID,
    rubric_id: UUID | None = None,
    num_main_questions: int = 3,
) -> QuestionPool:
    """
    Generate MAIN questions only for a pool using RAG-grounded LLM prompting.

    Follow-up questions are NOT generated here. They are dynamically produced
    during the student's session based on the student's actual answer —
    see sessions.py:_generate_ai_followup().

    Steps:
    1. Retrieve relevant material chunks via pgvector RAG search
    2. Load the rubric (if provided)
    3. Call the LLM via the AI Gateway
    4. Parse JSON output into Question ORM objects (main questions only)
    5. Persist all questions to the database

    Returns:
        The updated QuestionPool (refreshed from DB).
    """
    pool = db.query(QuestionPool).filter(QuestionPool.id == pool_id).first()
    if not pool:
        raise ValueError(f"Question pool {pool_id} not found")

    # ------------------------------------------------------------------
    # 1. Get rubric text
    # ------------------------------------------------------------------
    rubric_text = ""

    if rubric_id:
        rubric_material = db.query(Material).filter(
            Material.id == rubric_id,
            Material.material_category == "rubric",
        ).first()

        if rubric_material:
            rubric_chunks = (
                db.query(MaterialChunk)
                .filter(MaterialChunk.material_id == rubric_id)
                .order_by(MaterialChunk.chunk_index)
                .all()
            )

            rubric_text = "\n\n".join(c.chunk_text for c in rubric_chunks)

    # ------------------------------------------------------------------
    # 2. RAG: retrieve relevant chunks from the selected materials only
    # ------------------------------------------------------------------
    # Strategy:
    #   A) Vector RAG (preferred) — 5 diverse queries scoped to selected
    #      material_ids.  Returns empty list (not raises) when embeddings are
    #      zero vectors or Gemini key is absent.
    #   B) Direct text fallback — if RAG returns nothing, read extracted_text
    #      from the materials table directly.  This always works because
    #      extracted_text is stored during the Extract stage, before embedding.
    #
    # This ensures questions are grounded in actual uploaded content even when
    # the vector index is not yet built.

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
        for query in _COVERAGE_QUERIES:
            hits = await rag_search.search(
                db=db,
                query_text=query,
                course_id=course_id,
                top_k=chunks_per_query,
                material_id=material_id,
            )
            all_chunks.extend(hits)

    except Exception as exc:  # noqa: BLE001
        rag_error = f"{type(exc).__name__}: {exc}"
        logger.warning(
            "generate_pool %s: RAG vector search raised %s — will try text fallback",
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
        "generate_pool %s: %d unique RAG vector chunks for material %s%s",
        pool_id,
        len(unique_chunks),
        material_id,
        f" (RAG error: {rag_error})" if rag_error else "",
    )

    # ------------------------------------------------------------------
    # 2b. Text fallback — load extracted_text when RAG returned nothing
    # ------------------------------------------------------------------
    text_fallback_excerpts: list[dict] = []

    if not unique_chunks:
        logger.warning(
            "generate_pool %s: RAG returned 0 usable chunks. "
            "Falling back to extracted_text from materials table. "
            "To enable vector RAG, ensure GEMINI_API_KEY is set and re-upload materials.",
            pool_id,
        )
        text_fallback_excerpts = rag_search.get_extracted_text_chunks(
            db=db,
            material_id=material_id,
            max_chars=12000,
        )

        if not text_fallback_excerpts:
            logger.error(
                "generate_pool %s: No extracted_text found for material %s. "
                "Material may not have completed the Extract pipeline stage.",
                pool_id, material_id,
            )

    # ------------------------------------------------------------------
    # 3. Build the prompt
    # ------------------------------------------------------------------
    rubric_section = rubric_text.strip() if rubric_text else "No rubric provided — generate generally applicable questions."

    if unique_chunks:
        # Vector RAG path — semantically ranked excerpts
        chunks_section = "\n\n---\n\n".join(
            f"[Excerpt {i+1} | relevance score {c.score:.2f}]\n{c.chunk_text}"
            for i, c in enumerate(unique_chunks)
        )
        context_source = f"vector RAG ({len(unique_chunks)} chunks)"

    elif text_fallback_excerpts:
        # Text fallback path — raw extracted text
        chunks_section = "\n\n---\n\n".join(
            f"[Material: {ex['file_name']}]\n{ex['text']}"
            for ex in text_fallback_excerpts
        )
        context_source = f"extracted_text fallback ({len(text_fallback_excerpts)} materials)"

    else:
        chunks_section = (
            "No course material context available. "
            "Generate questions appropriate for a university-level course on this topic."
        )
        context_source = "no context (no materials processed)"

    logger.info("generate_pool %s: building prompt using %s", pool_id, context_source)

    user_prompt = _GENERATION_PROMPT_TEMPLATE.format(
        num_main=num_main_questions,
        rubric_section=rubric_section,
        chunks_section=chunks_section,
    )

    # ------------------------------------------------------------------
    # 4. Call LLM
    # ------------------------------------------------------------------
    try:
        raw_response = await chat_complete(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=2000,
        )
        questions_data = _parse_llm_response(raw_response, num_main_questions)

    except (RuntimeError, ValueError) as exc:
        logger.error("Question generation LLM call failed: %s", exc)
        # Fall back to clearly labelled placeholder questions
        questions_data = _fallback_questions(num_main_questions)

    # ------------------------------------------------------------------
    # 5. Persist to database
    # ------------------------------------------------------------------
    # Clear existing questions (idempotent retry)
    db.query(Question).filter(Question.question_pool_id == pool_id).delete()

    for order, qdata in enumerate(questions_data, start=1):
        main_q = Question(
            question_pool_id=pool_id,
            question_text=qdata["main_question"],
            question_index = order,
        )
        db.add(main_q)

    db.commit()
    db.refresh(pool)

    logger.info(
        "generate_pool %s: %d main questions saved (follow-ups generated dynamically during sessions)",
        pool_id,
        len(questions_data),
    )
    return pool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_llm_response(
    raw: str,
    expected_main: int,
) -> list[dict]:
    """
    Parse the LLM's JSON response into a list of main question dicts.
    Strips markdown code fences if the model includes them.
    Falls back to placeholder questions on parse failure.
    """
    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()

    # Find the JSON array even if there is surrounding text
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    try:
        data = json.loads(cleaned)

    except json.JSONDecodeError as exc:
        logger.error("LLM response JSON parse failed: %s\nRaw: %.500s", exc, raw)
        return _fallback_questions(expected_main)

    if not isinstance(data, list) or not data:
        logger.warning("LLM returned non-list or empty JSON: %.200s", raw)
        return _fallback_questions(expected_main)

    # Validate / normalise each item (main questions only)
    validated: list[dict] = []
    for item in data[:expected_main]:
        if not isinstance(item, dict) or "main_question" not in item:
            continue

        validated.append({
            "main_question": str(item["main_question"]),
            "learning_objective": str(item.get("learning_objective", "")),
            "difficulty": str(item.get("difficulty", "medium")),
            "answer_style": str(item.get("answer_style", "long")),
        })

    if not validated:
        return _fallback_questions(expected_main)

    return validated


def _fallback_questions(num_main: int) -> list[dict]:
    """Return clearly-labelled placeholder main questions for dev/fallback use."""
    return [
        {
            "main_question": f"[AI generation failed — main question {i+1}. Check OPENROUTER_API_KEY.]",
            "learning_objective": "Pending AI integration",
            "difficulty": "medium",
            "answer_style": "long",
        }
        for i in range(num_main)
    ]
