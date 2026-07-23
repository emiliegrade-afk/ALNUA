-- Multi-tenancy Sprint — tenants, personality, agent feedback, plugins + tenant_id columns

-- ---------------------------------------------------------------------------
-- tenants
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tenants (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  owner_email TEXT,
  settings    JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO public.tenants (id, name, owner_email)
VALUES ('alnua_coo', 'ALNUA Default', 'alnua.global@gmail.com')
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- tenant_personality — per-tenant agent tone overrides
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tenant_personality (
  tenant_id        TEXT PRIMARY KEY REFERENCES public.tenants (id) ON DELETE CASCADE,
  tone             TEXT NOT NULL DEFAULT 'balanced',
  vocabulary       TEXT NOT NULL DEFAULT 'business',
  emoji            BOOLEAN NOT NULL DEFAULT false,
  response_length  INT NOT NULL DEFAULT 800,
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO public.tenant_personality (tenant_id)
VALUES ('alnua_coo')
ON CONFLICT (tenant_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- agent_feedback — thumbs up/down on agent responses
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.agent_feedback (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         TEXT NOT NULL DEFAULT 'alnua_coo' REFERENCES public.tenants (id),
  agent_id          TEXT NOT NULL,
  response_id       TEXT NOT NULL,
  rating            SMALLINT NOT NULL CHECK (rating IN (-1, 1)),
  comment           TEXT,
  original_message  TEXT,
  original_response TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_feedback_tenant_agent
  ON public.agent_feedback (tenant_id, agent_id);

-- ---------------------------------------------------------------------------
-- hub_plugins — marketplace registry
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.hub_plugins (
  id              TEXT PRIMARY KEY,
  name            TEXT NOT NULL,
  version         TEXT NOT NULL DEFAULT '0.1.0',
  author          TEXT,
  description     TEXT,
  storage_path    TEXT,
  compatible_hub  TEXT DEFAULT '>=0.1.0',
  enabled         BOOLEAN NOT NULL DEFAULT true,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO public.hub_plugins (id, name, description, storage_path)
VALUES ('example_echo', 'Echo Agent', 'Example plugin template', 'plugins/example_echo')
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- tenant_id on core tables (nullable for backward compat, default alnua_coo)
-- ---------------------------------------------------------------------------
ALTER TABLE public.projects
  ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'alnua_coo' REFERENCES public.tenants (id);
CREATE INDEX IF NOT EXISTS idx_projects_tenant ON public.projects (tenant_id);

ALTER TABLE public.tickets
  ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'alnua_coo' REFERENCES public.tenants (id);
CREATE INDEX IF NOT EXISTS idx_tickets_tenant ON public.tickets (tenant_id);

ALTER TABLE public.agent_logs
  ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'alnua_coo' REFERENCES public.tenants (id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_tenant ON public.agent_logs (tenant_id);

ALTER TABLE public.beta_testers
  ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'alnua_coo' REFERENCES public.tenants (id);

ALTER TABLE public.beta_feedback
  ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'alnua_coo' REFERENCES public.tenants (id);

ALTER TABLE public.daily_briefings
  ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'alnua_coo' REFERENCES public.tenants (id);

ALTER TABLE public.composio_connections
  ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'alnua_coo' REFERENCES public.tenants (id);

ALTER TABLE public.brand_kits
  ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'alnua_coo' REFERENCES public.tenants (id);
