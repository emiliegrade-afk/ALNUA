"""R&D dossier pipeline status (phase 8) — cross-phase progress tracker."""

from __future__ import annotations

from typing import Any, Literal

from services.rnd_product import get_rnd_product_repository, is_product_pipeline_unlocked
from services.rnd_repository import get_rnd_repository
from services.rnd_schemas import RndDossierOut
from services.rnd_social import get_rnd_social_repository, is_social_pipeline_unlocked

StageStatus = Literal["done", "in_progress", "pending", "locked", "skipped"]

STAGE_DEFS: list[dict[str, Any]] = [
    {"id": "dossier", "phase": 1, "label": "Dossier R&D", "tab": "pitch"},
    {"id": "enrich", "phase": 2, "label": "Enrichissement & finance", "tab": "pitch"},
    {"id": "committee", "phase": 3, "label": "Comité multi-agents", "tab": "committee"},
    {"id": "visuals", "phase": 4, "label": "Visuels & deck", "tab": "visuals"},
    {"id": "social", "phase": 5, "label": "Pipeline social", "tab": "social"},
    {"id": "ceo", "phase": 6, "label": "Package CEO & dispatch", "tab": "ceo"},
    {"id": "product", "phase": 7, "label": "Fiche produit publique", "tab": "product"},
]


def build_dossier_pipeline(dossier: RndDossierOut) -> dict[str, Any]:
    repo = get_rnd_repository()
    social = get_rnd_social_repository()
    product_repo = get_rnd_product_repository()

    assets = repo.list_assets(dossier.id)
    calendar = social.list_calendar(dossier.id)
    product_page = product_repo.get_by_dossier_id(dossier.id)
    sessions = repo.db.select(
        "rnd_committee_sessions",
        filters={"dossier_id": dossier.id},
        order_by="created_at",
        ascending=False,
        limit=5,
    )

    ceo_unlocked = is_social_pipeline_unlocked(dossier.status, dossier.ceo_status)
    post_ceo = dossier.ceo_status == "approved" or dossier.status in (
        "ceo_approved",
        "in_conception",
        "published",
    )
    is_hub_internal = (dossier.branch or "").lower() == "hub"

    stages: list[dict[str, Any]] = []

    # Phase 1 — dossier skeleton
    s1 = _stage("dossier", "done" if dossier.sections_total_count > 0 else "pending")
    s1["detail"] = f"{dossier.sections_total_count} sections"
    stages.append(s1)

    # Phase 2 — enrich
    has_finance = bool(dossier.finance_json)
    validated = dossier.sections_validated_count
    if has_finance and validated >= max(1, dossier.sections_total_count // 2):
        s2_status: StageStatus = "done"
    elif has_finance or validated > 0:
        s2_status = "in_progress"
    else:
        s2_status = "pending"
    s2 = _stage("enrich", s2_status)
    s2["detail"] = (
        f"{validated}/{dossier.sections_total_count} validées · "
        f"{'finance OK' if has_finance else 'finance en attente'}"
    )
    stages.append(s2)

    # Phase 3 — committee
    has_cr = bool(dossier.committee_report_md)
    closed_session = any(s.get("status") == "closed" for s in sessions)
    active_session = any(s.get("status") == "active" for s in sessions)
    if has_cr or closed_session:
        s3_status = "done"
    elif active_session or dossier.status == "committee_active":
        s3_status = "in_progress"
    else:
        s3_status = "pending"
    s3 = _stage("committee", s3_status)
    s3["detail"] = "CR structuré" if has_cr else (
        "Session active" if active_session else "Comité non démarré"
    )
    stages.append(s3)

    # Phase 4 — visuals + deck
    has_assets = len(assets) >= 3
    has_deck = bool(dossier.deck_html_path)
    if has_assets and has_deck:
        s4_status = "done"
    elif has_assets or has_deck:
        s4_status = "in_progress"
    else:
        s4_status = "pending"
    s4 = _stage("visuals", s4_status)
    s4["detail"] = f"{len(assets)} visuel(s) · {'deck OK' if has_deck else 'deck absent'}"
    stages.append(s4)

    # Phase 5 — social (locked pre-CEO; skipped for Hub interne)
    if is_hub_internal:
        s5 = _stage("social", "skipped")
        s5["detail"] = "N/A — amélioration Hub interne (pas de calendrier social)"
    elif not ceo_unlocked:
        s5 = _stage("social", "locked")
        s5["detail"] = "Verrouillé — validation CEO requise"
    elif len(calendar) >= 5:
        s5 = _stage("social", "done")
        s5["detail"] = f"{len(calendar)} jalons calendrier"
    elif len(calendar) > 0:
        s5 = _stage("social", "in_progress")
        s5["detail"] = f"{len(calendar)} jalons (incomplet)"
    else:
        s5 = _stage("social", "pending")
        s5["detail"] = "Calendrier social à générer"
    stages.append(s5)

    # Phase 6 — CEO
    has_package = bool(dossier.ceo_package_json)
    dispatched = dossier.dispatch_status == "dispatched"
    if post_ceo and dispatched:
        s6_status = "done"
    elif post_ceo and dossier.ceo_status == "approved":
        s6_status = "in_progress" if not dispatched else "done"
    elif has_package or dossier.status == "ready_for_ceo":
        s6_status = "in_progress"
    elif dossier.ceo_status == "rejected":
        s6_status = "skipped"
    else:
        s6_status = "pending"
    s6 = _stage("ceo", s6_status)
    s6["detail"] = (
        f"CEO {dossier.ceo_status} · dispatch {dossier.dispatch_status}"
    )
    stages.append(s6)

    # Phase 7 — product page
    if is_hub_internal:
        s7 = _stage("product", "skipped")
        s7["detail"] = "N/A — pas de fiche produit publique pour infra Hub"
    elif not is_product_pipeline_unlocked(dossier.status, dossier.ceo_status):
        s7 = _stage("product", "locked")
        s7["detail"] = "Verrouillé — validation CEO requise"
    elif product_page and product_page.published:
        s7 = _stage("product", "done")
        s7["detail"] = f"Publiée · /p/{product_page.slug}"
        s7["public_url"] = f"/p/{product_page.slug}"
    elif product_page:
        s7 = _stage("product", "in_progress")
        s7["detail"] = "Brouillon — publier pour rendre public"
    else:
        s7 = _stage("product", "pending")
        s7["detail"] = "Fiche produit à générer"
    stages.append(s7)

    done = sum(1 for s in stages if s["status"] == "done")
    total = len(stages)
    progress_pct = round(100 * done / total) if total else 0

    next_stage = next(
        (s for s in stages if s["status"] in ("pending", "in_progress", "locked")),
        None,
    )

    return {
        "dossier_id": dossier.id,
        "dossier_slug": dossier.slug,
        "dossier_status": dossier.status,
        "ceo_status": dossier.ceo_status,
        "progress_pct": progress_pct,
        "stages_done": done,
        "stages_total": total,
        "stages": stages,
        "next_action": _next_action_hint(next_stage),
        "next_tab": next_stage.get("tab") if next_stage else None,
        "pipeline_complete": done == total,
    }


def rnd_module_health(db) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    ok = True
    for table in (
        "rnd_ideas",
        "rnd_dossiers",
        "rnd_dossier_sections",
        "rnd_product_pages",
    ):
        try:
            rows = db.select(table, limit=1)
            checks[table] = {"ok": True, "sample": len(rows) >= 0}
        except Exception as exc:
            ok = False
            checks[table] = {"ok": False, "error": str(exc)[:120]}
    try:
        ideas_n = len(db.select("rnd_ideas", limit=500))
        dossiers_n = len(db.select("rnd_dossiers", limit=500))
        checks["counts"] = {"ideas": ideas_n, "dossiers": dossiers_n}
    except Exception:
        pass
    return {
        "status": "ok" if ok else "degraded",
        "module": "rnd_dossier",
        "checks": checks,
    }


def _stage(stage_id: str, status: StageStatus) -> dict[str, Any]:
    meta = next(s for s in STAGE_DEFS if s["id"] == stage_id)
    return {
        "id": stage_id,
        "phase": meta["phase"],
        "label": meta["label"],
        "tab": meta["tab"],
        "status": status,
    }


def _next_action_hint(stage: dict[str, Any] | None) -> str | None:
    if not stage:
        return "Pipeline complet — dossier prêt."
    sid = stage["id"]
    status = stage["status"]
    if status == "locked":
        if sid in ("social", "product"):
            return "Valider le dossier CEO pour débloquer social et fiche produit."
        return "Étape verrouillée."
    hints = {
        "dossier": "Créer ou compléter le dossier R&D.",
        "enrich": "Enrichir sections + business case (finance).",
        "committee": "Ouvrir le comité ou générer le CR.",
        "visuals": "Générer visuels Pillow et deck pitch.",
        "social": "Générer le calendrier social post-CEO.",
        "ceo": "Générer package CEO, décider, dispatcher au COO.",
        "product": "Générer et publier la fiche produit /p/{slug}.",
    }
    return hints.get(sid)
