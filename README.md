# ALNUA Hub

Backend Python + dashboard Next.js pour le système d'agents IA d'**ALNUA** — société
solo d'Emilie, couvrant 3 branches :

| Branche | Projet | Description |
|---------|--------|-------------|
| App | Naïa | Application bien-être |
| Gaming | Wyrdheim Online | MMORPG fantasy nordique |
| Robotique | Eve | Robot compagnon domestique |

**49** personas LLM, frontend dans `web/` (lobby + bureaux `*-v2`).
Détail code : `CLAUDE.md`. **Bible docs** : [`docs/README.md`](docs/README.md).

## Architecture

```
agents/     → Agents IA (49 personas — COO, PM, QA, Content, R&D, Gaming, Robo…)
bots/       → Bots automatisés (Discord, Telegram, Publisher, Reviews, Analytics, SAV, Watchdog)
database/   → Client Supabase + schéma SQL
api/        → API REST FastAPI (routers + gdd conditionnel)
config/     → Configuration pydantic-settings + personas / specs
services/   → Logique métier (compétition, coûts, R&D, workflows…)
web/        → Dashboard Next.js 16 (lobby, départements, Marketing/Finance/R&D v2)
docs/       → Bible / classeur (specs, guides, archives) — voir docs/README.md
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # puis remplir les variables
```

`HUB_API_KEY` est **obligatoire dans tous les environnements**, y compris en local —
l'API refuse de démarrer sans elle (plus de mode dev ouvert, voir `DECISIONS.md` /
`BUGS.md` SEC-002). Génère-en une avec
`python -c "import secrets; print(secrets.token_urlsafe(32))"` et colle-la dans
`.env`, puis passe-la dans le header `X-Hub-Key` de chaque requête.

Ne commite jamais `.venv/` ni `.pytest_cache/` — déjà listés dans `.gitignore`.

Frontend :

```bash
cd web
npm install
npm run dev                   # http://localhost:3000
```

## Base de données

1. Créer un projet Supabase
2. Exécuter `database/schema.sql` dans le SQL Editor
3. Renseigner `SUPABASE_URL` et `SUPABASE_KEY` dans `.env`

## Lancer l'API

```bash
python -m api.main
# ou
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Documentation interactive : http://localhost:8000/docs

## Lancer le bot Discord

```bash
python -m bots.discord_bot
```

Commandes disponibles (préfixe `!alnua `) :

- `briefing` — Briefing COO du jour
- `projects` — Liste des projets
- `triage <project_id>` — Triage PM
- `qa <project_id>` — Analyse QA des feedbacks
- `content <project_id>` — Génération de posts depuis dev logs
- `brainstorm <project_id> <sujet>` — Session brainstorming
- `spec <ticket_id>` — Prompt Cursor pour un ticket

## Lancer le bot Telegram

1. Créer un bot via [@BotFather](https://t.me/BotFather) et copier le token
2. Ajouter `TELEGRAM_BOT_TOKEN=<ton_token>` dans `.env`
3. Activer le venv et installer les deps si besoin :

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

### Mode dev (polling — recommandé en local)

```bash
python -m bots.telegram_bot
```

Envoie un message texte au bot sur Telegram : le COO ALNUA le traite et répond dans le même chat.

> **Une seule instance à la fois** — si tu vois `409 Conflict`, arrête les autres processus `bots.telegram_bot` (Ctrl+C ou Gestionnaire des tâches) avant de relancer.

> Ne pas lancer l'API en mode webhook en parallèle du polling — Telegram n'accepte qu'une seule connexion par bot.

### Mode production (webhook via FastAPI)

```bash
python -m api.main
```

Configurer le webhook Telegram vers `https://<ton-domaine>/webhook/telegram` :

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://<ton-domaine>/webhook/telegram"
```

## Bots planifiés

| Bot | Fréquence | Rôle |
|-----|-----------|------|
| PublisherBot | */15 min | Publie les posts approuvés |
| ReviewsBot | Daily 08:00 | Importe les reviews stores |
| AnalyticsBot | Daily 06:00 | Sync métriques (Plausible, etc.) |
| WatchdogBot | */30 min | Surveillance santé système |

## Endpoints API principaux

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/health` | Health check |
| GET | `/projects` | Liste projets |
| POST | `/dev-log` | Ajouter un dev log |
| POST | `/tickets` | Créer un ticket |
| POST | `/feedback` | Soumettre un feedback |
| POST | `/agents/coo/briefing` | Briefing COO |
| POST | `/agents/coo/instruction` | Instruction COO |
| POST | `/webhook/telegram` | Webhook Telegram (production) |
| POST | `/agents/spec/{ticket_id}` | Générer prompt Cursor |
| POST | `/sav/ask` | Question support client |

## Variables d'environnement

**Guide complet (features à activer plus tard)** → [`docs/ENV_ACTIVATION.md`](docs/ENV_ACTIVATION.md)

| Variable | Requis | Description |
|----------|--------|-------------|
| `HUB_API_KEY` | **Oui** | Clé API Hub (`X-Hub-Key`) — obligatoire partout, y compris local |
| `SUPABASE_URL` | Oui | URL du projet Supabase |
| `SUPABASE_KEY` | Oui | Clé service role ou anon |
| `OPENROUTER_API_KEY` | Oui | Clé API OpenRouter (LLM) |
| `DISCORD_TOKEN` | Non | Token bot Discord |
| `TELEGRAM_BOT_TOKEN` | Non | Token bot Telegram (via BotFather) |
| `SENTRY_DSN` | Non | DSN Sentry pour monitoring |
| `PLAUSIBLE_API_KEY` | Non | Clé API Plausible (AnalyticsBot) |

## Licence

Propriétaire — ALNUA © 2026
