--
-- PostgreSQL database dump
--

-- Dumped from database version 16.6
-- Dumped by pg_dump version 18.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_summaries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_summaries (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    suggested_grade integer NOT NULL,
    detailed_feedback jsonb NOT NULL,
    CONSTRAINT ck_ai_summaries_suggested_grade_range CHECK (((suggested_grade IS NULL) OR ((suggested_grade >= 0) AND (suggested_grade <= 100))))
);


--
-- Name: COLUMN ai_summaries.session_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ai_summaries.session_id IS 'One AI summary per assessment session.';


--
-- Name: COLUMN ai_summaries.suggested_grade; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ai_summaries.suggested_grade IS 'Advisory numeric score suggested by the AI (0-100).';


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: assessment_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.assessment_configs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    course_id uuid NOT NULL,
    title character varying NOT NULL,
    status character varying DEFAULT 'draft'::character varying NOT NULL,
    description text,
    total_time_minute integer NOT NULL,
    main_question_num integer NOT NULL,
    follow_up_num integer DEFAULT 1 NOT NULL,
    release_time timestamp with time zone,
    due_time timestamp with time zone,
    rubric_id uuid NOT NULL,
    buffer_time_minute integer DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN assessment_configs.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.assessment_configs.status IS 'draft | published';


--
-- Name: COLUMN assessment_configs.main_question_num; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.assessment_configs.main_question_num IS 'Maximum number of main questions shown to a student per session. Must be set before publishing.';


--
-- Name: COLUMN assessment_configs.release_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.assessment_configs.release_time IS 'When students can start the assessment.';


--
-- Name: COLUMN assessment_configs.due_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.assessment_configs.due_time IS 'Hard deadline after which no new sessions should start.';


--
-- Name: COLUMN assessment_configs.buffer_time_minute; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.assessment_configs.buffer_time_minute IS 'Extra minutes for technical issues, added to total_time_minute when computing a session''s deadline.';


--
-- Name: assessment_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.assessment_sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    assessment_config_id uuid NOT NULL,
    status character varying DEFAULT 'not_started'::character varying NOT NULL,
    user_s_id uuid NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    resume_count integer DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN assessment_sessions.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.assessment_sessions.status IS 'not_started | in_progress | under_review | released';


--
-- Name: COLUMN assessment_sessions.resume_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.assessment_sessions.resume_count IS 'Times the student re-entered the in-progress session (reload / re-login / reopen).';


--
-- Name: course_enrollments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.course_enrollments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    course_id uuid NOT NULL,
    user_id uuid,
    upi character varying NOT NULL
);


--
-- Name: course_join_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.course_join_requests (
    id uuid NOT NULL,
    course_id uuid NOT NULL,
    requester_user_id uuid NOT NULL,
    status character varying DEFAULT 'pending'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: courses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.courses (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    course_code character varying NOT NULL,
    course_name character varying NOT NULL,
    term character varying NOT NULL,
    description text NOT NULL
);


--
-- Name: COLUMN courses.course_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.courses.course_code IS 'e.g. COMPSCI 399';


--
-- Name: COLUMN courses.term; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.courses.term IS 'e.g. 26S1';


--
-- Name: material_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.material_chunks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    material_id uuid NOT NULL,
    chunk_index integer NOT NULL,
    chunk_text text NOT NULL,
    embedding public.vector(768)
);


--
-- Name: COLUMN material_chunks.chunk_index; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.material_chunks.chunk_index IS '0-based position within material';


--
-- Name: COLUMN material_chunks.embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.material_chunks.embedding IS 'Gemini gemini-embedding-001, 768-dim vector (outputDimensionality=768), HNSW indexed';


--
-- Name: materials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.materials (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    course_id uuid NOT NULL,
    mime_type character varying NOT NULL,
    storage_key character varying NOT NULL,
    material_category character varying DEFAULT 'course_material'::character varying NOT NULL,
    filename character varying NOT NULL,
    CONSTRAINT ck_materials_category CHECK (((material_category)::text = ANY ((ARRAY['course_material'::character varying, 'rubric'::character varying])::text[])))
);


--
-- Name: COLUMN materials.storage_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.materials.storage_key IS 'S3 key: courses/{course_id}/materials/{material_id}/{filename}';


--
-- Name: COLUMN materials.material_category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.materials.material_category IS 'course_material | rubric';


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    id uuid NOT NULL,
    session_id uuid NOT NULL,
    user_id uuid NOT NULL,
    blur_count integer NOT NULL,
    is_read boolean DEFAULT false NOT NULL,
    disconnect_count integer DEFAULT 0 NOT NULL,
    resume_count integer DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN notifications.disconnect_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.notifications.disconnect_count IS 'Number of network reconnects recorded during the session (best-effort, client-reported).';


--
-- Name: COLUMN notifications.resume_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.notifications.resume_count IS 'Re-entries into the in-progress session, copied from AssessmentSession.resume_count at completion.';


--
-- Name: question_pool_materials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_pool_materials (
    question_pool_id uuid NOT NULL,
    material_id uuid NOT NULL
);


--
-- Name: question_pools; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_pools (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    status character varying DEFAULT 'draft'::character varying NOT NULL,
    assessment_config_id uuid NOT NULL
);


--
-- Name: COLUMN question_pools.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.question_pools.status IS 'draft | published';


--
-- Name: questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.questions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    question_pool_id uuid NOT NULL,
    question_text text NOT NULL,
    question_index integer NOT NULL
);


--
-- Name: rubrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rubrics (
    id uuid NOT NULL,
    course_id uuid NOT NULL,
    total_points integer NOT NULL,
    criteria_data jsonb NOT NULL
);


--
-- Name: session_feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_feedback (
    id uuid NOT NULL,
    session_id uuid NOT NULL,
    user_i_id uuid NOT NULL,
    comments text,
    final_grade integer NOT NULL,
    status character varying DEFAULT 'draft'::character varying NOT NULL
);


--
-- Name: COLUMN session_feedback.session_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.session_feedback.session_id IS 'One instructor feedback record per assessment session.';


--
-- Name: COLUMN session_feedback.comments; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.session_feedback.comments IS 'Internal instructor notes.';


--
-- Name: COLUMN session_feedback.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.session_feedback.status IS 'draft | published';


--
-- Name: session_question_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_question_items (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    source_question_id uuid NOT NULL,
    question_kind character varying NOT NULL,
    main_group_no integer NOT NULL,
    followup_no integer NOT NULL
);


--
-- Name: COLUMN session_question_items.question_kind; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.session_question_items.question_kind IS 'main | followup';


--
-- Name: COLUMN session_question_items.main_group_no; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.session_question_items.main_group_no IS 'Runtime main-question position for the session.';


--
-- Name: COLUMN session_question_items.followup_no; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.session_question_items.followup_no IS 'Runtime follow-up position within a main-question group.';


--
-- Name: transcript_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transcript_messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    session_question_item_id uuid NOT NULL,
    message_type character varying NOT NULL,
    sequence_no integer NOT NULL,
    content text NOT NULL
);


--
-- Name: COLUMN transcript_messages.session_question_item_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transcript_messages.session_question_item_id IS 'if not None, this is question';


--
-- Name: COLUMN transcript_messages.message_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transcript_messages.message_type IS 'main_question | followup_question | student_answer';


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying,
    full_name character varying NOT NULL,
    role character varying NOT NULL,
    image character varying,
    upi character varying NOT NULL
);


--
-- Name: COLUMN users.role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.role IS 'student | instructor';


--
-- Name: ai_summaries ai_summaries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_summaries
    ADD CONSTRAINT ai_summaries_pkey PRIMARY KEY (id);


--
-- Name: ai_summaries ai_summaries_session_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_summaries
    ADD CONSTRAINT ai_summaries_session_id_key UNIQUE (session_id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: assessment_configs assessment_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assessment_configs
    ADD CONSTRAINT assessment_configs_pkey PRIMARY KEY (id);


--
-- Name: assessment_sessions assessment_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assessment_sessions
    ADD CONSTRAINT assessment_sessions_pkey PRIMARY KEY (id);


--
-- Name: course_enrollments course_enrollments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course_enrollments
    ADD CONSTRAINT course_enrollments_pkey PRIMARY KEY (id);


--
-- Name: course_join_requests course_join_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course_join_requests
    ADD CONSTRAINT course_join_requests_pkey PRIMARY KEY (id);


--
-- Name: courses courses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (id);


--
-- Name: material_chunks material_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.material_chunks
    ADD CONSTRAINT material_chunks_pkey PRIMARY KEY (id);


--
-- Name: materials materials_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.materials
    ADD CONSTRAINT materials_pkey PRIMARY KEY (id);


--
-- Name: materials materials_storage_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.materials
    ADD CONSTRAINT materials_storage_key_key UNIQUE (storage_key);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_session_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_session_id_key UNIQUE (session_id);


--
-- Name: question_pool_materials question_pool_materials_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_pool_materials
    ADD CONSTRAINT question_pool_materials_pkey PRIMARY KEY (question_pool_id, material_id);


--
-- Name: question_pools question_pools_assessment_config_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_pools
    ADD CONSTRAINT question_pools_assessment_config_id_key UNIQUE (assessment_config_id);


--
-- Name: question_pools question_pools_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_pools
    ADD CONSTRAINT question_pools_pkey PRIMARY KEY (id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- Name: rubrics rubrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rubrics
    ADD CONSTRAINT rubrics_pkey PRIMARY KEY (id);


--
-- Name: session_feedback session_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_feedback
    ADD CONSTRAINT session_feedback_pkey PRIMARY KEY (id);


--
-- Name: session_feedback session_feedback_session_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_feedback
    ADD CONSTRAINT session_feedback_session_id_key UNIQUE (session_id);


--
-- Name: session_question_items session_question_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_question_items
    ADD CONSTRAINT session_question_items_pkey PRIMARY KEY (id);


--
-- Name: transcript_messages transcript_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transcript_messages
    ADD CONSTRAINT transcript_messages_pkey PRIMARY KEY (id);


--
-- Name: assessment_sessions uq_assessment_sessions_config_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assessment_sessions
    ADD CONSTRAINT uq_assessment_sessions_config_user UNIQUE (assessment_config_id, user_s_id);


--
-- Name: material_chunks uq_chunk_material_index; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.material_chunks
    ADD CONSTRAINT uq_chunk_material_index UNIQUE (material_id, chunk_index);


--
-- Name: course_enrollments uq_course_enrollments_course_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course_enrollments
    ADD CONSTRAINT uq_course_enrollments_course_user UNIQUE (course_id, user_id);


--
-- Name: courses uq_courses_code_term; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT uq_courses_code_term UNIQUE (course_code, term);


--
-- Name: transcript_messages uq_transcript_session_seq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transcript_messages
    ADD CONSTRAINT uq_transcript_session_seq UNIQUE (session_id, sequence_no);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_upi_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_upi_key UNIQUE (upi);


--
-- Name: uq_one_pending_join_request; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_one_pending_join_request ON public.course_join_requests USING btree (course_id, requester_user_id) WHERE ((status)::text = 'pending'::text);


--
-- Name: ai_summaries ai_summaries_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_summaries
    ADD CONSTRAINT ai_summaries_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.assessment_sessions(id) ON DELETE CASCADE;


--
-- Name: assessment_configs assessment_configs_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assessment_configs
    ADD CONSTRAINT assessment_configs_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- Name: assessment_configs assessment_configs_rubric_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assessment_configs
    ADD CONSTRAINT assessment_configs_rubric_id_fkey FOREIGN KEY (rubric_id) REFERENCES public.rubrics(id) ON DELETE RESTRICT;


--
-- Name: assessment_sessions assessment_sessions_assessment_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assessment_sessions
    ADD CONSTRAINT assessment_sessions_assessment_config_id_fkey FOREIGN KEY (assessment_config_id) REFERENCES public.assessment_configs(id) ON DELETE CASCADE;


--
-- Name: assessment_sessions assessment_sessions_user_s_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assessment_sessions
    ADD CONSTRAINT assessment_sessions_user_s_id_fkey FOREIGN KEY (user_s_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: course_enrollments course_enrollments_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course_enrollments
    ADD CONSTRAINT course_enrollments_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- Name: course_enrollments course_enrollments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course_enrollments
    ADD CONSTRAINT course_enrollments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: course_join_requests course_join_requests_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course_join_requests
    ADD CONSTRAINT course_join_requests_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- Name: course_join_requests course_join_requests_requester_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course_join_requests
    ADD CONSTRAINT course_join_requests_requester_user_id_fkey FOREIGN KEY (requester_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: material_chunks material_chunks_material_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.material_chunks
    ADD CONSTRAINT material_chunks_material_id_fkey FOREIGN KEY (material_id) REFERENCES public.materials(id) ON DELETE CASCADE;


--
-- Name: materials materials_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.materials
    ADD CONSTRAINT materials_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.assessment_sessions(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: question_pool_materials question_pool_materials_material_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_pool_materials
    ADD CONSTRAINT question_pool_materials_material_id_fkey FOREIGN KEY (material_id) REFERENCES public.materials(id) ON DELETE CASCADE;


--
-- Name: question_pool_materials question_pool_materials_question_pool_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_pool_materials
    ADD CONSTRAINT question_pool_materials_question_pool_id_fkey FOREIGN KEY (question_pool_id) REFERENCES public.question_pools(id) ON DELETE CASCADE;


--
-- Name: question_pools question_pools_assessment_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_pools
    ADD CONSTRAINT question_pools_assessment_config_id_fkey FOREIGN KEY (assessment_config_id) REFERENCES public.assessment_configs(id) ON DELETE CASCADE;


--
-- Name: questions questions_question_pool_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_question_pool_id_fkey FOREIGN KEY (question_pool_id) REFERENCES public.question_pools(id) ON DELETE CASCADE;


--
-- Name: rubrics rubrics_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rubrics
    ADD CONSTRAINT rubrics_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- Name: session_feedback session_feedback_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_feedback
    ADD CONSTRAINT session_feedback_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.assessment_sessions(id) ON DELETE CASCADE;


--
-- Name: session_feedback session_feedback_user_i_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_feedback
    ADD CONSTRAINT session_feedback_user_i_id_fkey FOREIGN KEY (user_i_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: session_question_items session_question_items_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_question_items
    ADD CONSTRAINT session_question_items_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.assessment_sessions(id) ON DELETE CASCADE;


--
-- Name: session_question_items session_question_items_source_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_question_items
    ADD CONSTRAINT session_question_items_source_question_id_fkey FOREIGN KEY (source_question_id) REFERENCES public.questions(id) ON DELETE RESTRICT;


--
-- Name: transcript_messages transcript_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transcript_messages
    ADD CONSTRAINT transcript_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.assessment_sessions(id) ON DELETE CASCADE;


--
-- Name: transcript_messages transcript_messages_session_question_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transcript_messages
    ADD CONSTRAINT transcript_messages_session_question_item_id_fkey FOREIGN KEY (session_question_item_id) REFERENCES public.session_question_items(id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

