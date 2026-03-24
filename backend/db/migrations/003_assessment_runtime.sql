-- ============================================================
-- Project 20 - AI-Supported Oral Assessment Tool
-- Migration 003: Assessment Runtime and Post-Assessment Tables
--
-- Tables created:
-- assessment_configs, assessment_sessions,
-- session_question_items, transcript_messages,
-- ai_summaries, instructor_feedback
--
-- Prerequisite: 001_foundation_tables.sql
-- Idempotent: Yes
-- ============================================================

CREATE TABLE IF NOT EXISTS assessment_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    question_pool_id UUID REFERENCES question_pools(id) ON DELETE RESTRICT,
    title VARCHAR NOT NULL,
    instructions TEXT,
    assessment_mode VARCHAR NOT NULL DEFAULT 'generic'
                                    CHECK (assessment_mode IN ('generic', 'personalized')),
    rubric_id UUID REFERENCES rubrics(id) ON DELETE SET NULL,
    total_time_minutes INT NOT NULL DEFAULT 15,
    per_question_time_limit_seconds INT,
    max_followups_per_main INT NOT NULL DEFAULT 3,
    followup_enabled BOOLEAN NOT NULL DEFAULT true,
    open_at TIMESTAMPTZ,
    close_at TIMESTAMPTZ,
    status VARCHAR NOT NULL DEFAULT 'draft'
                                    CHECK (status IN ('draft', 'published', 'closed')),
    published_by UUID REFERENCES users(id) ON DELETE SET NULL,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_schedule_order CHECK (
        open_at IS NULL OR close_at IS NULL OR close_at > open_at
    ),
    CONSTRAINT chk_config_question_source CHECK (
        (assessment_mode = 'generic' AND question_pool_id IS NOT NULL)
        OR assessment_mode = 'personalized'
    )
);

CREATE INDEX IF NOT EXISTS idx_assessment_configs_course_id ON assessment_configs(course_id);
CREATE INDEX IF NOT EXISTS idx_assessment_configs_status ON assessment_configs(status);

COMMENT ON TABLE assessment_configs IS 'Assessment setup for publishing, timing, and question-source mode.';
COMMENT ON COLUMN assessment_configs.question_pool_id IS 'Required for generic assessments; null for personalized assessments until runtime generation.';
COMMENT ON COLUMN assessment_configs.per_question_time_limit_seconds IS 'Null means the overall timer is the only enforced limit.';
COMMENT ON COLUMN assessment_configs.max_followups_per_main IS 'Adaptive follow-up limit per main question.';

CREATE TABLE IF NOT EXISTS assessment_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_config_id UUID NOT NULL REFERENCES assessment_configs(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_by UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR NOT NULL DEFAULT 'not_started'
                            CHECK (status IN ('not_started', 'in_progress', 'submitted',
                                              'time_expired', 'under_review', 'released')),
    started_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    total_messages INT,
    current_main_index INT,
    current_followup_index INT,
    transcript_locked BOOLEAN NOT NULL DEFAULT false,
    released_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sessions_student_id ON assessment_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_course_id ON assessment_sessions(course_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON assessment_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_config_student ON assessment_sessions(assessment_config_id, student_id);

COMMENT ON TABLE assessment_sessions IS 'One student attempt at one published assessment.';
COMMENT ON COLUMN assessment_sessions.course_id IS 'Denormalized for instructor dashboard queries.';
COMMENT ON COLUMN assessment_sessions.transcript_locked IS 'Set to true when the session ends to prevent further message writes.';

CREATE TABLE IF NOT EXISTS session_question_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    source_question_id UUID REFERENCES questions(id) ON DELETE SET NULL,
    parent_item_id UUID REFERENCES session_question_items(id) ON DELETE SET NULL,
    asked_text TEXT NOT NULL,
    question_kind VARCHAR NOT NULL
                        CHECK (question_kind IN ('main', 'followup', 'probe')),
    main_group_no INT,
    followup_no INT,
    generated_by VARCHAR NOT NULL
                        CHECK (generated_by IN ('approved_pool', 'adaptive_ai', 'instructor_override')),
    rag_chunk_refs JSONB,
    asked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_answered BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_sqi_session_id ON session_question_items(session_id);
CREATE INDEX IF NOT EXISTS idx_sqi_source_question_id ON session_question_items(source_question_id);
CREATE INDEX IF NOT EXISTS idx_sqi_parent_item_id ON session_question_items(parent_item_id);
CREATE INDEX IF NOT EXISTS idx_sqi_session_group ON session_question_items(session_id, main_group_no, followup_no);

COMMENT ON TABLE session_question_items IS 'Runtime questions actually asked during a session.';
COMMENT ON COLUMN session_question_items.source_question_id IS 'Null for fully dynamic AI-generated questions.';
COMMENT ON COLUMN session_question_items.generated_by IS 'approved_pool | adaptive_ai | instructor_override';

CREATE TABLE IF NOT EXISTS transcript_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    session_question_item_id UUID REFERENCES session_question_items(id) ON DELETE SET NULL,
    sender_role VARCHAR NOT NULL
                                CHECK (sender_role IN ('system', 'assistant', 'student', 'instructor')),
    message_type VARCHAR NOT NULL
                                CHECK (message_type IN ('main_question', 'followup_question',
                                                        'student_answer', 'system_notice', 'summary_notice')),
    sequence_no INT NOT NULL,
    content TEXT NOT NULL,
    token_count INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, sequence_no)
);

CREATE INDEX IF NOT EXISTS idx_transcript_session_id ON transcript_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_transcript_sqi_id ON transcript_messages(session_question_item_id);

COMMENT ON TABLE transcript_messages IS 'Immutable transcript turns recorded during a live session.';
COMMENT ON COLUMN transcript_messages.sequence_no IS 'Strictly ordered within a session.';

CREATE TABLE IF NOT EXISTS ai_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL UNIQUE REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    summary_text TEXT NOT NULL,
    strengths TEXT,
    gaps TEXT,
    evidence_refs JSONB,
    model_name VARCHAR NOT NULL,
    advisory_only BOOLEAN NOT NULL DEFAULT true,
    status VARCHAR NOT NULL DEFAULT 'success'
                    CHECK (status IN ('success', 'failed')),
    error_message TEXT,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE ai_summaries IS 'Evidence-based AI summary used to support, not replace, instructor judgement.';
COMMENT ON COLUMN ai_summaries.advisory_only IS 'Always true; the AI summary does not assign the official grade.';

CREATE TABLE IF NOT EXISTS instructor_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL UNIQUE REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    instructor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    comments TEXT,
    grading_rationale TEXT,
    provisional_grade VARCHAR,
    final_grade VARCHAR,
    student_visible_comments TEXT,
    released_to_student BOOLEAN NOT NULL DEFAULT false,
    released_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_instructor_id ON instructor_feedback(instructor_id);
CREATE INDEX IF NOT EXISTS idx_feedback_released ON instructor_feedback(released_to_student);

COMMENT ON TABLE instructor_feedback IS 'Instructor-authored grade and feedback.';
COMMENT ON COLUMN instructor_feedback.released_to_student IS 'Controls whether the student can view feedback and transcript results.';
