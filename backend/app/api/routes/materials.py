"""
Material upload & processing routes

Endpoints:
  POST /courses/:id/materials/upload → upload PDF to S3, create materials row
  GET /courses/:id/materials → list all materials for a course
  GET /materials/:id → get material details + processing status
  GET /materials/:id/status → poll processing status (SSE preferred)
  DELETE /materials/:id → soft-delete material + S3 object

Pipeline flow triggered by upload:
  upload → extracting → chunking → embedding → ready
  (see app/services/material_pipeline.py)

TODO (Week 4-5):
- POST upload endpoint with multipart/form-data
- S3 upload via boto3 (or local file storage for dev)
- Background task to trigger pipeline
- GET list and detail endpoints
- Status polling endpoint
"""
from fastapi import APIRouter

router = APIRouter()

# TODO: Implement material endpoints
