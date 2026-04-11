"""
AI summary generation service.
Called after a session is submitted to produce an advisory analysis.

Per the user flow (Phase 5), the summary must be:
  - Evidence-based: short quotes from the transcript
  - Rubric-linked: evaluates against the provided rubric criteria
  - Strengths & gaps: clearly highlights understanding vs. gaps
  - Advisory only: suggested grade, NEVER auto-assigned

AI provider: OpenRouter free  (openrouter/free)
Gateway:      app.services.ai_gateway.chat_complete
"""
from __future__ import annotations

import json
import logging
import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.assessment import AssessmentConfig, AssessmentSession
from app.models.feedback import AISummary
from app.models.material import Material, MaterialChunk
from app.models.session_runtime import TranscriptMessage
from app.services.ai_gateway import chat_complete

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an expert academic assessor analysing a student's oral assessment transcript.
Your role is advisory: provide structured analytical feedback to help the instructor
grade the student — you do NOT assign final grades yourself.

Guidelines:
- Be specific and evidence-based. Quote short fragments (< 15 words) from the transcript.
- Be constructive. Identify concrete gaps without being harsh.
- Be accurate. Only reference content actually present in the transcript.
- Do not return letter grades. Return only a numeric score from 0 to 100.
- Output must be valid JSON — no markdown fences, no extra text.
"""

_SUMMARY_PROMPT_TEMPLATE = """\
Analyse the following oral assessment transcript against the rubric and provide
structured feedback for the instructor.

=== GRADING RUBRIC ===
{rubric_section}

=== TRANSCRIPT ===
{transcript_section}

=== OUTPUT FORMAT (strict JSON) ===
Return a single JSON object with these fields:
{{
  "summary_text": "string — 2-4 paragraph narrative overview of the student's performance, including strengths, gaps, and evidence",
  "suggested_grade": "number - integer from 0 to 100 — advisory only"
}}

Important: suggested_grade is advisory only for instructor consideration.
Do not assign or finalise grades.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_summary(db: Session, session_id: UUID) -> AISummary:
    """
    Generate an AI advisory summary for a completed assessment session.

    Steps:
    1. Load the full transcript
    2. Load the rubric linked to the assessment
    3. Build a structured prompt and call the LLM via the AI Gateway
    4. Parse the response into an AISummary ORM object
    5. Save to ai_summaries, transition session → under_review

    Returns:
        The newly created AISummary record.

    Raises:
        ValueError: if the session does not exist.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # ------------------------------------------------------------------
    # 1. Load transcript messages
    # ------------------------------------------------------------------
    messages = (
        db.query(TranscriptMessage)
        .filter(TranscriptMessage.session_id == session_id)
        .order_by(TranscriptMessage.sequence_no.asc())
        .all()
    )

    transcript_text = _build_transcript_text(messages)
    logger.info(
        "generate_summary: session %s — %d messages, %d transcript chars",
        session_id, len(messages), len(transcript_text),
    )

    # ------------------------------------------------------------------
    # 2. Load rubric via material_r_id on AssessmentConfig
    # ------------------------------------------------------------------
    config = (
        db.query(AssessmentConfig)
        .filter(AssessmentConfig.id == session.assessment_config_id)
        .first()
    )
    rubric_text = ""
    if config and config.material_r_id:
        rubric_material = db.query(Material).filter(
            Material.id == config.material_r_id,
            Material.material_category == "rubric",
        ).first()
        if rubric_material:
            rubric_chunks = (
                db.query(MaterialChunk)
                .filter(MaterialChunk.material_id == rubric_material.id)
                .order_by(MaterialChunk.chunk_index)
                .all()
            )
            rubric_text = "\n\n".join(c.chunk_text for c in rubric_chunks)

    # ------------------------------------------------------------------
    # 3. Build and call LLM
    # ------------------------------------------------------------------
    rubric_section = rubric_text.strip() if rubric_text else "No rubric provided — assess based on academic quality and depth."
    user_prompt = _SUMMARY_PROMPT_TEMPLATE.format(
        rubric_section=rubric_section,
        transcript_section=transcript_text or "[Empty transcript]",
    )

    summary_text = "Advisory AI summary generation failed."
    suggested_grade: int = 0

    try:
        raw = await chat_complete(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=_SYSTEM_PROMPT,
            temperature=0.5,
            max_tokens=1800,
        )
        parsed = _parse_summary_response(raw)
        summary_text = parsed["summary_text"]

        raw_grade = parsed.get("suggested_grade")
        try:
            suggested_grade = int(raw_grade) if raw_grade is not None else 0
        except (TypeError, ValueError):
            suggested_grade = 0
        suggested_grade = max(0, min(100, suggested_grade))

    except (RuntimeError, ValueError) as exc:
        logger.error("AI summary LLM call failed for session %s: %s", session_id, exc)
        summary_text = (
            f"AI summary could not be generated (check OPENROUTER_API_KEY).\n"
            f"Session contained {len(messages)} transcript messages.\n"
            f"Rubric: {'provided' if rubric_text else 'not linked'}."
        )
        suggested_grade = 0

    # ------------------------------------------------------------------
    # 4. Save AI summary
    # ------------------------------------------------------------------
    existing = db.query(AISummary).filter(AISummary.session_id == session_id).first()
    if existing:
        db.delete(existing)
        db.flush()

    summary = AISummary(
        session_id=session_id,
        summary_text=summary_text,
        suggested_grade=suggested_grade,
    )

    db.add(summary)

    # ------------------------------------------------------------------
    # 5. Transition session to under_review
    # ------------------------------------------------------------------
    if session.status in ("under_review",):
        pass
    else:
        session.status = "under_review"

    db.commit()
    db.refresh(summary)

    logger.info("AI summary created for session %s", session_id)
    return summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_transcript_text(messages: list[TranscriptMessage]) -> str:
    """Format transcript messages as a readable dialogue string."""
    lines: list[str] = []
    for m in messages:
        role_label = {
            "main_question": "Assessor",
            "followup_question": "Assessor",
            "student_answer": "Student",
        }.get(m.message_type, "System")
        lines.append(f"[{role_label}] {m.content}")
    return "\n".join(lines)


def _parse_summary_response(raw: str) -> dict:
    """
    Parse the LLM's JSON response into a structured summary dict.
    Falls back gracefully on parse errors.
    """
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("AI summary JSON parse failed: %s\nRaw: %.500s", exc, raw)
        raise ValueError(f"Could not parse LLM summary JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("LLM summary response is not a JSON object")

    return {
        "summary_text": str(data.get("summary_text", "[No summary generated]")),
        "suggested_grade": data.get("suggested_grade"),
    }
