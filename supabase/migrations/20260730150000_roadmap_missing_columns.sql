-- Complète le rattrapage schéma de la table `roadmap` commencé par
-- 20260730140000_roadmap_status_priority_fix.sql (BUG-007, BUGS.md) : deux
-- colonnes documentées dans database/schema.sql et dans le type TypeScript
-- `RoadmapItem` n'existaient pas réellement en base — `updated_at` (jamais
-- créée, ni de trigger pour la maintenir, contrairement à `tickets`) et
-- `linked_ticket_id` (utilisée par POST /roadmap/from-ticket/{ticket_id} et
-- son check d'existence, qui échouaient donc tous les deux systématiquement
-- — colonne inconnue de PostgREST).

ALTER TABLE public.roadmap
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE public.roadmap
  ADD COLUMN IF NOT EXISTS linked_ticket_id UUID REFERENCES public.tickets (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_roadmap_linked_ticket_id
  ON public.roadmap (linked_ticket_id)
  WHERE linked_ticket_id IS NOT NULL;

DROP TRIGGER IF EXISTS trg_roadmap_updated_at ON public.roadmap;
CREATE TRIGGER trg_roadmap_updated_at
  BEFORE UPDATE ON public.roadmap
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
