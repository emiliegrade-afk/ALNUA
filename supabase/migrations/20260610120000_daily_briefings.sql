-- Daily morning briefings + roadmap due dates

ALTER TABLE public.roadmap
  ADD COLUMN IF NOT EXISTS due_date DATE;

CREATE INDEX IF NOT EXISTS idx_roadmap_due_date
  ON public.roadmap (due_date)
  WHERE due_date IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.daily_briefings (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date          DATE NOT NULL,
  summary       TEXT NOT NULL,
  raw_data      JSONB,
  has_urgent    BOOLEAN NOT NULL DEFAULT false,
  urgent_count  INT NOT NULL DEFAULT 0,
  pending_count INT NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_daily_briefings_date
  ON public.daily_briefings (date DESC);

ALTER TABLE public.daily_briefings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.daily_briefings;
CREATE POLICY "authenticated_full_access" ON public.daily_briefings
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_read_daily_briefings" ON public.daily_briefings;
DROP POLICY IF EXISTS "anon_insert_daily_briefings" ON public.daily_briefings;

CREATE POLICY "anon_read_daily_briefings" ON public.daily_briefings
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_daily_briefings" ON public.daily_briefings
  FOR INSERT TO anon WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_daily_briefings" ON public.daily_briefings;
CREATE POLICY "anon_update_daily_briefings" ON public.daily_briefings
  FOR UPDATE TO anon USING (true) WITH CHECK (true);
