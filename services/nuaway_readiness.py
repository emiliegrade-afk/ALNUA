"""NUAWAY beta readiness — Phase 6 checklist + rapport CEO."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
READINESS_PATH = _PROJECT_ROOT / "data" / "nuaway_readiness.json"

BETA_LAUNCH_CHECKLIST: list[dict[str, Any]] = [
    {
        "id": "agents_gate_open",
        "label": "Gate agents ouverte (critères Phase 5)",
        "critical": True,
        "category": "agents",
    },
    {
        "id": "academy_n4_complete",
        "label": "Académie N4 terminée (0 échec)",
        "critical": True,
        "category": "agents",
    },
    {
        "id": "engineering_spec_validated",
        "label": "PRD §10 validé (spec + QA)",
        "critical": True,
        "category": "product",
    },
    {
        "id": "nomad_repo_local",
        "label": "Repo NUAWAY cloné localement",
        "critical": True,
        "category": "infra",
    },
    {
        "id": "sentry_e2e_tested",
        "label": "Pipeline Sentry testé (≥1 ingest)",
        "critical": True,
        "category": "ops",
    },
    {
        "id": "build_manifest_ready",
        "label": "Issues PRD créées sur GitHub",
        "critical": False,
        "category": "product",
    },
    {
        "id": "beta_portal_configured",
        "label": "Portail beta configuré",
        "critical": False,
        "category": "infra",
    },
    {
        "id": "ceo_beta_go",
        "label": "Go/no-go CEO enregistré",
        "critical": True,
        "category": "ceo",
    },
]


def _default_state() -> dict[str, Any]:
    return {
        "version": 1,
        "ceo_beta_go": False,
        "ceo_beta_note": "",
        "ceo_beta_at": None,
        "last_report_at": None,
        "last_report_headline": "",
    }


def load_readiness_state() -> dict[str, Any]:
    if not READINESS_PATH.is_file():
        return _default_state()
    try:
        data = json.loads(READINESS_PATH.read_text(encoding="utf-8"))
        base = _default_state()
        base.update(data if isinstance(data, dict) else {})
        return base
    except Exception as exc:
        logger.warning("readiness state load failed: %s", exc)
        return _default_state()


def save_readiness_state(state: dict[str, Any]) -> None:
    READINESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    READINESS_PATH.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def set_ceo_beta_go(*, approved: bool, note: str = "") -> dict[str, Any]:
    state = load_readiness_state()
    state["ceo_beta_go"] = approved
    state["ceo_beta_note"] = note.strip()[:500]
    state["ceo_beta_at"] = datetime.now(timezone.utc).isoformat()
    save_readiness_state(state)
    return evaluate_beta_readiness(refresh_gate=True)


def _nomad_local_path() -> Path | None:
    try:
        from config.github_repos import get_target_by_slug

        target = get_target_by_slug("nomad")
        if target:
            return target.local_path
    except Exception:
        pass
    raw = os.getenv("REPO_PATH_NOMAD", "").strip()
    return Path(raw) if raw else None


def _engineering_spec_ok(ceo_doc: dict[str, Any] | None) -> bool:
    if not ceo_doc:
        return False
    pkg = ceo_doc.get("ceo_package_json") or {}
    if not isinstance(pkg, dict):
        return False
    spec = pkg.get("engineering_spec") or {}
    if not isinstance(spec, dict):
        return False
    tasks = spec.get("task_breakdown") or []
    if not tasks:
        return False
    verdict = str(spec.get("qa_verdict") or "").lower()
    if verdict in ("approve", "approved", "converged", "ok"):
        return True
    return ceo_doc.get("ceo_status") == "approved" and len(tasks) >= 5


def _beta_portal_ok() -> bool:
    try:
        from database.supabase_client import get_supabase

        db = get_supabase()
        for slug in ("nuaway", "nomad", "NUAWAY"):
            rows = db.select("projects", filters={"slug": slug}, limit=1)
            if rows:
                return True
    except Exception:
        pass
    return bool(os.getenv("BETA_PORTAL_BASE_URL", "").strip())


def evaluate_beta_readiness(*, refresh_gate: bool = True) -> dict[str, Any]:
    """Checklist beta formelle — agents + infra + produit + go CEO."""
    from services.nuaway_gate import evaluate_nuaway_gate

    gate = evaluate_nuaway_gate(refresh_academy=refresh_gate)
    state = load_readiness_state()
    ceo_doc = gate.get("ceo_dossier") or {}
    metrics = gate.get("metrics") or {}

    local_path = _nomad_local_path()
    local_ok = bool(local_path and local_path.is_dir())

    try:
        from services.academy_progress import load_progress

        prog = load_progress()
        lv4 = (prog.get("levels") or {}).get("4") or {}
        n4_complete = (
            int(lv4.get("done") or 0) >= int(lv4.get("total") or 20)
            and int(lv4.get("failed") or 0) == 0
        )
    except Exception:
        n4_complete = False

    sentry_count = 0
    try:
        from services.sentry_ops import _load_dedup

        dedup = _load_dedup()
        sentry_count = len(dedup.get("recent") or dedup.get("fingerprints") or {})
    except Exception:
        sentry_count = 0

    checks: dict[str, bool] = {
        "agents_gate_open": bool(gate.get("gate_open")),
        "academy_n4_complete": n4_complete,
        "engineering_spec_validated": _engineering_spec_ok(ceo_doc if isinstance(ceo_doc, dict) else None),
        "nomad_repo_local": local_ok,
        "sentry_e2e_tested": sentry_count > 0,
        "build_manifest_ready": int(metrics.get("build_issues_created") or 0) > 0,
        "beta_portal_configured": _beta_portal_ok(),
        "ceo_beta_go": bool(state.get("ceo_beta_go")),
    }

    criteria: list[dict[str, Any]] = []
    passed = 0
    critical_passed = 0
    critical_total = 0

    for defn in BETA_LAUNCH_CHECKLIST:
        ok = checks.get(defn["id"], False)
        criteria.append({**defn, "passed": ok})
        if ok:
            passed += 1
        if defn.get("critical"):
            critical_total += 1
            if ok:
                critical_passed += 1

    total = len(BETA_LAUNCH_CHECKLIST)
    readiness_pct = round(100.0 * passed / total, 1) if total else 0.0
    beta_ready = critical_passed == critical_total and critical_total > 0

    missing_critical = [c["label"] for c in criteria if c.get("critical") and not c.get("passed")]

    return {
        "beta_ready": beta_ready,
        "readiness_pct": readiness_pct,
        "passed": passed,
        "total": total,
        "critical_passed": critical_passed,
        "critical_total": critical_total,
        "criteria": criteria,
        "checks": checks,
        "missing_critical": missing_critical,
        "agents_gate": {
            "gate_open": gate.get("gate_open"),
            "readiness_pct": gate.get("readiness_pct"),
        },
        "ceo_beta": {
            "approved": state.get("ceo_beta_go"),
            "note": state.get("ceo_beta_note"),
            "at": state.get("ceo_beta_at"),
        },
        "infra": {
            "nomad_local_path": str(local_path) if local_path else None,
            "nomad_repo": metrics.get("github_repo"),
        },
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


def _format_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Rapport readiness NUAWAY",
        "",
        f"**Beta ready :** {'OUI' if report.get('beta_ready') else 'NON'}",
        f"**Score checklist :** {report.get('readiness_pct')}% "
        f"({report.get('passed')}/{report.get('total')})",
        "",
        "## Gate agents",
        f"- Ouverte : {'oui' if (report.get('agents_gate') or {}).get('gate_open') else 'non'}",
        f"- Readiness agents : {(report.get('agents_gate') or {}).get('readiness_pct')}%",
        "",
        "## Checklist beta",
    ]
    for c in report.get("criteria") or []:
        mark = "x" if c.get("passed") else " "
        crit = " (bloquant)" if c.get("critical") else ""
        lines.append(f"- [{mark}] {c.get('label')}{crit}")
    missing = report.get("missing_critical") or []
    if missing:
        lines.extend(["", "## Bloquants", *[f"- {m}" for m in missing]])
    ceo = report.get("ceo_beta") or {}
    if ceo.get("approved"):
        lines.extend(["", f"**Go CEO :** oui — {ceo.get('note') or 'sans note'}"])
    lines.append("")
    lines.append(f"_Généré {report.get('evaluated_at')}_")
    return "\n".join(lines)


def generate_readiness_report(*, refresh_gate: bool = True) -> dict[str, Any]:
    """Rapport structuré pour briefing CEO / n8n."""
    report = evaluate_beta_readiness(refresh_gate=refresh_gate)
    if report.get("beta_ready"):
        headline = "NUAWAY beta-ready — go CEO enregistré, lancer staging beta."
    elif report.get("missing_critical"):
        headline = f"Beta bloquée : {report['missing_critical'][0]}"
    else:
        headline = f"Readiness beta {report.get('readiness_pct')}% — critères en cours"

    report["headline"] = headline
    report["markdown"] = _format_report_markdown(report)

    state = load_readiness_state()
    state["last_report_at"] = report["evaluated_at"]
    state["last_report_headline"] = headline
    save_readiness_state(state)

    return report
