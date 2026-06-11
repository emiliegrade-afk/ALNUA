-- Roadmap v2: phase, string priority, due_date, linked_ticket_id, idea status
-- Run in Supabase SQL Editor before using /roadmap page

-- New columns
ALTER TABLE public.roadmap ADD COLUMN IF NOT EXISTS phase TEXT;
ALTER TABLE public.roadmap ADD COLUMN IF NOT EXISTS due_date DATE;
ALTER TABLE public.roadmap ADD COLUMN IF NOT EXISTS linked_ticket_id UUID
  REFERENCES public.tickets (id) ON DELETE SET NULL;
ALTER TABLE public.roadmap ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- Migrate sprint → phase (legacy)
UPDATE public.roadmap
SET phase = sprint
WHERE (phase IS NULL OR phase = '')
  AND sprint IS NOT NULL
  AND sprint <> '';

-- Convert INT priority → TEXT priority (if still integer type)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'roadmap'
      AND column_name = 'priority'
      AND data_type = 'integer'
  ) THEN
    ALTER TABLE public.roadmap ADD COLUMN IF NOT EXISTS priority_new TEXT NOT NULL DEFAULT 'medium';
    UPDATE public.roadmap SET priority_new = CASE
      WHEN priority >= 8 THEN 'critical'
      WHEN priority >= 6 THEN 'high'
      WHEN priority >= 3 THEN 'medium'
      ELSE 'low'
    END;
    ALTER TABLE public.roadmap DROP COLUMN priority;
    ALTER TABLE public.roadmap RENAME COLUMN priority_new TO priority;
  END IF;
END $$;

-- Ensure priority is TEXT with check
ALTER TABLE public.roadmap DROP CONSTRAINT IF EXISTS roadmap_priority_check;
ALTER TABLE public.roadmap
  ALTER COLUMN priority TYPE TEXT USING priority::TEXT;
ALTER TABLE public.roadmap
  ALTER COLUMN priority SET DEFAULT 'medium';
ALTER TABLE public.roadmap
  ADD CONSTRAINT roadmap_priority_check
  CHECK (priority IN ('critical', 'high', 'medium', 'low'));

-- Status: add 'idea'
ALTER TABLE public.roadmap DROP CONSTRAINT IF EXISTS roadmap_status_check;
ALTER TABLE public.roadmap
  ADD CONSTRAINT roadmap_status_check
  CHECK (status IN ('idea', 'planned', 'in_progress', 'done'));

-- updated_at trigger (reuse set_updated_at if present)
DROP TRIGGER IF EXISTS trg_roadmap_updated_at ON public.roadmap;
CREATE TRIGGER trg_roadmap_updated_at
  BEFORE UPDATE ON public.roadmap
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE INDEX IF NOT EXISTS idx_roadmap_due_date ON public.roadmap (due_date);
CREATE INDEX IF NOT EXISTS idx_roadmap_phase ON public.roadmap (phase);

-- RLS for Hub CRUD
DROP POLICY IF EXISTS "anon_update_roadmap" ON public.roadmap;
DROP POLICY IF EXISTS "anon_delete_roadmap" ON public.roadmap;

CREATE POLICY "anon_update_roadmap" ON public.roadmap
  FOR UPDATE TO anon USING (true) WITH CHECK (true);

CREATE POLICY "anon_delete_roadmap" ON public.roadmap
  FOR DELETE TO anon USING (true);
