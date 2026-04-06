BEGIN;

ALTER TABLE rubrics
ADD COLUMN IF NOT EXISTS material_id UUID NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_rubrics_material_id'
    ) THEN
        ALTER TABLE rubrics
        ADD CONSTRAINT fk_rubrics_material_id
        FOREIGN KEY (material_id)
        REFERENCES materials(id)
        ON DELETE SET NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_rubrics_material_id'
    ) THEN
        ALTER TABLE rubrics
        ADD CONSTRAINT uq_rubrics_material_id UNIQUE (material_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_rubrics_material_id
ON rubrics(material_id);

COMMIT;