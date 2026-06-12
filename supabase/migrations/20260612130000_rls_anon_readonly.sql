-- Restrict anon RLS to SELECT-only on sensitive tables.
-- INSERT/UPDATE/DELETE must go through the API using service_role (bypasses RLS).

-- composio_connections
DROP POLICY IF EXISTS "anon_all_composio" ON public.composio_connections;
CREATE POLICY "anon_read_composio_connections" ON public.composio_connections
  FOR SELECT TO anon USING (true);

-- bom_eve
DROP POLICY IF EXISTS "anon_full_access_bom_eve" ON public.bom_eve;
CREATE POLICY "anon_read_bom_eve" ON public.bom_eve
  FOR SELECT TO anon USING (true);

-- agent_error_journal
DROP POLICY IF EXISTS "anon_insert_agent_error_journal" ON public.agent_error_journal;
DROP POLICY IF EXISTS "anon_update_agent_error_journal" ON public.agent_error_journal;
-- anon_read_agent_error_journal (SELECT) unchanged
