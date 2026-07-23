"""Autonomy Super Plan — CEO cockpit + Academy gate (Phase 5/6)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/autonomy", tags=["autonomy"])


@router.get("/ceo-cockpit")
def autonomy_ceo_cockpit() -> dict[str, Any]:
    """Dashboard CEO — gate, académie, ops prod, file dossiers."""
    from services.ceo_cockpit import get_ceo_cockpit

    return get_ceo_cockpit()


@router.get("/academy-gate")
def autonomy_academy_gate(refresh: bool = True) -> dict[str, Any]:
    """Critères gate Academy → Lounge + readiness %."""
    from services.academy_gate import evaluate_academy_gate

    return evaluate_academy_gate(refresh_academy=refresh)


@router.post("/academy-gate/evaluate")
def autonomy_academy_gate_evaluate() -> dict[str, Any]:
    """Force refresh gate (sync GitHub academy + métriques)."""
    from services.academy_gate import evaluate_academy_gate

    result = evaluate_academy_gate(refresh_academy=True)
    return {
        "message": (
            "Gate Academy ouverte"
            if result.get("gate_open")
            else f"Readiness {result.get('readiness_pct')}% — critères manquants"
        ),
        **result,
    }
