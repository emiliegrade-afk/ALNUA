-- GDD chunks — gaming design documents per project (Phase 3 activation)

CREATE TABLE IF NOT EXISTS public.gdd_chunks (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id      UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  document_title  TEXT NOT NULL DEFAULT 'GDD',
  source_filename TEXT,
  section_title   TEXT NOT NULL DEFAULT 'Document',
  chunk_index     INTEGER NOT NULL DEFAULT 0,
  content         TEXT NOT NULL,
  token_estimate  INTEGER NOT NULL DEFAULT 0,
  gdd_version     TEXT NOT NULL DEFAULT '1',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gdd_chunks_project_id
  ON public.gdd_chunks (project_id);

CREATE INDEX IF NOT EXISTS idx_gdd_chunks_project_section
  ON public.gdd_chunks (project_id, section_title);

COMMENT ON TABLE public.gdd_chunks IS 'Chunked GDD markdown per gaming project — v1 text search only';
