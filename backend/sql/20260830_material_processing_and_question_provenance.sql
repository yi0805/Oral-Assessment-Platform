-- Upgrade an existing deployment without Alembic.
-- Historical materials are ready only when persisted chunks prove that every
-- chunk has a non-zero embedding. All uncertain historical materials are failed so an
-- instructor can explicitly retry them; new uploads default to processing.
BEGIN;

ALTER TABLE public.materials
    ADD COLUMN IF NOT EXISTS processing_status character varying;

ALTER TABLE public.materials
    ADD COLUMN IF NOT EXISTS processing_started_at timestamp with time zone;

UPDATE public.materials AS material
SET processing_status = CASE
    WHEN EXISTS (
        SELECT 1
        FROM public.material_chunks AS chunk
        WHERE chunk.material_id = material.id
    )
    AND NOT EXISTS (
        SELECT 1
        FROM public.material_chunks AS chunk
        WHERE chunk.material_id = material.id
          AND (chunk.embedding IS NULL OR vector_norm(chunk.embedding) = 0)
    ) THEN 'ready'
    ELSE 'failed'
END
WHERE material.processing_status IS NULL;

ALTER TABLE public.materials
    ALTER COLUMN processing_status SET NOT NULL,
    ALTER COLUMN processing_status SET DEFAULT 'processing';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_materials_processing_status'
          AND conrelid = 'public.materials'::regclass
    ) THEN
        ALTER TABLE public.materials
            ADD CONSTRAINT ck_materials_processing_status
            CHECK (processing_status IN ('processing', 'ready', 'failed'));
    END IF;
END $$;

ALTER TABLE public.questions
    ADD COLUMN IF NOT EXISTS generation_provenance jsonb;

COMMENT ON COLUMN public.materials.processing_status IS 'processing | ready | failed';
COMMENT ON COLUMN public.materials.processing_started_at IS
    'UTC time at which the current processing attempt began; null when terminal';
COMMENT ON COLUMN public.questions.generation_provenance IS
    'AI generation context metadata; null for manually created questions';

COMMIT;
