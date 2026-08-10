"""Build Mission aggregates from plans / objectives (DEC-023)."""

from __future__ import annotations

from typing import Any

from services.mission_graph_models import Mission, MissionProject, MissionTask, new_mission_id
from services.mission_graph_store import save_mission
from services.plan_executor_models import ExecutionPlan, ExecutionStep


def tasks_from_steps(steps: list[ExecutionStep] | list[dict[str, Any]]) -> list[MissionTask]:
    out: list[MissionTask] = []
    for s in steps:
        if isinstance(s, ExecutionStep):
            out.append(
                MissionTask(
                    task_id=str(s.step_id),
                    description=s.description,
                    agent_id=s.agent_id,
                    method=s.method,
                    kwargs=dict(s.kwargs or {}),
                    depends_on=[str(d) for d in (s.depends_on or [])],
                    lock_keys=list(s.lock_keys or []),
                    repo_slug=s.repo_slug or "",
                    repo_path=s.repo_path or "",
                    status="PENDING",
                )
            )
        else:
            out.append(
                MissionTask(
                    task_id=str(s.get("task_id") or s.get("step_id") or ""),
                    description=str(s.get("description") or ""),
                    agent_id=str(s.get("agent_id") or ""),
                    method=str(s.get("method") or ""),
                    kwargs=dict(s.get("kwargs") or {}),
                    depends_on=[str(d) for d in (s.get("depends_on") or [])],
                    lock_keys=[str(k) for k in (s.get("lock_keys") or [])],
                    repo_slug=str(s.get("repo_slug") or ""),
                    repo_path=str(s.get("repo_path") or ""),
                    project_id=s.get("project_id"),
                    status="PENDING",
                )
            )
    return [t for t in out if t.task_id and t.agent_id and t.method]


def mission_from_plan(
    plan: ExecutionPlan,
    *,
    source: str = "from_plan",
    persist: bool = True,
) -> Mission:
    mission = Mission(
        mission_id=new_mission_id(),
        title=plan.title or plan.objective[:80] or "Mission",
        objective=plan.objective or plan.title,
        context=plan.context,
        tasks=tasks_from_steps(plan.steps),
        source=source,
        status="DRAFTED",
    )
    mission.recompute_status()
    if persist:
        save_mission(mission)
    return mission


def mission_from_steps(
    *,
    title: str,
    tasks: list[dict[str, Any]],
    objective: str = "",
    context: str = "",
    projects: list[dict[str, Any]] | None = None,
    source: str = "manual",
    persist: bool = True,
) -> Mission:
    proj = [
        MissionProject(
            project_id=str(p["project_id"]),
            title=str(p.get("title") or p["project_id"]),
            depends_on=[str(d) for d in (p.get("depends_on") or [])],
        )
        for p in (projects or [])
        if p.get("project_id")
    ]
    mission = Mission(
        mission_id=new_mission_id(),
        title=title.strip() or "Mission",
        objective=objective or title,
        context=context,
        tasks=tasks_from_steps(tasks),
        projects=proj,
        source=source,
        status="DRAFTED",
    )
    if not mission.tasks:
        raise ValueError("Mission requires at least one valid task (task_id, agent_id, method)")
    mission.recompute_status()
    if persist:
        save_mission(mission)
    return mission


def mission_from_objective(
    objective: str,
    context: str = "",
    *,
    persist: bool = True,
) -> Mission:
    """Ask COO to decompose, then persist as Mission Graph."""
    from services.input_sanitizer import sanitize_user_input
    from services.plan_executor_parser import parse_coo_plan

    obj = sanitize_user_input(objective, redact_pii_enabled=False)[:2000]
    ctx = sanitize_user_input(context, redact_pii_enabled=False)[:4000] if context else ""
    plan = parse_coo_plan(obj, ctx)
    if not plan.steps:
        raise ValueError("COO n'a pas pu générer de plan pour cet objectif")
    return mission_from_plan(plan, source="coo_plan", persist=persist)


def ensure_integrate_task(
    mission: Mission,
    *,
    target_branch: str = "staging",
    persist: bool = True,
) -> MissionTask | None:
    """Append dev_integrator task when ≥2 coding tasks share a repo (DEC-025)."""
    codingish = [
        t
        for t in mission.tasks
        if t.agent_id
        in {
            "dev_app",
            "dev_backend",
            "dev_frontend",
            "dev_gaming",
            "dev_integrator",
            "embedded_dev",
        }
        or (t.method or "").startswith(("code", "implement", "fix", "merge"))
    ]
    feature = [t for t in codingish if t.agent_id != "dev_integrator"]
    if len(feature) < 2:
        return None
    if any(t.method in {"integrate_worktrees", "review_chain"} for t in mission.tasks):
        return None
    deps = [t.task_id for t in feature]
    task = MissionTask(
        task_id=f"integrate-{mission.mission_id[-8:]}",
        description=f"Integrate {len(feature)} feature branches → {target_branch}",
        agent_id="dev_integrator",
        method="integrate_worktrees",
        depends_on=deps,
        kwargs={
            "target_branch": target_branch,
            "feature_task_ids": deps,
        },
        lock_keys=[f"mission:{mission.mission_id}:integrate"],
        repo_slug=feature[0].repo_slug,
        repo_path=feature[0].repo_path,
    )
    mission.tasks.append(task)
    mission.recompute_status()
    if persist:
        save_mission(mission)
    return task
