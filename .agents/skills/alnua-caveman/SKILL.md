# ALNUA Caveman — Mode Compression Tokens

**Quand actif : réponds en mode compressé. Rémi Chassagne (Contrôleur) mesure les coûts OpenRouter.**

---

## Règles de compression

Quand on travaille sur ALNUA Hub :

**Shrink output :**
- Skip intro phrases ("Bien sûr", "Voici", "Je vais")
- Skip summary at end ("En résumé", "J'espère que")
- Code → direct, no explain unless asked
- Error → cause + fix, skip "This error occurs because..."
- Lists → 1 line per item max
- JSON output → compact, no pretty-print unless user needs to read it

**Keep full verbosity for :**
- SYSTEM_PROMPT writing (quality critical)
- API contract specs
- SKILL.md files
- Any user-facing documentation
- Complex architecture decisions

---

## Compression cibles par type de tâche

| Tâche | Mode | Ratio cible |
|-------|------|-------------|
| Debug rapide | caveman | -70% |
| Code review | caveman | -50% |
| Nouveau fichier agent | normal | 0% |
| SYSTEM_PROMPT quality | verbose | +20% |
| Endpoint CRUD | caveman | -60% |
| Architecture decision | normal | 0% |

---

## Template caveman pour réponses code

```
# Au lieu de :
"Voici le code corrigé. J'ai modifié la ligne 42 pour corriger le bug..."
[code long avec commentaires évidents]
"Ce code fait maintenant X, Y et Z."

# Mode caveman :
fix: line 42 — None check missing
[code minimal]
```

---

## Trigger complet pour activer avec Cursor

Commence ta session Cursor avec :
```
/alnua-caveman — mode compression ON pour cette session
```

Et pour désactiver :
```
mode verbeux ON
```

---

## Suivi coût (Rémi Chassagne, Contrôleur)

```python
from services.competition import add_points

# Quand une session se termine avec compression activée :
add_points("controller", "insight_actioned", note="Token compression session — estimated -60% cost")
```

OpenRouter facturation : vérifier dans `services/competition.py::costs_analysis()`.

Rémi alerte automatiquement via `POST /agents/controller/llm-alert` si le seuil est dépassé.

---

## Pourquoi ça compte

Chaque appel LLM dans ALNUA Hub passe par OpenRouter. 20 agents × N méthodes × volume quotidien = coût non négligeable. La compression token-side (dans les prompts utilisateurs/Cursor) complète la compression côté agent (`temperature` bas + `max_tokens` serré). Double levier.
