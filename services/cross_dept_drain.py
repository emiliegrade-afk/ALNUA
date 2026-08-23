"""Cross-dept drain — Phase 36 Depth+.

Turns queued fan-out items into real drafts (Camille / Rémi / Layla) and
writes artifacts under ``data/cross_dept_artifacts/``. No fabricated metrics.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from config.paths import get_hub_repo_path
from services.cross_dept_handlers import list_cross_dept_queue, update_queue_item
from services.input_sanitizer import sanitize_user_input

logger = logging.getLogger(__name__)

_ARTIFACTS = get_hub_repo_path() / "data" / "cross_dept_artifacts"


def _llm_enabled() -> bool:
    return os.getenv("CROSS_DEPT_DRAIN_LLM", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _write_artifact(item_id: str, action: str, payload: dict[str, Any]) -> str:
    _ARTIFACTS.mkdir(parents=True, exist_ok=True)
    path = _ARTIFACTS / f"{item_id}_{action}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def _title_of(item: dict[str, Any]) -> str:
    raw = str(item.get("title") or item.get("payload", {}).get("project_id") or "projet")
    return sanitize_user_input(raw, redact_pii_enabled=False)[:120]


def _exec_draft_launch_plan(item: dict[str, Any]) -> dict[str, Any]:
    title = _title_of(item)
    if not _llm_enabled():
        return {
            "kind": "launch_plan_skeleton",
            "project": title,
            "channels": ["organic_social", "email", "landing"],
            "note": "Skeleton only — CROSS_DEPT_DRAIN_LLM=0",
            "next_steps": [
                "Brief Camille pour plan détaillé",
                "Valider budget avec Rémi",
            ],
        }
    from agents.base import LLMClient, parse_json_response

    llm = LLMClient()
    prompt = (
        "Tu es Camille (Marketing ALNUA). Rédige un plan de lancement JSON pour "
        f"le projet « {title} ». Pas de métriques inventées (reach/ROI) — "
        "uniquement canaux, messages, séquence, owners. Schéma : "
        '{"project","objective","channels":[{"name","message","owner","week"}],'
        '"risks":[],"open_questions":[]}'
    )
    raw = llm.chat(
        [
            {"role": "system", "content": "Marketing ALNUA — JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=2048,
        agent_id="marketing",
    )
    data = parse_json_response(raw)
    if not isinstance(data, dict):
        data = {"project": title, "raw": str(raw)[:800]}
    data["kind"] = "launch_plan"
    return data


def _exec_budget_forecast(item: dict[str, Any]) -> dict[str, Any]:
    title = _title_of(item)
    if not _llm_enabled():
        return {
            "kind": "budget_forecast_skeleton",
            "project": title,
            "horizon_months": 6,
            "confidence": "low",
            "note": "Skeleton — CROSS_DEPT_DRAIN_LLM=0",
            "key_assumptions": ["À affiner avec dépenses réelles"],
        }
    from agents.controller_agent import ControllerAgent

    result = ControllerAgent().build_forecast(
        project=title,
        horizon_months=6,
        assumptions=(
            "Lancement produit ALNUA. Hypothèses conservatrices ; "
            "aucune métrique de marché inventée — marquer confidence low si doute."
        ),
        historical_data=None,
    )
    if isinstance(result, dict):
        result["kind"] = "budget_forecast"
        return result
    return {"kind": "budget_forecast", "project": title, "result": result}


def _exec_kpi_sheet(item: dict[str, Any]) -> dict[str, Any]:
    title = _title_of(item)
    if not _llm_enabled():
        return {
            "kind": "kpi_sheet_skeleton",
            "project": title,
            "stage": "pre-launch",
            "note": "Skeleton — CROSS_DEPT_DRAIN_LLM=0",
            "primary_kpis": [],
            "anti_metrics": ["Vanity reach sans baseline"],
        }
    from agents.analyst_business_agent import BusinessAnalystAgent

    result = BusinessAnalystAgent().define_kpis(
        project=title,
        stage="pre-launch",
        business_goal="Préparer un tableau KPI honnête avant lancement (pas de cibles inventées).",
    )
    if isinstance(result, dict):
        result["kind"] = "kpi_sheet"
        return result
    return {"kind": "kpi_sheet", "project": title, "result": result}


def _exec_checklist(item: dict[str, Any], checklist: list[str]) -> dict[str, Any]:
    """Non-LLM actions — honest checklists, no fake numbers."""
    return {
        "kind": "checklist",
        "action": item.get("action"),
        "project": _title_of(item),
        "checklist": checklist,
        "status": "ready_for_human",
    }


_ACTION_HANDLERS: dict[str, Any] = {
    "draft_launch_plan": _exec_draft_launch_plan,
    "draft_budget_forecast": _exec_budget_forecast,
    "prepare_kpi_sheet": _exec_kpi_sheet,
    "schedule_distribution": lambda item: _exec_checklist(
        item,
        [
            "Choisir créneaux publication",
            "Assigner Content sectoriel",
            "Lier posts_queue si campagne existante",
        ],
    ),
    "track_content_performance": lambda item: _exec_checklist(
        item,
        [
            "Saisir reach/engagements réels post-publication",
            "Pas de % inventé sans audience totale",
        ],
    ),
    "link_campaign_budget": lambda item: _exec_checklist(
        item,
        [
            "Lier campaign_id au ledger budgets",
            "Vérifier spent_usd réel avant ROI",
        ],
    ),
    "prepare_campaign_kpis": lambda item: _exec_checklist(
        item,
        [
            "Définir KPIs campagne mesurables",
            "Attendre stats manuelles plateformes",
        ],
    ),
}


def execute_item(item: dict[str, Any]) -> dict[str, Any]:
    item_id = str(item.get("id") or "")
    action = str(item.get("action") or "")
    if not item_id:
        return {"ok": False, "error": "missing_id"}
    if item.get("status") not in (None, "queued", "failed"):
        return {"ok": False, "error": "not_runnable", "status": item.get("status")}

    update_queue_item(item_id, {"status": "running"})
    handler = _ACTION_HANDLERS.get(action)
    if handler is None:
        update_queue_item(
            item_id,
            {"status": "failed", "result_summary": f"Unknown action: {action}"},
        )
        return {"ok": False, "id": item_id, "error": "unknown_action"}

    try:
        artifact = handler(item)
        path = _write_artifact(item_id, action, artifact if isinstance(artifact, dict) else {"data": artifact})
        summary = str(artifact.get("kind") or action)[:80] if isinstance(artifact, dict) else action
        updated = update_queue_item(
            item_id,
            {
                "status": "done",
                "result_summary": summary,
                "artifact_path": path,
            },
        )
        return {"ok": True, "id": item_id, "item": updated, "artifact_path": path}
    except Exception as exc:
        logger.exception("cross_dept drain failed id=%s action=%s", item_id, action)
        update_queue_item(
            item_id,
            {"status": "failed", "result_summary": str(exc)[:200]},
        )
        return {"ok": False, "id": item_id, "error": str(exc)[:200]}


def drain_cross_dept_queue(*, limit: int = 3, item_ids: list[str] | None = None) -> dict[str, Any]:
    """Execute up to ``limit`` queued items (FIFO among pending)."""
    limit = max(1, min(int(limit), 10))
    if item_ids:
        from services.cross_dept_handlers import get_queue_item

        pending = [get_queue_item(i) for i in item_ids]
        pending = [p for p in pending if p and p.get("status") == "queued"]
    else:
        # list is newest-first — reverse for FIFO drain
        pending = list(reversed(list_cross_dept_queue(limit=100, status="queued")))[:limit]

    results = [execute_item(item) for item in pending[:limit]]
    return {
        "processed": len(results),
        "ok": sum(1 for r in results if r.get("ok")),
        "failed": sum(1 for r in results if not r.get("ok")),
        "results": results,
        "llm_enabled": _llm_enabled(),
    }


def emit_project_validated(
    *,
    title: str,
    project_id: str | None = None,
    source_agent: str = "ceo",
) -> dict[str, Any]:
    """CEO / Hub trigger — emit event so handlers enqueue Marketing/Finance/Analytics."""
    from services.event_bus import emit

    safe_title = sanitize_user_input(title, redact_pii_enabled=False)[:120]
    payload: dict[str, Any] = {"title": safe_title}
    if project_id:
        payload["project_id"] = sanitize_user_input(project_id, redact_pii_enabled=False)[:64]
    # Sync handlers so the response includes the freshly queued items.
    event = emit(
        "project_validated",
        payload=payload,
        source_agent=source_agent[:64],
        async_handlers=False,
    )
    return {
        "emitted": True,
        "event_id": event.event_id,
        "queued": list_cross_dept_queue(limit=9, status="queued"),
    }
