BEGIN;

ALTER TABLE materials
ADD COLUMN IF NOT EXISTS material_category VARCHAR;

UPDATE materials
SET material_category = 'course_material'
WHERE material_category IS NULL;

ALTER TABLE materials
ALTER COLUMN material_category SET DEFAULT 'course_material';

ALTER TABLE materials
ALTER COLUMN material_category SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_materials_category'
    ) THEN
        ALTER TABLE materials
        ADD CONSTRAINT ck_materials_category
        CHECK (material_category IN ('course_material', 'rubric'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_materials_course_id_category
ON materials(course_id, material_category);

COMMIT;