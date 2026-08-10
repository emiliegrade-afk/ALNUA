"""Brainstorm agent — shared constants and prompt templates."""
from __future__ import annotations

from pathlib import Path

from config.agent_system_prompts import (
    BRAINSTORM_CHAT_PROMPT,
    BRAINSTORM_SUMMARIZE_PROMPT,
)

# Racine des exports markdown
BRAINSTORM_NOTES_ROOT = Path(__file__).resolve().parent.parent / "brainstorm_notes"

# Correspondance noms de projets → dossiers sur disque
PROJECT_FOLDER_SLUGS: dict[str, str] = {
    "naïa": "naia",
    "naia": "naia",
    "wyrdheim online": "wyrdheim",
    "wyrdheim": "wyrdheim",
    "eve": "eve",
    "alnua global": "alnua_global",
}

WELCOME_MESSAGE = (
    "Bonjour Emilie. Sur quoi tu veux brainstormer aujourd'hui ? Je peux t'aider à explorer "
    "des idées de features, de nouveaux produits, des mécaniques de jeu, ou n'importe quelle "
    "direction stratégique pour ALNUA."
)

CHAT_SYSTEM_PROMPT = BRAINSTORM_CHAT_PROMPT

SUMMARIZE_SYSTEM_PROMPT = BRAINSTORM_SUMMARIZE_PROMPT + """

Utilise EXACTEMENT ce template (remplace les [placeholders]) :

---
session: [NNN]
projet: [Nom du projet]
date: [DD/MM/YYYY]
tags: [2-4 mots-clés]
---

# [Titre descriptif et accrocheur — 5-8 mots]
*Session #[NNN] · [Projet] · [Date longue]*

---

## 📋 Contexte
[2-3 phrases sur le sujet exploré et pourquoi]

---

## 💡 Idées explorées
[Liste numérotée de TOUTES les idées abordées, même les rejetées]
1. ...
2. ...

---

## [OK] Idees retenues
[Seulement les idées validées ou intéressantes, avec une phrase d'explication chacune]
- **[Idée]** → [Pourquoi c'est retenu]

---

## 🎯 Décisions prises
[Ce qui a été acté, orienté, ou écarté définitivement]
- ...

---

## ❓ Questions ouvertes
[Ce qui reste à explorer, trancher ou creuser]
- ...

---

## 🚀 Prochaines étapes
[Actions concrètes et actionnables]
- [ ] ...
- [ ] ...

---
*Compte-rendu généré automatiquement par ALNUA Hub*"""
