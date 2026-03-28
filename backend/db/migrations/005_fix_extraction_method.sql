-- ============================================================
-- Migration 005: Fix extraction_method CHECK constraint
--
-- Problem: The original constraint only allowed the old/planned extractor names
--   ('pypdf', 'python-pptx', 'docx-parser', 'tika')
-- but the actual pipeline code writes the real library names:
--   'pdfplumber'  — for PDF files  (uses pdfplumber library)
--   'plain_text'  — for TXT files  (raw UTF-8 decode)
--   'python-docx' — for DOCX files (uses python-docx library)
--   'python-pptx' — for PPTX files (uses python-pptx library, already in old list)
--
-- This migration:
--   1. Drops the old restrictive constraint
--   2. Migrates any stale rows that used the old names
--   3. Adds the correct constraint matching actual code values
--
-- Idempotent: Yes (IF EXISTS guards, UPDATE is safe to run multiple times)
-- ============================================================

BEGIN;

-- Step 1: Drop the old check constraint (name from migration 001)
ALTER TABLE materials
    DROP CONSTRAINT IF EXISTS materials_extraction_method_check;

-- Step 2: Migrate any existing rows that used the old extractor names
UPDATE materials SET extraction_method = 'pdfplumber'
    WHERE extraction_method = 'pypdf';

UPDATE materials SET extraction_method = 'python-docx'
    WHERE extraction_method = 'docx-parser';

-- 'tika' had no direct replacement — set to NULL so pipeline reprocesses
UPDATE materials SET extraction_method = NULL,
                     processing_status = 'uploaded',
                     processing_error  = 'Reprocessing required: tika extractor replaced'
    WHERE extraction_method = 'tika';

-- Step 3: Add correct constraint matching actual pipeline code values
ALTER TABLE materials
    ADD CONSTRAINT materials_extraction_method_check
    CHECK (extraction_method IS NULL
        OR extraction_method IN ('pdfplumber', 'plain_text', 'python-docx', 'python-pptx'));

COMMIT;
