-- R&D + projects: add hub branch for internal ALNUA platform work

ALTER TABLE rnd_dossiers DROP CONSTRAINT IF EXISTS rnd_dossiers_branch_check;
ALTER TABLE rnd_dossiers ADD CONSTRAINT rnd_dossiers_branch_check
  CHECK (branch IN ('app', 'gaming', 'robotics', 'hub', 'other'));

ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_branch_check;
ALTER TABLE projects ADD CONSTRAINT projects_branch_check
  CHECK (branch IN ('app', 'gaming', 'robotics', 'hub', 'other'));
