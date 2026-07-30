-- Phase 14 (ROADMAP.md) — système Modules réel pour la page détail projet.
-- Remplace modulesForProject() (mock-data.ts) par une vraie table, commune à
-- App / Gaming / Robotique.

CREATE TABLE IF NOT EXISTS public.project_modules (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id       UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  name             TEXT NOT NULL,
  status           TEXT NOT NULL DEFAULT 'a_faire'
                   CHECK (status IN ('a_faire', 'en_developpement', 'en_test', 'termine')),
  progress         INT NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
  features_done    INT NOT NULL DEFAULT 0 CHECK (features_done >= 0),
  features_total   INT NOT NULL DEFAULT 0 CHECK (features_total >= 0),
  tests_passed_pct INT NOT NULL DEFAULT 0 CHECK (tests_passed_pct BETWEEN 0 AND 100),
  open_bugs        INT NOT NULL DEFAULT 0 CHECK (open_bugs >= 0),
  position         INT NOT NULL DEFAULT 0,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_project_modules_project_id ON public.project_modules (project_id);

DROP TRIGGER IF EXISTS trg_project_modules_updated_at ON public.project_modules;
CREATE TRIGGER trg_project_modules_updated_at
  BEFORE UPDATE ON public.project_modules
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Row Level Security — même posture que tickets/roadmap (service_role bypass
-- RLS côté API ; authenticated peut tout faire, pas d'accès anon).
ALTER TABLE public.project_modules ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.project_modules;
CREATE POLICY "authenticated_full_access" ON public.project_modules
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
