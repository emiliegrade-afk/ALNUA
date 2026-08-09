-- Incubateur R&D (Phase 24, ROADMAP.md) — étape Kanban Idée → Prototype →
-- Validation → MVP → Projet → Département, sur rnd_ideas (pas rnd_dossiers :
-- l'étape "Idée" précède la création d'un dossier).

ALTER TABLE public.rnd_ideas
  ADD COLUMN IF NOT EXISTS incubator_stage TEXT NOT NULL DEFAULT 'idee'
    CHECK (incubator_stage IN ('idee', 'prototype', 'validation', 'mvp', 'projet', 'departement')),
  ADD COLUMN IF NOT EXISTS incubator_stage_updated_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_rnd_ideas_incubator_stage ON public.rnd_ideas (incubator_stage);
