-- Phase 9 : Workspace disque R&D — ajoute workspace_path sur projects + rnd_dossiers

-- projects : chemin disque du workspace pôles
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS workspace_path TEXT;

-- rnd_dossiers : chemin disque + statut validation livrables
ALTER TABLE rnd_dossiers
    ADD COLUMN IF NOT EXISTS workspace_path TEXT,
    ADD COLUMN IF NOT EXISTS workspace_validation JSONB DEFAULT '{}'::jsonb;

-- Index pour retrouver rapidement les projets avec workspace
CREATE INDEX IF NOT EXISTS idx_projects_workspace_path
    ON projects (workspace_path)
    WHERE workspace_path IS NOT NULL;

COMMENT ON COLUMN projects.workspace_path IS
    'Chemin absolu du workspace disque (ALNUA_WORKSPACE/{slug}) — rempli au dispatch CEO';

COMMENT ON COLUMN rnd_dossiers.workspace_path IS
    'Chemin absolu du workspace disque du dossier R&D — rempli au dispatch CEO';

COMMENT ON COLUMN rnd_dossiers.workspace_validation IS
    'JSON {success, missing_files, completed_at} — résultat validation livrables Phase 9';
