# Catalogue détaillé — abonnements & outils ALNUA

> Inventaire pour le Hub + le développement d’apps (NuAway, Resonance, landings, gaming…).  
> Prix publics **août 2026** (TVA / conversion FX non inclus).  
> Fourchettes calibrées pour 1 fondatrice solo + Hub actif + 1–3 apps en construction.

**Priorités :** `essentiel` · `recommandé prod` · `optionnel` · `gratuit / usage`

---

## Budget mensuel (3 scénarios)

| Poste | Socle ($) | Confort ($) | Scale ($) | Notes |
|-------|-----------|-------------|-----------|-------|
| Cursor | 20 | 20–60 | 60–200 | Pro → Pro+ si agents saturés |
| OpenRouter (LLM Hub) | 25 | 40 | 100–150 | Config CN actuelle |
| Supabase | 25 | 25–35 | 45–55 | +10 $/projet Micro extra |
| n8n Cloud | 22 | 55 | 55 | Starter 20 € · Pro 50 € |
| Vercel | 0 | 20 | 20–40 | Hobby → Pro + usage |
| Railway / Render (API Hub) | 0 | 10–20 | 20–40 | Local OK en socle |
| Mem0 | 0 | 19 | 19–79 | Hobby → Starter |
| Langfuse | 0 | 0–29 | 29 | Hobby / self-host / Core |
| Composio | 0 | 0–29 | 29 | Gmail/Notion OAuth |
| Sentry | 0 | 29 | 29–80 | Free → Team |
| GitHub | 0 | 0–4 | 4 | Free souvent OK |
| Google Workspace | 0–8 | 8 | 8–14 | 1 siège alnua.global |
| Expo EAS | 0 | 0–19 | 19–99 | Si builds mobiles réguliers |
| Domaines / DNS | 3 | 5 | 8 | Amorti annuel |
| Apple Developer | 8 | 8 | 8 | 99 $/an amorti |
| Stripe | 0 | 0 + % | 0 + % | Pas d’abo — frais sur GMV |
| Maps / TTS / divers | 0 | 0–20 | 30–80 | Selon produit live |
| **TOTAL estimé** | **~100–110** | **~240–320** | **~450–650** | Hors TVA |

**Résumé :** Socle ~100 $ · Confort prod ~250 $ · Scale multi-apps ~450–650 $

---

## 1. Cursor — IDE & agents de code

**Priorité :** essentiel · **Type :** abonnement fixe

C’est le poste de travail principal. Distinct d’OpenRouter : Cursor facture ses propres pools (Auto/Tab + « Other Models »). Le Hub et Aider passent par OpenRouter, pas par l’abo Cursor.

| Plan | Prix | Usage inclus | Pour qui |
|------|------|--------------|----------|
| Hobby | 0 $ | Agent + Tab limités | Essai seulement |
| Pro | 20 $/mois (16 $ annuel) | ~20 $ pool Other Models + Auto/Tab illimités | Usage quotidien normal |
| Pro+ | 60 $/mois (48 $ annuel) | ~70 $ pool (3× Pro) | Agents lourds tous les jours |
| Ultra | 200 $/mois (160 $ annuel) | ~400 $ pool | Full-time agent farming |
| Teams Standard | 40 $/user | Pool équipe | Plusieurs sièges |

**Chez ALNUA :** MCP Hub, GitHub, n8n, context7, browser-tools…  
**Reco :** Pro 20 $. Passe Pro+ si tu tapes souvent la limite mid-month.

---

## 2. OpenRouter — cerveau LLM du Hub

**Priorité :** essentiel · **Type :** pay-as-you-go (+5,5 % sur crédits)

Tous les agents (`agents/*.py`), coding pipeline, R&D, content via `OPENROUTER_API_KEY`.

| Modèle (config actuelle) | Input / 1M | Output / 1M | Usage ALNUA |
|--------------------------|------------|-------------|-------------|
| minimax/minimax-m3 | 0,30 $ | 1,20 $ | Coding + R&D dominant |
| deepseek/deepseek-chat-v3.1 | 0,25 $ | 0,95 $ | Tier standard / coach |
| deepseek/deepseek-r1-0528 | 0,50 $ | 2,15 $ | PM, analysts, committee |
| z-ai/glm-5.2 | 0,07 $ | 0,22 $ | dev_backend, secretary |
| anthropic/claude-haiku-4.5 | 1,00 $ | 5,00 $ | accounting, controller |
| google/gemini-2.5-pro | 1,25 $ | 10,00 $ | rnd_dossier, game_director |
| anthropic/claude-sonnet-4.x | 3,00 $ | 15,00 $ | Si premium west forcé |

| Intensité | Coût mensuel typique |
|-----------|----------------------|
| Léger | ~15–25 $ |
| Actif | ~30–50 $ |
| Sprint MVP | ~80–150 $ (config CN) |

**Piège :** coding en Claude Sonnet ≈ ×10 sur la facture. Garder MiniMax/DeepSeek/GLM sur `dev_*`.

---

## 3. Supabase — DB & BaaS

**Priorité :** essentiel · **Type :** abo + usage

Source de vérité Hub (`SUPABASE_URL` / keys). Auth, Postgres, Storage, Edge Functions.

| Plan | Prix base | Inclus clés | Limites |
|------|-----------|-------------|---------|
| Free | 0 $ | 2 projets, 500 MB DB, 1 GB storage, 50k MAU | Pause après 1 sem. inactivité |
| Pro | from 25 $ | 100k MAU, 8 GB disk, 250 GB egress, backups 7 j | Email support · spend cap ON |
| Team | from 599 $ | SOC2, SSO, backups 14 j | Overkill solo early |

### Compute (par projet)

| Taille | $/mois | RAM | Note |
|--------|--------|-----|------|
| Micro | 10 $ | 1 GB | Inclus via 10 $ crédit Pro (1er projet) |
| Small | 15 $ | 2 GB | Si API saturée |
| Medium | 60 $ | 4 GB | Prod chargée |

**Exemple :** Pro + 1 Micro = **25 $**. Pro + 2 Micro = **35 $**.  
**Reco :** Pro 25 $ dès qu’une app/Hub ne doit plus être pausé.

---

## 4. Neon — Postgres alternatif

**Priorité :** optionnel · Free / Launch (usage) / Scale  

**Décision ALNUA :** ne pas payer Neon + Supabase. Stack actuelle = **Supabase seul**.

---

## 5. n8n Cloud — automatisation

**Priorité :** essentiel · Instance : `alnua.app.n8n.cloud`  
Facturation au **workflow execution** (pas par step).

| Plan | Prix (annuel) | Exécutions / mois | Inclus utiles |
|------|---------------|-------------------|---------------|
| Starter | 20 €/mois | 2 500 | 1 projet, 5 concurrent, 2 300 AI credits |
| Pro | 50 €/mois | 10 000 | 3 projets, variables globales, history |
| Business | 667 €/mois | 40 000 | Self-host licence, SSO — trop tôt |
| Community | 0 $ | Illimité self-host | Tu gères le serveur |

1 workflow quotidien ≈ 30 exec/mois. Toutes les 5 min ≈ 8 600 → Pro minimum.

---

## 6. Vercel — front Next.js

| Plan | Prix | Ce que tu gagnes |
|------|------|------------------|
| Hobby | 0 $ | Preview / perso — limites strictes |
| Pro | 20 $/user | 20 $ crédit usage, commercial OK |
| Enterprise | Custom | SLA, SSO, WAF |

Add-ons : Analytics Plus ~10 $, Speed Insights ~10 $/projet.  
**Reco :** Hobby en itération · Pro dès landing commerciale.

---

## 7. Railway / Render — API Hub cloud

| Option | Prix | Détail |
|--------|------|--------|
| Local only (dev) | 0 $ | n8n cloud via tunnel |
| Railway Hobby | 5 $ | 5 $ crédits inclus |
| Railway Pro | 20 $/workspace | 20 $ crédits, logs 30 j |

Nécessaire pour Hub 24/7 (n8n + apps).

---

## 8. Mem0 — mémoire agents

`skills/skill_mem0.py`

| Plan | Prix | Add / mois | Retrieval / mois |
|------|------|------------|------------------|
| Hobby | 0 $ | 10 000 | 1 000 |
| Starter | 19 $ | 50 000 | 5 000 |
| Growth | 79 $ | 200 000 | 20 000 |
| Pro | 249 $ | 500 000 | 50 000 |

**Reco :** Hobby puis Starter dès usage continu de tous les agents.

---

## 9. Langfuse — traces LLM

`@trace_agent` → cloud.langfuse.com (ou self-host)

| Plan | Prix | Units | Rétention | Users |
|------|------|-------|-----------|-------|
| Hobby | 0 $ | 50k | 30 j | 2 |
| Core | 29 $ | 100k (+8 $/100k) | 90 j | Illimité |
| Pro | 199 $ | 100k (+usage) | 3 ans | Illimité |
| Self-host | 0 $ + infra | Illimité | Toi | Toi |

---

## 10. Composio — OAuth pour agents

`COMPOSIO_API_KEY` — Gmail, Calendar, Notion, Sheets…

| Plan | Prix approx. | Tool calls |
|------|--------------|------------|
| Hobby | 0 $ | ~20k / mois |
| Starter | ~29 $ | ~200k |
| Professional | ~229 $ | ~2M |

---

## 11. GitHub

| Plan | Prix | Utile pour |
|------|------|------------|
| Free | 0 $ | Repos, Actions limitées, MCP |
| Pro | 4 $/user/mois | Features avancées |
| Team | 4 $+ /user | Org multi-devs |

**Reco solo :** Free.

---

## 12. Sentry — erreurs prod

Webhook Hub → issues GitHub (`sentry_ops.py`)

| Plan | Prix | Quota | Users |
|------|------|-------|-------|
| Developer | 0 $ | 5k errors | 1 |
| Team | 26 $/mois annuel (29 $ mensuel) | 50k errors · 5M spans | Illimité |
| Business | 80 $/mois annuel | + SSO / retention | Illimité |

---

## 13. Stripe — paiements (France)

**0 $ d’abonnement.** Frais uniquement sur paiement réussi.

| Type de carte | Frais Stripe FR | Sur 100 € |
|---------------|-----------------|-----------|
| Carte EEE standard | 1,5 % + 0,25 € | 1,75 € |
| Carte EEE premium | 1,9 % + 0,25 € | 2,15 € |
| Carte UK | 2,5 % + 0,25 € | ~2,75 € |
| Internationale | 3,25 % + 0,25 € (+ FX) | ~3,50 €+ |

| Add-on | Coût | Quand |
|--------|------|-------|
| Billing | ~0,7 % du volume | Abos SaaS |
| Tax | ~0,5 % | TVA auto |
| Connect | frais plateforme | Marketplace NuAway |

Exemple : 10 000 € GMV/mois EEE standard ≈ **175 €** de frais Stripe.

---

## 14. Expo EAS — builds mobiles

NuAway / Resonance. Free limité · Starter ~19 $ · Production plus haut selon offre.

---

## 15. Stores Apple & Google

| Store | Coût | Type |
|-------|------|------|
| Apple Developer Program | 99 $/an (~8 $/mois) | Abonnement annuel |
| Google Play Console | 25 $ | One-shot |
| Commission stores | 15–30 % IAP | Sur revenus in-app |

---

## 16. Google Workspace & Cloud

| Produit | Prix | Usage ALNUA |
|---------|------|-------------|
| Business Starter | ~7–8 $/user/mois | Mail / Drive / Calendar |
| Business Standard | ~14 $/user | Meet / stockage |
| Maps Platform | Crédit free puis usage | NuAway carte — **cap budget obligatoire** |

---

## 17. Comms gratuites (déjà dans le Hub)

| Outil | Coût | Rôle |
|-------|------|------|
| Telegram Bot API | 0 $ | Aria COO + Nadia |
| Discord Bot | 0 $ | Communauté |
| Obsidian (local) | 0 $ (+ Sync optionnel) | Vault lore / library |

---

## 18. Optionnels produit / média

| Outil | Prix typique | Quand |
|-------|--------------|-------|
| ElevenLabs | 0–22 $+ | Voice Resonance |
| Magnific / gen image | crédits | Brand kit, assets |
| Plausible | 0 self / ~9 €+ | Analytics landings |
| Upstash Redis | 0–10 $ | Redis cloud Hub |
| AWS S3 backups | 1–5 $ | DR |
| RevenueCat | 0 puis % | Abos IAP |
| Domaines | ~10–15 $/an/domaine | alnua.*, apps |

---

## Déjà câblé dans ALUNA_HUB (`.env`)

| Variable / intégration | Service | Statut |
|------------------------|---------|--------|
| OPENROUTER_API_KEY | OpenRouter | Obligatoire |
| SUPABASE_URL / KEY / SERVICE_ROLE | Supabase | Obligatoire |
| HUB_API_KEY | Auth Hub | Obligatoire |
| N8N_BASE_URL / MCP | n8n Cloud | Actif |
| COMPOSIO_API_KEY | Composio | Optionnel prévu |
| GITHUB_TOKEN / REPO* | GitHub | Coding + issues |
| SENTRY_DSN | Sentry | Optionnel |
| LANGFUSE_* | Langfuse | Optionnel |
| Mem0 via SDK | Mem0 | Optionnel dégradé |
| AWS_* / BACKUP_S3 | S3 | Optionnel DR |
| TELEGRAM_* | Telegram | Bots |
| CEO_GMAIL | Google via Composio | Nadia |

---

## Décisions anti double-paiement

1. **1 DB provider** — Supabase OU Neon (chez toi : Supabase).  
2. **2 couches LLM** — Cursor (IDE) ≠ OpenRouter (Hub).  
3. **Observabilité** — Langfuse (LLM) + Sentry (runtime), pas Datadog au début.  
4. **Automation** — n8n Cloud déjà là, éviter Make/Zapier en parallèle.

---

## Ordre d’achat recommandé

| # | Acheter | Pourquoi | ~$/mois |
|---|---------|----------|---------|
| 1 | Cursor Pro | Vélocité | 20 |
| 2 | OpenRouter crédits | Hub | 25+ |
| 3 | Supabase Pro | Prod DB sans pause | 25 |
| 4 | n8n Starter/Pro | Déjà utilisé | 22–55 |
| 5 | Vercel Pro | Landing commerciale | 20 |
| 6 | Railway Hub | API 24/7 | 5–20 |
| 7 | Apple + Play | Stores | ~8 + 0 |
| 8 | Mem0 / Sentry | Qualité + stabilité | 19–29 |
| 9 | Workspace + Composio | Ops CEO | 8–37 |
| 10 | Langfuse / EAS / Maps | Quand volume justifie | variable |

---

## Glossaire

- **MAU** — Monthly Active Users (Auth)  
- **CU-hour** — heure de compute Neon  
- **Execution n8n** — 1 run complet d’un workflow  
- **Tool call Composio** — 1 action OAuth  
- **GMV** — volume de paiements (base frais Stripe)

---

## Sources

cursor.com/pricing · vercel.com/pricing · supabase.com/pricing · n8n.io/pricing · openrouter.ai · mem0.ai · langfuse.com/pricing · neon.tech · railway.com/pricing · stripe.com/fr/pricing · github.com/pricing · sentry.io · croisé avec `.env.example` et `ARCHITECTURE.md` du Hub (août 2026).

*Canvas Cursor équivalent :* `C:\Users\emili\.cursor\projects\c-Dev-ALUNA-HUB\canvases\alnua-subscriptions-catalog.canvas.tsx`
