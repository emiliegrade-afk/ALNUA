# Documentation Audit Log — ALNUA Hub

Historique des audits de gouvernance effectués.

---

## Audit 001 — Bootstrap gouvernance + audit sécurité/qualité

- **Date :** 2026-07-25
- **Scope :** ALNUA_HUB était le seul des 4 projets de `C:\Dev` (`NAÏA`, `NUAWAY`,
  `RESONANCE`, `ALUNA_HUB`) sans couche de gouvernance (`ARCHITECTURE.md`,
  `ROADMAP.md`, `DECISIONS.md`, `BUGS.md`, `CHANGELOG.md`, `IMPLEMENTATION_STATUS.md`,
  `TESTING.md`, `DOC_AUDIT.md`). Bootstrap complet des 8 fichiers + audit sécurité et
  audit qualité de code menés en parallèle par deux agents dédiés, sur demande
  explicite ("tout ce qui est security, gouvernance et tout le reste").
- **Méthode :** reconstitution rétroactive depuis `git log` (68 commits, historique
  depuis 2026-06-11), `CLAUDE.md`, `ruff.toml`, `.github/workflows/ci.yml`, les
  fichiers `SPEC_*.md`, et lecture directe du code (routers, agents, services). Pas
  de contenu inventé — tout ce qui n'était pas vérifiable a été marqué explicitement
  comme non tranché plutôt que deviné (voir DEC-009, SEC-002, BUG-003 dans
  `DECISIONS.md`/`BUGS.md`).
- **Audit sécurité — findings :**
  - 🔴 1 critique (SEC-001, injection shell sur `/ide/run`) — **corrigé**
  - 🟠 2 hautes (SEC-002 mode dev ouvert par défaut, SEC-003 RCE SSH Pi qui en dépend)
    — **laissées ouvertes**, décision produit/déploiement à trancher avec Emilie
  - 🟡 3 moyennes (SEC-004/005/006, sanitization manquante sur `/sav/ask`,
    `/agents/brainstorm*`, `trend_monitor`) — **corrigées**
  - ✅ Vérifié sans anomalie : secrets en dur, `.env` commité, injection SQL, CORS,
    path traversal, logs, contrôle d'accès `/mcp`
- **Audit qualité de code — findings :**
  - ruff : 0 erreur avant et après corrections
  - tests : 354 passed / 6 skipped (skips justifiés par dépendances d'environnement
    absentes — Hermes local, disque D, clé Composio) avant et après corrections
  - 2 violations de la règle `AgentBase.__init__` (`rnd_agent.py`, `rnd_social_agent.py`)
    — **corrigées** (BUG-001)
  - Montage routers, imports `route_common`, `agent_scores.json` non tracké,
    enregistrement `AGENT_PERSONAS` : conformes, aucune anomalie
  - Fichiers >300 lignes (15 fichiers, jusqu'à 1475 lignes) : dette pré-existante,
    non traitée (BUG-004) — refactor hors périmètre d'un audit sécurité/gouvernance
- **Trouvaille hors périmètre initial :** `skills/skill_nwiro.py` (intégration
  Unreal Engine 5, référencée par 3 agents) contredit la règle invariante "Pas d'UE5"
  de `CLAUDE.md`. Ni supprimé ni "gardé" par défaut — documenté comme décision
  ouverte (`DECISIONS.md` DEC-009) précisément parce que les deux lectures (règle
  obsolète vs. code à corriger) sont plausibles depuis le code seul.
- **Findings corrected :** SEC-001, SEC-004, SEC-005, SEC-006, BUG-001 (voir `BUGS.md`
  section "Corrigés"). Tests + ruff vérifiés verts après chaque correction, suite
  complète revérifiée à la fin.
- **Findings deferred :** SEC-002, SEC-003, DEC-009, BUG-002, BUG-003, BUG-004,
  BUG-005 (voir `BUGS.md` section "Ouverts") — tous nécessitent soit une décision
  produit (Nwiro/UE5), soit une décision de déploiement/sécurité qui change un
  comportement documenté (mode dev ouvert), soit un refactor de taille non demandé
  (fichiers volumineux) : volontairement non résolus en autonome.
- **Next audit planned :** pas de date fixée — à relancer après la décision SEC-002 /
  DEC-009, ou au prochain sprint significatif, pour garder ce cycle vivant plutôt que
  de le laisser retomber en retard comme avant ce bootstrap.
