-- ------------------------------
-- 1. ai_summaries.suggested_grade
-- ------------------------------

ALTER TABLE ai_summaries
ALTER COLUMN suggested_grade DROP DEFAULT;

UPDATE ai_summaries
SET suggested_grade = NULL
WHERE suggested_grade IS NOT NULL
  AND suggested_grade !~ '^\d+$';

ALTER TABLE ai_summaries
ALTER COLUMN suggested_grade TYPE INTEGER
USING suggested_grade::INTEGER;

-- constraint
ALTER TABLE ai_summaries
ADD CONSTRAINT ck_ai_summaries_suggested_grade_range
CHECK (suggested_grade IS NULL OR suggested_grade BETWEEN 0 AND 100);


-- ------------------------------
-- 2. instructor_feedback.final_grade
-- ------------------------------

ALTER TABLE instructor_feedback
ALTER COLUMN final_grade DROP DEFAULT;

UPDATE instructor_feedback
SET final_grade = NULL
WHERE final_grade IS NOT NULL
  AND final_grade !~ '^\d+$';

ALTER TABLE instructor_feedback
ALTER COLUMN final_grade TYPE INTEGER
USING final_grade::INTEGER;

ALTER TABLE instructor_feedback
ADD CONSTRAINT ck_instructor_feedback_final_grade_range
CHECK (final_grade IS NULL OR final_grade BETWEEN 0 AND 100);


-- ------------------------------
-- 3. instructor_feedback.provisional_grade
-- ------------------------------

ALTER TABLE instructor_feedback
ALTER COLUMN provisional_grade DROP DEFAULT;

UPDATE instructor_feedback
SET provisional_grade = NULL
WHERE provisional_grade IS NOT NULL
  AND provisional_grade !~ '^\d+$';

ALTER TABLE instructor_feedback
ALTER COLUMN provisional_grade TYPE INTEGER
USING provisional_grade::INTEGER;

ALTER TABLE instructor_feedback
ADD CONSTRAINT ck_instructor_feedback_provisional_grade_range
CHECK (provisional_grade IS NULL OR provisional_grade BETWEEN 0 AND 100);