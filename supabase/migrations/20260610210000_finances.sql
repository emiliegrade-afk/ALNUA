-- Finance module — transactions upgrade + monthly summaries

-- ---------------------------------------------------------------------------
-- financial_summaries
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
-- Upgrade transactions (from analytics schema → finance schema)
-- ---------------------------------------------------------------------------
ALTER TABLE public.transactions DROP CONSTRAINT IF EXISTS transactions_type_check;
ALTER TABLE public.transactions DROP CONSTRAINT IF EXISTS transactions_category_check;
ALTER TABLE public.transactions DROP CONSTRAINT IF EXISTS transactions_source_check;

UPDATE public.transactions SET type = 'income' WHERE type = 'revenue';

UPDATE public.transactions SET category = 'saas_tools'
  WHERE category IN ('subscription', 'tool_ai');
UPDATE public.transactions SET category = 'hosting'
  WHERE category = 'hosting';
UPDATE public.transactions SET category = 'marketing'
  WHERE category = 'marketing';
UPDATE public.transactions SET category = 'app_revenue'
  WHERE category = 'robot_sale';
UPDATE public.transactions SET category = 'autre'
  WHERE category = 'other';

ALTER TABLE public.transactions ALTER COLUMN project_id DROP NOT NULL;
ALTER TABLE public.transactions ALTER COLUMN description DROP NOT NULL;
ALTER TABLE public.transactions ALTER COLUMN description SET DEFAULT NULL;

ALTER TABLE public.transactions
  ADD COLUMN IF NOT EXISTS is_recurring BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE public.transactions
  ADD COLUMN IF NOT EXISTS recurrence TEXT;
ALTER TABLE public.transactions
  ADD COLUMN IF NOT EXISTS receipt_url TEXT;

ALTER TABLE public.transactions DROP COLUMN IF EXISTS source;

ALTER TABLE public.transactions
  ADD CONSTRAINT transactions_type_check
  CHECK (type IN ('income', 'expense'));

ALTER TABLE public.transactions
  ADD CONSTRAINT transactions_recurrence_check
  CHECK (recurrence IS NULL OR recurrence IN ('monthly', 'annual', 'one_time'));

ALTER TABLE public.transactions
  ADD CONSTRAINT transactions_category_check
  CHECK (
    (type = 'expense' AND category IN (
      'saas_tools', 'hardware', 'freelance', 'marketing',
      'legal', 'hosting', 'formation', 'autre'
    ))
    OR (type = 'income' AND category IN (
      'app_revenue', 'grant', 'consulting', 'investment', 'autre'
    ))
  );

CREATE INDEX IF NOT EXISTS idx_transactions_recurring
  ON public.transactions (is_recurring)
  WHERE is_recurring = true;

-- RLS
ALTER TABLE public.financial_summaries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.financial_summaries;
CREATE POLICY "authenticated_full_access" ON public.financial_summaries
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
