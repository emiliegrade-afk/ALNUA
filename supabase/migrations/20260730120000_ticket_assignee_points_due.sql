-- Phase 12 (ROADMAP.md) — fondations données transverses : assigné, points,
-- échéance sur les tickets. Remplace les placeholders dérivés par hash dans
-- les onglets Missions/Backlog (app-v2/gaming-v2/robo-v2) par de vrais champs.

ALTER TABLE public.tickets
  ADD COLUMN IF NOT EXISTS assignee_agent_id TEXT,
  ADD COLUMN IF NOT EXISTS story_points INT,
  ADD COLUMN IF NOT EXISTS due_date DATE;

ALTER TABLE public.tickets
  DROP CONSTRAINT IF EXISTS tickets_story_points_check;
ALTER TABLE public.tickets
  ADD CONSTRAINT tickets_story_points_check
  CHECK (story_points IS NULL OR story_points BETWEEN 1 AND 21);

CREATE INDEX IF NOT EXISTS idx_tickets_assignee ON public.tickets (assignee_agent_id);
CREATE INDEX IF NOT EXISTS idx_tickets_due_date ON public.tickets (due_date);
