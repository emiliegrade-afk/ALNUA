# ALNUA Hub

Backend Python pour le système d'agents IA d'**ALNUA** — société solo d'Emilie, couvrant 3 branches :

| Branche | Projet | Description |
|---------|--------|-------------|
| App | Naïa | Application bien-être |
| Gaming | Wyrdheim Online | MMORPG fantasy nordique |
| Robotique | Eve | Robot compagnon domestique |

## Architecture

```
agents/     → Agents IA (COO, PM, QA, Content, Brainstorm, Spec)
bots/       → Bots automatisés (Discord, Telegram, Publisher, Reviews, Analytics, SAV, Watchdog)
database/   → Client Supabase + schéma SQL
api/        → API REST FastAPI
config/     → Configuration pydantic-settings
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # puis remplir les variables
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

| Variable | Requis | Description |
|----------|--------|-------------|
| `SUPABASE_URL` | Oui | URL du projet Supabase |
| `SUPABASE_KEY` | Oui | Clé service role ou anon |
| `OPENROUTER_API_KEY` | Oui | Clé API OpenRouter (LLM) |
| `DISCORD_TOKEN` | Non | Token bot Discord |
| `TELEGRAM_BOT_TOKEN` | Non | Token bot Telegram (via BotFather) |
| `SENTRY_DSN` | Non | DSN Sentry pour monitoring |
| `PLAUSIBLE_API_KEY` | Non | Clé API Plausible (AnalyticsBot) |

## Licence

Propriétaire — ALNUA © 2026
