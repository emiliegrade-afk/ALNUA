-- Phase 37 (ROADMAP.md) — Mesure de performance réelle Marketing.
-- Emilie a explicitement demandé qu'on cesse de traiter "pas de donnée
-- source" comme une fin de non-recevoir sur Performances par canal /
-- Top contenus / Entonnoir de conversion, et qu'on crée les champs
-- manquants. Pas d'intégration API Meta/TikTok/Google Ads (chantier
-- séparé, OAuth + vérification business) — saisie manuelle de chiffres
-- réels par les agents/Emilie, copiés depuis les dashboards natifs des
-- plateformes. Toujours zéro métrique fabriquée : ces colonnes sont
-- NULL tant que personne n'a saisi de vraie valeur, jamais 0 par défaut.

ALTER TABLE public.campaigns
  ADD COLUMN IF NOT EXISTS reach INTEGER CHECK (reach IS NULL OR reach >= 0),
  ADD COLUMN IF NOT EXISTS engagements INTEGER CHECK (engagements IS NULL OR engagements >= 0),
  ADD COLUMN IF NOT EXISTS conversions INTEGER CHECK (conversions IS NULL OR conversions >= 0),
  ADD COLUMN IF NOT EXISTS revenue_generated_usd NUMERIC(10, 2) CHECK (revenue_generated_usd IS NULL OR revenue_generated_usd >= 0),
  ADD COLUMN IF NOT EXISTS stats_updated_at TIMESTAMPTZ;

ALTER TABLE public.posts_queue
  ADD COLUMN IF NOT EXISTS reach INTEGER CHECK (reach IS NULL OR reach >= 0),
  ADD COLUMN IF NOT EXISTS engagement_count INTEGER CHECK (engagement_count IS NULL OR engagement_count >= 0),
  ADD COLUMN IF NOT EXISTS stats_updated_at TIMESTAMPTZ;

-- Entonnoir de conversion réel : saisie mensuelle par produit (Visiteurs →
-- Intéressés → Engagés → Abonnés → Clients), source = analytics propre à
-- chaque produit (App Store Connect / Play Console / Plausible / GA4 /
-- signups Supabase), pas une extrapolation. `source_note` documente d'où
-- vient le chiffre pour que la card reste auditable.
CREATE TABLE IF NOT EXISTS public.funnel_snapshots (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id          UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  period_month        DATE NOT NULL,
  visitors            INTEGER NOT NULL DEFAULT 0 CHECK (visitors >= 0),
  interested          INTEGER NOT NULL DEFAULT 0 CHECK (interested >= 0),
  engaged             INTEGER NOT NULL DEFAULT 0 CHECK (engaged >= 0),
  subscribers         INTEGER NOT NULL DEFAULT 0 CHECK (subscribers >= 0),
  customers           INTEGER NOT NULL DEFAULT 0 CHECK (customers >= 0),
  source_note         TEXT,
  entered_by_agent_id TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, period_month)
);

CREATE INDEX IF NOT EXISTS idx_funnel_snapshots_project_id ON public.funnel_snapshots (project_id);
CREATE INDEX IF NOT EXISTS idx_funnel_snapshots_period ON public.funnel_snapshots (period_month);

CREATE TRIGGER trg_funnel_snapshots_updated_at
  BEFORE UPDATE ON public.funnel_snapshots
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
