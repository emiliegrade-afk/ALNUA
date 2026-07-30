-- Phase 16 (ROADMAP.md) — réceptacle réel pour la télémétrie de build UE5.
-- Aucun pipeline de build UE5 n'existe encore (pas de projet Wyrdheim ni
-- d'UE5 installés dans cet environnement) : cette table est prête à recevoir
-- de vraies données dès qu'un build réel les rapporte via
-- POST /gaming/builds (voir scripts/report_ue5_build.py) — en attendant,
-- l'UI affiche un état vide honnête plutôt que des chiffres inventés.

CREATE TABLE IF NOT EXISTS public.gaming_builds (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id     UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  branch         TEXT NOT NULL,
  build_number   TEXT NOT NULL,
  game_version   TEXT,
  engine_version TEXT NOT NULL DEFAULT '5.8',
  status         TEXT NOT NULL DEFAULT 'success'
                 CHECK (status IN ('success', 'failed', 'running')),
  fps_avg        NUMERIC,
  crashes        INT CHECK (crashes IS NULL OR crashes >= 0),
  draw_calls     INT CHECK (draw_calls IS NULL OR draw_calls >= 0),
  commit_sha     TEXT,
  notes          TEXT NOT NULL DEFAULT '',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gaming_builds_project_id ON public.gaming_builds (project_id);
CREATE INDEX IF NOT EXISTS idx_gaming_builds_created_at ON public.gaming_builds (created_at DESC);

ALTER TABLE public.gaming_builds ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.gaming_builds;
CREATE POLICY "authenticated_full_access" ON public.gaming_builds
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
