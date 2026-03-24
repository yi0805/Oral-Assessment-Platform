"""
Question pool & question CRUD routes.

Owner: Bess (storage) + Joanne (AI generation)
Endpoints:
  POST /courses/:id/question-pools → create a new pool
  POST /question-pools/:id/generate → trigger AI question generation
  GET /question-pools/:id → get pool with all questions
  PUT /question-pools/:id/approve → mark pool as approved
  POST /question-pools/:id/questions → add custom question
  PUT /questions/:id → edit a question
  DELETE /questions/:id → remove question

TODO:
- CRUD endpoints for pools and questions
- Integration point with Joanne's AI generation service
"""
from fastapi import APIRouter

router = APIRouter()

# TODO: Implement question endpoints
