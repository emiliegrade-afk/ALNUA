-- Hub backend (anon/service) full access on posts_queue — same as rnd_* tables.
-- Required for Content agent + R&D social pipeline inserts via FastAPI.

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'posts_queue') THEN
    EXECUTE 'DROP POLICY IF EXISTS "anon_full_access_posts_queue" ON public.posts_queue';
    EXECUTE $p$
      CREATE POLICY "anon_full_access_posts_queue" ON public.posts_queue
      FOR ALL TO anon USING (true) WITH CHECK (true)
    $p$;
  END IF;
END $$;
