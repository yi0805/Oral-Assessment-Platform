"""
AI summary & instructor feedback routes.

Owner: Bess (persistence) + Joanne (AI summary)
Endpoints:
  POST /sessions/:id/ai-summary/generate → trigger AI summary generation
  GET /sessions/:id/ai-summary → get AI summary
  POST /sessions/:id/feedback → submit instructor feedback + grade
  PUT /sessions/:id/feedback → update feedback / grade
  PUT /sessions/:id/release → release results to student
  GET /sessions/:id/results → student views released results

TODO:
- AI summary trigger (calls Joanne's service)
- Instructor feedback CRUD
- Release workflow (sets released_to_student = true)
- Student results endpoint (only visible after release)
"""
from fastapi import APIRouter

router = APIRouter()

# TODO: Implement feedback endpoints
