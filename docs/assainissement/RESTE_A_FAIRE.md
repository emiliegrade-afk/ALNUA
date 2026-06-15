# Reste à faire — post assainissement

État après corrections finales (juin 2026).

---

## Corrigé depuis la première version

| Item | Statut |
|------|--------|
| Proxy Next bloquait sans `HUB_API_KEY` | **Corrigé** — `web/src/app/api/hub/[...path]/route.ts` transmet sans header si clé absente |
| `docs/API_ROUTES.md` ligne finances/rnd | **Corrigé** — plus d’aliases sur `rnd.py` |
| Clé Hub manquante | **Déjà configurée** — voir `CONFIGURATION_CLES.md` |

---

## Dette structurelle reportée (phase 4)

| Item | Raison du report |
|------|------------------|
| Split `api/routers/releases.py` (god router) | Refactor large |
| Allègement `api/route_common.py` (wildcard imports) | Impact cold-start tous routers |
| Deprecation routes briefing dans `advanced_services.py` | Clients MCP/n8n à migrer d’abord |

---

## Follow-ups optionnels

| Item | Priorité |
|------|----------|
| Migration rows BYOK XOR → Fernet v2 en base CreatorFlow | Basse (lecture legacy OK) |
| Retirer `NEXT_PUBLIC_HUB_API_KEY` du `.env` racine si plus utilisé côté browser | Hygiène secrets |

---

## Definition of Done globale

- [x] `pytest tests/` — 0 failed
- [x] `web`: `tsc` + `lint` — 0 error
- [x] Routes beta admin protégées
- [x] Webhooks signés en prod
- [x] Proxy Next sans boucle + dev open mode bout-en-bout
- [x] OpenRoom / Lobby erreurs visibles
- [x] `API_ROUTES.md` à jour
- [x] Personas alignés
