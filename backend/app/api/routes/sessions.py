"""
Assessment session routes (student-facing + instructor review).

Endpoints:
  POST /assessments/:id/sessions/start → start a student session
  POST /sessions/:id/respond → submit student answer
  POST /sessions/:id/complete → end session (manual or timeout)
  GET /sessions/:id → get full session with transcript

CRITICAL: Server-side timer enforcement.
  When session starts: expires_at = now() + total_time_minutes
  Every POST /respond checks: if now() > expires_at → 403 + auto-complete

TODO:
- Session start with timer calculation
- Student response persistence (transcript_messages)
- Integration with James's chat orchestrator
- Server-side expiry enforcement
"""
from fastapi import APIRouter

router = APIRouter()

# TODO: Implement session endpoints
