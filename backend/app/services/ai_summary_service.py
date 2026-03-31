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
from app.models.rubric import Rubric
from app.models.session_runtime import TranscriptMessage
from app.services.ai_gateway import OPENROUTER_MODEL, chat_complete

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
  "summary_text": "string — 2-4 paragraph narrative overview of the student's performance",
  "strengths": "string — bullet-point list (use \\n- prefix) of demonstrated strengths with evidence",
  "gaps": "string — bullet-point list (use \\n- prefix) of knowledge gaps or weak areas with evidence",
  "suggested_grade": "string — e.g. A, B+, C, Pass, Fail — advisory only",
  "evidence_quotes": ["array", "of", "short", "direct", "quotes", "from", "transcript"]
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
    # 2. Load rubric
    # ------------------------------------------------------------------
    config = (
        db.query(AssessmentConfig)
        .filter(AssessmentConfig.id == session.assessment_config_id)
        .first()
    )
    rubric_text = ""
    if config and config.rubric_id:
        rubric = db.query(Rubric).filter(Rubric.id == config.rubric_id).first()
        if rubric:
            rubric_text = rubric.rubric_text

    # ------------------------------------------------------------------
    # 3. Build and call LLM
    # ------------------------------------------------------------------
    rubric_section = rubric_text.strip() if rubric_text else "No rubric provided — assess based on academic quality and depth."
    user_prompt = _SUMMARY_PROMPT_TEMPLATE.format(
        rubric_section=rubric_section,
        transcript_section=transcript_text or "[Empty transcript]",
    )

    summary_text = "Advisory AI summary generation failed."
    strengths = ""
    gaps = ""
    evidence_refs: list[str] = []
    suggested_grade: str | None = None
    error_message: str | None = None
    summary_status = "success"

    try:
        raw = await chat_complete(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=_SYSTEM_PROMPT,
            temperature=0.5,
            max_tokens=1800,
        )
        parsed = _parse_summary_response(raw, messages)
        summary_text = parsed["summary_text"]
        strengths = parsed["strengths"]
        gaps = parsed["gaps"]
        suggested_grade = parsed.get("suggested_grade")
        evidence_refs = parsed.get("evidence_refs", [])
    except (RuntimeError, ValueError) as exc:
        logger.error("AI summary LLM call failed for session %s: %s", session_id, exc)
        error_message = str(exc)
        summary_status = "failed"
        summary_text = (
            f"AI summary could not be generated (check OPENROUTER_API_KEY).\n"
            f"Session contained {len(messages)} transcript messages.\n"
            f"Rubric: {'provided' if rubric_text else 'not linked'}."
        )
        strengths = "[Not available — AI generation failed]"
        gaps = "[Not available — AI generation failed]"
        # Still reference student message IDs as placeholders
        evidence_refs = [str(m.id) for m in messages if m.sender_role == "student"][:5]

    # ------------------------------------------------------------------
    # 4. Save AI summary
    # ------------------------------------------------------------------
    # Remove any existing summary for this session (idempotent)
    existing = db.query(AISummary).filter(AISummary.session_id == session_id).first()
    if existing:
        db.delete(existing)
        db.flush()

    summary = AISummary(
        session_id=session_id,
        summary_text=summary_text,
        strengths=strengths,
        gaps=gaps,
        evidence_refs=evidence_refs,
        suggested_grade=suggested_grade,
        model_name=f"{OPENROUTER_MODEL} (via OpenRouter)",
        advisory_only=True,
        status=summary_status,
        error_message=error_message,
    )

    db.add(summary)

    # ------------------------------------------------------------------
    # 5. Transition session to under_review
    # ------------------------------------------------------------------
    if session.status in ("submitted", "time_expired"):
        session.status = "under_review"

    db.commit()
    db.refresh(summary)

    logger.info("AI summary created for session %s [%s]", session_id, summary_status)
    return summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_transcript_text(messages: list[TranscriptMessage]) -> str:
    """Format transcript messages as a readable dialogue string."""
    lines: list[str] = []
    for m in messages:
        role_label = {
            "assistant": "Assessor",
            "student": "Student",
            "system": "System",
            "instructor": "Instructor",
        }.get(m.sender_role, m.sender_role.title())
        lines.append(f"[{role_label}] {m.content}")
    return "\n".join(lines)


def _parse_summary_response(
    raw: str,
    messages: list[TranscriptMessage],
) -> dict:
    """
    Parse the LLM's JSON response into a structured summary dict.
    Falls back gracefully on parse errors.
    """
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()

    # Find the outermost JSON object
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

    # Extract evidence: map quoted text fragments to message IDs
    evidence_quotes: list[str] = data.get("evidence_quotes", [])
    evidence_ids: list[str] = _match_evidence_to_messages(evidence_quotes, messages)

    return {
        "summary_text": str(data.get("summary_text", "[No summary generated]")),
        "strengths": str(data.get("strengths", "")),
        "gaps": str(data.get("gaps", "")),
        "suggested_grade": data.get("suggested_grade"),
        "evidence_refs": evidence_ids,
    }


def _match_evidence_to_messages(
    quotes: list[str],
    messages: list[TranscriptMessage],
) -> list[str]:
    """
    Attempt to find transcript messages that contain each evidence quote.
    Returns a list of message ID strings for use as evidence_refs.
    """
    matched_ids: list[str] = []
    for quote in quotes:
        quote_lower = quote.lower().strip()
        if not quote_lower:
            continue
        for msg in messages:
            if quote_lower in msg.content.lower():
                msg_id = str(msg.id)
                if msg_id not in matched_ids:
                    matched_ids.append(msg_id)
                break
    # If no matches, fall back to the first 3 student messages
    if not matched_ids:
        matched_ids = [
            str(m.id) for m in messages if m.sender_role == "student"
        ][:3]
    return matched_ids
