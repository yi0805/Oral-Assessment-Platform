-- ============================================================
-- Rename per_question_time_limit_seconds
-- ============================================================

ALTER TABLE assessment_configs
RENAME COLUMN per_question_time_limit_seconds TO per_question_time_limit_minutes;

COMMENT ON COLUMN assessment_configs.per_question_time_limit_minutes
IS 'Null means the overall session timer is the only enforced limit.';

-- ============================================================
-- Add a column image
-- ============================================================

ALTER TABLE users
ADD COLUMN image VARCHAR;