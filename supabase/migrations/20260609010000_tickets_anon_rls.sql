-- Policies anon pour la page /tickets (clé publishable)

DROP POLICY IF EXISTS "anon_read_tickets" ON public.tickets;
DROP POLICY IF EXISTS "anon_insert_tickets" ON public.tickets;
DROP POLICY IF EXISTS "anon_update_tickets" ON public.tickets;

CREATE POLICY "anon_read_tickets" ON public.tickets
  FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_tickets" ON public.tickets
  FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon_update_tickets" ON public.tickets
  FOR UPDATE TO anon USING (true) WITH CHECK (true);
