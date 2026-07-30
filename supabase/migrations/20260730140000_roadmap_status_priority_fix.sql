-- Corrige un écart de schéma production vs code trouvé pendant la Phase 15
-- (ROADMAP.md, 2026-07-30) : la table `roadmap` en production n'a jamais eu
-- 'idea' dans son CHECK de statut, et `priority` y est un INTEGER (défaut 0)
-- alors que tout le code applicatif (RoadmapCreate/RoadmapUpdate dans
-- api/schemas.py, agents/pm_agent.py, le composant /roadmap) envoie et
-- valide toujours un label texte ("critical"/"high"/"medium"/"low"). Résultat
-- constaté : POST /roadmap échouait à 100% dès qu'un statut ou une priorité
-- était fourni — jamais remarqué faute d'item roadmap existant (0 lignes
-- avant cette migration, vérifié). Voir BUGS.md BUG-007.

ALTER TABLE public.roadmap DROP CONSTRAINT IF EXISTS roadmap_status_check;
ALTER TABLE public.roadmap ADD CONSTRAINT roadmap_status_check
  CHECK (status IN ('idea', 'planned', 'in_progress', 'done'));

ALTER TABLE public.roadmap ALTER COLUMN priority DROP DEFAULT;
ALTER TABLE public.roadmap ALTER COLUMN priority TYPE TEXT USING (
  CASE
    WHEN priority::text ~ '^[0-9]+$' THEN
      CASE
        WHEN priority::int >= 8 THEN 'critical'
        WHEN priority::int >= 6 THEN 'high'
        WHEN priority::int >= 3 THEN 'medium'
        ELSE 'low'
      END
    ELSE priority::text
  END
);
ALTER TABLE public.roadmap ALTER COLUMN priority SET DEFAULT 'medium';
ALTER TABLE public.roadmap DROP CONSTRAINT IF EXISTS roadmap_priority_check;
ALTER TABLE public.roadmap ADD CONSTRAINT roadmap_priority_check
  CHECK (priority IN ('critical', 'high', 'medium', 'low'));
