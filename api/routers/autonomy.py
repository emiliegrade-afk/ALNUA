"""Autonomy Super Plan — CEO cockpit + NUAWAY gate (Phase 5/6)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/autonomy", tags=["autonomy"])


@router.get("/ceo-cockpit")
def autonomy_ceo_cockpit() -> dict[str, Any]:
    """Dashboard CEO — gate, académie, ops prod, file dossiers."""
    from services.ceo_cockpit import get_ceo_cockpit

    return get_ceo_cockpit()


@router.get("/nuaway-gate")
def autonomy_nuaway_gate(refresh: bool = True) -> dict[str, Any]:
    """Critères gate NUAWAY + readiness %."""
    from services.nuaway_gate import evaluate_nuaway_gate

    return evaluate_nuaway_gate(refresh_academy=refresh)


@router.post("/nuaway-gate/evaluate")
def autonomy_nuaway_gate_evaluate() -> dict[str, Any]:
    """Force refresh gate (sync GitHub academy + métriques)."""
    from services.nuaway_gate import evaluate_nuaway_gate

    result = evaluate_nuaway_gate(refresh_academy=True)
    return {
        "message": (
            "Gate NUAWAY ouverte"
            if result.get("gate_open")
            else f"Readiness {result.get('readiness_pct')}% — critères manquants"
        ),
        **result,
    }


@router.get("/nuaway-readiness")
def autonomy_nuaway_readiness(refresh: bool = True) -> dict[str, Any]:
    """Checklist beta formelle Phase 6."""
    from services.nuaway_readiness import evaluate_beta_readiness

    return evaluate_beta_readiness(refresh_gate=refresh)


@router.post("/nuaway-readiness/report")
def autonomy_nuaway_readiness_report() -> dict[str, Any]:
    """Génère le rapport readiness (markdown + headline)."""
    from services.nuaway_readiness import generate_readiness_report

    report = generate_readiness_report(refresh_gate=True)
    return {
        "message": report.get("headline", "Rapport généré"),
        **report,
    }


@router.post("/nuaway-readiness/ceo-go")
def autonomy_nuaway_ceo_go(body: NuawayCeoGoRequest) -> dict[str, Any]:
    """Enregistre le go/no-go CEO pour la beta NUAWAY."""
    from services.nuaway_readiness import set_ceo_beta_go

    result = set_ceo_beta_go(approved=body.approved, note=body.note or "")
    return {
        "message": "Go beta CEO enregistré" if body.approved else "Beta CEO en attente",
        **result,
    }


@router.get("/nuaway-bootstrap")
def autonomy_nuaway_bootstrap(refresh: bool = True) -> dict[str, Any]:
    """Diagnostic bootstrap ops NUAWAY (Phase 7)."""
    from services.nuaway_bootstrap import run_nuaway_bootstrap

    return run_nuaway_bootstrap(refresh=refresh)
