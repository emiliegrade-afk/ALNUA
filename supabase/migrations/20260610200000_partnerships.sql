-- Partenariats & Affiliés — CRM, demandes publiques, tracking liens

-- Extend tickets for partnership follow-up reminders
ALTER TABLE public.tickets DROP CONSTRAINT IF EXISTS tickets_type_check;
ALTER TABLE public.tickets ADD CONSTRAINT tickets_type_check
  CHECK (type IN ('bug', 'feature', 'improvement', 'crash', 'reminder'));

ALTER TABLE public.tickets DROP CONSTRAINT IF EXISTS tickets_source_check;
ALTER TABLE public.tickets ADD CONSTRAINT tickets_source_check
  CHECK (source IN (
    'qa_agent', 'sav_bot', 'reviews_bot', 'emilie',
    'quick_capture', 'beta_tester', 'partnerships_bot'
  ));

-- ---------------------------------------------------------------------------
-- partners
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

-- ---------------------------------------------------------------------------
-- partner_interactions
-- ---------------------------------------------------------------------------
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

-- ---------------------------------------------------------------------------
-- affiliate_links
-- ---------------------------------------------------------------------------
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

-- ---------------------------------------------------------------------------
-- affiliate_clicks (tracking per redirect)
-- ---------------------------------------------------------------------------
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

-- ---------------------------------------------------------------------------
-- partnership_requests (public form submissions)
-- ---------------------------------------------------------------------------
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

-- RLS
ALTER TABLE public.partners ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.partner_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.affiliate_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.affiliate_clicks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.partnership_requests ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.partners;
CREATE POLICY "authenticated_full_access" ON public.partners
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "authenticated_full_access" ON public.partner_interactions;
CREATE POLICY "authenticated_full_access" ON public.partner_interactions
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "authenticated_full_access" ON public.affiliate_links;
CREATE POLICY "authenticated_full_access" ON public.affiliate_links
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "authenticated_full_access" ON public.affiliate_clicks;
CREATE POLICY "authenticated_full_access" ON public.affiliate_clicks
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "authenticated_full_access" ON public.partnership_requests;
CREATE POLICY "authenticated_full_access" ON public.partnership_requests
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- Anon policies for Hub backend (service/anon key)
DROP POLICY IF EXISTS "anon_all_partners" ON public.partners;
CREATE POLICY "anon_all_partners" ON public.partners
  FOR ALL TO anon USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_all_partner_interactions" ON public.partner_interactions;
CREATE POLICY "anon_all_partner_interactions" ON public.partner_interactions
  FOR ALL TO anon USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_all_affiliate_links" ON public.affiliate_links;
CREATE POLICY "anon_all_affiliate_links" ON public.affiliate_links
  FOR ALL TO anon USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_all_affiliate_clicks" ON public.affiliate_clicks;
CREATE POLICY "anon_all_affiliate_clicks" ON public.affiliate_clicks
  FOR ALL TO anon USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_all_partnership_requests" ON public.partnership_requests;
CREATE POLICY "anon_all_partnership_requests" ON public.partnership_requests
  FOR ALL TO anon USING (true) WITH CHECK (true);
