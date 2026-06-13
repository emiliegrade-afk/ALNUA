"""
services/plan_executor.py — Exécuteur autonome de plans COO ALNUA.

Inspiré de ralphex (umputun, ⭐1.3k) — boucle d'exécution autonome de plans.
Aria (COO) génère un plan JSON → l'executor le déroule étape par étape
en appelant les bons agents, en respectant les dépendances, en collectant les résultats.

Usage:
    from services.plan_executor import run_coo_plan, execute_plan, ExecutionPlan

    # Pipeline complet : objectif → COO génère plan → executor le déroule
    result = run_coo_plan(
        objective="Lancer une campagne marketing pour le nouveau feature analytics",
        context="Le feature sort vendredi. Budget comm limité. Cible : devs indie."
    )

    # Exécuter un plan déjà construit
    plan = ExecutionPlan(
        title="Campagne lancement",
        steps=[
            ExecutionStep(step_id="1", description="Analyse marché",
                         agent_id="analyst_business", method="market_analysis",
                         kwargs={"product": "Analytics Feature", "market": "indie devs"}),
            ExecutionStep(step_id="2", description="Créer contenu",
                         agent_id="content", method="write_content",
                         kwargs={"topic": "Analytics Feature", "format": "linkedin"},
                         depends_on=["1"]),
        ]
    )
    result = execute_plan(plan)
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ExecutionStep:
    step_id: str
    description: str
    agent_id: str
    method: str
    kwargs: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)  # IDs des steps bloquants
    award_points: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "description": self.description,
            "agent_id": self.agent_id,
            "method": self.method,
            "depends_on": self.depends_on,
        }


@dataclass
class StepResult:
    step_id: str
    agent_id: str
    description: str
    success: bool
    result: Any
    error: str | None
    duration_ms: int
    retries: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "agent_id": self.agent_id,
            "description": self.description,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "retries": self.retries,
        }


@dataclass
class ExecutionPlan:
    title: str
    steps: list[ExecutionStep]
    context: str = ""
    plan_id: str = field(default_factory=lambda: f"plan_{int(time.time())}")
    objective: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "objective": self.objective,
            "total_steps": len(self.steps),
            "steps": [s.to_dict() for s in self.steps],
        }


# ---------------------------------------------------------------------------
# COO Plan Parser — COO génère le plan, on le parse
# ---------------------------------------------------------------------------

_COO_PLAN_SYSTEM = """Tu es Aria Stern, COO d'ALNUA. Tu décomposes des objectifs en plans d'action précis.
Chaque étape du plan est assignée à UN agent ALNUA spécifique avec ses paramètres exacts.
Les dépendances reflètent le flux de données réel (step B utilise le résultat de step A).
Réponds en JSON valide uniquement."""

_AVAILABLE_AGENTS = """AGENTS DISPONIBLES :
- coo → plan_week, morning_brief
- spec → write_spec
- qa → review_spec
- pm → plan_sprint, write_user_story
- dev_app → handle_instruction, design_api
- dev_backend → design_api, implement_feature, review_code, debug
- dev_gaming → handle_instruction
- game_director → game_concept, write_gdd
- brainstorm → ideate
- rnd_agent → prototype_spec, research_topic
- marketing → handle_instruction, seo_audit
- content → write_content, create_post
- accounting → analyze_expenses
- controller → analyze_costs, build_forecast, llm_cost_alert
- hardware → handle_instruction
- embedded_dev → handle_instruction
- secretary → draft_email, triage_emails, draft_contract, plan_meeting
- level_designer → design_quest, design_level, write_lore_entry
- analyst_business → market_analysis, define_kpis, user_research, strategic_brief
- analyst_data → sql_query, funnel_analysis, anomaly_report, dashboard_spec"""


def parse_coo_plan(objective: str, context: str = "") -> ExecutionPlan:
    """
    Fait générer un plan par Aria (COO) et le parse en ExecutionPlan.

    Le COO reçoit l'objectif → génère une liste de steps avec agents et kwargs.
    """
    try:
        from agents.base import LLMClient, parse_json_response

        llm = LLMClient()
        prompt = f"""OBJECTIF : {objective}
CONTEXTE : {context or 'Aucun contexte supplémentaire'}

{_AVAILABLE_AGENTS}

Génère un plan d'exécution JSON avec :
- title (string): titre court du plan
- steps (list): liste des étapes, chaque étape = {{
    "step_id": "1" | "2" | ...,
    "description": "Ce que cette étape accomplit",
    "agent_id": "agent_id exact de la liste ci-dessus",
    "method": "méthode exacte de l'agent",
    "kwargs": {{paramètres pour la méthode}},
    "depends_on": ["step_id_bloquant"] — vide [] si indépendant
  }}

Règles :
- Maximum 8 étapes
- Minimiser les dépendances (exécution parallèle quand possible)
- Les kwargs doivent être utilisables tels quels par l'agent
- Grouper les étapes indépendantes (même niveau de depends_on = parallèles)"""

        raw = llm.complete(_COO_PLAN_SYSTEM, prompt, agent_id="coo", temperature=0.3)
        data = parse_json_response(raw)

        steps = []
        for s in data.get("steps", []):
            steps.append(ExecutionStep(
                step_id=str(s.get("step_id", len(steps) + 1)),
                description=s.get("description", ""),
                agent_id=s.get("agent_id", ""),
                method=s.get("method", ""),
                kwargs=s.get("kwargs", {}),
                depends_on=[str(d) for d in s.get("depends_on", [])],
            ))

        return ExecutionPlan(
            title=data.get("title", objective[:50]),
            steps=steps,
            context=context,
            objective=objective,
        )

    except Exception as e:
        logger.error(f"COO plan parse failed: {e}")
        return ExecutionPlan(title=objective[:50], steps=[], context=context, objective=objective)


# ---------------------------------------------------------------------------
# Step Executor — exécute un step avec retry
# ---------------------------------------------------------------------------

def _execute_step(step: ExecutionStep, max_retries: int = 2) -> StepResult:
    """Exécute un step avec retry automatique (backoff linéaire)."""
    from services.parallel_runner import _get_agent_method

    start = time.time()
    retries = 0
    last_error = None

    while retries <= max_retries:
        try:
            method = _get_agent_method(step.agent_id, step.method)
            result = method(**step.kwargs)

            duration_ms = int((time.time() - start) * 1000)

            # Points compétition
            if step.award_points:
                try:
                    from services.competition import add_points
                    add_points(step.agent_id, "task_completed",
                               note=f"Plan step: {step.description[:50]}")
                except Exception:
                    pass

            return StepResult(
                step_id=step.step_id,
                agent_id=step.agent_id,
                description=step.description,
                success=True,
                result=result,
                error=None,
                duration_ms=duration_ms,
                retries=retries,
            )

        except Exception as e:
            last_error = str(e)
            retries += 1
            if retries <= max_retries:
                time.sleep(retries * 2)  # Backoff: 2s, 4s
                logger.warning(f"Step {step.step_id} retry {retries}/{max_retries}: {e}")

    return StepResult(
        step_id=step.step_id,
        agent_id=step.agent_id,
        description=step.description,
        success=False,
        result=None,
        error=last_error,
        duration_ms=int((time.time() - start) * 1000),
        retries=retries - 1,
    )


# ---------------------------------------------------------------------------
# Plan Executor principal
# ---------------------------------------------------------------------------

def execute_plan(
    plan: ExecutionPlan,
    max_concurrent: int = 3,
    stop_on_failure: bool = False,
    max_retries: int = 2,
) -> dict[str, Any]:
    """
    Exécute un plan en respectant les dépendances.
    Les steps sans dépendances s'exécutent en parallèle.

    Endpoint: POST /services/plan/execute
    """
    if not plan.steps:
        return {
            "plan_id": plan.plan_id,
            "title": plan.title,
            "error": "Plan vide — aucune étape à exécuter",
            "results": [],
        }

    completed: dict[str, StepResult] = {}
    all_results: list[StepResult] = []
    pending = list(plan.steps)
    start_total = time.time()

    logger.info(f"Executing plan '{plan.title}' — {len(plan.steps)} steps")

    while pending:
        # Trouver les steps dont toutes les dépendances sont satisfaites
        ready = [
            s for s in pending
            if all(dep in completed for dep in s.depends_on)
            and (not stop_on_failure or all(completed[dep].success for dep in s.depends_on))
        ]

        if not ready:
            # Dépendances impossibles à satisfaire (cycle ou failure bloquante)
            remaining_ids = [s.step_id for s in pending]
            logger.warning(f"Plan stalled — remaining: {remaining_ids}")
            for s in pending:
                all_results.append(StepResult(
                    step_id=s.step_id, agent_id=s.agent_id,
                    description=s.description, success=False,
                    result=None, error="Blocked by dependency failure or cycle",
                    duration_ms=0,
                ))
            break

        # Exécuter le batch en parallèle (threads, car agents sont sync)
        import concurrent.futures
        batch = ready[:max_concurrent]
        for s in batch:
            pending.remove(s)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch)) as executor:
            futures = {executor.submit(_execute_step, s, max_retries): s for s in batch}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                completed[result.step_id] = result
                all_results.append(result)
                logger.info(
                    f"Step {result.step_id} {'✅' if result.success else '❌'} "
                    f"({result.duration_ms}ms, {result.retries} retries)"
                )

    total_ms = int((time.time() - start_total) * 1000)
    success_count = sum(1 for r in all_results if r.success)

    # COO valide le plan complété
    if success_count == len(plan.steps):
        try:
            from services.competition import add_points
            add_points("coo", "task_validated", note=f"Plan completed: {plan.title[:50]}")
        except Exception:
            pass

    return {
        "plan_id": plan.plan_id,
        "title": plan.title,
        "objective": plan.objective,
        "total_steps": len(plan.steps),
        "success_count": success_count,
        "failure_count": len(all_results) - success_count,
        "total_duration_ms": total_ms,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "results": [r.to_dict() for r in all_results],
        "plan_summary": {s.step_id: s.to_dict() for s in plan.steps},
    }


def run_coo_plan(
    objective: str,
    context: str = "",
    max_concurrent: int = 3,
    stop_on_failure: bool = False,
) -> dict[str, Any]:
    """
    Pipeline complet : objectif → COO génère plan → executor le déroule.

    Endpoint: POST /services/plan/coo-run
    """
    logger.info(f"COO plan pipeline: {objective[:60]}")

    # Étape 1 : COO génère le plan
    plan = parse_coo_plan(objective, context)

    if not plan.steps:
        return {
            "error": "COO n'a pas pu générer de plan",
            "objective": objective,
            "plan": plan.to_dict(),
            "results": [],
        }

    # Étape 2 : Executor le déroule
    execution_result = execute_plan(
        plan,
        max_concurrent=max_concurrent,
        stop_on_failure=stop_on_failure,
    )

    return {
        "objective": objective,
        "plan": plan.to_dict(),
        **execution_result,
    }
