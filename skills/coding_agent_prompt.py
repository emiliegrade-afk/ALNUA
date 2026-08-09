"""Prompt builder for Claude Code — split from skill_coding_agent."""
from __future__ import annotations

from services.coding_pipeline import detect_stack, stack_expert_role, stack_rules_block


def build_claude_prompt(spec: dict) -> str:

    """

    Construit le prompt complet pour Claude Code depuis la spec JSON.
    Détecte la stack (Expo, Next.js, FastAPI) pour adapter les règles.
    """

    files_create = spec.get("files_to_create") or ["(détermine toi-même)"]
    files_modify = spec.get("files_to_modify") or ["(détermine toi-même)"]
    tests_pass = spec.get("tests_to_pass") or [
        "(aucun spécifié — crée des tests appropriés)"
    ]
    stack = detect_stack(spec)
    role = stack_expert_role(stack)
    rules = stack_rules_block(stack)
    prompt = f"""Tu es un {role} travaillant sur un projet ALNUA.
{rules}
TÂCHE : {spec['title']}
ID : {spec['task_id']}
DESCRIPTION COMPLÈTE :
{spec['description']}
FICHIERS POTENTIELLEMENT CONCERNÉS :
- À créer : {', '.join(files_create)}
- À modifier : {', '.join(files_modify)}
CRITÈRES DE SUCCÈS :
- Le code est fonctionnel et testé
- Les tests suivants passent : {', '.join(tests_pass)}
- Pas de debug oublié (print/console.log en prod)
- Gestion d'erreurs explicite
RÈGLES GÉNÉRALES ALNUA :
- Ne pas modifier les fichiers hors scope de la tâche
- Commit final avec message : "feat({spec['task_id']}): {spec['title']}"
IMPORTANT : Travaille uniquement dans le répertoire courant. Respecte la structure existante du repo.
"""

    return prompt

