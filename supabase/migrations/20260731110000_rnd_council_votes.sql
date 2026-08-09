-- Moteur Conseil R&D (Phase 25, ROADMAP.md) — Conseil stratégique IA
-- (Brainstorm refondu, débat libre) + Conseil IA (input structuré → vote).
--
-- Étend rnd_committee_sessions/rnd_committee_messages plutôt que d'inventer
-- un jeu de tables parallèle : le comité dossier existant (session_kind
-- par défaut 'dossier') continue de fonctionner sans changement, dossier_id
-- devient juste optionnel pour permettre les sessions 'strategic'/
-- 'evaluation' qui n'ont pas de dossier.

ALTER TABLE public.rnd_committee_sessions
  ALTER COLUMN dossier_id DROP NOT NULL,
  ADD COLUMN IF NOT EXISTS session_kind TEXT NOT NULL DEFAULT 'dossier'
    CHECK (session_kind IN ('dossier', 'strategic', 'evaluation')),
  ADD COLUMN IF NOT EXISTS idea_id UUID REFERENCES public.rnd_ideas (id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS structured_input JSONB,
  ADD COLUMN IF NOT EXISTS topic TEXT;

ALTER TABLE public.rnd_committee_messages
  ALTER COLUMN dossier_id DROP NOT NULL;

-- ---------------------------------------------------------------------------
-- rnd_committee_votes — verdict individuel par membre, live + final.
-- round_index + is_final permettent à une seule table de servir les jauges
-- live (dernière ligne par agent) ET la bannière "Décision Collective"
-- (lignes is_final=true) sans colonnes d'agrégat séparées.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rnd_committee_votes (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id     TEXT NOT NULL REFERENCES public.rnd_committee_sessions (session_id) ON DELETE CASCADE,
  agent_id       TEXT NOT NULL,
  agent_name     TEXT NOT NULL,
  verdict        TEXT NOT NULL CHECK (verdict IN ('GO', 'MAYBE', 'NO')),
  confidence_pct SMALLINT NOT NULL CHECK (confidence_pct BETWEEN 0 AND 100),
  axis_scores    JSONB,
  stance_text    TEXT NOT NULL,
  round_index    INT NOT NULL DEFAULT 0,
  is_final       BOOLEAN NOT NULL DEFAULT false,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rnd_committee_votes_session
  ON public.rnd_committee_votes (session_id, agent_id, round_index DESC);

ALTER TABLE public.rnd_committee_votes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.rnd_committee_votes;
CREATE POLICY "authenticated_full_access" ON public.rnd_committee_votes
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_full_access_rnd_committee_votes" ON public.rnd_committee_votes;
CREATE POLICY "anon_full_access_rnd_committee_votes" ON public.rnd_committee_votes
  FOR ALL TO anon USING (true) WITH CHECK (true);
