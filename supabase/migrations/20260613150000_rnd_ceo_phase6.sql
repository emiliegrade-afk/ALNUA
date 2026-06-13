-- Phase 6 — CEO package, comité CR structuré, dispatch COO

ALTER TABLE public.rnd_dossiers
  ADD COLUMN IF NOT EXISTS ceo_package_json JSONB,
  ADD COLUMN IF NOT EXISTS committee_report_md TEXT,
  ADD COLUMN IF NOT EXISTS dispatch_json JSONB,
  ADD COLUMN IF NOT EXISTS dispatch_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (dispatch_status IN ('pending', 'ready', 'dispatched'));

CREATE INDEX IF NOT EXISTS idx_rnd_dossiers_ceo_status
  ON public.rnd_dossiers (ceo_status, status);

-- Roadmap columns used by COO dispatch (safe if already present)
ALTER TABLE public.roadmap
  ADD COLUMN IF NOT EXISTS phase TEXT;

ALTER TABLE public.roadmap
  ADD COLUMN IF NOT EXISTS rnd_dossier_id UUID REFERENCES public.rnd_dossiers (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_roadmap_rnd_dossier
  ON public.roadmap (rnd_dossier_id)
  WHERE rnd_dossier_id IS NOT NULL;
