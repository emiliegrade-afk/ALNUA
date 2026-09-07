"""Brand voice debate — Élise (brand) ↔ Anouk (content_company).

Phase 35 Depth+: two-persona LLM deliberation on copy/artefacts.
Structural coherence always runs first; LLM rounds degrade silently on failure.
"""

from __future__ import annotations

from typing import Any

from services.input_sanitizer import sanitize_user_input


def debate_brand_voice(
    text: str,
    *,
    department: str = "",
    sector: str = "",
    rounds: int = 1,
) -> dict[str, Any]:
    """
    Returns structural review + optional Élise/Anouk debate.

    Always includes ``structural`` (brand_design_system). LLM debate is best-effort.
    """
    from services.brand_design_system import review_brand_coherence

    clean = sanitize_user_input(text, max_length=8000, redact_pii_enabled=False)
    dept = sanitize_user_input(department, max_length=64)
    sect = sanitize_user_input(sector, max_length=64)
    structural = review_brand_coherence(clean, sector=sect, department=dept)

    result: dict[str, Any] = {
        "ok": bool(structural.get("ok")),
        "recommendation": structural.get("recommendation", "revise"),
        "structural": structural,
        "deliberated": False,
        "mode": "structural_only",
        "rounds": [],
        "debate": None,
    }

    n = max(1, min(int(rounds or 1), 2))
    debate = _run_elise_anouk(clean, dept=dept, sect=sect, structural=structural, rounds=n)
    if not debate:
        return result

    result["deliberated"] = True
    result["mode"] = "elise_anouk"
    result["rounds"] = debate.get("rounds") or []
    result["debate"] = debate.get("consensus")
    verdict = str((debate.get("consensus") or {}).get("verdict") or "").lower()
    if verdict == "approve" and structural.get("ok"):
        result["ok"] = True
        result["recommendation"] = "approve"
    elif verdict == "revise" or not structural.get("ok"):
        result["ok"] = False
        result["recommendation"] = "revise"
    return result


def _run_elise_anouk(
    text: str,
    *,
    dept: str,
    sect: str,
    structural: dict[str, Any],
    rounds: int,
) -> dict[str, Any] | None:
    try:
        from agents.base import LLMClient, parse_json_response
        from config.agent_personas import persona_prompt_intro
    except Exception:
        return None

    llm = LLMClient()
    flags = structural.get("flags") or []
    preview = str(structural.get("preview") or text[:400])
    history: list[dict[str, Any]] = []
    anouk_note = ""

    for i in range(rounds):
        elise_system = (
            f"{persona_prompt_intro('brand', role='Brand Design')}. "
            "Tu es Élise Mercier. Juge cohérence visuelle/marque ALNUA. "
            "JSON uniquement."
        )
        elise_prompt = f"""Tour {i + 1}/{rounds}
Département: {dept or "—"} · Secteur: {sect or "—"}
Flags structurels: {flags}
Texte:
\"\"\"{preview}\"\"\"
{f"Réponse Anouk précédente: {anouk_note}" if anouk_note else ""}

Réponds:
{{"stance":"approve|revise","concerns":["…"],"asks":["…"],"summary":"1 phrase"}}"""
        try:
            raw_e = llm.complete(
                elise_system,
                elise_prompt,
                agent_id="brand",
                temperature=0.25,
                method_name="brand_voice_debate",
            )
            elise = parse_json_response(raw_e)
            if not isinstance(elise, dict):
                elise = {"stance": "revise", "summary": "parse_error", "concerns": []}
        except Exception:
            return None
        history.append({"round": i + 1, "agent": "brand", "name": "Élise", "payload": elise})

        anouk_system = (
            f"{persona_prompt_intro('content_company', role='Brand Voice')}. "
            "Tu es Anouk Gerard. Juge ton/voix ALNUA (anti-slop). JSON uniquement."
        )
        anouk_prompt = f"""Tour {i + 1}/{rounds}
Département: {dept or "—"} · Secteur: {sect or "—"}
Avis Élise: {elise}
Texte:
\"\"\"{preview}\"\"\"

Réponds:
{{"stance":"approve|revise","voice_notes":["…"],"rewrite_hint":"…","summary":"1 phrase"}}"""
        try:
            raw_a = llm.complete(
                anouk_system,
                anouk_prompt,
                agent_id="content_company",
                temperature=0.25,
                method_name="brand_voice_debate",
            )
            anouk = parse_json_response(raw_a)
            if not isinstance(anouk, dict):
                anouk = {"stance": "revise", "summary": "parse_error", "voice_notes": []}
        except Exception:
            return None
        anouk_note = str(anouk.get("summary") or "")[:300]
        history.append(
            {"round": i + 1, "agent": "content_company", "name": "Anouk", "payload": anouk}
        )

    e_ok = str((history[-2].get("payload") or {}).get("stance") or "").lower() == "approve"
    a_ok = str((history[-1].get("payload") or {}).get("stance") or "").lower() == "approve"
    verdict = "approve" if e_ok and a_ok and structural.get("ok") else "revise"
    consensus = {
        "verdict": verdict,
        "elise": (history[-2].get("payload") or {}).get("summary"),
        "anouk": (history[-1].get("payload") or {}).get("summary"),
        "dissent": [] if e_ok == a_ok else ["Élise et Anouk divergent"],
        "actions": ["Publier" if verdict == "approve" else "Réviser avant publication"],
    }
    return {"rounds": history, "consensus": consensus}
