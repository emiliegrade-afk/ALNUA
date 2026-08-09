# ALNUA Hub — Agents Cheat Sheet

20 agents, 8 pièces, 4 équipes compétitives. Référence rapide endpoints + méthodes.

---

## Direction (direction)

### Aria Voss — COO (`coo`)
Modèle : premium | Competitive : oui
```
POST /agents/coo/brief            briefing(topic, context)
POST /agents/coo/delegate         delegate_task(task, agents)
POST /agents/coo/review           review_output(output, criteria)
POST /agents/coo/prioritize       prioritize(items, constraints)
```

### Léon Marchand — Spec Rédacteur (`spec`)
Modèle : standard | Competitive : non
```
POST /agents/spec/write           write_spec(feature, context)
POST /agents/spec/review          review_spec(spec_text)
```

### Alex Okafor — QA (`qa`)
Modèle : standard | Competitive : non
```
POST /agents/qa/test-plan         test_plan(feature, acceptance_criteria)
POST /agents/qa/bug-report        bug_report(description, steps, expected)
```

### Sam Rivera — PM (`pm`)
Modèle : standard | Competitive : non
```
POST /agents/pm/roadmap           roadmap(goals, constraints, timeline)
POST /agents/pm/sprint            sprint_plan(backlog, capacity)
```

---

## App Office (app_office) — Équipe `app` compétitive

### Théo Laurent — Dev App (`dev_app`) vs Hao Chen — Dev Backend (`dev_backend`)

#### Théo — Dev App
```
POST /agents/dev-app/component    build_component(name, description, tech_stack)
POST /agents/dev-app/review       review_code(code, language)
POST /agents/dev-app/debug        debug(error, code_context)
POST /agents/dev-app/refactor     refactor(code, goals)
```

#### Hao — Dev Backend
```
POST /agents/dev-backend/design-api  design_api(resource, operations, auth)
POST /agents/dev-backend/implement   implement_endpoint(spec, framework)
POST /agents/dev-backend/review      review_backend_code(code, focus_areas)
POST /agents/dev-backend/debug       debug_backend(error, stack_trace, context)
```

---

## Gaming Studio (gaming_studio) — Équipe `innovation` compétitive

### Mira Chen — Game Director (`game_director`) vs Nova Fischer — Dev Gaming (`dev_gaming`)

#### Mira — Game Director
```
POST /agents/game-director/concept   game_concept(genre, theme, platform)
POST /agents/game-director/gdd       write_gdd(game_name, concept, scope)
POST /agents/game-director/balance   balance_review(mechanic, data)
```

#### Nova — Dev Gaming
```
POST /agents/dev-gaming/blueprint    blueprint(mechanic, engine)
POST /agents/dev-gaming/script       game_script(event, context)
POST /agents/dev-gaming/optimize     optimize(bottleneck, code)
```

---

## R&D Lab (rnd_lab)

### Idris Okonkwo — Brainstorm (`brainstorm`)
```
POST /agents/brainstorm/ideas        brainstorm(topic, constraints, n)
POST /agents/brainstorm/concept      concept_deep_dive(idea, context)
```

### Alex Mercer — R&D (`rnd_agent`)
```
POST /agents/rnd/research            research(topic, depth)
POST /agents/rnd/prototype           prototype_spec(concept, stack)
```

---

## Comms Hub (comms_hub)

### Camille Rousseau — Marketing (`marketing`)
```
POST /agents/marketing/strategy      strategy(product, target, budget)
POST /agents/marketing/campaign      campaign(objective, channels, message)
```

### Sofia Reyes — Content (`content`)
```
POST /agents/content/write           write(topic, format, tone)
POST /agents/content/optimize        optimize_seo(content, keywords)
```

---

## Accounting Office (accounting_office) — Équipe `finance` compétitive

### Jules Bernard — Comptabilité (`accounting`) vs Rémi Chassagne — Contrôleur (`controller`)

#### Jules — Comptabilité
```
POST /agents/accounting/advice       financial_advice(month, summary, question)
GET  /agents/accounting/invoices     list_open_invoices(status)
GET/POST/PATCH /finances/invoices    ledger factures (paiement externe)
GET  /finances/saas-spend            catalogue + OpenRouter + Revolut status
```

#### Rémi — Contrôleur
```
POST /agents/controller/costs        analyze_costs(period, costs_data, budget)
POST /agents/controller/forecast     build_forecast(project, horizon, assumptions)
POST /agents/controller/llm-alert    llm_cost_alert(daily_spend, monthly_budget)
POST /agents/controller/monthly-report monthly_report(month, all_data)
```

---

## Hardware Workshop (hardware_workshop)

### Yuki Tanaka — Hardware (`hardware`)
```
POST /agents/hardware/spec           hardware_spec(device, requirements)
POST /agents/hardware/bom            bill_of_materials(product, quantity)
```

### Zara Singh — Embedded Dev (`embedded_dev`)
```
POST /agents/embedded-dev/firmware   firmware_task(device, feature, language)
POST /agents/embedded-dev/review     review_embedded(code, target_mcu)
```

---

## Secrétaire — Nadia Faure (`secretary`)

```
POST /agents/secretary/draft-email   draft_email(to, subject, context, tone)
POST /agents/secretary/triage-emails triage_emails(emails)
POST /agents/secretary/draft-contract draft_contract(parties, type, terms)
POST /agents/secretary/plan-meeting  plan_meeting(attendees, agenda, duration)
POST /agents/secretary/meeting-notes meeting_notes(transcript, attendees, decisions)
```

---

## Analytics Room (analytics_room) — Équipe `analytics` compétitive

### Layla Hassan — Business Analyst (`analyst_business`) vs Axel Roux — Data Analyst (`analyst_data`)

#### Layla — Business Analyst
```
POST /agents/analyst-business/market      market_analysis(product, market, competitors)
POST /agents/analyst-business/kpis        define_kpis(project, stage, business_goal)
POST /agents/analyst-business/user-research user_research(product, question, segment)
POST /agents/analyst-business/brief       strategic_brief(topic, context, decision_needed)
```

#### Axel — Data Analyst
```
POST /agents/analyst-data/sql             sql_query(question, schema_context, db_type)
POST /agents/analyst-data/funnel          funnel_analysis(funnel_name, steps, data)
POST /agents/analyst-data/anomaly         anomaly_report(metric, recent_values, baseline)
POST /agents/analyst-data/dashboard-spec  dashboard_spec(name, audience, kpis, data_sources)
```

---

## Endpoints globaux

```
GET  /agents/personas    → tous les AGENT_PERSONAS en JSON
GET  /agents/logs        → derniers agent_logs Supabase
GET  /agents/scores      → scores mois courant
GET  /agents/leaderboard → classement individuel
GET  /agents/leaderboard/teams → classement équipes
POST /agents/scores/add  → add_points(agent_id, action, points, note)
GET  /health             → status API
```

---

## Tiers modèles (agent_models.py)

| Tier | Modèle OpenRouter | Agents |
|------|-----------------|--------|
| premium | google/gemini-2.5-pro | coo, rnd_agent |
| standard | anthropic/claude-3.5-haiku | dev_app, dev_backend, qa, pm, game_director, dev_gaming, brainstorm, marketing, content, secretary, analyst_business |
| fast | google/gemini-flash-1.5 | accounting, controller, analyst_data, hardware, embedded_dev, spec, level_designer |
