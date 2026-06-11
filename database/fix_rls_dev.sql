-- Dev fix: allow publishable/anon key from ALNUA Hub backend + frontend
-- Run in Supabase SQL Editor if agent_logs inserts fail (RLS 42501)

DROP POLICY IF EXISTS "anon_read_agent_logs" ON public.agent_logs;
DROP POLICY IF EXISTS "anon_insert_agent_logs" ON public.agent_logs;
DROP POLICY IF EXISTS "anon_read_projects" ON public.projects;

CREATE POLICY "anon_read_agent_logs" ON public.agent_logs
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_agent_logs" ON public.agent_logs
  FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon_read_projects" ON public.projects
  FOR SELECT TO anon USING (true);

-- Roadmap inserts from brainstorm modal
DROP POLICY IF EXISTS "anon_insert_roadmap" ON public.roadmap;
DROP POLICY IF EXISTS "anon_read_roadmap" ON public.roadmap;

CREATE POLICY "anon_read_roadmap" ON public.roadmap
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_roadmap" ON public.roadmap
  FOR INSERT TO anon WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_roadmap" ON public.roadmap;
DROP POLICY IF EXISTS "anon_delete_roadmap" ON public.roadmap;

CREATE POLICY "anon_update_roadmap" ON public.roadmap
  FOR UPDATE TO anon USING (true) WITH CHECK (true);

CREATE POLICY "anon_delete_roadmap" ON public.roadmap
  FOR DELETE TO anon USING (true);

-- Projets : création depuis le Hub
DROP POLICY IF EXISTS "anon_insert_projects" ON public.projects;
CREATE POLICY "anon_insert_projects" ON public.projects
  FOR INSERT TO anon WITH CHECK (true);

-- Comptes-rendus brainstorm
DROP POLICY IF EXISTS "anon_read_brainstorm_summaries" ON public.brainstorm_summaries;
DROP POLICY IF EXISTS "anon_insert_brainstorm_summaries" ON public.brainstorm_summaries;
DROP POLICY IF EXISTS "anon_update_brainstorm_summaries" ON public.brainstorm_summaries;

CREATE POLICY "anon_read_brainstorm_summaries" ON public.brainstorm_summaries
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_brainstorm_summaries" ON public.brainstorm_summaries
  FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon_update_brainstorm_summaries" ON public.brainstorm_summaries
  FOR UPDATE TO anon USING (true) WITH CHECK (true);

-- Tickets (page /tickets)
DROP POLICY IF EXISTS "anon_read_tickets" ON public.tickets;
DROP POLICY IF EXISTS "anon_insert_tickets" ON public.tickets;
DROP POLICY IF EXISTS "anon_update_tickets" ON public.tickets;

CREATE POLICY "anon_read_tickets" ON public.tickets
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_tickets" ON public.tickets
  FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon_update_tickets" ON public.tickets
  FOR UPDATE TO anon USING (true) WITH CHECK (true);

-- Analytics, feedback, transactions (page /analytics)
DROP POLICY IF EXISTS "anon_read_analytics" ON public.analytics;
DROP POLICY IF EXISTS "anon_insert_analytics" ON public.analytics;
DROP POLICY IF EXISTS "anon_read_feedback" ON public.feedback;
DROP POLICY IF EXISTS "anon_read_transactions" ON public.transactions;

CREATE POLICY "anon_read_analytics" ON public.analytics
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_analytics" ON public.analytics
  FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon_read_feedback" ON public.feedback
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_read_transactions" ON public.transactions
  FOR SELECT TO anon USING (true);

-- Brand kits (page /brand) — run database/brand_kits_migration.sql first if table missing
DROP POLICY IF EXISTS "anon_read_brand_kits" ON public.brand_kits;
DROP POLICY IF EXISTS "anon_insert_brand_kits" ON public.brand_kits;
DROP POLICY IF EXISTS "anon_update_brand_kits" ON public.brand_kits;

CREATE POLICY "anon_read_brand_kits" ON public.brand_kits
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_brand_kits" ON public.brand_kits
  FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon_update_brand_kits" ON public.brand_kits
  FOR UPDATE TO anon USING (true) WITH CHECK (true);

-- Agent LLM costs (Phase 2 pipeline)
DROP POLICY IF EXISTS "anon_read_agent_costs" ON public.agent_costs;
DROP POLICY IF EXISTS "anon_insert_agent_costs" ON public.agent_costs;

CREATE POLICY "anon_read_agent_costs" ON public.agent_costs
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_agent_costs" ON public.agent_costs
  FOR INSERT TO anon WITH CHECK (true);

-- Daily briefings (page /briefing + scheduler)
DROP POLICY IF EXISTS "anon_read_daily_briefings" ON public.daily_briefings;
DROP POLICY IF EXISTS "anon_insert_daily_briefings" ON public.daily_briefings;

CREATE POLICY "anon_read_daily_briefings" ON public.daily_briefings
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_daily_briefings" ON public.daily_briefings
  FOR INSERT TO anon WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_daily_briefings" ON public.daily_briefings;
CREATE POLICY "anon_update_daily_briefings" ON public.daily_briefings
  FOR UPDATE TO anon USING (true) WITH CHECK (true);

-- Quick notes (Quick Capture)
DROP POLICY IF EXISTS "anon_read_quick_notes" ON public.quick_notes;
DROP POLICY IF EXISTS "anon_insert_quick_notes" ON public.quick_notes;

CREATE POLICY "anon_read_quick_notes" ON public.quick_notes
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_quick_notes" ON public.quick_notes
  FOR INSERT TO anon WITH CHECK (true);

-- Partnerships CRM
DO $$
DECLARE
  tbl TEXT;
BEGIN
  FOREACH tbl IN ARRAY ARRAY[
    'partners', 'partner_interactions', 'affiliate_links',
    'affiliate_clicks', 'partnership_requests'
  ] LOOP
    EXECUTE format('DROP POLICY IF EXISTS "anon_all_%s" ON public.%I', tbl, tbl);
    EXECUTE format(
      'CREATE POLICY "anon_all_%s" ON public.%I
       FOR ALL TO anon USING (true) WITH CHECK (true)',
      tbl, tbl
    );
  END LOOP;
END $$;
