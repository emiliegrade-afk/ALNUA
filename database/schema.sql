-- ALNUA Hub — Supabase schema
-- Run this in the Supabase SQL Editor or via migration.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------------
-- Helper: auto-update updated_at
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- 1. projects
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.projects (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  branch      TEXT NOT NULL CHECK (branch IN ('app', 'gaming', 'robotics', 'other')),
  description TEXT NOT NULL DEFAULT '',
  status      TEXT NOT NULL DEFAULT 'dev'
                CHECK (status IN ('active', 'beta', 'dev', 'paused')),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_projects_branch ON public.projects (branch);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects (status);

-- ---------------------------------------------------------------------------
-- 2. dev_log
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.dev_log (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id       UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  date             DATE NOT NULL DEFAULT CURRENT_DATE,
  content          TEXT NOT NULL,
  used_for_content BOOLEAN NOT NULL DEFAULT false,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dev_log_project_id ON public.dev_log (project_id);
CREATE INDEX IF NOT EXISTS idx_dev_log_date ON public.dev_log (date DESC);
CREATE INDEX IF NOT EXISTS idx_dev_log_unused_content
  ON public.dev_log (project_id, used_for_content)
  WHERE used_for_content = false;

-- ---------------------------------------------------------------------------
-- 3. tickets
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tickets (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id    UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  type          TEXT NOT NULL CHECK (type IN ('bug', 'feature', 'improvement', 'crash', 'reminder')),
  priority      TEXT NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('critical', 'high', 'medium', 'low')),
  title         TEXT NOT NULL,
  description   TEXT NOT NULL DEFAULT '',
  source        TEXT NOT NULL
                CHECK (source IN (
                  'qa_agent', 'sav_bot', 'reviews_bot', 'emilie',
                  'quick_capture', 'beta_tester', 'partnerships_bot'
                )),
  status        TEXT NOT NULL DEFAULT 'open'
                CHECK (status IN ('open', 'in_progress', 'done', 'wont_fix')),
  cursor_prompt TEXT,
  -- Phase 12 (2026-07-30) — fondations données transverses
  assignee_agent_id TEXT,
  story_points  INT CHECK (story_points IS NULL OR story_points BETWEEN 1 AND 21),
  due_date      DATE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tickets_project_id ON public.tickets (project_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON public.tickets (status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON public.tickets (priority);
CREATE INDEX IF NOT EXISTS idx_tickets_assignee ON public.tickets (assignee_agent_id);
CREATE INDEX IF NOT EXISTS idx_tickets_due_date ON public.tickets (due_date);

DROP TRIGGER IF EXISTS trg_tickets_updated_at ON public.tickets;
CREATE TRIGGER trg_tickets_updated_at
  BEFORE UPDATE ON public.tickets
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- 4. roadmap
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.roadmap (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id        UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  title             TEXT NOT NULL,
  description       TEXT NOT NULL DEFAULT '',
  status            TEXT NOT NULL DEFAULT 'planned'
                    CHECK (status IN ('idea', 'planned', 'in_progress', 'done')),
  priority          TEXT NOT NULL DEFAULT 'medium'
                    CHECK (priority IN ('critical', 'high', 'medium', 'low')),
  phase             TEXT,
  due_date          DATE,
  linked_ticket_id  UUID REFERENCES public.tickets (id) ON DELETE SET NULL,
  rnd_dossier_id    UUID REFERENCES public.rnd_dossiers (id) ON DELETE SET NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_roadmap_project_id ON public.roadmap (project_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_status ON public.roadmap (status);
CREATE INDEX IF NOT EXISTS idx_roadmap_due_date
  ON public.roadmap (due_date)
  WHERE due_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_roadmap_linked_ticket_id
  ON public.roadmap (linked_ticket_id)
  WHERE linked_ticket_id IS NOT NULL;

DROP TRIGGER IF EXISTS trg_roadmap_updated_at ON public.roadmap;
CREATE TRIGGER trg_roadmap_updated_at
  BEFORE UPDATE ON public.roadmap
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- NB : cette définition documente le schéma *voulu* depuis le bootstrap ;
-- la table réelle en production en avait dérivé (BUG-007, BUGS.md) — voir
-- supabase/migrations/20260730140000_roadmap_status_priority_fix.sql et
-- 20260730150000_roadmap_missing_columns.sql pour le rattrapage réellement
-- appliqué (2026-07-30).

-- ---------------------------------------------------------------------------
-- 4b. project_modules — Phase 14 (ROADMAP.md, 2026-07-30). Ajoutée après le
-- bootstrap initial ; voir supabase/migrations/20260730130000_project_modules.sql
-- pour le DDL réellement appliqué (RLS incluse).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.project_modules (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id       UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  name             TEXT NOT NULL,
  status           TEXT NOT NULL DEFAULT 'a_faire'
                   CHECK (status IN ('a_faire', 'en_developpement', 'en_test', 'termine')),
  progress         INT NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
  features_done    INT NOT NULL DEFAULT 0 CHECK (features_done >= 0),
  features_total   INT NOT NULL DEFAULT 0 CHECK (features_total >= 0),
  tests_passed_pct INT NOT NULL DEFAULT 0 CHECK (tests_passed_pct BETWEEN 0 AND 100),
  open_bugs        INT NOT NULL DEFAULT 0 CHECK (open_bugs >= 0),
  position         INT NOT NULL DEFAULT 0,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_project_modules_project_id ON public.project_modules (project_id);

-- ---------------------------------------------------------------------------
-- 4c. gaming_builds — Phase 16 (ROADMAP.md, 2026-07-30). Réceptacle de
-- télémétrie de build UE5 ; voir supabase/migrations/20260730160000_gaming_builds.sql
-- et scripts/report_ue5_build.py. Aucun pipeline de build UE5 réel n'existe
-- encore — table prête à recevoir de vraies données le jour où il existera.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.gaming_builds (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id     UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  branch         TEXT NOT NULL,
  build_number   TEXT NOT NULL,
  game_version   TEXT,
  engine_version TEXT NOT NULL DEFAULT '5.8',
  status         TEXT NOT NULL DEFAULT 'success'
                 CHECK (status IN ('success', 'failed', 'running')),
  fps_avg        NUMERIC,
  crashes        INT CHECK (crashes IS NULL OR crashes >= 0),
  draw_calls     INT CHECK (draw_calls IS NULL OR draw_calls >= 0),
  commit_sha     TEXT,
  notes          TEXT NOT NULL DEFAULT '',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gaming_builds_project_id ON public.gaming_builds (project_id);
CREATE INDEX IF NOT EXISTS idx_gaming_builds_created_at ON public.gaming_builds (created_at DESC);

-- ---------------------------------------------------------------------------
-- 4d. gaming_assets — Phase 17 (ROADMAP.md, 2026-07-30). Inventaire réel
-- d'assets, synchronisé via scripts/sync_ue5_assets.py depuis un dossier réel
-- (le projet Wyrdheim est sur un disque séparé, non accessible ici) ; voir
-- supabase/migrations/20260730170000_gaming_assets.sql.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.gaming_assets (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id   UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  category     TEXT NOT NULL,
  name         TEXT NOT NULL,
  asset_type   TEXT NOT NULL,
  file_path    TEXT NOT NULL,
  size_bytes   BIGINT NOT NULL DEFAULT 0 CHECK (size_bytes >= 0),
  modified_at  TIMESTAMPTZ,
  synced_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gaming_assets_project_id ON public.gaming_assets (project_id);
CREATE INDEX IF NOT EXISTS idx_gaming_assets_category ON public.gaming_assets (project_id, category);

-- ---------------------------------------------------------------------------
-- 4e. robo_builds / robo_lab_tests / robo_telemetry — Phases 19-20
-- (ROADMAP.md, 2026-07-30). Réceptacles réels pour le suivi hardware d'Eve ;
-- voir supabase/migrations/20260730180000_robo_builds_lab_telemetry.sql et
-- scripts/report_robo_build.py, report_lab_test.py, report_robo_telemetry.py.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.robo_builds (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id        UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  branch            TEXT NOT NULL,
  stage             TEXT NOT NULL DEFAULT 'Prototype'
                    CHECK (stage IN ('Prototype', 'V2', 'V3', 'Certification', 'Production')),
  version           TEXT,
  pcb_revision      TEXT,
  firmware_version  TEXT,
  tests_passed_pct  INT CHECK (tests_passed_pct IS NULL OR tests_passed_pct BETWEEN 0 AND 100),
  open_issues       INT CHECK (open_issues IS NULL OR open_issues >= 0),
  notes             TEXT NOT NULL DEFAULT '',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_robo_builds_project_id ON public.robo_builds (project_id);
CREATE INDEX IF NOT EXISTS idx_robo_builds_created_at ON public.robo_builds (created_at DESC);

CREATE TABLE IF NOT EXISTS public.robo_lab_tests (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id     UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  category       TEXT NOT NULL,
  name           TEXT NOT NULL,
  status         TEXT NOT NULL DEFAULT 'in_progress'
                 CHECK (status IN ('pass', 'fail', 'in_progress')),
  measured_value TEXT,
  notes          TEXT NOT NULL DEFAULT '',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_robo_lab_tests_project_id ON public.robo_lab_tests (project_id);
CREATE INDEX IF NOT EXISTS idx_robo_lab_tests_created_at ON public.robo_lab_tests (created_at DESC);

CREATE TABLE IF NOT EXISTS public.robo_telemetry (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id       UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  power_w          NUMERIC,
  temperature_c    NUMERIC,
  cpu_pct          INT CHECK (cpu_pct IS NULL OR cpu_pct BETWEEN 0 AND 100),
  battery_pct      INT CHECK (battery_pct IS NULL OR battery_pct BETWEEN 0 AND 100),
  charge_cycles    INT CHECK (charge_cycles IS NULL OR charge_cycles >= 0),
  autonomy_hours   NUMERIC,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_robo_telemetry_project_id ON public.robo_telemetry (project_id);
CREATE INDEX IF NOT EXISTS idx_robo_telemetry_created_at ON public.robo_telemetry (created_at DESC);

-- ---------------------------------------------------------------------------
-- 4f. rnd_ideas / rnd_dossiers / rnd_dossier_sections / rnd_dossier_assets /
-- rnd_dossier_events / rnd_committee_sessions / rnd_committee_messages /
-- rnd_social_calendar / rnd_product_pages — R&D Dossier Hub (2026-06-13,
-- jamais mirroré ici avant Phase 22, ROADMAP.md, 2026-07-31). Définition
-- consolidée (base + colonnes ajoutées ensuite) ; voir
-- supabase/migrations/20260613120000_rnd_dossiers.sql (DDL + RLS anon/
-- authenticated d'origine) et 20260613150000_rnd_ceo_phase6.sql
-- (ceo_package_json/committee_report_md/dispatch_json/dispatch_status) et
-- 20260617120000_rnd_hub_branch.sql (branche 'hub' ajoutée au CHECK).
-- Colonnes rnd_dossier_id ajoutées par la même migration sur roadmap/
-- posts_queue/brainstorm_summaries (mirrorées ci-dessus/dessous) et sur
-- lore_entries/bom_eve — ces deux dernières tables ne sont pas encore
-- mirrorées dans ce fichier (gap préexistant, hors périmètre de cette phase).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rnd_ideas (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  legacy_id         TEXT UNIQUE,
  title             TEXT NOT NULL,
  description       TEXT NOT NULL DEFAULT '',
  domain            TEXT,
  effort            TEXT,
  why_now           TEXT,
  source            TEXT NOT NULL DEFAULT 'rnd_agent',
  status            TEXT NOT NULL DEFAULT 'pending_evaluation',
  score             INT,
  market_score      INT,
  feasibility_score INT,
  vision_score      INT,
  agent_verdict     TEXT,
  agent_reasoning   TEXT,
  next_step         TEXT,
  spec_file         TEXT,
  lifecycle_status  TEXT NOT NULL DEFAULT 'raw'
    CHECK (lifecycle_status IN (
      'raw', 'dossier_draft', 'in_committee', 'sections_review',
      'ceo_review', 'approved', 'rejected', 'in_conception', 'shipped', 'archived'
    )),
  project_id        UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  dossier_id        UUID REFERENCES public.rnd_dossiers (id) ON DELETE SET NULL,
  incubator_stage   TEXT NOT NULL DEFAULT 'idee'
    CHECK (incubator_stage IN ('idee', 'prototype', 'validation', 'mvp', 'projet', 'departement')),
  incubator_stage_updated_at TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  evaluated_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_rnd_ideas_legacy_id ON public.rnd_ideas (legacy_id);
CREATE INDEX IF NOT EXISTS idx_rnd_ideas_verdict ON public.rnd_ideas (agent_verdict);
CREATE INDEX IF NOT EXISTS idx_rnd_ideas_lifecycle ON public.rnd_ideas (lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_rnd_ideas_score ON public.rnd_ideas (score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_rnd_ideas_incubator_stage ON public.rnd_ideas (incubator_stage);
-- incubator_stage/incubator_stage_updated_at : Phase 24, ROADMAP.md — voir
-- supabase/migrations/20260731100000_rnd_incubator_stage.sql.

DROP TRIGGER IF EXISTS trg_rnd_ideas_updated_at ON public.rnd_ideas;
CREATE TRIGGER trg_rnd_ideas_updated_at
  BEFORE UPDATE ON public.rnd_ideas
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE IF NOT EXISTS public.rnd_dossiers (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  idea_id             UUID NOT NULL UNIQUE REFERENCES public.rnd_ideas (id) ON DELETE CASCADE,
  slug                TEXT NOT NULL UNIQUE,
  title               TEXT NOT NULL,
  tagline             TEXT,
  domain              TEXT NOT NULL,
  branch              TEXT CHECK (branch IN ('app', 'gaming', 'robotics', 'hub', 'other')),
  status              TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN (
      'draft', 'committee_active', 'partial_validated', 'ready_for_ceo',
      'ceo_approved', 'ceo_rejected', 'in_conception', 'published', 'archived'
    )),
  ceo_status          TEXT NOT NULL DEFAULT 'pending'
    CHECK (ceo_status IN ('pending', 'approved', 'rejected', 'pivot_requested')),
  ceo_note            TEXT,
  ceo_decided_at      TIMESTAMPTZ,
  committee_team      JSONB NOT NULL DEFAULT '[]'::jsonb,
  vision_snapshot     TEXT,
  competitive_context TEXT,
  deck_html_path      TEXT,
  deck_pdf_path       TEXT,
  one_pager_md        TEXT,
  finance_json        JSONB,
  ceo_package_json    JSONB,
  committee_report_md TEXT,
  dispatch_json       JSONB,
  dispatch_status     TEXT NOT NULL DEFAULT 'pending'
    CHECK (dispatch_status IN ('pending', 'ready', 'dispatched')),
  brand_kit_id        UUID REFERENCES public.brand_kits (id) ON DELETE SET NULL,
  project_id          UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  local_path          TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rnd_dossiers_status ON public.rnd_dossiers (status);
CREATE INDEX IF NOT EXISTS idx_rnd_dossiers_slug ON public.rnd_dossiers (slug);
CREATE INDEX IF NOT EXISTS idx_rnd_dossiers_domain ON public.rnd_dossiers (domain);
CREATE INDEX IF NOT EXISTS idx_rnd_dossiers_ceo_status ON public.rnd_dossiers (ceo_status, status);

DROP TRIGGER IF EXISTS trg_rnd_dossiers_updated_at ON public.rnd_dossiers;
CREATE TRIGGER trg_rnd_dossiers_updated_at
  BEFORE UPDATE ON public.rnd_dossiers
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE IF NOT EXISTS public.rnd_dossier_sections (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id      UUID NOT NULL REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  section_key     TEXT NOT NULL,
  title           TEXT NOT NULL,
  content_md      TEXT NOT NULL DEFAULT '',
  content_html    TEXT,
  status          TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'under_review', 'validated', 'needs_revision', 'skipped')),
  validated_by    TEXT,
  validated_at    TIMESTAMPTZ,
  revision_note   TEXT,
  sort_order      INT NOT NULL DEFAULT 0,
  hero_asset_id   UUID REFERENCES public.rnd_dossier_assets (id) ON DELETE SET NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (dossier_id, section_key)
);

CREATE INDEX IF NOT EXISTS idx_rnd_dossier_sections_dossier
  ON public.rnd_dossier_sections (dossier_id, sort_order);

DROP TRIGGER IF EXISTS trg_rnd_dossier_sections_updated_at ON public.rnd_dossier_sections;
CREATE TRIGGER trg_rnd_dossier_sections_updated_at
  BEFORE UPDATE ON public.rnd_dossier_sections
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE IF NOT EXISTS public.rnd_dossier_assets (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id       UUID NOT NULL REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  section_key      TEXT,
  asset_type       TEXT NOT NULL
    CHECK (asset_type IN (
      'hero', 'illustration', 'mockup', 'diagram', 'chart',
      'moodboard', 'social_teaser', 'logo_concept'
    )),
  file_path        TEXT NOT NULL,
  public_url       TEXT,
  image_prompt     TEXT,
  generation_model TEXT,
  width            INT,
  height           INT,
  metadata         JSONB,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rnd_dossier_assets_dossier
  ON public.rnd_dossier_assets (dossier_id);

CREATE TABLE IF NOT EXISTS public.rnd_dossier_events (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id  UUID NOT NULL REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  event_type  TEXT NOT NULL,
  actor       TEXT NOT NULL,
  payload     JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rnd_dossier_events_dossier
  ON public.rnd_dossier_events (dossier_id, created_at DESC);

-- dossier_id nullable + session_kind/idea_id/structured_input/topic : Phase 25
-- (ROADMAP.md, 2026-07-31) — voir supabase/migrations/20260731110000_rnd_council_votes.sql.
-- session_kind='dossier' par défaut = rétrocompatible avec le comité dossier
-- ci-dessous ; 'strategic'/'evaluation' n'ont pas de dossier (Conseil).
CREATE TABLE IF NOT EXISTS public.rnd_committee_sessions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id        UUID REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  session_id        TEXT NOT NULL UNIQUE,
  title             TEXT,
  mode              TEXT NOT NULL DEFAULT 'free'
    CHECK (mode IN ('free', 'round_robin', 'targeted')),
  active_section    TEXT,
  team              JSONB NOT NULL DEFAULT '[]'::jsonb,
  status            TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'paused', 'closed')),
  session_kind      TEXT NOT NULL DEFAULT 'dossier'
    CHECK (session_kind IN ('dossier', 'strategic', 'evaluation')),
  idea_id           UUID REFERENCES public.rnd_ideas (id) ON DELETE SET NULL,
  structured_input  JSONB,
  topic             TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at         TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_rnd_committee_sessions_dossier
  ON public.rnd_committee_sessions (dossier_id);

-- dossier_id nullable : Phase 25, même migration que ci-dessus.
CREATE TABLE IF NOT EXISTS public.rnd_committee_messages (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id   TEXT NOT NULL REFERENCES public.rnd_committee_sessions (session_id) ON DELETE CASCADE,
  dossier_id   UUID REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  speaker      TEXT NOT NULL,
  role         TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content      TEXT NOT NULL,
  section_key  TEXT,
  metadata     JSONB,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rnd_committee_messages_session
  ON public.rnd_committee_messages (session_id, created_at);

-- ---------------------------------------------------------------------------
-- rnd_committee_votes — Phase 25 (ROADMAP.md, 2026-07-31). Verdict individuel
-- par membre du Conseil, live (dernière ligne par agent_id) + final
-- (is_final=true) — sert à la fois les jauges live et la bannière
-- "Décision Collective". Voir agents/rnd_council_agent.py.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rnd_committee_votes (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id     TEXT NOT NULL REFERENCES public.rnd_committee_sessions (session_id) ON DELETE CASCADE,
  agent_id       TEXT NOT NULL,
  agent_name     TEXT NOT NULL,
  verdict        TEXT NOT NULL CHECK (verdict IN ('GO', 'MAYBE', 'NO')),
  confidence_pct SMALLINT NOT NULL CHECK (confidence_pct BETWEEN 0 AND 100),
  axis_scores    JSONB,
  stance_text    TEXT NOT NULL,
  round_index    INT NOT NULL DEFAULT 0,
  is_final       BOOLEAN NOT NULL DEFAULT false,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rnd_committee_votes_session
  ON public.rnd_committee_votes (session_id, agent_id, round_index DESC);

CREATE TABLE IF NOT EXISTS public.rnd_social_calendar (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id   UUID NOT NULL REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  phase        TEXT NOT NULL
    CHECK (phase IN ('internal', 'behind_scenes', 'teaser', 'pre_launch', 'launch', 'post_launch')),
  milestone    TEXT,
  planned_at   TIMESTAMPTZ,
  post_id      UUID REFERENCES public.posts_queue (id) ON DELETE SET NULL,
  status       TEXT NOT NULL DEFAULT 'planned'
    CHECK (status IN ('planned', 'generated', 'approved', 'published', 'cancelled')),
  notes        TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.rnd_product_pages (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id       UUID NOT NULL UNIQUE REFERENCES public.rnd_dossiers (id) ON DELETE CASCADE,
  project_id       UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  slug             TEXT NOT NULL UNIQUE,
  title            TEXT NOT NULL,
  tagline          TEXT,
  description_html TEXT,
  hero_asset_id    UUID REFERENCES public.rnd_dossier_assets (id) ON DELETE SET NULL,
  features         JSONB NOT NULL DEFAULT '[]'::jsonb,
  pricing_model    TEXT,
  faq              JSONB NOT NULL DEFAULT '[]'::jsonb,
  seo_title        TEXT,
  seo_description  TEXT,
  waitlist_enabled BOOLEAN NOT NULL DEFAULT false,
  published        BOOLEAN NOT NULL DEFAULT false,
  published_at     TIMESTAMPTZ,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS trg_rnd_product_pages_updated_at ON public.rnd_product_pages;
CREATE TRIGGER trg_rnd_product_pages_updated_at
  BEFORE UPDATE ON public.rnd_product_pages
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- RLS (anon + authenticated, même pattern que brainstorm_summaries) posée
-- directement dans 20260613120000_rnd_dossiers.sql sur les 9 tables
-- ci-dessus — non reproduite ici (cette section documente le DDL, pas les
-- policies ; voir la boucle RLS en fin de fichier pour le pattern standard
-- des tables plus anciennes).

-- ---------------------------------------------------------------------------
-- 5. feedback
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.feedback (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  source     TEXT NOT NULL
             CHECK (source IN (
               'beta_portal', 'discord', 'app_store', 'google_play', 'reddit', 'sav'
             )),
  author     TEXT,
  content    TEXT NOT NULL,
  sentiment  TEXT NOT NULL DEFAULT 'neutral'
             CHECK (sentiment IN ('positive', 'negative', 'neutral', 'mixed')),
  rating     INT CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5)),
  status     TEXT NOT NULL DEFAULT 'new'
             CHECK (status IN ('new', 'processed', 'ticket_created')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_project_id ON public.feedback (project_id);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON public.feedback (status);
CREATE INDEX IF NOT EXISTS idx_feedback_sentiment ON public.feedback (sentiment);

-- ---------------------------------------------------------------------------
-- 6. posts_queue
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.posts_queue (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id        UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  sector            TEXT
                    CHECK (sector IS NULL OR sector IN ('app', 'gaming', 'robo', 'company')),
  author_agent_id   TEXT,
  platform          TEXT NOT NULL
                    CHECK (platform IN (
                      'instagram', 'tiktok', 'x', 'youtube', 'linkedin', 'website_blog', 'discord'
                    )),
  content_type      TEXT NOT NULL
                    CHECK (content_type IN (
                      'announcement', 'teaser', 'tutorial', 'behind_scenes', 'short_video', 'lore'
                    )),
  text_content      TEXT NOT NULL,
  layout            JSONB,
  image_prompt      TEXT,
  media_urls        TEXT[] NOT NULL DEFAULT '{}',
  video_script      TEXT,
  hashtags          TEXT[] NOT NULL DEFAULT '{}',
  channel           TEXT,
  scheduled_at      TIMESTAMPTZ NOT NULL,
  published_at      TIMESTAMPTZ,
  status            TEXT NOT NULL DEFAULT 'draft'
                    CHECK (status IN (
                      'draft', 'pending_approval', 'approved', 'published', 'failed', 'rejected'
                    )),
  rnd_dossier_id          UUID REFERENCES public.rnd_dossiers (id) ON DELETE SET NULL,
  rnd_social_calendar_id  UUID REFERENCES public.rnd_social_calendar (id) ON DELETE SET NULL,
  image_asset_path        TEXT,
  -- Stats de performance réelle (Phase 37) — saisie manuelle après publication
  -- (copiée depuis les insights natifs Instagram/TikTok/etc.), NULL tant que
  -- personne ne l'a renseignée, jamais 0 par défaut.
  reach                   INTEGER CHECK (reach IS NULL OR reach >= 0),
  engagement_count        INTEGER CHECK (engagement_count IS NULL OR engagement_count >= 0),
  stats_updated_at        TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- content_type inclut 'lore' depuis la migration 20260731120000_marketing_campaigns.sql
-- (bug corrigé : le type TS PostContentType le déclarait depuis la Phase 26,
-- jamais reflété ici — un POST /posts avec content_type "lore" échouait).
CREATE INDEX IF NOT EXISTS idx_posts_queue_project_id ON public.posts_queue (project_id);
CREATE INDEX IF NOT EXISTS idx_posts_queue_status ON public.posts_queue (status);
CREATE INDEX IF NOT EXISTS idx_posts_queue_scheduled_at ON public.posts_queue (scheduled_at);
CREATE INDEX IF NOT EXISTS idx_posts_queue_sector_scheduled ON public.posts_queue (sector, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_posts_queue_author_agent ON public.posts_queue (author_agent_id);

-- ---------------------------------------------------------------------------
-- 7. analytics
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.analytics (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id   UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  date         DATE NOT NULL,
  metric_name  TEXT NOT NULL
               CHECK (metric_name IN (
                 'downloads', 'active_users', 'subscriptions', 'mrr', 'churn', 'web_visitors'
               )),
  value        NUMERIC NOT NULL,
  source       TEXT NOT NULL
               CHECK (source IN (
                 'app_store', 'google_play', 'stripe', 'revenuecat', 'plausible'
               )),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, date, metric_name, source)
);

CREATE INDEX IF NOT EXISTS idx_analytics_project_date
  ON public.analytics (project_id, date DESC);

-- ---------------------------------------------------------------------------
-- 8. transactions (finance)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.transactions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date          DATE NOT NULL DEFAULT CURRENT_DATE,
  type          TEXT NOT NULL CHECK (type IN ('income', 'expense')),
  amount        NUMERIC(10, 2) NOT NULL,
  currency      TEXT NOT NULL DEFAULT 'EUR',
  category      TEXT NOT NULL,
  project_id    UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  description   TEXT,
  is_recurring  BOOLEAN NOT NULL DEFAULT false,
  recurrence    TEXT CHECK (recurrence IS NULL OR recurrence IN ('monthly', 'annual', 'one_time')),
  receipt_url   TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT transactions_category_check CHECK (
    (type = 'expense' AND category IN (
      'saas_tools', 'hardware', 'freelance', 'marketing',
      'legal', 'hosting', 'formation', 'autre'
    ))
    OR (type = 'income' AND category IN (
      'app_revenue', 'grant', 'consulting', 'investment', 'autre'
    ))
  )
);

CREATE INDEX IF NOT EXISTS idx_transactions_project_id ON public.transactions (project_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON public.transactions (date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON public.transactions (type);
CREATE INDEX IF NOT EXISTS idx_transactions_recurring
  ON public.transactions (is_recurring)
  WHERE is_recurring = true;

-- ---------------------------------------------------------------------------
-- 8b. financial_summaries
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.financial_summaries (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  month           TEXT NOT NULL,
  summary_md      TEXT,
  total_income    NUMERIC(10, 2),
  total_expenses  NUMERIC(10, 2),
  balance         NUMERIC(10, 2),
  by_category     JSONB,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (month)
);

CREATE INDEX IF NOT EXISTS idx_financial_summaries_month
  ON public.financial_summaries (month DESC);

-- ---------------------------------------------------------------------------
-- 8c. campaigns (Phase 33, ROADMAP.md — 20260731120000_marketing_campaigns.sql)
-- Aucune persistance n'existait avant cette phase : skills/skill_ads.py ne
-- retournait que des dict en mémoire. campaign_roi_report (ROI/reach/
-- impressions) reste un stub explicite côté backend, jamais exposé comme un
-- chiffre réel — seul "dépensé" (somme des transactions.campaign_id liées)
-- est réel.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.campaigns (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id            UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  name                  TEXT NOT NULL,
  objective             TEXT NOT NULL
                        CHECK (objective IN ('awareness', 'traffic', 'conversions', 'engagement', 'video_views')),
  platform              TEXT NOT NULL CHECK (platform IN ('meta', 'google', 'tiktok')),
  status                TEXT NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft', 'active', 'paused', 'completed')),
  budget_allocated_usd  NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (budget_allocated_usd >= 0),
  audience              TEXT,
  brief                 TEXT,
  start_date            DATE,
  end_date              DATE,
  created_by_agent_id   TEXT,
  -- Stats de performance réelle (Phase 37, 20260731130000_marketing_performance_tracking.sql)
  -- — saisie manuelle depuis les dashboards natifs des plateformes ad
  -- (Meta/Google/TikTok Ads Manager). NULL tant que rien n'a été saisi —
  -- roi_pct n'est calculé côté API que si spent_usd (réel, transactions
  -- liées) ET revenue_generated_usd (saisi) sont tous les deux disponibles.
  reach                 INTEGER CHECK (reach IS NULL OR reach >= 0),
  engagements           INTEGER CHECK (engagements IS NULL OR engagements >= 0),
  conversions           INTEGER CHECK (conversions IS NULL OR conversions >= 0),
  revenue_generated_usd NUMERIC(10, 2) CHECK (revenue_generated_usd IS NULL OR revenue_generated_usd >= 0),
  stats_updated_at      TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_campaigns_project_id ON public.campaigns (project_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON public.campaigns (status);

CREATE TRIGGER trg_campaigns_updated_at
  BEFORE UPDATE ON public.campaigns
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- transactions.campaign_id (ajouté par la même migration) — rattache une
-- dépense réelle à sa campagne.
ALTER TABLE public.transactions
  ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES public.campaigns (id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_campaign_id ON public.transactions (campaign_id);

-- ---------------------------------------------------------------------------
-- 8d. funnel_snapshots (Phase 37 — 20260731130000_marketing_performance_tracking.sql)
-- Entonnoir de conversion réel : saisie mensuelle par produit (Visiteurs →
-- Intéressés → Engagés → Abonnés → Clients), source = analytics propre à
-- chaque produit (App Store Connect / Play Console / Plausible / GA4 /
-- signups Supabase). `source_note` documente d'où vient le chiffre.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.funnel_snapshots (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id          UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  period_month        DATE NOT NULL,
  visitors            INTEGER NOT NULL DEFAULT 0 CHECK (visitors >= 0),
  interested          INTEGER NOT NULL DEFAULT 0 CHECK (interested >= 0),
  engaged             INTEGER NOT NULL DEFAULT 0 CHECK (engaged >= 0),
  subscribers         INTEGER NOT NULL DEFAULT 0 CHECK (subscribers >= 0),
  customers           INTEGER NOT NULL DEFAULT 0 CHECK (customers >= 0),
  source_note         TEXT,
  entered_by_agent_id TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, period_month)
);

CREATE INDEX IF NOT EXISTS idx_funnel_snapshots_project_id ON public.funnel_snapshots (project_id);
CREATE INDEX IF NOT EXISTS idx_funnel_snapshots_period ON public.funnel_snapshots (period_month);

CREATE TRIGGER trg_funnel_snapshots_updated_at
  BEFORE UPDATE ON public.funnel_snapshots
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- 9. faq
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.faq (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  question   TEXT NOT NULL,
  answer     TEXT NOT NULL,
  tags       TEXT[] NOT NULL DEFAULT '{}',
  active     BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_faq_project_id ON public.faq (project_id);
CREATE INDEX IF NOT EXISTS idx_faq_active ON public.faq (project_id, active) WHERE active = true;

-- ---------------------------------------------------------------------------
-- 10. agent_logs
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.agent_logs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name      TEXT NOT NULL,
  action          TEXT NOT NULL,
  project_id      UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  input_summary   TEXT NOT NULL DEFAULT '',
  output_summary  TEXT NOT NULL DEFAULT '',
  status          TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('success', 'error', 'pending')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_name ON public.agent_logs (agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_logs_created_at ON public.agent_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_logs_project_id ON public.agent_logs (project_id);

-- ---------------------------------------------------------------------------
-- 11. brainstorm_summaries — mémoire cross-sessions brainstorm
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.brainstorm_summaries (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id      UUID REFERENCES public.projects (id) ON DELETE CASCADE,
  session_id      TEXT NOT NULL,
  session_number  INT NOT NULL,
  title           TEXT NOT NULL,
  summary         TEXT NOT NULL,
  key_ideas       TEXT[] NOT NULL DEFAULT '{}',
  decisions       TEXT[] NOT NULL DEFAULT '{}',
  next_steps      TEXT[] NOT NULL DEFAULT '{}',
  open_questions  TEXT[] NOT NULL DEFAULT '{}',
  file_path       TEXT,
  rnd_dossier_id  UUID REFERENCES public.rnd_dossiers (id) ON DELETE SET NULL,
  session_type    TEXT NOT NULL DEFAULT 'brainstorm',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_brainstorm_summaries_project
  ON public.brainstorm_summaries (project_id, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_brainstorm_summaries_session
  ON public.brainstorm_summaries (session_id);

-- ---------------------------------------------------------------------------
-- 12. brand_kits — analyses et assets Brand Design
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.brand_kits (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id        UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  brand_name        TEXT NOT NULL,
  analysis          JSONB NOT NULL,
  assets_path       TEXT NOT NULL DEFAULT '',
  formats_generated TEXT[] NOT NULL DEFAULT '{}',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_brand_kits_project_id
  ON public.brand_kits (project_id);
CREATE INDEX IF NOT EXISTS idx_brand_kits_created_at
  ON public.brand_kits (created_at DESC);

DROP TRIGGER IF EXISTS trg_brand_kits_updated_at ON public.brand_kits;
CREATE TRIGGER trg_brand_kits_updated_at
  BEFORE UPDATE ON public.brand_kits
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- 13. daily_briefings — digest matinal automatique
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.daily_briefings (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date          DATE NOT NULL,
  summary       TEXT NOT NULL,
  raw_data      JSONB,
  has_urgent    BOOLEAN NOT NULL DEFAULT false,
  urgent_count  INT NOT NULL DEFAULT 0,
  pending_count INT NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_daily_briefings_date
  ON public.daily_briefings (date DESC);

-- ---------------------------------------------------------------------------
-- 14. quick_notes — captures rapides (Quick Capture)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.quick_notes (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id  UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  content     TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_quick_notes_project
  ON public.quick_notes (project_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- 15. releases — notes de version App Store / Google Play / CHANGELOG
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.releases (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id       UUID REFERENCES public.projects (id) ON DELETE CASCADE,
  version          TEXT NOT NULL,
  release_date     DATE,
  app_store_notes  TEXT,
  google_play_notes TEXT,
  changelog_md     TEXT,
  dev_log_ids      UUID[],
  status           TEXT NOT NULL DEFAULT 'draft'
                   CHECK (status IN ('draft', 'published')),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_releases_project_id
  ON public.releases (project_id);
CREATE INDEX IF NOT EXISTS idx_releases_created_at
  ON public.releases (created_at DESC);

-- ---------------------------------------------------------------------------
-- 16. beta_testers — programme beta (portail testeuses)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.beta_testers (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id     UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  email          TEXT NOT NULL,
  first_name     TEXT,
  device         TEXT,
  os_version     TEXT,
  app_version    TEXT,
  joined_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  feedback_count INT NOT NULL DEFAULT 0,
  UNIQUE (project_id, email)
);

CREATE INDEX IF NOT EXISTS idx_beta_testers_project
  ON public.beta_testers (project_id);
CREATE INDEX IF NOT EXISTS idx_beta_testers_email
  ON public.beta_testers (email);

-- ---------------------------------------------------------------------------
-- 17. beta_feedback — retours soumis via le portail beta
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.beta_feedback (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tester_id       UUID NOT NULL REFERENCES public.beta_testers (id) ON DELETE CASCADE,
  project_id      UUID NOT NULL REFERENCES public.projects (id) ON DELETE CASCADE,
  type            TEXT CHECK (type IN ('bug', 'suggestion', 'crash', 'ux', 'autre')),
  title           TEXT NOT NULL,
  description     TEXT,
  screenshot_url  TEXT,
  severity        TEXT CHECK (severity IN ('bloquant', 'majeur', 'mineur', 'cosmétique')),
  ticket_id       UUID REFERENCES public.tickets (id) ON DELETE SET NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_beta_feedback_project
  ON public.beta_feedback (project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_beta_feedback_tester
  ON public.beta_feedback (tester_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- 18. waitlist — pré-inscriptions avant lancement
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.waitlist (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id  UUID REFERENCES public.projects (id) ON DELETE CASCADE,
  email       TEXT NOT NULL,
  first_name  TEXT,
  source      TEXT,
  message     TEXT,
  status      TEXT NOT NULL DEFAULT 'waiting'
              CHECK (status IN ('waiting', 'notified', 'converted')),
  notified_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (email, project_id)
);

CREATE INDEX IF NOT EXISTS idx_waitlist_project
  ON public.waitlist (project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_waitlist_status
  ON public.waitlist (status);
CREATE INDEX IF NOT EXISTS idx_waitlist_source
  ON public.waitlist (source);

-- ---------------------------------------------------------------------------
-- partnerships — CRM, demandes, affiliés
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.partners (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type                 TEXT NOT NULL,
  status               TEXT NOT NULL DEFAULT 'prospect',
  direction            TEXT NOT NULL,
  name                 TEXT NOT NULL,
  company              TEXT,
  email                TEXT,
  instagram_url        TEXT,
  tiktok_url           TEXT,
  youtube_url          TEXT,
  website              TEXT,
  audience_size        INT,
  audience_description TEXT,
  project_ids          UUID[],
  notes                TEXT,
  contract_path        TEXT,
  next_followup        DATE,
  last_contact_date    DATE,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_partners_status ON public.partners (status);
CREATE INDEX IF NOT EXISTS idx_partners_type ON public.partners (type);
CREATE INDEX IF NOT EXISTS idx_partners_direction ON public.partners (direction);
CREATE INDEX IF NOT EXISTS idx_partners_next_followup ON public.partners (next_followup);

DROP TRIGGER IF EXISTS trg_partners_updated_at ON public.partners;
CREATE TRIGGER trg_partners_updated_at
  BEFORE UPDATE ON public.partners
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE IF NOT EXISTS public.partner_interactions (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  partner_id UUID NOT NULL REFERENCES public.partners (id) ON DELETE CASCADE,
  date       TIMESTAMPTZ NOT NULL DEFAULT now(),
  type       TEXT,
  note       TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_partner_interactions_partner
  ON public.partner_interactions (partner_id, date DESC);

CREATE TABLE IF NOT EXISTS public.affiliate_links (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  partner_id        UUID NOT NULL REFERENCES public.partners (id) ON DELETE CASCADE,
  project_id        UUID REFERENCES public.projects (id) ON DELETE SET NULL,
  code              TEXT NOT NULL UNIQUE,
  redirect_url      TEXT NOT NULL,
  commission_type   TEXT,
  commission_value  DECIMAL(10, 2),
  clicks            INT NOT NULL DEFAULT 0,
  conversions       INT NOT NULL DEFAULT 0,
  revenue_generated DECIMAL(10, 2) NOT NULL DEFAULT 0,
  active            BOOLEAN NOT NULL DEFAULT true,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_affiliate_links_code ON public.affiliate_links (code);
CREATE INDEX IF NOT EXISTS idx_affiliate_links_partner ON public.affiliate_links (partner_id);

CREATE TABLE IF NOT EXISTS public.affiliate_clicks (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  link_id    UUID NOT NULL REFERENCES public.affiliate_links (id) ON DELETE CASCADE,
  event_type TEXT NOT NULL DEFAULT 'click'
             CHECK (event_type IN ('click', 'conversion')),
  revenue    DECIMAL(10, 2),
  user_agent TEXT,
  referer    TEXT,
  clicked_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_link_date
  ON public.affiliate_clicks (link_id, clicked_at DESC);

CREATE TABLE IF NOT EXISTS public.partnership_requests (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name             TEXT NOT NULL,
  email            TEXT NOT NULL,
  type             TEXT,
  message          TEXT,
  instagram_url    TEXT,
  tiktok_url       TEXT,
  website          TEXT,
  audience_size    TEXT,
  project_interest TEXT,
  status           TEXT NOT NULL DEFAULT 'new',
  partner_id       UUID REFERENCES public.partners (id) ON DELETE SET NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_partnership_requests_status
  ON public.partnership_requests (status, created_at DESC);

-- Migration : autoriser la branche « other » sur une base existante
ALTER TABLE public.projects DROP CONSTRAINT IF EXISTS projects_branch_check;
ALTER TABLE public.projects ADD CONSTRAINT projects_branch_check
  CHECK (branch IN ('app', 'gaming', 'robotics', 'other'));

-- ---------------------------------------------------------------------------
-- Row Level Security (service role bypasses RLS; policies for authenticated)
-- ---------------------------------------------------------------------------
ALTER TABLE public.projects      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dev_log       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tickets       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.roadmap       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedback      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posts_queue   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analytics     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.faq           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_logs           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brainstorm_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brand_kits            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_briefings       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quick_notes           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.releases              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.beta_testers          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.beta_feedback         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.waitlist              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.partners              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.partner_interactions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.affiliate_links       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.affiliate_clicks      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.financial_summaries     ENABLE ROW LEVEL SECURITY;

-- Authenticated users (Emilie) get full access via backend JWT
DO $$
DECLARE
  tbl TEXT;
BEGIN
  FOREACH tbl IN ARRAY ARRAY[
    'projects', 'dev_log', 'tickets', 'roadmap', 'feedback',
    'posts_queue', 'analytics', 'transactions', 'faq', 'agent_logs',
    'brainstorm_summaries', 'brand_kits', 'daily_briefings', 'quick_notes',
    'releases', 'beta_testers', 'beta_feedback', 'waitlist',
    'partners', 'partner_interactions', 'affiliate_links',
    'affiliate_clicks', 'partnership_requests', 'financial_summaries'
  ] LOOP
    EXECUTE format(
      'CREATE POLICY "authenticated_full_access" ON public.%I
       FOR ALL TO authenticated USING (true) WITH CHECK (true)',
      tbl
    );
  END LOOP;
END $$;

-- ---------------------------------------------------------------------------
-- Seed: ALNUA projects
-- ---------------------------------------------------------------------------
INSERT INTO public.projects (name, branch, description, status)
SELECT v.name, v.branch, v.description, v.status
FROM (VALUES
  ('Naïa', 'app', 'Application bien-être — méditation, journal, routines.', 'beta'),
  ('Wyrdheim Online', 'gaming', 'MMORPG fantasy nordique — monde ouvert, guildes, raids.', 'dev'),
  ('Eve', 'robotics', 'Robot compagnon domestique — Eve, premier produit robotique ALNUA.', 'dev')
) AS v(name, branch, description, status)
WHERE NOT EXISTS (
  SELECT 1 FROM public.projects p WHERE p.name = v.name
);
