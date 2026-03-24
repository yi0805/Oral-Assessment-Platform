"""
Material processing pipeline — BESS'S SIGNATURE DELIVERABLE.
 — BESS.

Owner: Bess
Pipeline stages:
  1. UPLOAD → S3 stores blob, materials row created (status: uploaded)
  2. EXTRACT → PyPDF2/pdfplumber extracts text (status: extracting → chunking)
  3. CHUNK → Split into ~500-token segments (status: chunking → embedding)
  4. EMBED → OpenAI embedding API → vector(1536) (status: embedding → ready)

Design principles (from schema architecture):
  - Idempotent: safe to retry from any failed stage
  - Observable: processing_status tracks current stage, processing_error stores failures
  - Resumable: pipeline restarts from failed stage, not from scratch

S3 key convention: courses/{course_id}/materials/{material_id}/{original_filename}

TODO (Week 4-5 — HIGHEST PRIORITY):
- [ ] implement upload_to_s3(file, course_id, material_id)
- [ ] implement extract_text(material_id) — PDF text extraction
- [ ] implement chunk_text(material_id) — ~500 token splitting with overlap
- [ ] implement embed_chunks(material_id) — OpenAI API → pgvector storage
- [ ] implement run_pipeline(material_id) — orchestrates all 4 stages
- [ ] implement retry_from_failure(material_id) — resumes from failed stage
"""
pass
