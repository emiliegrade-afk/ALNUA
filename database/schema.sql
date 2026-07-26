-- ALNUA Hub — Supabase schema
-- Run this in the Supabase SQL Editor or via migration.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------------
-- Helper: auto-update updated_at
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- 1. projects
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.projects (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  branch      TEXT NOT NULL CHECK (branch IN ('app', 'gaming', 'robotics', 'other')),
  description TEXT NOT NULL DEFAULT '',
  status      TEXT NOT NULL DEFAULT 'dev'
                CHECK (status IN ('active', 'beta', 'dev', 'paused')),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_projects_branch ON public.projects (branch);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects (status);

-- ---------------------------------------------------------------------------
-- 2. dev_log
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.dev_log (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id       UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  date             DATE NOT NULL DEFAULT CURRENT_DATE,
  content          TEXT NOT NULL,
  used_for_content BOOLEAN NOT NULL DEFAULT false,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dev_log_project_id ON public.dev_log (project_id);
CREATE INDEX IF NOT EXISTS idx_dev_log_date ON public.dev_log (date DESC);
CREATE INDEX IF NOT EXISTS idx_dev_log_unused_content
  ON public.dev_log (project_id, used_for_content)
  WHERE used_for_content = false;

-- ---------------------------------------------------------------------------
-- 3. tickets
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tickets (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id    UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  type          TEXT NOT NULL CHECK (type IN ('bug', 'feature', 'improvement', 'crash', 'reminder')),
  priority      TEXT NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('critical', 'high', 'medium', 'low')),
  title         TEXT NOT NULL,
  description   TEXT NOT NULL DEFAULT '',
  source        TEXT NOT NULL
                CHECK (source IN (
                  'qa_agent', 'sav_bot', 'reviews_bot', 'emilie',
                  'quick_capture', 'beta_tester', 'partnerships_bot'
                )),
  status        TEXT NOT NULL DEFAULT 'open'
                CHECK (status IN ('open', 'in_progress', 'done', 'wont_fix')),
  cursor_prompt TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tickets_project_id ON public.tickets (project_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON public.tickets (status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON public.tickets (priority);

DROP TRIGGER IF EXISTS trg_tickets_updated_at ON public.tickets;
CREATE TRIGGER trg_tickets_updated_at
  BEFORE UPDATE ON public.tickets
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- 4. roadmap
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.roadmap (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id        UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  title             TEXT NOT NULL,
  description       TEXT NOT NULL DEFAULT '',
  status            TEXT NOT NULL DEFAULT 'planned'
                    CHECK (status IN ('idea', 'planned', 'in_progress', 'done')),
  priority          TEXT NOT NULL DEFAULT 'medium'
                    CHECK (priority IN ('critical', 'high', 'medium', 'low')),
  phase             TEXT,
  due_date          DATE,
  linked_ticket_id  UUID REFERENCES public.tickets (id) ON DELETE SET NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_roadmap_project_id ON public.roadmap (project_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_status ON public.roadmap (status);
CREATE INDEX IF NOT EXISTS idx_roadmap_due_date
  ON public.roadmap (due_date)
  WHERE due_date IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 5. feedback
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.feedback (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  source     TEXT NOT NULL
             CHECK (source IN (
               'beta_portal', 'discord', 'app_store', 'google_play', 'reddit', 'sav'
             )),
  author     TEXT,
  content    TEXT NOT NULL,
  sentiment  TEXT NOT NULL DEFAULT 'neutral'
             CHECK (sentiment IN ('positive', 'negative', 'neutral', 'mixed')),
  rating     INT CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5)),
  status     TEXT NOT NULL DEFAULT 'new'
             CHECK (status IN ('new', 'processed', 'ticket_created')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_project_id ON public.feedback (project_id);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON public.feedback (status);
CREATE INDEX IF NOT EXISTS idx_feedback_sentiment ON public.feedback (sentiment);

-- ---------------------------------------------------------------------------
-- 6. posts_queue
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.posts_queue (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id        UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  sector            TEXT
                    CHECK (sector IS NULL OR sector IN ('app', 'gaming', 'robo', 'company')),
  author_agent_id   TEXT,
  platform          TEXT NOT NULL
                    CHECK (platform IN (
                      'instagram', 'tiktok', 'x', 'youtube', 'linkedin', 'website_blog', 'discord'
                    )),
  content_type      TEXT NOT NULL
                    CHECK (content_type IN (
                      'announcement', 'teaser', 'tutorial', 'behind_scenes', 'short_video'
                    )),
  text_content      TEXT NOT NULL,
  layout            JSONB,
  image_prompt      TEXT,
  media_urls        TEXT[] NOT NULL DEFAULT '{}',
  video_script      TEXT,
  hashtags          TEXT[] NOT NULL DEFAULT '{}',
  channel           TEXT,
  scheduled_at      TIMESTAMPTZ NOT NULL,
  published_at      TIMESTAMPTZ,
  status            TEXT NOT NULL DEFAULT 'draft'
                    CHECK (status IN (
                      'draft', 'pending_approval', 'approved', 'published', 'failed', 'rejected'
                    )),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_posts_queue_project_id ON public.posts_queue (project_id);
CREATE INDEX IF NOT EXISTS idx_posts_queue_status ON public.posts_queue (status);
CREATE INDEX IF NOT EXISTS idx_posts_queue_scheduled_at ON public.posts_queue (scheduled_at);
CREATE INDEX IF NOT EXISTS idx_posts_queue_sector_scheduled ON public.posts_queue (sector, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_posts_queue_author_agent ON public.posts_queue (author_agent_id);

-- ---------------------------------------------------------------------------
-- 7. analytics
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.analytics (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id   UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  date         DATE NOT NULL,
  metric_name  TEXT NOT NULL
               CHECK (metric_name IN (
                 'downloads', 'active_users', 'subscriptions', 'mrr', 'churn', 'web_visitors'
               )),
  value        NUMERIC NOT NULL,
  source       TEXT NOT NULL
               CHECK (source IN (
                 'app_store', 'google_play', 'stripe', 'revenuecat', 'plausible'
               )),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, date, metric_name, source)
);

CREATE INDEX IF NOT EXISTS idx_analytics_project_date
  ON public.analytics (project_id, date DESC);

-- ---------------------------------------------------------------------------
-- 8. transactions (finance)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.transactions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date          DATE NOT NULL DEFAULT CURRENT_DATE,
  type          TEXT NOT NULL CHECK (type IN ('income', 'expense')),
  amount        NUMERIC(10, 2) NOT NULL,
  currency      TEXT NOT NULL DEFAULT 'EUR',
  category      TEXT NOT NULL,
  project_id    UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  description   TEXT,
  is_recurring  BOOLEAN NOT NULL DEFAULT false,
  recurrence    TEXT CHECK (recurrence IS NULL OR recurrence IN ('monthly', 'annual', 'one_time')),
  receipt_url   TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT transactions_category_check CHECK (
    (type = 'expense' AND category IN (
      'saas_tools', 'hardware', 'freelance', 'marketing',
      'legal', 'hosting', 'formation', 'autre'
    ))
    OR (type = 'income' AND category IN (
      'app_revenue', 'grant', 'consulting', 'investment', 'autre'
    ))
  )
);

CREATE INDEX IF NOT EXISTS idx_transactions_project_id ON public.transactions (project_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON public.transactions (date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON public.transactions (type);
CREATE INDEX IF NOT EXISTS idx_transactions_recurring
  ON public.transactions (is_recurring)
  WHERE is_recurring = true;

-- ---------------------------------------------------------------------------
-- 8b. financial_summaries
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.financial_summaries (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  month           TEXT NOT NULL,
  summary_md      TEXT,
  total_income    NUMERIC(10, 2),
  total_expenses  NUMERIC(10, 2),
  balance         NUMERIC(10, 2),
  by_category     JSONB,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (month)
);

CREATE INDEX IF NOT EXISTS idx_financial_summaries_month
  ON public.financial_summaries (month DESC);

-- ---------------------------------------------------------------------------
-- 9. faq
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.faq (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  question   TEXT NOT NULL,
  answer     TEXT NOT NULL,
  tags       TEXT[] NOT NULL DEFAULT '{}',
  active     BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_faq_project_id ON public.faq (project_id);
CREATE INDEX IF NOT EXISTS idx_faq_active ON public.faq (project_id, active) WHERE active = true;

-- ---------------------------------------------------------------------------
-- 10. agent_logs
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.agent_logs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name      TEXT NOT NULL,
  action          TEXT NOT NULL,
  project_id      UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  input_summary   TEXT NOT NULL DEFAULT '',
  output_summary  TEXT NOT NULL DEFAULT '',
  status          TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('success', 'error', 'pending')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_name ON public.agent_logs (agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_logs_created_at ON public.agent_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_logs_project_id ON public.agent_logs (project_id);

-- ---------------------------------------------------------------------------
-- 11. brainstorm_summaries — mémoire cross-sessions brainstorm
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.brainstorm_summaries (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id      UUID REFERENCES public.projects (id) ON DELETE CASCADE,
  session_id      TEXT NOT NULL,
  session_number  INT NOT NULL,
  title           TEXT NOT NULL,
  summary         TEXT NOT NULL,
  key_ideas       TEXT[] NOT NULL DEFAULT '{}',
  decisions       TEXT[] NOT NULL DEFAULT '{}',
  next_steps      TEXT[] NOT NULL DEFAULT '{}',
  open_questions  TEXT[] NOT NULL DEFAULT '{}',
  file_path       TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_brainstorm_summaries_project
  ON public.brainstorm_summaries (project_id, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_brainstorm_summaries_session
  ON public.brainstorm_summaries (session_id);

-- ---------------------------------------------------------------------------
-- 12. brand_kits — analyses et assets Brand Design
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.brand_kits (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id        UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  brand_name        TEXT NOT NULL,
  analysis          JSONB NOT NULL,
  assets_path       TEXT NOT NULL DEFAULT '',
  formats_generated TEXT[] NOT NULL DEFAULT '{}',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_brand_kits_project_id
  ON public.brand_kits (project_id);
CREATE INDEX IF NOT EXISTS idx_brand_kits_created_at
  ON public.brand_kits (created_at DESC);

DROP TRIGGER IF EXISTS trg_brand_kits_updated_at ON public.brand_kits;
CREATE TRIGGER trg_brand_kits_updated_at
  BEFORE UPDATE ON public.brand_kits
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- 13. daily_briefings — digest matinal automatique
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.daily_briefings (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date          DATE NOT NULL,
  summary       TEXT NOT NULL,
  raw_data      JSONB,
  has_urgent    BOOLEAN NOT NULL DEFAULT false,
  urgent_count  INT NOT NULL DEFAULT 0,
  pending_count INT NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_daily_briefings_date
  ON public.daily_briefings (date DESC);

-- ---------------------------------------------------------------------------
-- 14. quick_notes — captures rapides (Quick Capture)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.quick_notes (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id  UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  content     TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_quick_notes_project
  ON public.quick_notes (project_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- 15. releases — notes de version App Store / Google Play / CHANGELOG
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.releases (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id       UUID REFERENCES public.projects (id) ON DELETE CASCADE,
  version          TEXT NOT NULL,
  release_date     DATE,
  app_store_notes  TEXT,
  google_play_notes TEXT,
  changelog_md     TEXT,
  dev_log_ids      UUID[],
  status           TEXT NOT NULL DEFAULT 'draft'
                   CHECK (status IN ('draft', 'published')),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_releases_project_id
  ON public.releases (project_id);
CREATE INDEX IF NOT EXISTS idx_releases_created_at
  ON public.releases (created_at DESC);

-- ---------------------------------------------------------------------------
-- 16. beta_testers — programme beta (portail testeuses)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.beta_testers (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id     UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  email          TEXT NOT NULL,
  first_name     TEXT,
  device         TEXT,
  os_version     TEXT,
  app_version    TEXT,
  joined_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  feedback_count INT NOT NULL DEFAULT 0,
  UNIQUE (project_id, email)
);

CREATE INDEX IF NOT EXISTS idx_beta_testers_project
  ON public.beta_testers (project_id);
CREATE INDEX IF NOT EXISTS idx_beta_testers_email
  ON public.beta_testers (email);

-- ---------------------------------------------------------------------------
-- 17. beta_feedback — retours soumis via le portail beta
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.beta_feedback (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tester_id       UUID NOT NULL REFERENCES public.beta_testers (id) ON DELETE CASCADE,
  project_id      UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  type            TEXT CHECK (type IN ('bug', 'suggestion', 'crash', 'ux', 'autre')),
  title           TEXT NOT NULL,
  description     TEXT,
  screenshot_url  TEXT,
  severity        TEXT CHECK (severity IN ('bloquant', 'majeur', 'mineur', 'cosmétique')),
  ticket_id       UUID REFERENCES public.tickets (id) ON DELETE SET NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_beta_feedback_project
  ON public.beta_feedback (project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_beta_feedback_tester
  ON public.beta_feedback (tester_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- 18. waitlist — pré-inscriptions avant lancement
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.waitlist (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id  UUID REFERENCES public.projects (id) ON DELETE CASCADE,
  email       TEXT NOT NULL,
  first_name  TEXT,
  source      TEXT,
  message     TEXT,
  status      TEXT NOT NULL DEFAULT 'waiting'
              CHECK (status IN ('waiting', 'notified', 'converted')),
  notified_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (email, project_id)
);

CREATE INDEX IF NOT EXISTS idx_waitlist_project
  ON public.waitlist (project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_waitlist_status
  ON public.waitlist (status);
CREATE INDEX IF NOT EXISTS idx_waitlist_source
  ON public.waitlist (source);

-- ---------------------------------------------------------------------------
-- partnerships — CRM, demandes, affiliés
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.partners (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type                 TEXT NOT NULL,
  status               TEXT NOT NULL DEFAULT 'prospect',
  direction            TEXT NOT NULL,
  name                 TEXT NOT NULL,
  company              TEXT,
  email                TEXT,
  instagram_url        TEXT,
  tiktok_url           TEXT,
  youtube_url          TEXT,
  website              TEXT,
  audience_size        INT,
  audience_description TEXT,
  project_ids          UUID[],
  notes                TEXT,
  contract_path        TEXT,
  next_followup        DATE,
  last_contact_date    DATE,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_partners_status ON public.partners (status);
CREATE INDEX IF NOT EXISTS idx_partners_type ON public.partners (type);
CREATE INDEX IF NOT EXISTS idx_partners_direction ON public.partners (direction);
CREATE INDEX IF NOT EXISTS idx_partners_next_followup ON public.partners (next_followup);

DROP TRIGGER IF EXISTS trg_partners_updated_at ON public.partners;
CREATE TRIGGER trg_partners_updated_at
  BEFORE UPDATE ON public.partners
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE IF NOT EXISTS public.partner_interactions (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  partner_id UUID NOT NULL REFERENCES public.partners (id) ON DELETE CASCADE,
  date       TIMESTAMPTZ NOT NULL DEFAULT now(),
  type       TEXT,
  note       TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_partner_interactions_partner
  ON public.partner_interactions (partner_id, date DESC);

CREATE TABLE IF NOT EXISTS public.affiliate_links (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  partner_id        UUID NOT NULL REFERENCES public.partners (id) ON DELETE CASCADE,
  project_id        UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  code              TEXT NOT NULL UNIQUE,
  redirect_url      TEXT NOT NULL,
  commission_type   TEXT,
  commission_value  DECIMAL(10, 2),
  clicks            INT NOT NULL DEFAULT 0,
  conversions       INT NOT NULL DEFAULT 0,
  revenue_generated DECIMAL(10, 2) NOT NULL DEFAULT 0,
  active            BOOLEAN NOT NULL DEFAULT true,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_affiliate_links_code ON public.affiliate_links (code);
CREATE INDEX IF NOT EXISTS idx_affiliate_links_partner ON public.affiliate_links (partner_id);

CREATE TABLE IF NOT EXISTS public.affiliate_clicks (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  link_id    UUID NOT NULL REFERENCES public.affiliate_links (id) ON DELETE CASCADE,
  event_type TEXT NOT NULL DEFAULT 'click'
             CHECK (event_type IN ('click', 'conversion')),
  revenue    DECIMAL(10, 2),
  user_agent TEXT,
  referer    TEXT,
  clicked_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_link_date
  ON public.affiliate_clicks (link_id, clicked_at DESC);

CREATE TABLE IF NOT EXISTS public.partnership_requests (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name             TEXT NOT NULL,
  email            TEXT NOT NULL,
  type             TEXT,
  message          TEXT,
  instagram_url    TEXT,
  tiktok_url       TEXT,
  website          TEXT,
  audience_size    TEXT,
  project_interest TEXT,
  status           TEXT NOT NULL DEFAULT 'new',
  partner_id       UUID REFERENCES public.partners (id) ON DELETE SET NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_partnership_requests_status
  ON public.partnership_requests (status, created_at DESC);

-- Migration : autoriser la branche « other » sur une base existante
ALTER TABLE public.projects DROP CONSTRAINT IF EXISTS projects_branch_check;
ALTER TABLE public.projects ADD CONSTRAINT projects_branch_check
  CHECK (branch IN ('app', 'gaming', 'robotics', 'other'));

-- ---------------------------------------------------------------------------
-- Row Level Security (service role bypasses RLS; policies for authenticated)
-- ---------------------------------------------------------------------------
ALTER TABLE public.projects      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dev_log       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tickets       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.roadmap       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedback      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posts_queue   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analytics     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.faq           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_logs           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brainstorm_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brand_kits            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_briefings       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quick_notes           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.releases              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.beta_testers          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.beta_feedback         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.waitlist              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.partners              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.partner_interactions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.affiliate_links       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.affiliate_clicks      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.financial_summaries     ENABLE ROW LEVEL SECURITY;

-- Authenticated users (Emilie) get full access via backend JWT
DO $$
DECLARE
  tbl TEXT;
BEGIN
  FOREACH tbl IN ARRAY ARRAY[
    'projects', 'dev_log', 'tickets', 'roadmap', 'feedback',
    'posts_queue', 'analytics', 'transactions', 'faq', 'agent_logs',
    'brainstorm_summaries', 'brand_kits', 'daily_briefings', 'quick_notes',
    'releases', 'beta_testers', 'beta_feedback', 'waitlist',
    'partners', 'partner_interactions', 'affiliate_links',
    'affiliate_clicks', 'partnership_requests', 'financial_summaries'
  ] LOOP
    EXECUTE format(
      'CREATE POLICY "authenticated_full_access" ON public.%I
       FOR ALL TO authenticated USING (true) WITH CHECK (true)',
      tbl
    );
  END LOOP;
END $$;

-- ---------------------------------------------------------------------------
-- Seed: ALNUA projects
-- ---------------------------------------------------------------------------
INSERT INTO public.projects (name, branch, description, status)
SELECT v.name, v.branch, v.description, v.status
FROM (VALUES
  ('Naïa', 'app', 'Application bien-être — méditation, journal, routines.', 'beta'),
  ('Wyrdheim Online', 'gaming', 'MMORPG fantasy nordique — monde ouvert, guildes, raids.', 'dev'),
  ('Eve', 'robotics', 'Robot compagnon domestique — Eve, premier produit robotique ALNUA.', 'dev')
) AS v(name, branch, description, status)
WHERE NOT EXISTS (
  SELECT 1 FROM public.projects p WHERE p.name = v.name
);
