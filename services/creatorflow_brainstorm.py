"""CreatorFlow V1 — brainstorm chat, scripts, shot lists."""

from __future__ import annotations

import logging
from typing import Any

from agents.base import log_agent_action, parse_json_response
from database.supabase_client import SupabaseClient
from database.creatorflow_supabase_client import get_cf_supabase
from services.creatorflow_dna import build_dna_context_block
from services.creatorflow_ideas import get_cf_idea, update_cf_idea
from services.creatorflow_llm import cf_llm_chat
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)

AGENT_ID = "cf_idea_brainstorm"
_CF_MESSAGES = "cf_idea_messages"
_CF_ARTIFACTS = "cf_idea_artifacts"

BRAINSTORM_SYSTEM = """Tu es l'assistant créatif CreatorFlow pour créateurs solo.
Tu développes UNE idée de contenu à la fois, en respectant le Creator DNA fourni.
Réponds en français, concret, orienté action. Pas de généralités vagues."""

SCRIPT_SYSTEM = """Tu es scénariste CreatorFlow. Produis un script structuré pour créateur solo.
Réponds UNIQUEMENT en JSON valide sans markdown."""

SHOT_LIST_SYSTEM = """Tu es réalisateur CreatorFlow. Produis un plan de tournage shot-by-shot.
Réponds UNIQUEMENT en JSON valide sans markdown."""


def list_idea_messages(
    idea_id: str,
    user_id: str,
    db: SupabaseClient | None = None,
) -> list[dict[str, Any]]:
    db = db or get_cf_supabase()
    idea = get_cf_idea(idea_id, user_id, db)
    if not idea:
        return []
    return db.select(
        _CF_MESSAGES,
        filters={"idea_id": idea_id},
        order_by="created_at",
        ascending=True,
    )


def list_idea_artifacts(
    idea_id: str,
    user_id: str,
    artifact_type: str | None = None,
    db: SupabaseClient | None = None,
) -> list[dict[str, Any]]:
    db = db or get_cf_supabase()
    idea = get_cf_idea(idea_id, user_id, db)
    if not idea:
        return []
    filters: dict[str, Any] = {"idea_id": idea_id}
    if artifact_type:
        filters["artifact_type"] = artifact_type
    return db.select(
        _CF_ARTIFACTS,
        filters=filters,
        order_by="version",
        ascending=False,
    )


def _next_artifact_version(
    idea_id: str,
    artifact_type: str,
    db: SupabaseClient,
) -> int:
    rows = db.select(
        _CF_ARTIFACTS,
        filters={"idea_id": idea_id, "artifact_type": artifact_type},
        order_by="version",
        ascending=False,
        limit=1,
    )
    return (rows[0]["version"] + 1) if rows else 1


def _save_artifact(
    idea_id: str,
    user_id: str,
    artifact_type: str,
    content: dict[str, Any],
    db: SupabaseClient,
) -> dict[str, Any]:
    version = _next_artifact_version(idea_id, artifact_type, db)
    return db.insert(
        _CF_ARTIFACTS,
        {
            "idea_id": idea_id,
            "user_id": user_id,
            "artifact_type": artifact_type,
            "version": version,
            "content": content,
        },
    )


@trace_agent(AGENT_ID)
def brainstorm_on_idea(
    idea_id: str,
    user_id: str,
    user_message: str,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    idea = get_cf_idea(idea_id, user_id, db)
    if not idea:
        raise ValueError("Idée introuvable")

    db.insert(
        _CF_MESSAGES,
        {
            "idea_id": idea_id,
            "user_id": user_id,
            "role": "user",
            "content": user_message.strip(),
        },
    )

    history = list_idea_messages(idea_id, user_id, db)
    dna_block = build_dna_context_block(user_id, idea.get("project_id"))
    platform = idea.get("platform_target") or "both"

    context = (
        f"IDÉE:\nTitre: {idea.get('title')}\nContenu: {idea.get('content')}\n"
        f"Plateforme cible: {platform}\nTags: {', '.join(idea.get('tags') or [])}\n\n"
        f"{dna_block}"
    )

    messages: list[dict[str, str]] = [
        {"role": "user", "content": f"Contexte idée:\n{context}"},
    ]
    for msg in history[:-1]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message.strip()})

    try:
        reply = cf_llm_chat(user_id, BRAINSTORM_SYSTEM, messages, temperature=0.6, max_tokens=2000)
        source = "llm"
    except Exception as exc:
        logger.warning("cf brainstorm fallback: %s", exc)
        reply = (
            f"Voici comment développer « {idea.get('title')} » :\n"
            "1. Accroche en 3 secondes — question ou contraste fort\n"
            "2. Développement en 3 points maximum\n"
            "3. CTA clair (abonnement, commentaire, lien)\n\n"
            f"(Mode fallback — configure ta clé OpenRouter dans Paramètres IA : {exc})"
        )[:2000]
        source = "fallback"

    assistant_row = db.insert(
        _CF_MESSAGES,
        {
            "idea_id": idea_id,
            "user_id": user_id,
            "role": "assistant",
            "content": reply,
        },
    )

    if idea.get("status") == "spark":
        update_cf_idea(idea_id, user_id, {"status": "developing"}, db)

    log_agent_action(
        db,
        AGENT_ID,
        "brainstorm",
        idea.get("title", "")[:80],
        reply[:120],
    )

    return {
        "message": assistant_row,
        "source": source,
    }


@trace_agent(AGENT_ID)
def generate_script_for_idea(
    idea_id: str,
    user_id: str,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    idea = get_cf_idea(idea_id, user_id, db)
    if not idea:
        raise ValueError("Idée introuvable")

    dna_block = build_dna_context_block(user_id, idea.get("project_id"))
    messages = db.select(
        _CF_MESSAGES,
        filters={"idea_id": idea_id},
        order_by="created_at",
        ascending=True,
    )
    chat_summary = "\n".join(f"{m['role']}: {m['content'][:400]}" for m in messages[-6:])

    prompt = (
        f"Idée: {idea.get('title')}\n{idea.get('content')}\n\n{dna_block}\n\n"
        f"Brainstorm récent:\n{chat_summary or 'N/A'}\n\n"
        'JSON: {"title":"...","hook":"...","sections":[{"label":"...","script":"...","duration_sec":0}],'
        '"cta":"...","estimated_duration_sec":0,"platform_notes":"..."}'
    )

    try:
        raw = cf_llm_chat(user_id, SCRIPT_SYSTEM, [{"role": "user", "content": prompt}], temperature=0.4)
        content = parse_json_response(raw)
        source = "llm"
    except Exception as exc:
        logger.warning("cf script fallback: %s", exc)
        content = {
            "title": idea.get("title"),
            "hook": idea.get("content", "")[:120],
            "sections": [
                {"label": "Intro", "script": "Accroche + promesse", "duration_sec": 15},
                {"label": "Corps", "script": "3 points clés", "duration_sec": 120},
                {"label": "Outro", "script": "CTA", "duration_sec": 15},
            ],
            "cta": "Abonne-toi / commente",
            "estimated_duration_sec": 150,
            "platform_notes": "Adapter ratio selon plateforme",
            "source": "fallback",
        }
        source = "fallback"

    artifact = _save_artifact(idea_id, user_id, "script", content, db)
    update_cf_idea(idea_id, user_id, {"status": "ready_to_shoot"}, db)
    log_agent_action(db, AGENT_ID, "generate_script", idea.get("title", "")[:80], str(content)[:100])
    return {"artifact": artifact, "source": source}


@trace_agent(AGENT_ID)
def generate_shot_list_for_idea(
    idea_id: str,
    user_id: str,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    idea = get_cf_idea(idea_id, user_id, db)
    if not idea:
        raise ValueError("Idée introuvable")

    scripts = list_idea_artifacts(idea_id, user_id, "script", db)
    script_ctx = str(scripts[0]["content"])[:2000] if scripts else idea.get("content", "")
    dna_block = build_dna_context_block(user_id, idea.get("project_id"))

    prompt = (
        f"Idée: {idea.get('title')}\nScript:\n{script_ctx}\n\n{dna_block}\n\n"
        'JSON: {"shots":[{"number":1,"type":"A-roll|B-roll","description":"...",'
        '"duration_sec":0,"setup":"...","notes":"..."}],"gear":[],"location":"...",'
        '"estimated_shoot_minutes":0}'
    )

    try:
        raw = cf_llm_chat(user_id, SHOT_LIST_SYSTEM, [{"role": "user", "content": prompt}], temperature=0.35)
        content = parse_json_response(raw)
        source = "llm"
    except Exception as exc:
        logger.warning("cf shot_list fallback: %s", exc)
        content = {
            "shots": [
                {"number": 1, "type": "A-roll", "description": "Face cam — accroche", "duration_sec": 10, "setup": "Trépied", "notes": ""},
                {"number": 2, "type": "B-roll", "description": "Plans cutaway", "duration_sec": 30, "setup": "Main levée", "notes": ""},
                {"number": 3, "type": "A-roll", "description": "Conclusion + CTA", "duration_sec": 15, "setup": "Trépied", "notes": ""},
            ],
            "gear": ["Caméra", "Micro"],
            "location": "Intérieur lumière naturelle",
            "estimated_shoot_minutes": 45,
            "source": "fallback",
        }
        source = "fallback"

    artifact = _save_artifact(idea_id, user_id, "shot_list", content, db)
    log_agent_action(db, AGENT_ID, "generate_shot_list", idea.get("title", "")[:80], str(content)[:100])
    return {"artifact": artifact, "source": source}
