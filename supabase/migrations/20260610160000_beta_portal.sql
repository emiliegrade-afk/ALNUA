-- Beta tester portal — tables, ticket source, storage bucket

-- Allow beta_tester as ticket source
ALTER TABLE public.tickets DROP CONSTRAINT IF EXISTS tickets_source_check;
ALTER TABLE public.tickets ADD CONSTRAINT tickets_source_check
  CHECK (source IN (
    'qa_agent', 'sav_bot', 'reviews_bot', 'emilie', 'quick_capture', 'beta_tester'
  ));

-- ---------------------------------------------------------------------------
-- beta_testers
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.beta_testers (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id     UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  email          TEXT NOT NULL,
  first_name     TEXT,
  device         TEXT,
  os_version     TEXT,
  app_version    TEXT,
  joined_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  feedback_count INT NOT NULL DEFAULT 0,
  UNIQUE (project_id, email)
);

CREATE INDEX IF NOT EXISTS idx_beta_testers_project
  ON public.beta_testers (project_id);
CREATE INDEX IF NOT EXISTS idx_beta_testers_email
  ON public.beta_testers (email);

-- ---------------------------------------------------------------------------
-- beta_feedback
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.beta_feedback (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tester_id       UUID NOT NULL REFERENCES public.beta_testers (id) ON DELETE CASCADE,
  project_id      UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  type            TEXT CHECK (type IN ('bug', 'suggestion', 'crash', 'ux', 'autre')),
  title           TEXT NOT NULL,
  description     TEXT,
  screenshot_url  TEXT,
  severity        TEXT CHECK (severity IN ('bloquant', 'majeur', 'mineur', 'cosmétique')),
  ticket_id       UUID REFERENCES public.tickets (id) ON DELETE SET NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_beta_feedback_project
  ON public.beta_feedback (project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_beta_feedback_tester
  ON public.beta_feedback (tester_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- RLS
-- ---------------------------------------------------------------------------
ALTER TABLE public.beta_testers  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.beta_feedback ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.beta_testers;
CREATE POLICY "authenticated_full_access" ON public.beta_testers
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "authenticated_full_access" ON public.beta_feedback;
CREATE POLICY "authenticated_full_access" ON public.beta_feedback
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- ---------------------------------------------------------------------------
-- Storage bucket for beta screenshots (service role uploads via API)
-- ---------------------------------------------------------------------------
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'beta-screenshots',
  'beta-screenshots',
  true,
  5242880,
  ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/gif']
)
ON CONFLICT (id) DO NOTHING;
