-- Trace les apps Composio connectées par agent
CREATE TABLE IF NOT EXISTS public.composio_connections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    app_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'expired', 'revoked')),
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    UNIQUE(user_id, app_name)
);

ALTER TABLE public.composio_connections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_all_composio" ON public.composio_connections FOR ALL TO anon USING (true) WITH CHECK (true);
