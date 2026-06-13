-- R&D Dossier Hub — ideas, dossiers, sections, events, assets, committee, social, product pages

-- ---------------------------------------------------------------------------
-- rnd_ideas (replaces data/rnd_ideas.json progressively)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rnd_ideas (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  legacy_id         TEXT UNIQUE,
  title             TEXT NOT NULL,
  description       TEXT NOT NULL DEFAULT '',
  domain            TEXT,
  effort            TEXT,
  why_now           TEXT,
  source            TEXT NOT NULL DEFAULT 'rnd_agent',
  status            TEXT NOT NULL DEFAULT 'pending_evaluation',
  score             INT,
  market_score      INT,
  feasibility_score INT,
  vision_score      INT,
  agent_verdict     TEXT,
  agent_reasoning   TEXT,
  next_step         TEXT,
  spec_file         TEXT,
  lifecycle_status  TEXT NOT NULL DEFAULT 'raw'
    CHECK (lifecycle_status IN (
      'raw', 'dossier_draft', 'in_committee', 'sections_review',
      'ceo_review', 'approved', 'rejected', 'in_conception', 'shipped', 'archived'
    )),
  project_id        UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  dossier_id        UUID,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  evaluated_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_rnd_ideas_legacy_id ON public.rnd_ideas (legacy_id);
CREATE INDEX IF NOT EXISTS idx_rnd_ideas_verdict ON public.rnd_ideas (agent_verdict);
CREATE INDEX IF NOT EXISTS idx_rnd_ideas_lifecycle ON public.rnd_ideas (lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_rnd_ideas_score ON public.rnd_ideas (score DESC NULLS LAST);

DROP TRIGGER IF EXISTS trg_rnd_ideas_updated_at ON public.rnd_ideas;
CREATE TRIGGER trg_rnd_ideas_updated_at
  BEFORE UPDATE ON public.rnd_ideas
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- rnd_dossiers
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rnd_dossiers (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  idea_id             UUID NOT NULL UNIQUE REFERENCES public.rnd_ideas (id) ON DELETE CASCADE,
  slug                TEXT NOT NULL UNIQUE,
  title               TEXT NOT NULL,
  tagline             TEXT,
  domain              TEXT NOT NULL,
  branch              TEXT CHECK (branch IN ('app', 'gaming', 'robotics', 'other')),
  status              TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN (
      'draft', 'committee_active', 'partial_validated', 'ready_for_ceo',
      'ceo_approved', 'ceo_rejected', 'in_conception', 'published', 'archived'
    )),
  ceo_status          TEXT NOT NULL DEFAULT 'pending'
    CHECK (ceo_status IN ('pending', 'approved', 'rejected', 'pivot_requested')),
  ceo_note            TEXT,
  ceo_decided_at      TIMESTAMPTZ,
  committee_team      JSONB NOT NULL DEFAULT '[]'::jsonb,
  vision_snapshot     TEXT,
  competitive_context TEXT,
  deck_html_path      TEXT,
  deck_pdf_path       TEXT,
  one_pager_md        TEXT,
  finance_json        JSONB,
  brand_kit_id        UUID REFERENCES public.brand_kits (id) ON DELETE SET NULL,
  project_id          UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  local_path          TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rnd_dossiers_status ON public.rnd_dossiers (status);
CREATE INDEX IF NOT EXISTS idx_rnd_dossiers_slug ON public.rnd_dossiers (slug);
CREATE INDEX IF NOT EXISTS idx_rnd_dossiers_domain ON public.rnd_dossiers (domain);

DROP TRIGGER IF EXISTS trg_rnd_dossiers_updated_at ON public.rnd_dossiers;
CREATE TRIGGER trg_rnd_dossiers_updated_at
  BEFORE UPDATE ON public.rnd_dossiers
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- FK rnd_ideas.dossier_id → rnd_dossiers
ALTER TABLE public.rnd_ideas DROP CONSTRAINT IF EXISTS rnd_ideas_dossier_id_fkey;
ALTER TABLE public.rnd_ideas
  ADD CONSTRAINT rnd_ideas_dossier_id_fkey
  FOREIGN KEY (dossier_id) REFERENCES public.rnd_dossiers (id) ON DELETE SET NULL;

-- ---------------------------------------------------------------------------
-- rnd_dossier_sections
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rnd_dossier_sections (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id      UUID NOT NULL REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  section_key     TEXT NOT NULL,
  title           TEXT NOT NULL,
  content_md      TEXT NOT NULL DEFAULT '',
  content_html    TEXT,
  status          TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'under_review', 'validated', 'needs_revision', 'skipped')),
  validated_by    TEXT,
  validated_at    TIMESTAMPTZ,
  revision_note   TEXT,
  sort_order      INT NOT NULL DEFAULT 0,
  hero_asset_id   UUID,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (dossier_id, section_key)
);

CREATE INDEX IF NOT EXISTS idx_rnd_dossier_sections_dossier
  ON public.rnd_dossier_sections (dossier_id, sort_order);

DROP TRIGGER IF EXISTS trg_rnd_dossier_sections_updated_at ON public.rnd_dossier_sections;
CREATE TRIGGER trg_rnd_dossier_sections_updated_at
  BEFORE UPDATE ON public.rnd_dossier_sections
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- rnd_dossier_assets
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rnd_dossier_assets (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id       UUID NOT NULL REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  section_key      TEXT,
  asset_type       TEXT NOT NULL
    CHECK (asset_type IN (
      'hero', 'illustration', 'mockup', 'diagram', 'chart',
      'moodboard', 'social_teaser', 'logo_concept'
    )),
  file_path        TEXT NOT NULL,
  public_url       TEXT,
  image_prompt     TEXT,
  generation_model TEXT,
  width            INT,
  height           INT,
  metadata         JSONB,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rnd_dossier_assets_dossier
  ON public.rnd_dossier_assets (dossier_id);

ALTER TABLE public.rnd_dossier_sections DROP CONSTRAINT IF EXISTS rnd_dossier_sections_hero_asset_id_fkey;
ALTER TABLE public.rnd_dossier_sections
  ADD CONSTRAINT rnd_dossier_sections_hero_asset_id_fkey
  FOREIGN KEY (hero_asset_id) REFERENCES public.rnd_dossier_assets (id) ON DELETE SET NULL;

-- ---------------------------------------------------------------------------
-- rnd_dossier_events
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rnd_dossier_events (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id  UUID NOT NULL REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  event_type  TEXT NOT NULL,
  actor       TEXT NOT NULL,
  payload     JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rnd_dossier_events_dossier
  ON public.rnd_dossier_events (dossier_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- rnd_committee_sessions (phase 3 — created now)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rnd_committee_sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id      UUID NOT NULL REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  session_id      TEXT NOT NULL UNIQUE,
  title           TEXT,
  mode            TEXT NOT NULL DEFAULT 'free'
    CHECK (mode IN ('free', 'round_robin', 'targeted')),
  active_section  TEXT,
  team            JSONB NOT NULL DEFAULT '[]'::jsonb,
  status          TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'paused', 'closed')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at       TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_rnd_committee_sessions_dossier
  ON public.rnd_committee_sessions (dossier_id);

-- ---------------------------------------------------------------------------
-- rnd_committee_messages
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rnd_committee_messages (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id   TEXT NOT NULL REFERENCES public.rnd_committee_sessions (session_id) ON DELETE CASCADE,
  dossier_id   UUID NOT NULL REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  speaker      TEXT NOT NULL,
  role         TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content      TEXT NOT NULL,
  section_key  TEXT,
  metadata     JSONB,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rnd_committee_messages_session
  ON public.rnd_committee_messages (session_id, created_at);

-- ---------------------------------------------------------------------------
-- rnd_social_calendar (phase 5)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rnd_social_calendar (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id   UUID NOT NULL REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  phase        TEXT NOT NULL
    CHECK (phase IN ('internal', 'behind_scenes', 'teaser', 'pre_launch', 'launch', 'post_launch')),
  milestone    TEXT,
  planned_at   TIMESTAMPTZ,
  post_id      UUID REFERENCES public.posts_queue (id) ON DELETE SET NULL,
  status       TEXT NOT NULL DEFAULT 'planned'
    CHECK (status IN ('planned', 'generated', 'approved', 'published', 'cancelled')),
  notes        TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- rnd_product_pages (phase 7)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rnd_product_pages (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id       UUID NOT NULL UNIQUE REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  project_id       UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  slug             TEXT NOT NULL UNIQUE,
  title            TEXT NOT NULL,
  tagline          TEXT,
  description_html TEXT,
  hero_asset_id    UUID REFERENCES public.rnd_dossier_assets (id) ON DELETE SET NULL,
  features         JSONB NOT NULL DEFAULT '[]'::jsonb,
  pricing_model    TEXT,
  faq              JSONB NOT NULL DEFAULT '[]'::jsonb,
  seo_title        TEXT,
  seo_description  TEXT,
  waitlist_enabled BOOLEAN NOT NULL DEFAULT false,
  published        BOOLEAN NOT NULL DEFAULT false,
  published_at     TIMESTAMPTZ,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS trg_rnd_product_pages_updated_at ON public.rnd_product_pages;
CREATE TRIGGER trg_rnd_product_pages_updated_at
  BEFORE UPDATE ON public.rnd_product_pages
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- Extensions tables existantes (safe if column exists)
-- ---------------------------------------------------------------------------
ALTER TABLE public.posts_queue
  ADD COLUMN IF NOT EXISTS rnd_dossier_id UUID REFERENCES public.rnd_dossiers (id) ON DELETE SET NULL;

ALTER TABLE public.posts_queue
  ADD COLUMN IF NOT EXISTS rnd_social_calendar_id UUID REFERENCES public.rnd_social_calendar (id) ON DELETE SET NULL;

ALTER TABLE public.posts_queue
  ADD COLUMN IF NOT EXISTS image_asset_path TEXT;

ALTER TABLE public.brainstorm_summaries
  ADD COLUMN IF NOT EXISTS rnd_dossier_id UUID REFERENCES public.rnd_dossiers (id) ON DELETE SET NULL;

ALTER TABLE public.brainstorm_summaries
  ADD COLUMN IF NOT EXISTS session_type TEXT NOT NULL DEFAULT 'brainstorm';

ALTER TABLE public.roadmap
  ADD COLUMN IF NOT EXISTS rnd_dossier_id UUID REFERENCES public.rnd_dossiers (id) ON DELETE SET NULL;

ALTER TABLE public.lore_entries
  ADD COLUMN IF NOT EXISTS rnd_dossier_id UUID REFERENCES public.rnd_dossiers (id) ON DELETE SET NULL;

ALTER TABLE public.bom_eve
  ADD COLUMN IF NOT EXISTS rnd_dossier_id UUID REFERENCES public.rnd_dossiers (id) ON DELETE SET NULL;

ALTER TABLE public.bom_eve
  ADD COLUMN IF NOT EXISTS project_slug TEXT;

-- ---------------------------------------------------------------------------
-- RLS (anon access for Hub backend — same pattern as brainstorm_summaries)
-- ---------------------------------------------------------------------------
ALTER TABLE public.rnd_ideas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rnd_dossiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rnd_dossier_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rnd_dossier_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rnd_dossier_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rnd_committee_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rnd_committee_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rnd_social_calendar ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rnd_product_pages ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
  t TEXT;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'rnd_ideas', 'rnd_dossiers', 'rnd_dossier_sections', 'rnd_dossier_assets',
    'rnd_dossier_events', 'rnd_committee_sessions', 'rnd_committee_messages',
    'rnd_social_calendar', 'rnd_product_pages'
  ]
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS "anon_full_access_%s" ON public.%I', t, t);
    EXECUTE format(
      'CREATE POLICY "anon_full_access_%s" ON public.%I FOR ALL TO anon USING (true) WITH CHECK (true)',
      t, t
    );
    EXECUTE format('DROP POLICY IF EXISTS "authenticated_full_access_%s" ON public.%I', t, t);
    EXECUTE format(
      'CREATE POLICY "authenticated_full_access_%s" ON public.%I FOR ALL TO authenticated USING (true) WITH CHECK (true)',
      t, t
    );
  END LOOP;
END $$;
