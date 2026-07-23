-- dev_log, releases, feedback — referenced by code (briefing_generator, release_generator,
-- content_agent, rnd_center) since before this migration existed. All three are guarded
-- with graceful fallbacks on PGRST205/missing-table errors, but the tables themselves were
-- never migrated — this closes that gap.

-- ---------------------------------------------------------------------------
-- dev_log — POST/GET /dev-log (api/routers/core.py), read by briefing + release generator
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.dev_log (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id       UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  content          TEXT NOT NULL,
  date             DATE NOT NULL DEFAULT CURRENT_DATE,
  used_for_content BOOLEAN NOT NULL DEFAULT false,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dev_log_project_date
  ON public.dev_log (project_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_dev_log_created_at
  ON public.dev_log (created_at DESC);

ALTER TABLE public.dev_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.dev_log;
CREATE POLICY "authenticated_full_access" ON public.dev_log
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- ---------------------------------------------------------------------------
-- releases — POST /releases/generate + GET/PATCH/DELETE /releases (api/routers/releases.py)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.releases (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id         UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  version            TEXT NOT NULL,
  release_date       DATE NOT NULL DEFAULT CURRENT_DATE,
  app_store_notes    TEXT,
  google_play_notes  TEXT,
  changelog_md       TEXT,
  dev_log_ids        UUID[] NOT NULL DEFAULT '{}',
  status             TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, version)
);

CREATE INDEX IF NOT EXISTS idx_releases_project_created
  ON public.releases (project_id, created_at DESC);

ALTER TABLE public.releases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.releases;
CREATE POLICY "authenticated_full_access" ON public.releases
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- ---------------------------------------------------------------------------
-- feedback — read-only observation source for rnd_center._observe_user_feedback().
-- Distinct from agent_feedback (thumbs up/down on agent responses) and beta_feedback
-- (beta portal submissions) — this one is generic product/app feedback with a 1-5 rating.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.feedback (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id  UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  content     TEXT NOT NULL,
  rating      SMALLINT CHECK (rating BETWEEN 1 AND 5),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_created_at
  ON public.feedback (created_at DESC);

ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.feedback;
CREATE POLICY "authenticated_full_access" ON public.feedback
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
