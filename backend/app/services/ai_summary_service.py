"""
AI summary generation service.
AI.

Owner: Joanne (prompt design) + Bess (data storage)
Called after session completes. Generates an advisory summary that is:
  - Evidence-Based: includes short quotes from transcript
  - Rubric-Linked: evaluates against the rubric
  - Strengths & Gaps: highlights understanding vs. gaps
  - Advisory only: never auto-assigns grades

TODO (Week 7):
- [ ] generate_summary(session_id) → AISummary record
- [ ] Reads transcript_messages + rubric_text as context
- [ ] Saves to ai_summaries table
"""
pass
