-- Roadmap columns for R&D COO dispatch (if missing on remote)

ALTER TABLE public.roadmap
  ADD COLUMN IF NOT EXISTS phase TEXT;

ALTER TABLE public.roadmap
  ADD COLUMN IF NOT EXISTS rnd_dossier_id UUID REFERENCES public.rnd_dossiers (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_roadmap_rnd_dossier
  ON public.roadmap (rnd_dossier_id)
  WHERE rnd_dossier_id IS NOT NULL;
