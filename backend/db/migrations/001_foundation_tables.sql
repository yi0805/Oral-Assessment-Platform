-- ============================================================
-- Project 20 - AI-Supported Oral Assessment Tool
-- Migration 001: Foundation Tables (Phase 1)
--
-- Tables created (8):
-- users, courses, course_enrollments, materials,
-- material_chunks, rubrics, question_pools, questions
--
-- Run target: PostgreSQL 15+ on AWS RDS
-- Idempotent: Yes
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- for uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- for gen_random_uuid() as alternative


-- ============================================================
-- 1. users
-- Who can use the system
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_sub VARCHAR UNIQUE, -- Google OAuth subject ID
    email VARCHAR NOT NULL UNIQUE,
    full_name VARCHAR NOT NULL,
    role VARCHAR NOT NULL -- student | instructor | admin
                    CHECK (role IN ('student', 'instructor', 'admin')),
    status VARCHAR NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'suspended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes (unique constraints already create indexes for email and google_sub)
-- (emailgoogle_sub)

COMMENT ON TABLE users IS 'System users authenticated via Google OAuth.';
COMMENT ON COLUMN users.role IS 'student | instructor | admin; enforced by a CHECK constraint and validated again at the API layer.';
COMMENT ON COLUMN users.google_sub IS 'Google OAuth subject ID — unique identifier from Google, populated on first login';


-- ============================================================
-- 2. courses
-- One-sentence truth: What courses exist
-- ============================================================
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_code VARCHAR, -- e.g. COMPSCI399
    course_name VARCHAR NOT NULL,
    term VARCHAR, -- e.g. 2026-S1
    description TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_courses_course_code ON courses(course_code);

COMMENT ON TABLE courses IS 'Course metadata including code, title, term, and creator.';


-- ============================================================
-- 3. course_enrollments
-- One-sentence truth: Who belongs to which course in what role
-- ============================================================
CREATE TABLE IF NOT EXISTS course_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_role VARCHAR NOT NULL -- student | instructor | ta
                    CHECK (course_role IN ('student', 'instructor', 'ta')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- One enrollment per user per course
    --
    UNIQUE (course_id, user_id)
);

COMMENT ON TABLE course_enrollments IS 'Junction table linking users to courses with a per-course role.';


-- ============================================================
-- 4. materials
-- One-sentence truth: What files were uploaded + processing state
-- ============================================================
CREATE TABLE IF NOT EXISTS materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR NOT NULL,
    original_filename VARCHAR NOT NULL,
    file_type VARCHAR NOT NULL -- pdf | pptx | docx | txt
                        CHECK (file_type IN ('pdf', 'pptx', 'docx', 'txt')),
    mime_type VARCHAR,
    storage_key VARCHAR NOT NULL UNIQUE, -- S3 object key
    file_size_bytes BIGINT,

    -- Extraction fields merged here for MVP simplicity
    -- MVP,
    extracted_text TEXT, -- Full extracted text for re-chunking
    page_count INT,
    extraction_method VARCHAR -- pypdf | python-pptx | docx-parser | tika
                        CHECK (extraction_method IS NULL OR
                               extraction_method IN ('pypdf', 'python-pptx', 'docx-parser', 'tika')),

    processing_status VARCHAR NOT NULL DEFAULT 'uploaded'
                        CHECK (processing_status IN ('uploaded', 'extracting', 'chunking', 'embedding', 'ready', 'failed')),
    processing_error TEXT,
    total_chunks INT,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_materials_course_id ON materials(course_id);
CREATE INDEX IF NOT EXISTS idx_materials_processing_status ON materials(processing_status);

COMMENT ON TABLE materials IS 'Uploaded course files plus extraction and processing state.';
COMMENT ON COLUMN materials.storage_key IS 'S3 object key, for example courses/{course_id}/materials/{material_id}/{filename}.';
COMMENT ON COLUMN materials.processing_status IS 'Pipeline state machine: uploaded → extracting → chunking → embedding → ready | failed';


-- ============================================================
-- 5. material_chunks
-- One-sentence truth: RAG-ready text segments with vector embeddings
-- NOTE: The embedding column uses pgvector's vector(1536) type,
-- created in migration 002_pgvector_patch.sql
-- DBML represents this as varchar because DBML has no vector type.
-- ============================================================
CREATE TABLE IF NOT EXISTS material_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL, -- 0-based position within material
    chunk_text TEXT NOT NULL, -- ~500 tokens per chunk
    token_count INT,
    -- embedding column added in 002_pgvector_patch.sql as vector(1536)
    source_page_start INT,
    source_page_end INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (material_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_material_chunks_material_id ON material_chunks(material_id);

COMMENT ON TABLE material_chunks IS 'RAG course memory: chunked text with vector embeddings / RAG:';
COMMENT ON COLUMN material_chunks.chunk_index IS '0-based sequential position within the parent material';


-- ============================================================
-- 6. rubrics
-- One-sentence truth: What rubric guides AI generation and evaluation
-- ============================================================
CREATE TABLE IF NOT EXISTS rubrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR NOT NULL,
    description TEXT,
    rubric_text TEXT NOT NULL, -- Full rubric content as text — fed to AI as prompt context
    original_filename VARCHAR, -- Null if manually entered
    storage_key VARCHAR, -- S3 key if uploaded as PDF/CSV; null if typed in
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rubrics_course_id ON rubrics(course_id);

COMMENT ON TABLE rubrics IS 'Assessment rubrics used to guide AI question generation and summary support.';
COMMENT ON COLUMN rubrics.rubric_text IS 'Full rubric content as plain text; this is the version injected into AI prompts.';


-- ============================================================
-- 7. question_pools
-- One-sentence truth: Container for approved question sets
-- ============================================================
CREATE TABLE IF NOT EXISTS question_pools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR NOT NULL,
    description TEXT,
    generated_from_materials JSONB, -- Array of material IDs (JSONB for query flexibility)
    generation_method VARCHAR NOT NULL -- manual | ai_generated | hybrid
                            CHECK (generation_method IN ('manual', 'ai_generated', 'hybrid')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR NOT NULL DEFAULT 'draft'
                            CHECK (status IN ('draft', 'reviewed', 'approved', 'archived')),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_question_pools_course_id ON question_pools(course_id);
CREATE INDEX IF NOT EXISTS idx_question_pools_status ON question_pools(status);

COMMENT ON TABLE question_pools IS 'Approval container for a reusable set of generated or manually curated questions.';
COMMENT ON COLUMN question_pools.generated_from_materials IS 'JSONB array of material UUIDs used as source context for question generation.';


-- ============================================================
-- 8. questions
-- One-sentence truth: Individual bank questions (main + follow-up templates)
-- ============================================================
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_pool_id UUID NOT NULL REFERENCES question_pools(id) ON DELETE CASCADE,
    parent_question_id UUID REFERENCES questions(id) ON DELETE SET NULL, -- Null = main; set = follow-up template
    question_text TEXT NOT NULL,
    question_kind VARCHAR NOT NULL -- main | followup | probe
                        CHECK (question_kind IN ('main', 'followup', 'probe')),
    answer_style VARCHAR NOT NULL -- short | long | mixed
                        CHECK (answer_style IN ('short', 'long', 'mixed')),
    difficulty VARCHAR -- easy | medium | hard
                        CHECK (difficulty IS NULL OR difficulty IN ('easy', 'medium', 'hard')),
    learning_objective TEXT,
    source_chunk_refs JSONB, -- Chunk IDs grounding this bank question
    display_order INT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_questions_pool_id ON questions(question_pool_id);
CREATE INDEX IF NOT EXISTS idx_questions_parent_id ON questions(parent_question_id);
CREATE INDEX IF NOT EXISTS idx_questions_pool_order ON questions(question_pool_id, display_order);

COMMENT ON TABLE questions IS 'Approved question-bank entries, including main questions and follow-up templates.';
COMMENT ON COLUMN questions.parent_question_id IS 'Self-reference: NULL means a main question; a value means this row is a follow-up template attached to a parent main question.';


-- ============================================================
-- Migration complete. .
-- Next: 002_pgvector_patch.sql (adds vector column + HNSW index)
-- ============================================================
