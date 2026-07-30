-- Phases 19 + 20 (ROADMAP.md) — réceptacles réels pour le suivi hardware
-- d'Eve : itérations PCB/firmware/tests, résultats de bancs de test
-- (Laboratoire), et télémétrie IoT (Analytics). Prêts à recevoir de vraies
-- données dès qu'Eve (le robot physique) ou un banc de test les rapporte via
-- scripts/report_robo_build.py, report_lab_test.py, report_robo_telemetry.py.

CREATE TABLE IF NOT EXISTS public.robo_builds (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id        UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  branch            TEXT NOT NULL,
  stage             TEXT NOT NULL DEFAULT 'Prototype'
                    CHECK (stage IN ('Prototype', 'V2', 'V3', 'Certification', 'Production')),
  version           TEXT,
  pcb_revision      TEXT,
  firmware_version  TEXT,
  tests_passed_pct  INT CHECK (tests_passed_pct IS NULL OR tests_passed_pct BETWEEN 0 AND 100),
  open_issues       INT CHECK (open_issues IS NULL OR open_issues >= 0),
  notes             TEXT NOT NULL DEFAULT '',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_robo_builds_project_id ON public.robo_builds (project_id);
CREATE INDEX IF NOT EXISTS idx_robo_builds_created_at ON public.robo_builds (created_at DESC);

CREATE TABLE IF NOT EXISTS public.robo_lab_tests (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id     UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  category       TEXT NOT NULL,
  name           TEXT NOT NULL,
  status         TEXT NOT NULL DEFAULT 'in_progress'
                 CHECK (status IN ('pass', 'fail', 'in_progress')),
  measured_value TEXT,
  notes          TEXT NOT NULL DEFAULT '',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_robo_lab_tests_project_id ON public.robo_lab_tests (project_id);
CREATE INDEX IF NOT EXISTS idx_robo_lab_tests_created_at ON public.robo_lab_tests (created_at DESC);

CREATE TABLE IF NOT EXISTS public.robo_telemetry (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id       UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  power_w          NUMERIC,
  temperature_c    NUMERIC,
  cpu_pct          INT CHECK (cpu_pct IS NULL OR cpu_pct BETWEEN 0 AND 100),
  battery_pct      INT CHECK (battery_pct IS NULL OR battery_pct BETWEEN 0 AND 100),
  charge_cycles    INT CHECK (charge_cycles IS NULL OR charge_cycles >= 0),
  autonomy_hours   NUMERIC,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_robo_telemetry_project_id ON public.robo_telemetry (project_id);
CREATE INDEX IF NOT EXISTS idx_robo_telemetry_created_at ON public.robo_telemetry (created_at DESC);

ALTER TABLE public.robo_builds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.robo_lab_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.robo_telemetry ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.robo_builds;
CREATE POLICY "authenticated_full_access" ON public.robo_builds
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "authenticated_full_access" ON public.robo_lab_tests;
CREATE POLICY "authenticated_full_access" ON public.robo_lab_tests
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "authenticated_full_access" ON public.robo_telemetry;
CREATE POLICY "authenticated_full_access" ON public.robo_telemetry
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
