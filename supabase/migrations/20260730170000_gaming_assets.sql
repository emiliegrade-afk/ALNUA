-- Phase 17 (ROADMAP.md) — inventaire réel des assets Gaming. Le projet UE5
-- Wyrdheim est sur un disque séparé (pas accessible depuis cet environnement)
-- : cette table est prête à recevoir un vrai inventaire scanné localement via
-- scripts/sync_ue5_assets.py, plutôt que les exemples fictifs actuels.

CREATE TABLE IF NOT EXISTS public.gaming_assets (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id   UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  category     TEXT NOT NULL,
  name         TEXT NOT NULL,
  asset_type   TEXT NOT NULL,
  file_path    TEXT NOT NULL,
  size_bytes   BIGINT NOT NULL DEFAULT 0 CHECK (size_bytes >= 0),
  modified_at  TIMESTAMPTZ,
  synced_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gaming_assets_project_id ON public.gaming_assets (project_id);
CREATE INDEX IF NOT EXISTS idx_gaming_assets_category ON public.gaming_assets (project_id, category);

ALTER TABLE public.gaming_assets ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.gaming_assets;
CREATE POLICY "authenticated_full_access" ON public.gaming_assets
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
