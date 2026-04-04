-- ============================================================
-- Project 20 — AI-Supported Oral Assessment Tool
-- Migration 001: Complete Schema
--
-- Replaces: 001_foundation_tables.sql + 002_pgvector_patch.sql
--           + 003_assessment_runtime.sql + 004_gemini_vector_patch.sql
--           + 008_suggested_grade.sql
--
-- Run target: PostgreSQL 15+ (AWS RDS or local)
-- Idempotent: Yes (all statements use IF NOT EXISTS / DO blocks)
-- pgvector must be installed: run CREATE EXTENSION vector first
--   (or set it via RDS parameter group / Trusted Extensions)
-- ============================================================


-- ============================================================
-- Extensions
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";    -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;        -- pgvector (768-dim embeddings)


-- ============================================================
-- 1. users
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    google_sub   VARCHAR     UNIQUE,
    email        VARCHAR     NOT NULL UNIQUE,
    full_name    VARCHAR     NOT NULL,
    role         VARCHAR     NOT NULL CHECK (role IN ('student', 'instructor', 'admin')),
    status       VARCHAR     NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  users            IS 'System users authenticated via Google OAuth.';
COMMENT ON COLUMN users.role       IS 'student | instructor | admin';
COMMENT ON COLUMN users.google_sub IS 'Google OAuth subject ID — unique identifier from Google.';


-- ============================================================
-- 2. courses
-- ============================================================

CREATE TABLE IF NOT EXISTS courses (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_code  VARCHAR,
    course_name  VARCHAR     NOT NULL,
    term         VARCHAR,
    description  TEXT,
    created_by   UUID        REFERENCES users(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_courses_course_code ON courses(course_code);
COMMENT ON TABLE courses IS 'Course metadata including code, title, term, and creator.';


-- ============================================================
-- 3. course_enrollments
-- ============================================================

CREATE TABLE IF NOT EXISTS course_enrollments (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id   UUID        NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    user_id     UUID        NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
    course_role VARCHAR     NOT NULL CHECK (course_role IN ('student', 'instructor', 'ta')),
    is_active   BOOLEAN     NOT NULL DEFAULT true,
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (course_id, user_id)
);

COMMENT ON TABLE course_enrollments IS 'Junction table linking users to courses with a per-course role.';


-- ============================================================
-- 4. materials
-- ============================================================

CREATE TABLE IF NOT EXISTS materials (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id         UUID        NOT NULL REFERENCES courses(id)  ON DELETE CASCADE,
    uploaded_by       UUID        REFERENCES users(id)             ON DELETE SET NULL,
    title             VARCHAR     NOT NULL,
    original_filename VARCHAR     NOT NULL,
    file_type         VARCHAR     NOT NULL CHECK (file_type IN ('pdf', 'pptx', 'docx', 'txt')),
    mime_type         VARCHAR,
    storage_key       VARCHAR     NOT NULL UNIQUE,
    file_size_bytes   BIGINT,
    extracted_text    TEXT,
    page_count        INT,
    extraction_method VARCHAR     CHECK (
                          extraction_method IS NULL OR
                          extraction_method IN ('pdfplumber', 'python-pptx', 'python-docx', 'plain_text')
                      ),
    processing_status VARCHAR     NOT NULL DEFAULT 'uploaded' CHECK (
                          processing_status IN ('uploaded', 'extracting', 'chunking', 'embedding', 'ready', 'failed')
                      ),
    processing_error  TEXT,
    total_chunks      INT,
    uploaded_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at      TIMESTAMPTZ,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_materials_course_id         ON materials(course_id);
CREATE INDEX IF NOT EXISTS idx_materials_processing_status ON materials(processing_status);

COMMENT ON TABLE  materials                   IS 'Uploaded course files plus extraction and processing state.';
COMMENT ON COLUMN materials.storage_key       IS 'S3 object key: courses/{course_id}/materials/{material_id}/{filename}';
COMMENT ON COLUMN materials.processing_status IS 'Pipeline state: uploaded → extracting → chunking → embedding → ready | failed';


-- ============================================================
-- 5. material_chunks  (with vector(768) from the start)
-- ============================================================

CREATE TABLE IF NOT EXISTS material_chunks (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id       UUID        NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    chunk_index       INT         NOT NULL,
    chunk_text        TEXT        NOT NULL,
    token_count       INT,
    embedding         vector(768),          -- Google gemini-embedding-001 (768-dim)
    source_page_start INT,
    source_page_end   INT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (material_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_material_chunks_material_id ON material_chunks(material_id);

-- HNSW index for fast cosine similarity search (RAG retrieval)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
    ON material_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

COMMENT ON TABLE  material_chunks           IS 'RAG course memory: chunked text with 768-dim vector embeddings.';
COMMENT ON COLUMN material_chunks.embedding IS 'vector(768) — Google gemini-embedding-001, indexed via HNSW cosine.';
COMMENT ON COLUMN material_chunks.chunk_index IS '0-based sequential position within the parent material.';


-- ============================================================
-- 6. rubrics
-- ============================================================

CREATE TABLE IF NOT EXISTS rubrics (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id         UUID        NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title             VARCHAR     NOT NULL,
    description       TEXT,
    rubric_text       TEXT        NOT NULL,
    original_filename VARCHAR,
    storage_key       VARCHAR,
    created_by        UUID        REFERENCES users(id) ON DELETE SET NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rubrics_course_id ON rubrics(course_id);
COMMENT ON TABLE  rubrics            IS 'Assessment rubrics used to guide AI question generation and evaluation.';
COMMENT ON COLUMN rubrics.rubric_text IS 'Full rubric content as plain text; injected into AI prompts.';


-- ============================================================
-- 7. question_pools
-- ============================================================

CREATE TABLE IF NOT EXISTS question_pools (
    id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id                   UUID        NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title                       VARCHAR     NOT NULL,
    description                 TEXT,
    generated_from_materials    JSONB,
    generation_method           VARCHAR     NOT NULL CHECK (generation_method IN ('manual', 'ai_generated', 'hybrid')),
    created_by                  UUID        REFERENCES users(id) ON DELETE SET NULL,
    approved_by                 UUID        REFERENCES users(id) ON DELETE SET NULL,
    status                      VARCHAR     NOT NULL DEFAULT 'draft'
                                    CHECK (status IN ('draft', 'reviewed', 'approved', 'archived')),
    approved_at                 TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_question_pools_course_id ON question_pools(course_id);
CREATE INDEX IF NOT EXISTS idx_question_pools_status    ON question_pools(status);
COMMENT ON TABLE question_pools IS 'Approval container for a reusable set of generated or curated questions.';


-- ============================================================
-- 8. questions
-- ============================================================

CREATE TABLE IF NOT EXISTS questions (
    id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    question_pool_id   UUID        NOT NULL REFERENCES question_pools(id) ON DELETE CASCADE,
    parent_question_id UUID        REFERENCES questions(id) ON DELETE SET NULL,
    question_text      TEXT        NOT NULL,
    question_kind      VARCHAR     NOT NULL CHECK (question_kind IN ('main', 'followup', 'probe')),
    answer_style       VARCHAR     NOT NULL CHECK (answer_style IN ('short', 'long', 'mixed')),
    difficulty         VARCHAR     CHECK (difficulty IS NULL OR difficulty IN ('easy', 'medium', 'hard')),
    learning_objective TEXT,
    source_chunk_refs  JSONB,
    display_order      INT,
    is_active          BOOLEAN     NOT NULL DEFAULT true,
    created_by         UUID        REFERENCES users(id) ON DELETE SET NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_questions_pool_id    ON questions(question_pool_id);
CREATE INDEX IF NOT EXISTS idx_questions_parent_id  ON questions(parent_question_id);
CREATE INDEX IF NOT EXISTS idx_questions_pool_order ON questions(question_pool_id, display_order);
COMMENT ON TABLE questions IS 'Approved question-bank entries, including main questions and follow-up templates.';


-- ============================================================
-- 9. assessment_configs
-- ============================================================

CREATE TABLE IF NOT EXISTS assessment_configs (
    id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id                   UUID        NOT NULL REFERENCES courses(id)       ON DELETE CASCADE,
    question_pool_id            UUID        REFERENCES question_pools(id)          ON DELETE RESTRICT,
    title                       VARCHAR     NOT NULL,
    instructions                TEXT,
    assessment_mode             VARCHAR     NOT NULL DEFAULT 'generic'
                                    CHECK (assessment_mode IN ('generic', 'personalized')),
    rubric_id                   UUID        REFERENCES rubrics(id)                ON DELETE SET NULL,
    total_time_minutes          INT         NOT NULL DEFAULT 15,
    per_question_time_limit_minutes INT,
    max_main_questions          INT,
    max_followups_per_main      INT         NOT NULL DEFAULT 3,
    followup_enabled            BOOLEAN     NOT NULL DEFAULT true,
    open_at                     TIMESTAMPTZ,
    close_at                    TIMESTAMPTZ,
    status                      VARCHAR     NOT NULL DEFAULT 'draft'
                                    CHECK (status IN ('draft', 'published', 'closed')),
    published_by                UUID        REFERENCES users(id)                  ON DELETE SET NULL,
    published_at                TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_schedule_order CHECK (
        open_at IS NULL OR close_at IS NULL OR close_at > open_at
    ),
    CONSTRAINT chk_config_question_source CHECK (
        (assessment_mode = 'generic' AND question_pool_id IS NOT NULL)
        OR assessment_mode = 'personalized'
    )
);

CREATE INDEX IF NOT EXISTS idx_assessment_configs_course_id ON assessment_configs(course_id);
CREATE INDEX IF NOT EXISTS idx_assessment_configs_status    ON assessment_configs(status);
COMMENT ON TABLE  assessment_configs                         IS 'Assessment setup: timing, mode, and question source.';
COMMENT ON COLUMN assessment_configs.max_main_questions      IS 'Max main questions per session (null = use all in pool).';
COMMENT ON COLUMN assessment_configs.per_question_time_limit_minutes IS 'Null means only the overall timer is enforced.';


-- ============================================================
-- 10. assessment_sessions
-- ============================================================

CREATE TABLE IF NOT EXISTS assessment_sessions (
    id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_config_id  UUID        NOT NULL REFERENCES assessment_configs(id) ON DELETE CASCADE,
    course_id             UUID        NOT NULL REFERENCES courses(id)            ON DELETE CASCADE,
    student_id            UUID        NOT NULL REFERENCES users(id)              ON DELETE CASCADE,
    started_by            UUID        REFERENCES users(id)                       ON DELETE SET NULL,
    status                VARCHAR     NOT NULL DEFAULT 'not_started'
                              CHECK (status IN ('not_started', 'in_progress', 'submitted',
                                                'time_expired', 'under_review', 'released')),
    started_at            TIMESTAMPTZ,
    expires_at            TIMESTAMPTZ,
    ended_at              TIMESTAMPTZ,
    total_messages        INT,
    current_main_index    INT,
    current_followup_index INT,
    transcript_locked     BOOLEAN     NOT NULL DEFAULT false,
    released_at           TIMESTAMPTZ,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sessions_student_id      ON assessment_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_course_id       ON assessment_sessions(course_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status          ON assessment_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_config_student  ON assessment_sessions(assessment_config_id, student_id);
COMMENT ON TABLE  assessment_sessions                  IS 'One student attempt at one published assessment.';
COMMENT ON COLUMN assessment_sessions.transcript_locked IS 'True when the session ends — prevents further message writes.';


-- ============================================================
-- 11. session_question_items
-- ============================================================

CREATE TABLE IF NOT EXISTS session_question_items (
    id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id         UUID        NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    source_question_id UUID        REFERENCES questions(id)                    ON DELETE SET NULL,
    parent_item_id     UUID        REFERENCES session_question_items(id)       ON DELETE SET NULL,
    asked_text         TEXT        NOT NULL,
    question_kind      VARCHAR     NOT NULL CHECK (question_kind IN ('main', 'followup', 'probe')),
    main_group_no      INT,
    followup_no        INT,
    generated_by       VARCHAR     NOT NULL
                           CHECK (generated_by IN ('approved_pool', 'adaptive_ai', 'instructor_override')),
    rag_chunk_refs     JSONB,
    asked_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_answered        BOOLEAN     NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_sqi_session_id        ON session_question_items(session_id);
CREATE INDEX IF NOT EXISTS idx_sqi_source_question_id ON session_question_items(source_question_id);
CREATE INDEX IF NOT EXISTS idx_sqi_parent_item_id    ON session_question_items(parent_item_id);
CREATE INDEX IF NOT EXISTS idx_sqi_session_group     ON session_question_items(session_id, main_group_no, followup_no);
COMMENT ON TABLE session_question_items IS 'Runtime questions actually asked during a live session.';


-- ============================================================
-- 12. transcript_messages
-- ============================================================

CREATE TABLE IF NOT EXISTS transcript_messages (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id              UUID        NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    session_question_item_id UUID       REFERENCES session_question_items(id)      ON DELETE SET NULL,
    sender_role             VARCHAR     NOT NULL
                                CHECK (sender_role IN ('system', 'assistant', 'student', 'instructor')),
    message_type            VARCHAR     NOT NULL
                                CHECK (message_type IN ('main_question', 'followup_question',
                                                        'student_answer', 'system_notice', 'summary_notice')),
    sequence_no             INT         NOT NULL,
    content                 TEXT        NOT NULL,
    token_count             INT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, sequence_no)
);

CREATE INDEX IF NOT EXISTS idx_transcript_session_id ON transcript_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_transcript_sqi_id     ON transcript_messages(session_question_item_id);
COMMENT ON TABLE  transcript_messages            IS 'Immutable transcript turns recorded during a live session.';
COMMENT ON COLUMN transcript_messages.sequence_no IS 'Strictly ordered within a session.';


-- ============================================================
-- 13. ai_summaries  (includes suggested_grade from the start)
-- ============================================================

CREATE TABLE IF NOT EXISTS ai_summaries (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID        NOT NULL UNIQUE REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    summary_text    TEXT        NOT NULL,
    strengths       TEXT,
    gaps            TEXT,
    suggested_grade INTEGER,    -- Advisory only (e.g. 0-100)
    evidence_refs   JSONB,
    model_name      VARCHAR     NOT NULL,
    advisory_only   BOOLEAN     NOT NULL DEFAULT true,
    status          VARCHAR     NOT NULL DEFAULT 'success' CHECK (status IN ('success', 'failed')),
    error_message   TEXT,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  ai_summaries                IS 'AI-generated evidence summary to support instructor judgement.';
COMMENT ON COLUMN ai_summaries.advisory_only  IS 'Always true — the AI never assigns the official grade.';
COMMENT ON COLUMN ai_summaries.suggested_grade IS 'Advisory grade from AI (e.g. 0-100). Never auto-assigned.';


-- ============================================================
-- 14. instructor_feedback
-- ============================================================

CREATE TABLE IF NOT EXISTS instructor_feedback (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id              UUID        NOT NULL UNIQUE REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    instructor_id           UUID        REFERENCES users(id) ON DELETE SET NULL,
    comments                TEXT,
    grading_rationale       TEXT,
    provisional_grade       INTEGER,
    final_grade             INTEGER,
    student_visible_comments TEXT,
    released_to_student     BOOLEAN     NOT NULL DEFAULT false,
    released_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_instructor_id ON instructor_feedback(instructor_id);
CREATE INDEX IF NOT EXISTS idx_feedback_released      ON instructor_feedback(released_to_student);
COMMENT ON TABLE  instructor_feedback                      IS 'Instructor-authored grade and feedback.';
COMMENT ON COLUMN instructor_feedback.released_to_student  IS 'Controls student visibility of feedback and results.';


-- ============================================================
-- Schema complete.
-- ============================================================
