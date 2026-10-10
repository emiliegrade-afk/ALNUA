# /alnua-search — Recherche web avec citations ALNUA
> Adapté de google-ai-mode-skill (PleasePrompto) pour Idris Okonkwo (Brainstorm) et Alex Mercer (R&D).
> Invoque avec `/alnua-search` pour lancer une recherche documentée avec sources vérifiées.

## Objectif
Permettre aux agents de recherche ALNUA de produire des outputs ancrés dans des faits vérifiables, avec citations systématiques. Fin de l'hallucination non sourcée.

---

## Protocole de recherche ALNUA

### Règle 1 — Citations obligatoires
Tout claim factuellement vérifiable DOIT avoir une source. Format :
```
[claim factuel] (Source: [titre], [URL ou publication], [date])
```
Si la source ne peut pas être citée → le claim est retiré ou formulé comme hypothèse explicite.

### Règle 2 — Niveaux de confiance
Chaque section de recherche indique son niveau :
- **🟢 Vérifié** : source primaire citée, dato récent (< 2 ans)
- **🟡 Probable** : source secondaire ou donnée > 2 ans
- **🔴 Hypothèse** : raisonnement logique, pas de source directe

### Règle 3 — Structure du rapport de recherche
```markdown
## Recherche : [Sujet]
**Agent** : Idris (Brainstorm) | Alex (R&D)
**Date** : YYYY-MM-DD
**Profondeur** : Quick (< 30min) | Standard (1-2h) | Deep (> 2h)

### Résumé exécutif (3 phrases max)
[Ce qu'on a trouvé, ce que ça implique, ce qu'on recommande]

### Findings
#### [Point 1] 🟢
[Claim] (Source: [source])
[Implication pour ALNUA]

#### [Point 2] 🟡
[Claim] (Source: [source])
[Nuance ou limite de la donnée]

### Sources primaires consultées
1. [Titre] — [URL] — [Date]
2. [Titre] — [URL] — [Date]

### Gaps identifiés (ce qu'on n'a pas trouvé)
- [information manquante et pourquoi c'est un problème]

### Next steps recommandés
1. [action] → [agent ALNUA responsable]
```

---

## Stratégies de recherche par type

### Recherche concurrentielle (Camille / Layla)
```
Rechercher : [concurrent] site:[concurrent.com] pricing OR features OR review
Compléter avec : [concurrent] reddit review 2024 OR 2025
Éviter : articles sponsorisés, pages de vente directes
```

### Recherche technologique (Alex / Idris)
```
Priorité 1 : arxiv.org, papers.google.com, github.com
Priorité 2 : blog.engineering.[company].com
Éviter : Medium articles sans peer review
```

### Recherche marché (Layla)
```
Sources fiables : statista.com, forrester.com, gartner.com, similarweb.com
Sources gratuites : producthunt.com/posts, g2.com/reviews, capterra.com
Recherche approximative : "[secteur] market size 2024 report PDF"
```

### Recherche technique / API (Hao / Théo / Nova)
```
Sources : docs officielles > GitHub issues > StackOverflow > Reddit
Vérifier la date : les réponses > 2 ans peuvent être obsolètes
Tester : chaque snippet de code avant de le proposer
```

---

## Workflow agents ALNUA

### Idris (Brainstorm) — Recherche exploratoire
```python
# Appel API
POST /agents/brainstorm/ideate
{
  "topic": "sujet à explorer",
  "context": "ce qu'on sait déjà",
  "research_depth": "standard"
}
# Output : ideas[] + research_notes[] avec citations
```

### Alex (R&D) — Recherche approfondie
```python
POST /agents/rnd/prototype-spec
{
  "concept": "idée à investiguer",
  "technical_constraints": [...],
  "research_sources": ["arxiv", "github", "docs"]
}
# Output : technical_spec + feasibility + sources[]
```

---

## Checklist anti-hallucination

Avant de livrer tout output de recherche :
```
[ ] Chaque chiffre a une source avec URL
[ ] Chaque "tendance" a au moins 2 sources indépendantes
[ ] Les dates des sources sont mentionnées
[ ] Les sections 🔴 Hypothèse sont clairement marquées
[ ] Les contradictions entre sources sont signalées, pas ignorées
[ ] Le résumé exécutif ne contient rien qui ne soit pas dans les findings
```

---

## Sources de référence ALNUA (à toujours vérifier en premier)

| Domaine | Source prioritaire | URL |
|---------|-------------------|-----|
| Gaming | GDC talks, Game Developer Magazine | gdconf.com |
| AI/ML | Papers With Code, Hugging Face Blog | paperswithcode.com |
| FastAPI | Docs officielles | fastapi.tiangolo.com |
| Supabase | Changelog + Docs | supabase.com/changelog |
| Marketing | Product Hunt trends | producthunt.com |
| Crypto/Finance | CoinGecko, DeFiLlama | coingecko.com |
| Business | HBR, McKinsey Insights | hbr.org |

---

## Règle d'or Idris & Alex
> Un insight sans source est une opinion. Une source sans contexte est du bruit. Le travail de recherche, c'est transformer le bruit en signal vérifiable.
