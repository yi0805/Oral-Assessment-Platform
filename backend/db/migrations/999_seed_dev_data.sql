-- ============================================================
-- Project 20 seed data for local development
--
-- Run after migrations 001, 002, and 003.
-- This creates a simple end-to-end dataset with:
-- 1 instructor, 2 students, 1 course, 1 material, 1 rubric,
-- 1 approved question pool, 4 main questions, and 1 draft assessment.
-- ============================================================

INSERT INTO users (id, email, full_name, role, google_sub) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'instructor@test.auckland.ac.nz', 'Test Instructor', 'instructor', 'google_sub_instructor_001'),
    ('a0000000-0000-0000-0000-000000000002', 'student1@test.auckland.ac.nz', 'Test Student One', 'student', 'google_sub_student_001'),
    ('a0000000-0000-0000-0000-000000000003', 'student2@test.auckland.ac.nz', 'Test Student Two', 'student', 'google_sub_student_002')
ON CONFLICT (email) DO NOTHING;

INSERT INTO courses (id, course_code, course_name, term, description, created_by) VALUES
    ('b0000000-0000-0000-0000-000000000001', 'COMPSCI235', 'Software Development Methodologies', '2026-S1', 'Test course for Project 20 development', 'a0000000-0000-0000-0000-000000000001')
ON CONFLICT DO NOTHING;

INSERT INTO course_enrollments (course_id, user_id, course_role) VALUES
    ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'instructor'),
    ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000002', 'student'),
    ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000003', 'student')
ON CONFLICT (course_id, user_id) DO NOTHING;

INSERT INTO rubrics (id, course_id, title, rubric_text, created_by) VALUES
    ('c0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001',
     'Midterm Oral Assessment Rubric',
     'Excellent (A): Demonstrates deep understanding with specific examples. Connects concepts across topics. Good (B): Shows solid understanding of core concepts. Can explain with some examples. Pass (C): Basic understanding of key ideas. Limited elaboration. Fail (D/E): Cannot explain fundamental concepts. Significant gaps in understanding.',
     'a0000000-0000-0000-0000-000000000001')
ON CONFLICT DO NOTHING;

INSERT INTO materials (id, course_id, uploaded_by, title, original_filename, file_type, storage_key, processing_status, total_chunks) VALUES
    ('d0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001',
     'a0000000-0000-0000-0000-000000000001',
     'Lecture 1 - Agile Methodologies', 'lecture1_agile.pdf', 'pdf',
     'courses/b0000000-0000-0000-0000-000000000001/materials/d0000000-0000-0000-0000-000000000001/lecture1_agile.pdf',
     'ready', 3)
ON CONFLICT DO NOTHING;

INSERT INTO question_pools (id, course_id, title, generation_method, created_by, status) VALUES
    ('e0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001',
     'Midterm Q Pool - Agile', 'ai_generated',
     'a0000000-0000-0000-0000-000000000001', 'approved')
ON CONFLICT DO NOTHING;

INSERT INTO questions (id, question_pool_id, question_text, question_kind, answer_style, difficulty, display_order, created_by) VALUES
    ('f0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000001',
     'Explain the core principles of Agile software development and why they matter in modern team settings.',
     'main', 'long', 'medium', 1, 'a0000000-0000-0000-0000-000000000001'),
    ('f0000000-0000-0000-0000-000000000002', 'e0000000-0000-0000-0000-000000000001',
     'Compare Scrum and Kanban. When would you choose one over the other?',
     'main', 'long', 'medium', 2, 'a0000000-0000-0000-0000-000000000001'),
    ('f0000000-0000-0000-0000-000000000003', 'e0000000-0000-0000-0000-000000000001',
     'What is a user story? Write an example user story for a library management system.',
     'main', 'mixed', 'easy', 3, 'a0000000-0000-0000-0000-000000000001'),
    ('f0000000-0000-0000-0000-000000000004', 'e0000000-0000-0000-0000-000000000001',
     'How would you explain iterative delivery to a client who expects a full specification up front?',
     'main', 'long', 'medium', 4, 'a0000000-0000-0000-0000-000000000001')
ON CONFLICT DO NOTHING;

INSERT INTO assessment_configs (
    id,
    course_id,
    question_pool_id,
    rubric_id,
    title,
    assessment_mode,
    total_time_minutes,
    max_followups_per_main,
    status
) VALUES (
    '90000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000001',
    'e0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001',
    'Midterm Oral Assessment - Agile',
    'generic',
    15,
    3,
    'draft'
)
ON CONFLICT DO NOTHING;
