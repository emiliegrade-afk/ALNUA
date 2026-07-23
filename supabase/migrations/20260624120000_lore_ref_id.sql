-- Lore entries: stable ref_id from Obsidian nomenclature (LORE-WYR-001, etc.)

ALTER TABLE public.lore_entries
  ADD COLUMN IF NOT EXISTS ref_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_lore_entries_ref_id
  ON public.lore_entries (ref_id)
  WHERE ref_id IS NOT NULL;

COMMENT ON COLUMN public.lore_entries.ref_id IS 'ALNUA nomenclature ref — synced from Obsidian frontmatter';
