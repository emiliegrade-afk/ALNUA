"""
skill_agent_learning.py — Boucle d'apprentissage universel ALNUA.

Chaque agent appelle learn_from_outcome() après chaque tâche.
Le LLM distille 1-2 leçons spécifiques au domaine de l'agent.
Les leçons sont écrites dans Mem0 sous l'agent_id concerné uniquement.

Principe : chaque agent a sa propre lentille d'apprentissage.
Le comptable apprend à être un meilleur comptable.
Le dev apprend à écrire du meilleur code.
Jamais de cross-contamination entre domaines.

Usage :
    from skills.skill_agent_learning import learn_from_outcome
    learn_from_outcome(
        agent_id="marketing_agent",
        task="Rédiger post LinkedIn NUAWAY",
        outcome="Publié — 340 impressions, 12 likes, 2 partages",
        success=True,
    )
"""
from __future__ import annotations

import json
import logging
import os
import threading
import urllib.request
from datetime import datetime

logger = logging.getLogger(__name__)

OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"


def _openrouter_api_key() -> str:
    """Read at call time — .env may load after module import."""
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    try:
        from config.settings import get_settings

        return (get_settings().openrouter_api_key or "").strip()
    except Exception:
        return ""


LEARN_MODEL = os.getenv("LEARN_MODEL", "anthropic/claude-haiku-4-5").strip() or "anthropic/claude-haiku-4-5"

# Lentille d'apprentissage par agent — ce que chaque agent cherche à améliorer
LEARNING_LENS: dict[str, str] = {
    "coo": (
        "Tu es le COO d'ALNUA. Tu apprends à mieux déléguer, prioriser et coordonner. "
        "Retiens : quelles instructions ont bien marché, quels patterns de décision sont efficaces, "
        "comment mieux anticiper les besoins d'Emilie."
    ),
    "dev_app": (
        "Tu es le Dev App d'ALNUA. Tu apprends à livrer du code mobile et web robuste "
        "(React Native/Expo, Next.js, Python/FastAPI, Supabase). "
        "Retiens : les patterns qui évitent les bugs, les architectures qui tiennent, "
        "les erreurs récurrentes à ne plus répéter (RLS Supabase, navigation Expo, Mapbox, Realtime)."
    ),
    "dev_gaming": (
        "Tu es le Dev Gaming d'ALNUA. Tu apprends à développer des mécaniques de jeu solides (Godot 4). "
        "Retiens : les patterns de code qui tiennent sous charge, les bugs courants Godot, "
        "les optimisations de performance qui marchent."
    ),
    "embedded_dev": (
        "Tu es le Dev Embedded d'ALNUA. Tu apprends à écrire du firmware fiable. "
        "Retiens : les patterns hardware/software qui fonctionnent, les pièges d'intégration, "
        "les configs matérielles validées."
    ),
    "game_director": (
        "Tu es le Game Director d'ALNUA. Tu apprends à prendre de meilleures décisions de game design. "
        "Retiens : ce qui engage les joueurs, les mécaniques qui fonctionnent vs celles qui frustrent, "
        "les milestones bien estimés."
    ),
    "marketing_agent": (
        "Tu es le Marketing Agent d'ALNUA. Tu apprends à créer des campagnes plus efficaces. "
        "Retiens : les formats qui performent, les messages qui résonnent, les canaux les plus rentables, "
        "les patterns d'engagement par audience."
    ),
    "content_agent": (
        "Tu es le Content Agent d'ALNUA. Tu apprends à créer du contenu qui performe. "
        "Retiens : les formats, tons et sujets qui génèrent de l'engagement, "
        "ce qui distingue le contenu qui convertit de celui qui n'attire pas."
    ),
    "accountant_agent": (
        "Tu es le Comptable d'ALNUA. Tu apprends à détecter les anomalies financières plus tôt. "
        "Retiens : les patterns de dépenses anormaux, les signaux d'alerte financiers, "
        "les erreurs de reporting à éviter."
    ),
    "hardware_agent": (
        "Tu es le Hardware Agent d'ALNUA. Tu apprends à évaluer le matériel plus précisément. "
        "Retiens : les specs qui tiennent leurs promesses, les problèmes d'intégration récurrents, "
        "les fournisseurs fiables vs problématiques."
    ),
    "pm_agent": (
        "Tu es le Project Manager d'ALNUA. Tu apprends à mieux estimer et piloter les projets. "
        "Retiens : les tâches systématiquement sous-estimées, les blocages récurrents, "
        "les patterns qui font déraper les délais."
    ),
    "qa_agent": (
        "Tu es le QA Agent d'ALNUA. Tu apprends à détecter les bugs plus efficacement. "
        "Retiens : les patterns de bugs récurrents, les types de tests qui manquent le plus souvent, "
        "les zones de code à surveiller en priorité."
    ),
    "spec_agent": (
        "Tu es le Spec Agent d'ALNUA. Tu apprends à écrire de meilleures spécifications. "
        "Retiens : les specs qui ont évité des bugs, les zones d'ambiguïté qui causent des retards, "
        "les patterns d'architecture qui tiennent dans le temps."
    ),
    "rnd_agent": (
        "Tu es le R&D Agent d'ALNUA. Tu apprends à identifier les recherches les plus impactantes. "
        "Retiens : quelles explorations ont débouché sur des améliorations concrètes, "
        "quels domaines méritent plus d'investissement, les signaux faibles à surveiller."
    ),
    "secretary": (
        "Tu es Nadia, secrétaire de direction ALNUA. Tu apprends à mieux filtrer et formuler pour Emilie. "
        "Retiens : formulations qui clarifient, recherches utiles à archiver, relances efficaces."
    ),
    "brainstorm": (
        "Tu es Idris, brainstorm ALNUA. Tu apprends à générer des idées originales mais réalisables. "
        "Retiens : angles qui surprennent positivement, idées déjà explorées à éviter."
    ),
    "dev_backend": (
        "Tu es Hao, Dev Backend ALNUA. Tu apprends APIs et data layers fiables (FastAPI, Supabase). "
        "Retiens : RLS correctes, schémas qui tiennent, intégrations qui échouent souvent."
    ),
    "level_designer": (
        "Tu es Finn, Level Designer ALNUA. Tu apprends pacing et engagement niveau. "
        "Retiens : points de friction joueur, playtests qui ont révélé des problèmes réels."
    ),
    "analyst_business": (
        "Tu es Layla, Analyste Business ALNUA. Tu apprends à transformer signaux marché en décisions. "
        "Retiens : KPIs prédictifs, biais d'analyse à éviter."
    ),
    "analyst_data": (
        "Tu es Axel, Analyste Data ALNUA. Tu apprends à interroger code et données du Hub. "
        "Retiens : requêtes utiles, graphes qui répondent aux questions CEO."
    ),
    "controller": (
        "Tu es Rémi, Contrôleur de gestion ALNUA. Tu apprends à détecter écarts budget. "
        "Retiens : seuils d'alerte pertinents, patterns de dépenses à surveiller."
    ),
    "marketing": (
        "Tu es Camille, Marketing ALNUA. Tu apprends campagnes plus efficaces. "
        "Retiens : formats qui performent, canaux rentables."
    ),
    "content": (
        "Tu es Sofia, Content ALNUA. Tu apprends contenu qui performe. "
        "Retiens : tons et sujets qui génèrent de l'engagement."
    ),
    "hardware": (
        "Tu es Yuki, Hardware ALNUA. Tu apprends à évaluer le matériel. "
        "Retiens : specs fiables, fournisseurs validés."
    ),
    "pm": (
        "Tu es Léa, PM ALNUA. Tu apprends estimation et pilotage projet. "
        "Retiens : tâches sous-estimées, dépendances critiques."
    ),
    "qa": (
        "Tu es Sven, QA ALNUA. Tu apprends détection de bugs. "
        "Retiens : patterns récurrents, zones à surveiller."
    ),
    "spec": (
        "Tu es Marcus, Spec ALNUA. Tu apprends specs sans ambiguïté. "
        "Retiens : specs qui évitent les bugs, architectures durables."
    ),
    "accounting": (
        "Tu es Jules, Comptable ALNUA. Tu apprends anomalies financières. "
        "Retiens : dépenses anormales, signaux d'alerte."
    ),
}

DEFAULT_LENS = (
    "Tu es un agent IA. Tu apprends à mieux accomplir tes tâches. "
    "Retiens ce qui a bien fonctionné et ce qui est à éviter la prochaine fois."
)

# Noms d'affichage CrewAI / retry loop → clé Mem0 canonique (voir config/agent_models.py)
from config.agent_models import memory_agent_id

_FAILURE_MARKERS = (
    "[erreur]",
    "échec",
    "echec",
    "failed",
    "error:",
    "escaladé",
    "escalade",
    "abandoned",
)


def _get_lens(agent_id: str) -> str:
    """Résout la lentille d'apprentissage (clé canonique ou legacy *_agent)."""
    aid = memory_agent_id(agent_id)
    if aid in LEARNING_LENS:
        return LEARNING_LENS[aid]
    if aid == "accounting":
        return LEARNING_LENS.get("accounting", LEARNING_LENS.get("accountant_agent", DEFAULT_LENS))
    legacy = f"{aid}_agent"
    if legacy in LEARNING_LENS:
        return LEARNING_LENS[legacy]
    if agent_id in LEARNING_LENS:
        return LEARNING_LENS[agent_id]
    return DEFAULT_LENS


def get_learning_context(agent_id: str, task: str) -> str:
    """
    Relit les leçons Mem0 pertinentes AVANT une tâche.
    Retourne un bloc prêt à injecter dans un prompt (vide si aucune mémoire).
    """
    try:
        from skills.skill_mem0 import recall

        aid = memory_agent_id(agent_id)
        memories = recall(query=task[:300], agent_id=aid)
        if not memories:
            return ""
        return (
            "\n\n─── LEÇONS APPRISES (à appliquer) ───\n"
            f"{memories}\n"
            "─── Ne répète pas les erreurs déjà documentées ───"
        )
    except Exception as exc:
        logger.debug("get_learning_context failed for %s: %s", agent_id, exc)
        return ""


def get_library_context(agent_id: str, task: str = "") -> str:
    """
    Topic catalog hits relevant to this agent/task — scannable, not truncated bodies.

    Agents see which subjects exist in the library and can deep-learn on demand.
    Strong / ``now`` matches trigger a one-shot ``learn_topic`` and inject the digest.
    """
    try:
        from services.bureau_library import bureau_for_agent
        from services.topic_catalog import search_topics_for_task

        bureau = bureau_for_agent(agent_id)
        hits = search_topics_for_task(task or "", bureau=bureau, limit=5)
        if not hits:
            # Fallback: recent bureau cards (titles only — full text lives in vault)
            from services.bureau_library import list_entries

            res = list_entries(bureau=bureau, limit=8)
            entries = list(res.get("entries", []))
            if not entries and bureau != "hub":
                hub_res = list_entries(bureau="hub", timing="now", limit=4)
                entries = list(hub_res.get("entries", []))
            if not entries:
                return ""
            lines = [
                f"- [{e.get('timing', 'later')}] {e.get('title', '')} "
                f"(sujets: {', '.join(str(t) for t in (e.get('topics') or [])[:4]) or 'n/a'})"
                for e in entries[:5]
            ]
            return (
                "\n\n─── BIBLIOTHÈQUE DU BUREAU (catalogue) ───\n"
                + "\n".join(lines)
                + "\n─── Utilise learn_topic(slug) pour charger le digest complet ───"
            )

        lines: list[str] = []
        deep_block = ""
        for row in hits:
            slug = row.get("slug", "")
            n = len(row.get("entry_ids") or [])
            now_flag = "now" if row.get("has_now") else "later"
            titles = "; ".join((row.get("titles") or [])[:2])
            lines.append(
                f"- [{now_flag}] `{slug}` ({n} fiches) — {titles}"
            )

        # Auto deep-learn the strongest now/hot hit once (non-blocking failure)
        top = hits[0]
        should_deep = bool(top.get("has_now")) or (
            task and top.get("slug") and str(top.get("slug")) in (task or "").lower().replace(" ", "-")
        )
        if should_deep and top.get("slug"):
            try:
                from skills.skill_library_memory import learn_topic

                learned = learn_topic(agent_id, str(top["slug"]), promote=True)
                if learned.get("ok") and learned.get("lesson"):
                    deep_block = (
                        f"\n─── DIGEST APPRIS (`{top.get('slug')}`) ───\n"
                        f"{str(learned['lesson'])[:2500]}\n"
                        "─── Fin digest ───"
                    )
                    try:
                        auto_compress_if_needed(agent_id)
                    except Exception:
                        pass
            except Exception as exc:
                logger.debug("auto learn_topic skipped: %s", exc)

        return (
            "\n\n─── CATALOGUE BIBLIOTHÈQUE (sujets disponibles) ───\n"
            + "\n".join(lines)
            + "\n─── Charge un sujet via learn_topic si besoin ───"
            + deep_block
        )
    except Exception as exc:
        logger.debug("get_library_context failed for %s: %s", agent_id, exc)
        return ""


def inject_learning_context(prompt: str, agent_id: str, task: str) -> str:
    """Injecte leçons Mem0 + catalogue bibliothèque (et digest si deep-learn) dans un prompt."""
    block = get_learning_context(agent_id, task)
    library = get_library_context(agent_id, task)
    extra = block + library
    return prompt + extra if extra else prompt


def record_task_learning(
    agent_id: str,
    task: str,
    outcome: str,
    *,
    success: bool | None = None,
) -> None:
    """Enregistre une leçon après tâche (succès auto-détecté si non fourni)."""
    learn_from_outcome(
        agent_id=agent_id,
        task=task,
        outcome=outcome,
        success=success if success is not None else not is_task_failure(outcome),
    )


def is_task_failure(outcome: str) -> bool:
    """Heuristique : détecte un échec dans la sortie texte d'un agent."""
    text = str(outcome).lower()
    return any(marker in text for marker in _FAILURE_MARKERS)


def _distill_lessons(agent_id: str, task: str, outcome: str, success: bool) -> str:
    """
    Appelle le LLM pour distiller 1-2 leçons concrètes depuis le résultat d'une tâche.
    Retourne une leçon en 2-3 phrases max.
    """
    lens = _get_lens(agent_id)
    status = "réussie" if success else "échouée"

    system = f"""{lens}
Après chaque tâche, tu distilles UNE leçon concrète et actionnable.
Réponds en 2-3 phrases max. Pas de bullet points. Pas d'intro.
Format : "[Leçon] Ce que j'ai appris et comment je l'appliquerai la prochaine fois."
Sois spécifique — pas de généralités."""

    user = f"""Tâche ({status}) : {task[:400]}

Résultat : {outcome[:600]}

Quelle est la leçon concrète à retenir pour être plus efficace la prochaine fois ?"""

    model = (LEARN_MODEL or "anthropic/claude-haiku-4-5").replace("openrouter/", "")
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 200,
    }).encode()

    req = urllib.request.Request(
        OPENROUTER_BASE,
        data=payload,
        headers={
            "Authorization": f"Bearer {_openrouter_api_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            content = data["choices"][0]["message"].get("content") or ""
            return content.strip()
    except Exception as exc:
        logger.warning("skill_agent_learning: LLM call failed: %s", exc)
        return ""


def learn_from_outcome(
    agent_id: str,
    task: str,
    outcome: str,
    success: bool = True,
    blocking: bool = False,
    tag: str = "",
) -> None:
    """
    Point d'entrée principal. À appeler après chaque tâche complétée.

    Args:
        agent_id : ID de l'agent qui apprend (ex: "marketing_agent")
        task     : Description de la tâche accomplie
        outcome  : Résultat obtenu (métriques, output, feedback)
        success  : True si la tâche a réussi, False si échouée
        blocking : False = daemon thread (ne bloque jamais l'agent)
        tag      : Marqueur optionnel (ex: "[learned:<entry_id>]") préfixé à la
                   leçon stockée, pour pouvoir la retrouver/vérifier plus tard
                   sans dépendre d'une recherche sémantique seule.

    L'apprentissage tourne en arrière-plan — l'agent n'attend pas.
    """
    canonical_id = memory_agent_id(agent_id)

    def _run():
        try:
            lesson = _distill_lessons(canonical_id, task, outcome, success)
            if not lesson:
                return

            from skills.skill_mem0 import remember
            date = datetime.now().strftime("%Y-%m-%d")
            status_tag = "✅" if success else "⚠️"
            prefix = f"{tag} " if tag else ""
            memory_entry = (
                f"{prefix}{status_tag} [{date}] Apprentissage {canonical_id} : {lesson}"
            )
            remember(memory_entry, agent_id=canonical_id)
            logger.info("skill_agent_learning: leçon enregistrée pour %s", canonical_id)

        except Exception as exc:
            logger.warning("skill_agent_learning: échec apprentissage %s: %s", agent_id, exc)

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


def learn_from_failure(agent_id: str, task: str, error: str) -> None:
    """Raccourci pour enregistrer un échec. L'agent apprend aussi de ses erreurs."""
    learn_from_outcome(
        agent_id=agent_id,
        task=task,
        outcome=f"ÉCHEC : {error}",
        success=False,
    )


# ---------------------------------------------------------------------------
# Session Compression — inspiré de claude-mem
# ---------------------------------------------------------------------------
# Quand un agent accumule trop de mémoires, on les compresse en un digest
# synthétique. Évite le bloat Mem0 et améliore la pertinence des leçons injectées.

_COMPRESS_SYSTEM = """Tu es un système de compression de mémoire pour un agent IA.
Tu reçois une liste de leçons apprises par un agent sur une période donnée.
Tu les synthétises en 3-5 règles comportementales durables, concises et actionnables.
Format : chaque règle commence par "→ " et tient en une phrase.
Pas d'intro. Pas de conclusion. Juste les règles."""


def compress_agent_memory(
    agent_id: str,
    raw_memories: list[str],
    blocking: bool = True,
) -> str | None:
    """
    Compresse une liste de mémoires brutes en un digest synthétique.
    Écrit le digest compressé dans Mem0 sous un tag spécial [DIGEST].

    Args:
        agent_id:    ID de l'agent
        raw_memories: Liste de leçons brutes récupérées depuis Mem0
        blocking:    True = attend la completion (défaut pour compression)

    Returns:
        Le digest compressé (string) ou None si erreur.
    """
    if not raw_memories:
        return None

    canonical_id = memory_agent_id(agent_id)
    memories_text = "\n".join(f"- {m}" for m in raw_memories[:50])  # cap 50

    payload = json.dumps({
        "model": LEARN_MODEL or "anthropic/claude-haiku-4-5",
        "messages": [
            {"role": "system", "content": _COMPRESS_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Agent : {canonical_id}\n"
                    f"Nombre de leçons : {len(raw_memories)}\n\n"
                    f"Leçons à synthétiser :\n{memories_text}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 300,
    }).encode()

    req = urllib.request.Request(
        OPENROUTER_BASE,
        data=payload,
        headers={
            "Authorization": f"Bearer {_openrouter_api_key()}",
            "Content-Type": "application/json",
        },
    )

    def _run() -> str | None:
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
                digest = data["choices"][0]["message"].get("content", "").strip()

            if not digest:
                return None

            # Écrire le digest dans Mem0 avec tag [DIGEST]
            try:
                from skills.skill_mem0 import remember
                date = datetime.now().strftime("%Y-%m-%d")
                remember(
                    f"[DIGEST {date}] Règles durables {canonical_id} :\n{digest}",
                    agent_id=canonical_id,
                )
                logger.info(
                    "skill_agent_learning: digest écrit pour %s (%d leçons → digest)",
                    canonical_id, len(raw_memories),
                )
            except Exception as exc:
                logger.warning("compress_agent_memory: Mem0 write failed: %s", exc)

            return digest
        except Exception as exc:
            logger.warning("compress_agent_memory: LLM call failed: %s", exc)
            return None

    if blocking:
        return _run()
    else:
        threading.Thread(target=_run, daemon=True).start()
        return None


def auto_compress_if_needed(
    agent_id: str,
    threshold: int = 20,
    blocking: bool = False,
) -> bool:
    """
    Vérifie si l'agent a trop de mémoires et compresse si nécessaire.
    Appelable en fin de session pour maintenir la base Mem0 propre.

    Args:
        agent_id:  ID de l'agent
        threshold: Nombre de mémoires avant compression (défaut: 20)
        blocking:  Attendre la compression ou non

    Returns:
        True si compression lancée, False si pas nécessaire.
    """
    try:
        from skills.skill_mem0 import recall

        canonical_id = memory_agent_id(agent_id)
        # Récupère un échantillon large pour compter
        raw = recall(query="leçons apprises", agent_id=canonical_id)
        if not raw:
            return False

        # Heuristique : si la réponse Mem0 dépasse 2000 chars, on compresse
        if len(str(raw)) < threshold * 80:
            return False

        memories = str(raw).split("\n") if isinstance(raw, str) else [str(raw)]
        compress_agent_memory(canonical_id, memories, blocking=blocking)
        return True

    except Exception as exc:
        logger.debug("auto_compress_if_needed failed for %s: %s", agent_id, exc)
        return False
