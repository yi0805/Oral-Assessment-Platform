"""
AI summary generation service.
Called after a session completes to produce an advisory analysis.

Per the user flow (Phase 5), the summary must be:
  - Evidence-based: includes short quotes from the transcript
  - Rubric-linked: evaluates against the provided rubric
  - Strengths & gaps: clearly highlights understanding vs. gaps
  - Advisory only: suggested grade, never auto-assigned

Owned jointly by Joanne (prompt design) and Bess (data storage).
"""
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.assessment import AssessmentConfig, AssessmentSession
from app.models.session_runtime import TranscriptMessage
from app.models.rubric import Rubric
from app.models.feedback import AISummary

logger = logging.getLogger(__name__)


async def generate_summary(db: Session, session_id: UUID) -> AISummary:
    """
    Generate an AI summary for a completed assessment session.

    Steps:
    1. Load the full transcript
    2. Load the rubric associated with the assessment
    3. Call LLM with transcript + rubric context
    4. Parse response into structured summary (strengths, gaps, evidence)
    5. Save to ai_summaries table

    Joanne will provide the actual prompt template and LLM integration.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Load transcript messages
    messages = (
        db.query(TranscriptMessage)
        .filter(TranscriptMessage.session_id == session_id)
        .order_by(TranscriptMessage.sequence_no.asc())
        .all()
    )

    # Build transcript text for the LLM prompt
    transcript_text = "\n".join(
        f"[{m.sender_role}] {m.content}" for m in messages
    )

    # Load rubric if linked
    config = db.query(AssessmentConfig).filter(AssessmentConfig.id == session.assessment_config_id).first()
    rubric_text = ""
    if config and config.rubric_id:
        rubric = db.query(Rubric).filter(Rubric.id == config.rubric_id).first()
        if rubric:
            rubric_text = rubric.rubric_text

    # TODO: Joanne replaces this section with actual LLM call
    # The prompt should produce:
    #   - summary_text: overall narrative
    #   - strengths: what the student demonstrated well
    #   - gaps: where understanding is lacking
    #   - evidence_refs: message IDs that support the analysis
    #
    # For now, create a placeholder summary
    logger.info(f"Generating AI summary for session {session_id} ({len(messages)} messages)")

    evidence_ids = [str(m.id) for m in messages if m.sender_role == "student"][:5]

    summary = AISummary(
        session_id=session_id,
        summary_text=(
            f"[AI summary pending Joanne's LLM integration]\n"
            f"Session contained {len(messages)} messages.\n"
            f"Rubric context: {'provided' if rubric_text else 'not linked'}"
        ),
        strengths="[Pending LLM analysis of student strengths]",
        gaps="[Pending LLM analysis of understanding gaps]",
        evidence_refs=evidence_ids,
        model_name="gpt-4o",
        advisory_only=True,
        status="success",
    )
    db.add(summary)

    # Transition session status
    session.status = "under_review"
    db.commit()
    db.refresh(summary)

    logger.info(f"AI summary created for session {session_id}")
    return summary
