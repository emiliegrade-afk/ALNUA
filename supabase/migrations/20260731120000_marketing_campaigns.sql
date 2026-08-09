-- Phase 33 (ROADMAP.md) — Marketing Command Center : Campagnes + Content Studio.
--
-- Aucune table `campaigns` n'existait jusqu'ici (confirmé) — skills/skill_ads.py
-- n'avait aucune persistance (draft_campaign/amplify_organic_post/
-- campaign_roi_report retournent tous des dict en mémoire). Cette migration
-- crée la table réelle + rattache les dépenses déjà catégorisées "marketing"
-- dans `transactions` à une campagne, pour calculer un "dépensé réel" sans
-- jamais fabriquer de ROI/reach/impressions (campaign_roi_report reste un
-- stub explicite côté backend, non exposé côté API dans cette phase).

CREATE TABLE IF NOT EXISTS public.campaigns (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id            UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  name                  TEXT NOT NULL,
  objective             TEXT NOT NULL
                        CHECK (objective IN ('awareness', 'traffic', 'conversions', 'engagement', 'video_views')),
  platform              TEXT NOT NULL CHECK (platform IN ('meta', 'google', 'tiktok')),
  status                TEXT NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft', 'active', 'paused', 'completed')),
  budget_allocated_usd  NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (budget_allocated_usd >= 0),
  audience              TEXT,
  brief                 TEXT,
  start_date            DATE,
  end_date              DATE,
  created_by_agent_id   TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_campaigns_project_id ON public.campaigns (project_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON public.campaigns (status);

DROP TRIGGER IF EXISTS trg_campaigns_updated_at ON public.campaigns;
CREATE TRIGGER trg_campaigns_updated_at
  BEFORE UPDATE ON public.campaigns
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.campaigns ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.campaigns;
CREATE POLICY "authenticated_full_access" ON public.campaigns
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_full_access_campaigns" ON public.campaigns;
CREATE POLICY "anon_full_access_campaigns" ON public.campaigns
  FOR ALL TO anon USING (true) WITH CHECK (true);

-- Rattache une dépense réelle à sa campagne (nullable — la grande majorité
-- des transactions marketing existantes n'en ont pas). Sert uniquement à
-- sommer un "dépensé" réel par campagne, jamais un ROI/ROAS fabriqué.
ALTER TABLE public.transactions
  ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES public.campaigns (id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_campaign_id ON public.transactions (campaign_id);

-- ---------------------------------------------------------------------------
-- Bug pré-existant corrigé au passage : web/src/components/content/
-- content.constants.ts::PostContentType déclare "lore" depuis la Phase 26,
-- jamais reflété dans la CHECK constraint SQL de posts_queue.content_type —
-- un POST /posts avec content_type "lore" échoue en base aujourd'hui.
-- Le nom réel de la contrainte n'a pas pu être vérifié à l'avance (accès
-- direct à la base indisponible dans cet environnement) : on la retrouve
-- dynamiquement via pg_constraint plutôt que de supposer son nom, pour que
-- cette migration soit sûre quel que soit le nom réel généré par Postgres.
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  existing_constraint text;
BEGIN
  SELECT conname INTO existing_constraint
  FROM pg_constraint
  WHERE conrelid = 'public.posts_queue'::regclass
    AND contype = 'c'
    AND pg_get_constraintdef(oid) ILIKE '%content_type%';

  IF existing_constraint IS NOT NULL THEN
    EXECUTE format('ALTER TABLE public.posts_queue DROP CONSTRAINT %I', existing_constraint);
  END IF;
END $$;

ALTER TABLE public.posts_queue ADD CONSTRAINT posts_queue_content_type_check
  CHECK (content_type IN ('announcement', 'teaser', 'tutorial', 'behind_scenes', 'short_video', 'lore'));
