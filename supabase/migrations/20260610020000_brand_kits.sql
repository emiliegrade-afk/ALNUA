-- Brand kits table for /brand page
CREATE TABLE IF NOT EXISTS public.brand_kits (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id        UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  brand_name        TEXT NOT NULL,
  analysis          JSONB NOT NULL,
  assets_path       TEXT NOT NULL DEFAULT '',
  formats_generated TEXT[] NOT NULL DEFAULT '{}',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_brand_kits_project_id
  ON public.brand_kits (project_id);
CREATE INDEX IF NOT EXISTS idx_brand_kits_created_at
  ON public.brand_kits (created_at DESC);

ALTER TABLE public.brand_kits ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_read_brand_kits" ON public.brand_kits;
DROP POLICY IF EXISTS "anon_insert_brand_kits" ON public.brand_kits;
DROP POLICY IF EXISTS "anon_update_brand_kits" ON public.brand_kits;

CREATE POLICY "anon_read_brand_kits" ON public.brand_kits
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_brand_kits" ON public.brand_kits
  FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon_update_brand_kits" ON public.brand_kits
  FOR UPDATE TO anon USING (true) WITH CHECK (true);
