-- Agent LLM cost tracking — run once in Supabase SQL Editor
-- Project: vadmtrbhoeoxzdozuark (ALNUA Hub)

CREATE TABLE IF NOT EXISTS public.agent_costs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_name TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost_usd NUMERIC(10,6) DEFAULT 0,
    task_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_costs_created_at ON public.agent_costs(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_costs_agent_name ON public.agent_costs(agent_name);

ALTER TABLE public.agent_costs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_read_agent_costs" ON public.agent_costs;
DROP POLICY IF EXISTS "anon_insert_agent_costs" ON public.agent_costs;

CREATE POLICY "anon_read_agent_costs" ON public.agent_costs
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_agent_costs" ON public.agent_costs
  FOR INSERT TO anon WITH CHECK (true);
