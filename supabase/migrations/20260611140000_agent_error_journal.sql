-- Agent error journal — persistent learning memory for coding/R&D agents

CREATE TABLE IF NOT EXISTS public.agent_error_journal (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_name TEXT NOT NULL,
    task_id TEXT,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    context TEXT,
    solution TEXT,
    attempts INTEGER DEFAULT 1,
    status TEXT DEFAULT 'open'
        CHECK (status IN ('open', 'resolved', 'abandoned', 'escalated')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_error_agent ON public.agent_error_journal(agent_name);
CREATE INDEX IF NOT EXISTS idx_error_type ON public.agent_error_journal(error_type);
CREATE INDEX IF NOT EXISTS idx_error_status ON public.agent_error_journal(status);
CREATE INDEX IF NOT EXISTS idx_error_fts ON public.agent_error_journal
    USING GIN (to_tsvector('french', error_message || ' ' || COALESCE(context, '')));

CREATE OR REPLACE FUNCTION public.increment_error_attempts(entry_id UUID)
RETURNS void AS $$
    UPDATE public.agent_error_journal
    SET attempts = attempts + 1
    WHERE id = entry_id;
$$ LANGUAGE sql;

ALTER TABLE public.agent_error_journal ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_read_agent_error_journal" ON public.agent_error_journal;
DROP POLICY IF EXISTS "anon_insert_agent_error_journal" ON public.agent_error_journal;
DROP POLICY IF EXISTS "anon_update_agent_error_journal" ON public.agent_error_journal;

CREATE POLICY "anon_read_agent_error_journal" ON public.agent_error_journal
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_agent_error_journal" ON public.agent_error_journal
  FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon_update_agent_error_journal" ON public.agent_error_journal
  FOR UPDATE TO anon USING (true) WITH CHECK (true);
