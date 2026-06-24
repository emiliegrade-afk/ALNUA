"""
SkillSynthesizer — Boucle d'auto-apprentissage inspirée de Hermes Agent.

Après chaque instruction COO réussie, analyse ce qui a été accompli.
Si le pattern est répétable, génère automatiquement un nouveau skill Python
dans skills/ et l'enregistre dans Mem0 pour les agents.

Usage (appelé en background par coo_agent.py) :
    from agents.skill_synthesizer import maybe_synthesize_skill
    maybe_synthesize_skill(instruction=msg, result=response)
"""

from __future__ import annotations

import logging
import os
import re
import textwrap
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent.parent / "skills"

# Seuil : on ne génère un skill que si l'instruction ressemble à un pattern répétable.
REPEATABLE_KEYWORDS = (
    "chaque", "tous les", "chaque matin", "automatiquement", "à chaque fois",
    "génère", "créé un rapport", "analyse", "vérifie", "scrape", "résumé",
    "liste les", "trouve les", "recherche les",
)

# Patterns qui ne méritent PAS un skill (one-shot)
ONESHOT_KEYWORDS = (
    "supprime", "renomme", "migre", "configure une fois", "initialise",
)


def _should_synthesize(instruction: str) -> bool:
    """True si l'instruction ressemble à une tâche répétable."""
    low = instruction.lower()
    if any(kw in low for kw in ONESHOT_KEYWORDS):
        return False
    return any(kw in low for kw in REPEATABLE_KEYWORDS)


def _skill_name_from_instruction(instruction: str) -> str:
    """Génère un nom snake_case pour le skill depuis l'instruction."""
    # Garde les 6 premiers mots significatifs
    words = re.sub(r"[^\w\s]", "", instruction.lower()).split()
    stop = {"le", "la", "les", "un", "une", "des", "de", "du", "et", "ou",
            "pour", "par", "sur", "dans", "avec", "qui", "que", "à", "au"}
    clean = [w for w in words if w not in stop][:5]
    slug = "_".join(clean) if clean else "auto_skill"
    return f"skill_auto_{slug}"


def _generate_skill_code(instruction: str, result: str, skill_name: str) -> str:
    """Demande au LLM de générer le code du skill."""
    try:
        from agents.base import LLMClient
        from config.agent_operating_spec import get_system_prompt

        client = LLMClient()

        system = get_system_prompt("skill_synthesizer")

        user = textwrap.dedent(f"""
            Instruction originale qui a déclenché la création de ce skill :
            "{instruction}"

            Résultat obtenu (résumé) :
            "{result[:500]}"

            Nom de la fonction à créer : {skill_name}(...)

            Génère le skill Python complet et réutilisable.
        """).strip()

        return client.complete(
            system=system, user=user, agent_id="coo", temperature=0.3, max_tokens=1500
        )

    except Exception as exc:
        logger.warning("LLM skill generation failed: %s", exc)
        # Fallback : template générique
        safe_result = repr(result[:400])
        return textwrap.dedent(f'''
            """Auto-generated skill — {skill_name}."""
            import logging
            logger = logging.getLogger(__name__)

            _BASELINE = {safe_result}

            def {skill_name}(**kwargs) -> str:
                """Auto-generated from: {instruction[:120]}"""
                logger.info("Skill {skill_name} invoked with %s", kwargs)
                return _BASELINE
        ''').strip()


def _save_skill(skill_name: str, code: str) -> Path:
    """Sauve le skill dans skills/ et retourne le chemin."""
    path = SKILLS_DIR / f"{skill_name}.py"

    # Si le skill existe déjà, on incrémente
    if path.exists():
        i = 2
        while (SKILLS_DIR / f"{skill_name}_v{i}.py").exists():
            i += 1
        path = SKILLS_DIR / f"{skill_name}_v{i}.py"
        skill_name = f"{skill_name}_v{i}"

    path.write_text(code, encoding="utf-8")
    logger.info("SkillSynthesizer: skill sauvé → %s", path.name)
    return path


def _register_in_mem0(skill_name: str, instruction: str, path: Path) -> None:
    """Enregistre le nouveau skill dans Mem0 pour que le COO s'en souvienne."""
    try:
        from skills.skill_mem0 import remember
        fact = (
            f"Skill auto-généré disponible : {skill_name}(). "
            f"Déclenché par : '{instruction[:150]}'. "
            f"Fichier : skills/{path.name}. "
            f"Utilise ce skill pour des demandes similaires à l'avenir."
        )
        remember(fact, agent_id="coo", user_id="emilie")
        remember(fact, agent_id="spec_agent", user_id="emilie")
    except Exception as exc:
        logger.warning("Mem0 registration failed for %s: %s", skill_name, exc)


def maybe_synthesize_skill(instruction: str, result: str) -> str | None:
    """
    Point d'entrée principal — appelé après chaque instruction COO réussie.

    Retourne le nom du skill créé, ou None si pas de synthèse.
    """
    if not instruction or not result:
        return None

    if not _should_synthesize(instruction):
        return None

    skill_name = _skill_name_from_instruction(instruction)

    # Vérifie si un skill similaire existe déjà
    existing = list(SKILLS_DIR.glob(f"{skill_name}*.py"))
    if existing:
        logger.info("SkillSynthesizer: skill similaire existe déjà (%s), skip.", existing[0].name)
        return None

    logger.info("SkillSynthesizer: génération skill '%s' pour '%s'", skill_name, instruction[:60])

    try:
        code = _generate_skill_code(instruction, result, skill_name)
        path = _save_skill(skill_name, code)
        _register_in_mem0(skill_name, instruction, path)

        print(f"\n🧠 Self-improvement review: Skill '{path.stem}' created → skills/{path.name}")
        return path.stem

    except Exception as exc:
        logger.error("SkillSynthesizer failed: %s", exc)
        return None
