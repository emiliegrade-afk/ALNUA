-- P1 SAV lite — product KB + support cases (Nadia)

CREATE TABLE IF NOT EXISTS public.product_kb (
  slug              TEXT PRIMARY KEY,
  name              TEXT NOT NULL DEFAULT '',
  support_email     TEXT DEFAULT '',
  faq_md            TEXT DEFAULT '',
  tone              TEXT DEFAULT 'professionnel et chaleureux',
  auto_reply_ok     BOOLEAN NOT NULL DEFAULT false,
  escalation_rules  TEXT DEFAULT '',
  metadata          JSONB NOT NULL DEFAULT '{}'::jsonb,
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.sav_cases (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_slug      TEXT NOT NULL REFERENCES public.product_kb (slug) ON DELETE CASCADE,
  channel           TEXT NOT NULL DEFAULT 'manual'
    CHECK (channel IN ('email', 'beta', 'telegram', 'manual', 'api')),
  customer_ref      TEXT DEFAULT '',
  subject           TEXT NOT NULL DEFAULT '',
  body              TEXT NOT NULL DEFAULT '',
  category          TEXT DEFAULT 'other'
    CHECK (category IN ('bug', 'howto', 'billing', 'complaint', 'feature', 'other')),
  status            TEXT NOT NULL DEFAULT 'open'
    CHECK (status IN ('open', 'draft_ready', 'awaiting_ceo', 'replied', 'escalated', 'closed')),
  draft_reply       TEXT DEFAULT '',
  needs_ceo         BOOLEAN NOT NULL DEFAULT false,
  confidence        NUMERIC(3, 2) DEFAULT 0,
  ticket_id         UUID REFERENCES public.tickets (id) ON DELETE SET NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sav_cases_product_status
  ON public.sav_cases (product_slug, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_sav_cases_needs_ceo
  ON public.sav_cases (needs_ceo, status)
  WHERE needs_ceo = true;

DROP TRIGGER IF EXISTS trg_sav_cases_updated_at ON public.sav_cases;
CREATE TRIGGER trg_sav_cases_updated_at
  BEFORE UPDATE ON public.sav_cases
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Seed KB rows from apps registry is done at runtime; allow hub slug
INSERT INTO public.product_kb (slug, name, faq_md, auto_reply_ok)
VALUES (
  'hub',
  'ALNUA Hub',
  '## FAQ Hub\n- Le Hub est le QG IA d''ALNUA (agents, R&D, ops).\n- Support interne : pas de SLA public.',
  false
)
ON CONFLICT (slug) DO NOTHING;
