-- ALNUA Hub — brainstorm_summaries, branche « other », statut rejected, RLS dev

-- ---------------------------------------------------------------------------
-- 1. brainstorm_summaries — mémoire cross-sessions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.brainstorm_summaries (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id      UUID REFERENCES public.projects (id) ON DELETE CASCADE,
  session_id      TEXT NOT NULL,
  session_number  INT NOT NULL,
  title           TEXT NOT NULL,
  summary         TEXT NOT NULL,
  key_ideas       TEXT[] NOT NULL DEFAULT '{}',
  decisions       TEXT[] NOT NULL DEFAULT '{}',
  next_steps      TEXT[] NOT NULL DEFAULT '{}',
  open_questions  TEXT[] NOT NULL DEFAULT '{}',
  file_path       TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_brainstorm_summaries_project
  ON public.brainstorm_summaries (project_id, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_brainstorm_summaries_session
  ON public.brainstorm_summaries (session_id);

ALTER TABLE public.brainstorm_summaries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.brainstorm_summaries;
CREATE POLICY "authenticated_full_access" ON public.brainstorm_summaries
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- ---------------------------------------------------------------------------
-- 2. Branche « other » sur projects
-- ---------------------------------------------------------------------------
ALTER TABLE public.projects DROP CONSTRAINT IF EXISTS projects_branch_check;
ALTER TABLE public.projects ADD CONSTRAINT projects_branch_check
  CHECK (branch IN ('app', 'gaming', 'robotics', 'other'));

-- ---------------------------------------------------------------------------
-- 3. Statut « rejected » sur posts_queue
-- ---------------------------------------------------------------------------
ALTER TABLE public.posts_queue DROP CONSTRAINT IF EXISTS posts_queue_status_check;
ALTER TABLE public.posts_queue ADD CONSTRAINT posts_queue_status_check
  CHECK (status IN (
    'draft', 'pending_approval', 'approved', 'published', 'failed', 'rejected'
  ));

-- ---------------------------------------------------------------------------
-- 4. Policies anon (backend avec clé publishable — fix_rls_dev)
-- ---------------------------------------------------------------------------
DROP POLICY IF EXISTS "anon_read_agent_logs" ON public.agent_logs;
DROP POLICY IF EXISTS "anon_insert_agent_logs" ON public.agent_logs;
CREATE POLICY "anon_read_agent_logs" ON public.agent_logs
  FOR SELECT TO anon USING (true);
CREATE POLICY "anon_insert_agent_logs" ON public.agent_logs
  FOR INSERT TO anon WITH CHECK (true);

DROP POLICY IF EXISTS "anon_read_projects" ON public.projects;
DROP POLICY IF EXISTS "anon_insert_projects" ON public.projects;
CREATE POLICY "anon_read_projects" ON public.projects
  FOR SELECT TO anon USING (true);
CREATE POLICY "anon_insert_projects" ON public.projects
  FOR INSERT TO anon WITH CHECK (true);

DROP POLICY IF EXISTS "anon_read_roadmap" ON public.roadmap;
DROP POLICY IF EXISTS "anon_insert_roadmap" ON public.roadmap;
CREATE POLICY "anon_read_roadmap" ON public.roadmap
  FOR SELECT TO anon USING (true);
CREATE POLICY "anon_insert_roadmap" ON public.roadmap
  FOR INSERT TO anon WITH CHECK (true);

DROP POLICY IF EXISTS "anon_read_brainstorm_summaries" ON public.brainstorm_summaries;
DROP POLICY IF EXISTS "anon_insert_brainstorm_summaries" ON public.brainstorm_summaries;
DROP POLICY IF EXISTS "anon_update_brainstorm_summaries" ON public.brainstorm_summaries;
CREATE POLICY "anon_read_brainstorm_summaries" ON public.brainstorm_summaries
  FOR SELECT TO anon USING (true);
CREATE POLICY "anon_insert_brainstorm_summaries" ON public.brainstorm_summaries
  FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "anon_update_brainstorm_summaries" ON public.brainstorm_summaries
  FOR UPDATE TO anon USING (true) WITH CHECK (true);
