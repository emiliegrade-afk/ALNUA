"""Academy → Lounge readiness gate — critères formation dev_app (Phase 5/6)."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

GATE_DEFINITIONS: list[dict[str, Any]] = [
    {
        "id": "success_rate_65",
        "label": "Taux succès académie ≥ 65%",
        "critical": True,
        "phase": 5,
    },
    {
        "id": "academy_n4_stable",
        "label": "Niveau 4 académie stable (0 échec)",
        "critical": True,
        "phase": 5,
    },
    {
        "id": "mem0_lessons_35",
        "label": "Mem0 dev_app enrichi (leçons coding)",
        "critical": True,
        "phase": 5,
    },
    {
        "id": "error_journal_top5",
        "label": "≥ 5 erreurs coding résolues documentées",
        "critical": True,
        "phase": 5,
    },
    {
        "id": "github_pipeline",
        "label": "Pipeline Academy (Aider + GitHub) actif",
        "critical": True,
        "phase": 5,
    },
    {
        "id": "prd_build_manifest",
        "label": "Build manifest Lounge (optionnel)",
        "critical": False,
        "phase": 6,
    },
    {
        "id": "sentry_ops",
        "label": "Ops production Sentry actif",
        "critical": False,
        "phase": 6,
    },
    {
        "id": "lounge_product_ready",
        "label": "Dossier produit Lounge/arcade défini",
        "critical": False,
        "phase": 6,
    },
]


def _count_resolved_errors() -> int:
    total = 0
    try:
        from database.supabase_client import get_supabase

        db = get_supabase()
        result = (
            db.raw.table("agent_error_journal")
            .select("id", count="exact")
            .eq("status", "resolved")
            .not_.is_("solution", "null")
            .execute()
        )
        total += int(result.count or 0)
    except Exception as exc:
        logger.warning("error journal count failed: %s", exc)
    try:
        from services.coding_error_journal import count_resolved

        total += count_resolved()
    except Exception:
        pass
    return total


def _academy_pipeline_ok() -> bool:
    from config.github_repos import get_target_by_slug, pipeline_enabled

    if not pipeline_enabled():
        return False
    target = get_target_by_slug("academy")
    if not target:
        return False
    local = os.getenv("REPO_PATH_ACADEMY", "").strip()
    if local and not Path(local).is_dir():
        return False
    return bool(target.github_repo)


def _lounge_product_ready() -> bool:
    path = Path(__file__).resolve().parent.parent / "data" / "lounge_product.json"
    if not path.is_file():
        return False
    try:
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        return bool(data.get("mvp_features")) and data.get("status") in (
            "scaffold",
            "active",
            "live",
        )
    except Exception:
        return False


def _mem0_lesson_count() -> int:
    try:
        from skills.skill_mem0 import recall

        text = recall(query="dev_app lessons patterns fixes academy", agent_id="dev_app") or ""
        return max(0, len(text) // 40)
    except Exception:
        return 0


def _lounge_build_manifest() -> dict[str, Any]:
    for slug in ("lounge", "alnua-lounge", "academy"):
        try:
            from services.prd_issues import read_build_manifest

            data = read_build_manifest(slug)
            if data:
                return {"slug": slug, **data}
        except Exception:
            continue
    return {}


def _ceo_lounge_dossier() -> dict[str, Any] | None:
    try:
        from database.supabase_client import get_supabase

        db = get_supabase()
        rows = db.select(
            "rnd_dossiers",
            order_by="updated_at",
            ascending=False,
            limit=30,
        )
        for row in rows or []:
            hay = f"{row.get('slug','')} {row.get('title','')}".lower()
            if any(k in hay for k in ("lounge", "arcade", "academy")):
                pkg = row.get("ceo_package_json") or {}
                return {
                    "id": row.get("id"),
                    "slug": row.get("slug"),
                    "title": row.get("title"),
                    "ceo_status": row.get("ceo_status"),
                    "ceo_package_json": pkg if isinstance(pkg, dict) else {},
                    "has_engineering_spec": bool(
                        isinstance(pkg, dict) and pkg.get("engineering_spec")
                    ),
                }
    except Exception as exc:
        logger.warning("ceo dossier lookup failed: %s", exc)
    return None


def _sentry_ops_active() -> bool:
    try:
        from services.sentry_ops import _load_dedup

        dedup = _load_dedup()
        return bool(dedup.get("fingerprints") or dedup.get("recent"))
    except Exception:
        return False


def evaluate_academy_gate(*, refresh_academy: bool = True) -> dict[str, Any]:
    """Evaluate Academy → Lounge gate criteria and overall readiness."""
    academy: dict[str, Any] = {}
    if refresh_academy:
        try:
            from services.academy_progress import get_academy_status

            academy = get_academy_status()
        except Exception as exc:
            academy = {"error": str(exc)[:200]}
    else:
        from services.academy_progress import load_progress

        academy = {"progress": load_progress()}

    progress = academy.get("progress") or {}
    gate_base = dict(progress.get("gate_academy") or progress.get("gate_nuaway") or {})

    resolved_count = _count_resolved_errors()
    mem0_count = _mem0_lesson_count()
    build = _lounge_build_manifest()
    ceo_doc = _ceo_lounge_dossier()

    from config.github_repos import get_target_by_slug

    academy_target = get_target_by_slug("academy")
    github_ok = _academy_pipeline_ok()

    checks: dict[str, bool] = {
        "success_rate_65": bool(gate_base.get("success_rate_65")),
        "academy_n4_stable": bool(gate_base.get("academy_n4_stable")),
        "mem0_lessons_35": mem0_count >= 35 or bool(gate_base.get("mem0_lessons_35")),
        "error_journal_top5": resolved_count >= 5,
        "github_pipeline": github_ok,
        "prd_build_manifest": int(build.get("issues_created") or 0) > 0,
        "sentry_ops": _sentry_ops_active(),
        "lounge_product_ready": _lounge_product_ready(),
    }

    criteria: list[dict[str, Any]] = []
    passed = 0
    critical_passed = 0
    critical_total = 0

    for defn in GATE_DEFINITIONS:
        gid = defn["id"]
        ok = checks.get(gid, False)
        criteria.append({**defn, "passed": ok})
        if ok:
            passed += 1
        if defn.get("critical"):
            critical_total += 1
            if ok:
                critical_passed += 1

    total = len(GATE_DEFINITIONS)
    readiness_pct = round(100.0 * passed / total, 1) if total else 0.0
    gate_open = critical_passed == critical_total and critical_total > 0

    try:
        from services.academy_progress import load_progress, save_progress

        prog = load_progress()
        prog["gate_academy"] = {**checks, "gate_open": gate_open, "readiness_pct": readiness_pct}
        prog.pop("gate_nuaway", None)
        prog["gate_evaluated_at"] = datetime.now(timezone.utc).isoformat()
        save_progress(prog)
    except Exception:
        pass

    return {
        "gate_open": gate_open,
        "readiness_pct": readiness_pct,
        "passed": passed,
        "total": total,
        "critical_passed": critical_passed,
        "critical_total": critical_total,
        "criteria": criteria,
        "metrics": {
            "success_rate_pct": progress.get("success_rate_pct", 0),
            "completed_exercises": progress.get("completed_exercises", 0),
            "current_level": progress.get("current_level", 1),
            "resolved_errors": resolved_count,
            "mem0_lesson_estimate": mem0_count,
            "build_issues_created": int(build.get("issues_created") or 0),
            "github_repo": academy_target.github_repo if academy_target else None,
        },
        "ceo_dossier": ceo_doc,
        "build_manifest_slug": build.get("slug"),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
