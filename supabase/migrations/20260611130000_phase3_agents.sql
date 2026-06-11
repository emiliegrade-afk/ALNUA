-- Phase 3 : lore database + BOM Eve robot

CREATE TABLE IF NOT EXISTS public.lore_entries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('factions','personnages','lieux','histoire','magie','economie','quetes')),
    project TEXT NOT NULL CHECK (project IN ('wyrdheim','naia_world','shared')),
    content TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lore_project ON public.lore_entries(project);
CREATE INDEX IF NOT EXISTS idx_lore_category ON public.lore_entries(category);
CREATE INDEX IF NOT EXISTS idx_lore_fts ON public.lore_entries
  USING GIN (to_tsvector('french', title || ' ' || content));

ALTER TABLE public.lore_entries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.lore_entries;
CREATE POLICY "authenticated_full_access" ON public.lore_entries
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_read_lore_entries" ON public.lore_entries;
CREATE POLICY "anon_read_lore_entries" ON public.lore_entries
  FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS "anon_insert_lore_entries" ON public.lore_entries;
CREATE POLICY "anon_insert_lore_entries" ON public.lore_entries
  FOR INSERT TO anon WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_lore_entries" ON public.lore_entries;
CREATE POLICY "anon_update_lore_entries" ON public.lore_entries
  FOR UPDATE TO anon USING (true) WITH CHECK (true);

-- BOM (Bill of Materials) Eve robot
CREATE TABLE IF NOT EXISTS public.bom_eve (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    component TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('vision','audio','moteur','alimentation','microcontroleur','chassis','autre')),
    quantity INTEGER DEFAULT 1,
    unit_price NUMERIC(10,2),
    total_price NUMERIC(10,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    supplier TEXT,
    url TEXT,
    status TEXT DEFAULT 'a_commander' CHECK (status IN ('a_commander','commande','livre','utilise')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bom_eve_category ON public.bom_eve(category);
CREATE INDEX IF NOT EXISTS idx_bom_eve_status ON public.bom_eve(status);

ALTER TABLE public.bom_eve ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "authenticated_full_access" ON public.bom_eve;
CREATE POLICY "authenticated_full_access" ON public.bom_eve
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_full_access_bom_eve" ON public.bom_eve;
CREATE POLICY "anon_full_access_bom_eve" ON public.bom_eve
  FOR ALL TO anon USING (true) WITH CHECK (true);
