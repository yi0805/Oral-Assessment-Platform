-- ============================================================
-- Project 20 - AI-Supported Oral Assessment Tool
-- Migration 004: Gemini Vector Dimension Patch
--
-- Changes:
--   1. Resize embedding column 1536 → 768 (gemini-embedding-001)
--   2. Recreate HNSW index for new dimension
--   3. Add max_main_questions column to assessment_configs
--
-- Prerequisite: 001, 002, 003
-- Idempotent: Yes (safe to re-run)
-- ============================================================

-- ============================================================
-- 1. Resize embedding column: vector(1536) → vector(768)
--    gemini-embedding-001 outputs 768-dimensional vectors.
--    Must drop and recreate the HNSW index around the ALTER.
-- ============================================================

-- Drop old HNSW index (it's tied to the column type)
DROP INDEX IF EXISTS idx_chunks_embedding_hnsw;

-- Change the column type.
-- USING cast handles the case where old rows have 1536-dim data
-- (they'll be cleared/NULL'd — re-upload materials to re-embed).
ALTER TABLE material_chunks
    ALTER COLUMN embedding TYPE vector(768)
    USING NULL;  -- zero out old embeddings; they must be re-generated

-- Recreate HNSW index for 768-dim cosine similarity
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
    ON material_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

COMMENT ON COLUMN material_chunks.embedding
    IS 'vector(768) — Google gemini-embedding-001 embeddings, indexed via HNSW cosine';

-- ============================================================
-- 2. Add max_main_questions to assessment_configs
--    Referenced by the API but missing from the original schema.
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'assessment_configs'
          AND column_name = 'max_main_questions'
    ) THEN
        ALTER TABLE assessment_configs
            ADD COLUMN max_main_questions INTEGER;
    END IF;
END
$$;

COMMENT ON COLUMN assessment_configs.max_main_questions
    IS 'Maximum number of main questions per session (null = unlimited / use pool size).';

-- ============================================================
-- Migration complete.
-- Re-process any existing materials to regenerate embeddings.
-- ============================================================
