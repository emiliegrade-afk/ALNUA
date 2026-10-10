"""Idle recipes — idle_plan_day / idle_drain (DEC-021, Phase 39)."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from typing import Any

from config.paths import get_hub_repo_path
from services.workflow_engine_models import WorkflowRecipe, WorkflowStepDef

logger = logging.getLogger(__name__)

_DELIVERABLES = get_hub_repo_path() / "data" / "idle_deliverables"

IDLE_RECIPES: list[WorkflowRecipe] = [
    WorkflowRecipe(
        id="idle_plan_day",
        name="Idle — file du jour (COO)",
        description="Budget check + construction file L0–L2 (CEO valide pour L2).",
        head_agent="coo",
        priority="P1",
        steps=[
            WorkflowStepDef(id="idle_check_budget", label="Budget LLM adaptatif", head_agent="coo"),
            WorkflowStepDef(id="idle_build_queue", label="Construire file du jour", head_agent="coo"),
        ],
    ),
    WorkflowRecipe(
        id="idle_drain",
        name="Idle — drain prochain item",
        description="Exécute 1–N items éligibles (trust / CEO / budget).",
        head_agent="coo",
        priority="P1",
        steps=[
            WorkflowStepDef(id="idle_check_budget", label="Budget LLM adaptatif", head_agent="coo"),
            WorkflowStepDef(id="idle_pick_item", label="Sélectionner item éligible", head_agent="coo"),
            WorkflowStepDef(id="idle_execute_item", label="Exécuter item", head_agent="coo"),
        ],
    ),
]


def _step_idle_check_budget(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.idle_work_queue import budget_severity

    alert = budget_severity(daily_budget_usd=ctx.get("daily_budget_usd"))
    severity = str(alert.get("severity") or "ok")
    ctx["_idle_budget"] = alert
    if severity == "critical" and ctx.get("_recipe_id") == "idle_drain":
        return {
            "status": "ECART",
            "detail": f"Budget critical — idle drain stop ({alert.get('pct_used')}%)",
            "result": alert,
            "gaps": ["budget.critical"],
        }
    status = "A_VERIFIER" if severity == "warning" else "OK"
    return {
        "status": status,
        "detail": f"Budget {severity} — {alert.get('spent_usd')} / {alert.get('daily_budget_usd')} USD",
        "result": alert,
    }


def _step_idle_build_queue(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.autonomy_resolver import resolve_idle_autonomy_level
    from services.idle_work_queue import build_day_plan, clamp_autonomy

    if ctx.get("autonomy_level") is not None:
        autonomy = clamp_autonomy(ctx["autonomy_level"])
    else:
        agent_id = str(ctx.get("agent_id") or "coo")
        autonomy = resolve_idle_autonomy_level(agent_id)
        ctx["autonomy_level"] = autonomy
    queue = build_day_plan(autonomy_level=autonomy)
    return {
        "status": "OK",
        "detail": f"File {queue['date']} — {len(queue.get('items') or [])} items (L2 gated)",
        "result": {
            "date": queue["date"],
            "item_count": len(queue.get("items") or []),
            "ceo_validated": queue.get("ceo_validated"),
            "autonomy_level": autonomy,
        },
    }


def _step_idle_pick_item(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.idle_work_queue import pick_next_item

    try:
        from config.settings import settings

        max_items = int(getattr(settings, "idle_max_items_per_drain", 1) or 1)
    except Exception:
        max_items = 1
    max_items = max(1, min(int(ctx.get("max_items") or max_items), 3))

    picked = pick_next_item(max_items=max_items)
    ctx["_idle_picked"] = picked
    if not picked.get("ok"):
        return {
            "status": "A_VERIFIER",
            "detail": f"Rien à drain — {picked.get('reason')}",
            "result": picked,
        }
    titles = [i.get("title") for i in picked.get("items") or []]
    return {
        "status": "OK",
        "detail": f"Picked {len(titles)}: {', '.join(str(t) for t in titles)[:200]}",
        "result": picked,
    }


def _write_deliverable(item: dict[str, Any], body: dict[str, Any]) -> str:
    _DELIVERABLES.mkdir(parents=True, exist_ok=True)
    path = _DELIVERABLES / f"{item.get('id')}.json"
    path.write_text(
        json.dumps(
            {
                "item": item,
                "body": body,
                "written_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return str(path)


def _execute_one(item: dict[str, Any], run_id: str | None) -> dict[str, Any]:
    from services.idle_work_queue import mark_item

    kind = str(item.get("kind") or "")
    agent_id = str(item.get("agent_id") or "coo")
    detail = ""
    path = ""

    if kind == "ops_snapshot":
        try:
            from services.workflow_engine import run_workflow

            snap = run_workflow("run_ops", {"auto_remediate": False, "branch": None})
            path = _write_deliverable(item, {"ops": snap.get("summary"), "run_id": snap.get("run_id")})
            detail = f"ops snapshot → {path}"
        except Exception as exc:
            mark_item(item["id"], status="error", run_id=run_id, detail=str(exc)[:300])
            return {"ok": False, "detail": str(exc)[:300]}

    elif kind == "cost_snapshot":
        from services.idle_work_queue import budget_severity

        alert = budget_severity()
        path = _write_deliverable(item, {"budget": alert})
        detail = f"budget {alert.get('severity')} → {path}"

    elif kind in {"company_draft", "product_triage"}:
        try:
            from services.idle_work_execute_l1 import execute_l1_item

            body = execute_l1_item(item)
            path = _write_deliverable(item, body)
            detail = f"draft L1 LLM ({kind}) → {path}"
        except Exception as exc:
            logger.exception("idle L1 %s failed", kind)
            path = _write_deliverable(
                item,
                {
                    "status": "draft_error",
                    "error": str(exc)[:300],
                    "title": item.get("title"),
                    "payload": item.get("payload") or {},
                },
            )
            detail = f"draft L1 soft-fail → {path}"

    elif kind == "academy_wake":
        try:
            from services.agent_wake import queue_academy_if_idle

            result = queue_academy_if_idle()
            path = _write_deliverable(item, result)
            detail = f"academy {result.get('reason')} marked={result.get('marked_count')}"
        except Exception as exc:
            mark_item(item["id"], status="error", run_id=run_id, detail=str(exc)[:300])
            return {"ok": False, "detail": str(exc)[:300]}

    elif kind.endswith("_academy_exercise"):
        # Generic studio-academy dispatch (DEC-036): gaming, robo, comms…
        # The program registry maps the kind prefix to its runner module.
        program_id = kind[: -len("_academy_exercise")]
        try:
            import importlib

            from services.studio_academy_program import get_program

            runner = importlib.import_module(get_program(program_id).runner_module)
            result = runner.run_next_exercise()
            path = _write_deliverable(item, result)
            ref = result.get("exercise_id") or result.get("reason") or "?"
            detail = f"{program_id} academy {ref} → {result.get('status', 'done')} → {path}"
        except Exception as exc:
            mark_item(item["id"], status="error", run_id=run_id, detail=str(exc)[:300])
            return {"ok": False, "detail": str(exc)[:300]}

    elif kind == "self_dev":
        try:
            from skills.skill_agent_learning import auto_compress_if_needed

            result = auto_compress_if_needed(agent_id, threshold=20)
            path = _write_deliverable(item, {"compress": result})
            detail = f"self_dev {agent_id} → {path}"
        except Exception as exc:
            # Soft fail — still mark done with note
            path = _write_deliverable(item, {"error": str(exc)[:300]})
            detail = f"self_dev soft-fail {agent_id}"

    elif kind == "lounge_session":
        try:
            from services.lounge_activities.catalog import ACTIVITY_IDS
            from services.lounge_runtime import run_session_with_llm, start_session

            payload = item.get("payload") or {}
            puzzle_id = payload.get("puzzle_id") or payload.get("challenge_id")
            activity = str(payload.get("activity") or "").strip()
            if isinstance(puzzle_id, str) and puzzle_id.strip():
                activity = activity or "puzzle"
                session = start_session(agent_id, activity, puzzle_id.strip())
            else:
                if activity not in ACTIVITY_IDS:
                    activity = ACTIVITY_IDS[date.today().toordinal() % len(ACTIVITY_IDS)]
                session = start_session(agent_id, activity)
            try:
                done = run_session_with_llm(session["id"])
            except Exception as llm_exc:
                logger.warning(
                    "idle lounge_session LLM failed agent=%s: %s",
                    agent_id,
                    llm_exc,
                )
                done = {
                    **session,
                    "status": "active",
                    "llm_error": str(llm_exc)[:200],
                }
            path = _write_deliverable(
                item,
                {
                    "session": done,
                    "model_policy": "lounge_cn_cheap",
                },
            )
            detail = (
                f"lounge {done.get('status')} won={done.get('won')} "
                f"xp={done.get('points_awarded')} → {path}"
            )
        except Exception as exc:
            logger.exception("idle lounge_session failed")
            path = _write_deliverable(item, {"error": str(exc)[:300]})
            detail = f"lounge soft-fail {agent_id}"

    else:
        detail = f"kind {kind} not implemented"
        mark_item(item["id"], status="error", run_id=run_id, detail=detail)
        return {
            "ok": False,
            "detail": detail,
            "agent_id": agent_id,
            "item_id": item.get("id"),
        }

    mark_item(item["id"], status="done", run_id=run_id, detail=detail)
    return {"ok": True, "detail": detail, "path": path, "agent_id": agent_id, "item_id": item.get("id")}


def _step_idle_execute_item(ctx: dict[str, Any], prior_steps: list[Any]) -> dict[str, Any]:
    picked = ctx.get("_idle_picked") or {}
    items = list(picked.get("items") or [])
    if not items:
        return {
            "status": "A_VERIFIER",
            "detail": "Aucun item à exécuter",
            "result": picked,
        }

    run_id = str(ctx.get("_run_id") or "") or None
    results = [_execute_one(item, run_id) for item in items]
    ok_n = sum(1 for r in results if r.get("ok"))
    # Expose for OpenRoom overlay
    ctx["_idle_agent_ids"] = [r.get("agent_id") for r in results if r.get("agent_id")]
    ctx["_idle_item_ids"] = [r.get("item_id") for r in results if r.get("item_id")]
    return {
        "status": "OK" if ok_n else "ECART",
        "detail": f"{ok_n}/{len(results)} item(s) exécutés",
        "result": {"executed": results},
        "gaps": [] if ok_n else ["idle.execute_failed"],
    }


_IDLE_HANDLERS = {
    "idle_check_budget": _step_idle_check_budget,
    "idle_build_queue": _step_idle_build_queue,
    "idle_pick_item": _step_idle_pick_item,
    "idle_execute_item": _step_idle_execute_item,
}


def register_idle_recipes() -> None:
    from services.workflow_engine_catalog import RECIPE_CATALOG
    from services.workflow_engine_handlers import _STEP_HANDLERS

    existing = {r.id for r in RECIPE_CATALOG}
    for recipe in IDLE_RECIPES:
        if recipe.id not in existing:
            RECIPE_CATALOG.append(recipe)
    _STEP_HANDLERS.update(_IDLE_HANDLERS)
    logger.info("Idle recipes registered: %s", [r.id for r in IDLE_RECIPES])
