-- Waitlist — pre-launch email collection

CREATE TABLE IF NOT EXISTS public.waitlist (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id  UUID REFERENCES public.projects (id) ON DELETE CASCADE,
  email       TEXT NOT NULL,
  first_name  TEXT,
  source      TEXT,
  message     TEXT,
  status      TEXT NOT NULL DEFAULT 'waiting'
              CHECK (status IN ('waiting', 'notified', 'converted')),
  notified_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (email, project_id)
);

CREATE INDEX IF NOT EXISTS idx_waitlist_project
  ON public.waitlist (project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_waitlist_status
  ON public.waitlist (status);
CREATE INDEX IF NOT EXISTS idx_waitlist_source
  ON public.waitlist (source);

ALTER TABLE public.waitlist ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.waitlist;
CREATE POLICY "authenticated_full_access" ON public.waitlist
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
