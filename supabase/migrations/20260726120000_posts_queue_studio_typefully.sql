-- ALNUA Hub — Studio Typefully : posts_queue sectorisation + layouts + médias + Discord.
-- Ajoute ce qu'il faut pour un calendrier/composer transverse par secteur (app/gaming/robo/company)
-- et pour les devlogs Discord, sans casser les lignes existantes (toutes colonnes nullable/défaut).

-- ---------------------------------------------------------------------------
-- 1. Colonnes : secteur, agent auteur, layout structuré, médias, canal Discord
-- ---------------------------------------------------------------------------
ALTER TABLE public.posts_queue ADD COLUMN IF NOT EXISTS sector TEXT;
ALTER TABLE public.posts_queue ADD COLUMN IF NOT EXISTS author_agent_id TEXT;
ALTER TABLE public.posts_queue ADD COLUMN IF NOT EXISTS layout JSONB;
ALTER TABLE public.posts_queue ADD COLUMN IF NOT EXISTS media_urls TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE public.posts_queue ADD COLUMN IF NOT EXISTS channel TEXT;

ALTER TABLE public.posts_queue DROP CONSTRAINT IF EXISTS posts_queue_sector_check;
ALTER TABLE public.posts_queue ADD CONSTRAINT posts_queue_sector_check
  CHECK (sector IS NULL OR sector IN ('app', 'gaming', 'robo', 'company'));

-- ---------------------------------------------------------------------------
-- 2. Platform : ajout discord (devlogs / MAJ communauté)
-- ---------------------------------------------------------------------------
ALTER TABLE public.posts_queue DROP CONSTRAINT IF EXISTS posts_queue_platform_check;
ALTER TABLE public.posts_queue ADD CONSTRAINT posts_queue_platform_check
  CHECK (platform IN (
    'instagram', 'tiktok', 'x', 'youtube', 'linkedin', 'website_blog', 'discord'
  ));

-- ---------------------------------------------------------------------------
-- 3. Index calendrier par secteur + par agent auteur
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_posts_queue_sector_scheduled
  ON public.posts_queue (sector, scheduled_at);

CREATE INDEX IF NOT EXISTS idx_posts_queue_author_agent
  ON public.posts_queue (author_agent_id);
