"""Review Chain integrate gate — multi-branch merge helpers."""

from __future__ import annotations

from typing import Any, Callable

from services.review_chain_models import GateResult

IntegrateFn = Callable[..., dict[str, Any]]


def needs_integrate(feature_branches: list[str] | None) -> bool:
    return len([b for b in (feature_branches or []) if b]) > 1


def run_integrate(
    *,
    repo_path: str,
    integration_branch: str,
    feature_branches: list[str],
    base_branch: str,
    dry_run: bool,
    integrate_fn: IntegrateFn | None,
) -> GateResult:
    if dry_run:
        return GateResult(
            gate="INTEGRATE",
            outcome="pass",
            detail="dry_run integrate skipped",
            meta={
                "dry_run": True,
                "branches": feature_branches,
                "integration_branch": integration_branch,
            },
        )

    def _default_integrate() -> dict[str, Any]:
        from agents.dev_integrator_agent import DevIntegratorAgent

        agent = DevIntegratorAgent()
        return agent.integrate_worktrees(
            repo_path=repo_path,
            branch=integration_branch,
            worktrees=feature_branches,
            base_branch=base_branch,
        )

    fn = integrate_fn or _default_integrate
    try:
        out = fn(
            repo_path=repo_path,
            branch=integration_branch,
            worktrees=feature_branches,
            base_branch=base_branch,
        )
    except TypeError:
        out = fn()
    except Exception as exc:
        return GateResult(
            gate="INTEGRATE",
            outcome="fail",
            detail=str(exc),
            feedback=f"Integrate exception: {type(exc).__name__}: {exc}",
            meta={},
        )

    conflicts = out.get("conflicts") or []
    status = str(out.get("status") or "")
    if conflicts or status in {"error", "conflict", "conflicts"}:
        fb = "; ".join(
            f"{c.get('branch')}: {c.get('error')}" for c in conflicts if isinstance(c, dict)
        ) or str(out.get("error") or status)
        return GateResult(
            gate="INTEGRATE",
            outcome="fail",
            detail="integrate conflicts",
            feedback=fb[:2000],
            meta={"integrate": out},
        )
    return GateResult(
        gate="INTEGRATE",
        outcome="pass",
        detail=f"merged={out.get('merged')}",
        meta={"integrate": out},
    )
