"""
Assessment configuration routes.

Endpoints:
  POST /courses/:id/assessments → create assessment config
  GET /courses/:id/assessments → list assessments for course
  PUT /assessments/:id → update config
  PUT /assessments/:id/publish → publish assessment
  GET /assessments/:id/sessions → list all student sessions

TODO:
- [ ] CRUD for assessment configs (including v5 fields)
- [ ] Publish workflow with validation (pool approved? rubric set? open/close dates?)
"""
from fastapi import APIRouter

router = APIRouter()

# TODO: Implement assessment endpoints
