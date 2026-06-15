# /alnua-prd — PRD structuré ALNUA
> Adapté de prd-taskmaster (anombyte93) pour Léon Marchand (Spec) et Sam Rivera (PM).
> Invoque avec `/alnua-prd` pour générer un PRD complet + task breakdown depuis un brief.

## Objectif
Transformer un brief en PRD complet et actionnable, puis le décomposer en tâches priorisées.
Léon écrit la spec technique. Sam traduit en plan de delivery. Ce skill coordonne les deux.

---

## Template PRD ALNUA

### Structure obligatoire

```markdown
# PRD — [Nom de la Feature]
**Auteur Spec** : Léon Marchand (Spec Agent)
**Auteur PM** : Sam Rivera (PM Agent)
**Date** : YYYY-MM-DD
**Status** : Draft | Review | Approved
**Version** : 1.0

---

## 1. Contexte & Problème
> Quel problème business on résout ? Pour qui ? Depuis combien de temps ?
- **Utilisateur cible** : [persona]
- **Douleur actuelle** : [ce qui se passe sans cette feature]
- **Impact si non résolu** : [chiffre ou conséquence mesurable]

## 2. Objectif & Success Metrics
> Qu'est-ce qu'on veut accomplir ? Comment on sait qu'on a réussi ?

**Objectif principal** : [une phrase]

**KPIs de succès** :
| Métrique | Baseline | Target | Délai |
|----------|----------|--------|-------|
| [metric1] | [valeur] | [valeur] | [date] |
| [metric2] | [valeur] | [valeur] | [date] |

## 3. Scope — IN / OUT

**IN (ce qu'on fait)** :
- [feature 1]
- [feature 2]

**OUT (explicitement exclus)** :
- [ce qu'on ne fait PAS et pourquoi]

## 4. Spec Technique (Léon)

### 4.1 Architecture
```
[Diagramme ASCII ou description du flux de données]
```

### 4.2 Endpoints API
| Méthode | Route | Description | Auth |
|---------|-------|-------------|------|
| POST | /api/... | ... | API Key |

### 4.3 Modèles de données
```python
class FeatureRequest(BaseModel):
    field: type  # description
```

### 4.4 Dépendances & Risques
- **Dépendances** : [services, agents, APIs externes]
- **Risques techniques** : [ce qui peut mal tourner]
- **Hypothèses** : [ce qu'on prend pour acquis]

## 5. Plan de Delivery (Sam)

### 5.1 Task Breakdown
| # | Tâche | Agent | Points | Bloqueurs | Priorité |
|---|-------|-------|--------|-----------|----------|
| 1 | [task] | [agent_id] | [pts] | [rien/task_n] | P0/P1/P2 |

### 5.2 Timeline
- **Sprint 1** (sem 1-2) : [livrable]
- **Sprint 2** (sem 3-4) : [livrable]
- **Go-live** : [date cible]

### 5.3 Definition of Done
- [ ] Tests unitaires passent (Alex)
- [ ] Endpoint documenté dans CLAUDE.md
- [ ] Review COO (Aria) validée
- [ ] Déployé en staging sans erreur

## 6. Open Questions
| Question | Owner | Deadline |
|----------|-------|----------|
| [question bloquante] | [qui répond] | [date] |

## 7. Changelog
| Date | Version | Auteur | Changement |
|------|---------|--------|------------|
| [date] | 1.0 | Léon/Sam | Création |
```

---

## Workflow d'utilisation

### Étape 1 — Brief → PRD (Léon)
```
Input : "Je veux une feature X qui fait Y pour Z"
Léon appelle : spec_agent.write_spec(brief) → structure PRD sections 1-4
```

### Étape 2 — PRD → Tasks (Sam)
```
Input : PRD sections 1-4 complet
Sam appelle : pm_agent.plan_sprint(spec) → remplie sections 5-6
```

### Étape 3 — Adversarial Review (Alex)
```
Input : PRD complet
Alex critique : qa_agent.review_spec(prd) → liste des holes
Léon révise → version 1.1
```

### Étape 4 — Approval (Aria)
```
Aria lit le PRD en 2min → GO / NO-GO / Clarification needed
```

---

## Règles de qualité PRD

- **Section 1** : si le problème prend plus de 3 phrases à expliquer, c'est trop flou → recommencer
- **Section 3** : la liste OUT est aussi importante que IN — tout ce qui n'est pas explicitement IN est OUT
- **Section 4** : les endpoints doivent être copier-collables dans un test curl
- **Section 5** : chaque tâche a un agent assigné — jamais "l'équipe"
- **Section 6** : les questions ouvertes ont une deadline. Sans deadline, elles disparaissent.

---

## Commandes Cursor

```bash
# Générer un PRD depuis un brief
POST /agents/spec/spec {"feature": "brief complet", "context": "projet"}

# Transformer la spec en plan de delivery
POST /agents/pm/sprint-plan {"spec": "contenu PRD", "team_capacity": 10}

# Review adversariale du PRD
POST /services/adversarial-spec/quick-check {"spec_text": "contenu PRD"}
```

---

## Critères de qualité (Alex valide)
Un PRD est prêt pour implémentation si :
- Chaque section est remplie (pas de [placeholder] restant)
- Les KPIs sont mesurables (pas "améliorer l'expérience")
- Le task breakdown est faisable en ≤ 2 sprints
- Les open questions ont une deadline
