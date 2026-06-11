-- Quick Capture — table quick_notes + source quick_capture sur tickets

CREATE TABLE IF NOT EXISTS public.quick_notes (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id  UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  content     TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_quick_notes_project
  ON public.quick_notes (project_id, created_at DESC);

ALTER TABLE public.quick_notes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.quick_notes;
CREATE POLICY "authenticated_full_access" ON public.quick_notes
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_read_quick_notes" ON public.quick_notes;
DROP POLICY IF EXISTS "anon_insert_quick_notes" ON public.quick_notes;

CREATE POLICY "anon_read_quick_notes" ON public.quick_notes
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_quick_notes" ON public.quick_notes
  FOR INSERT TO anon WITH CHECK (true);

-- Étendre la source tickets pour Quick Capture
ALTER TABLE public.tickets DROP CONSTRAINT IF EXISTS tickets_source_check;
ALTER TABLE public.tickets ADD CONSTRAINT tickets_source_check
  CHECK (source IN ('qa_agent', 'sav_bot', 'reviews_bot', 'emilie', 'quick_capture'));
