-- ============================================================
-- Project 20 - AI-Supported Oral Assessment Tool
-- Migration 002: pgvector Extension & HNSW Index
-- 002:pgvectorHNSW
--
-- Prerequisite: 001_foundation_tables.sql
-- Idempotent: Yes
-- ============================================================

-- Enable pgvector extension (requires superuser or rds_superuser on AWS RDS)
-- pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Add the embedding column as proper vector(1536) type
-- DBML represents this as varchar; this is the real DDL
-- vector(1536)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'material_chunks' AND column_name = 'embedding'
    ) THEN
        ALTER TABLE material_chunks ADD COLUMN embedding vector(1536);
    END IF;
END
$$;

-- HNSW index for cosine similarity search
-- HNSW
-- m=16 (connections per node), ef_construction=64 (build-time accuracy)
-- These are good defaults for datasets < 100K vectors (our scale)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
    ON material_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

COMMENT ON COLUMN material_chunks.embedding IS 'vector(1536) — OpenAI ada-002 compatible embeddings, indexed via HNSW';

-- ============================================================
-- Migration complete. .
-- Next: 003_assessment_runtime.sql
-- ============================================================
