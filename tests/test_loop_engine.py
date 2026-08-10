"""Loop Engine — Phase C (DEC-024)."""

from __future__ import annotations

import pytest

from services.loop_engine import (
    EvalVerdict,
    IllegalTransitionError,
    LoopContext,
    LoopState,
    run_loop,
    run_loop_async,
)
from services.loop_engine_models import FeedbackRequiredError


def test_fsm_cannot_skip_evaluating() -> None:
    state = LoopState.create(max_iterations=3)
    state.advance_to_execution()
    with pytest.raises(IllegalTransitionError):
        state.approve()


def test_reject_requires_feedback() -> None:
    state = LoopState.create(max_iterations=3)
    state.advance_to_execution()
    state.submit_for_review()
    with pytest.raises(FeedbackRequiredError):
        state.reject("")
    with pytest.raises(FeedbackRequiredError):
        EvalVerdict(approved=False, feedback="  ")


def test_run_loop_retry_then_success() -> None:
    calls = {"n": 0}

    def execute(ctx: LoopContext) -> dict:
        calls["n"] += 1
        return {"n": calls["n"], "feedback_seen": ctx.last_feedback}

    def evaluate(value: dict, ctx: LoopContext) -> EvalVerdict:
        if value["n"] < 3:
            return EvalVerdict(
                approved=False,
                feedback=f"tests failed on attempt {value['n']}: AssertionError line 12",
            )
        assert "tests failed on attempt" in ctx.feedback_block()
        return EvalVerdict(approved=True)

    result = run_loop(execute=execute, evaluate=evaluate, max_iterations=3, sleep_s=0)
    assert result.success
    assert result.status == "COMPLETED"
    assert result.iterations == 3
    assert len(result.feedback_log) == 2
    assert result.value["feedback_seen"]  # saw prior feedback on last run


def test_run_loop_escalates_at_cap() -> None:
    def execute(ctx: LoopContext) -> str:
        return "x"

    def evaluate(value: str, ctx: LoopContext) -> EvalVerdict:
        return EvalVerdict(approved=False, feedback="still broken")

    result = run_loop(execute=execute, evaluate=evaluate, max_iterations=3, sleep_s=0)
    assert not result.success
    assert result.status == "ESCALATED"
    assert result.iterations == 3
    assert len(result.feedback_log) == 3


def test_run_loop_fatal_non_retryable() -> None:
    def execute(ctx: LoopContext) -> str:
        return "x"

    def evaluate(value: str, ctx: LoopContext) -> EvalVerdict:
        return EvalVerdict(
            approved=False,
            feedback="permission denied",
            retryable=False,
        )

    result = run_loop(execute=execute, evaluate=evaluate, max_iterations=5, sleep_s=0)
    assert result.status == "FAILED"
    assert result.iterations == 1


def test_run_loop_async_basic() -> None:
    import asyncio

    async def _main() -> None:
        async def execute(ctx: LoopContext) -> int:
            return ctx.iteration

        async def evaluate(value: int, ctx: LoopContext) -> EvalVerdict:
            return EvalVerdict(approved=True)

        result = await run_loop_async(
            execute=execute, evaluate=evaluate, max_iterations=2, sleep_s=0
        )
        assert result.success
        assert result.value == 1

    asyncio.run(_main())


def test_plan_executor_step_uses_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.plan_executor_models import ExecutionStep
    from services.plan_executor_run import _execute_step

    monkeypatch.setenv("ISOLATION_ENABLED", "0")
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass

    calls = {"n": 0}

    def boom_then_ok(**kwargs):
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError(f"fail#{calls['n']}")
        return {"ok": True, "saw": kwargs.get("_loop_feedback", "")}

    monkeypatch.setattr(
        "services.parallel_runner._get_agent_method",
        lambda agent_id, method: boom_then_ok,
    )
    step = ExecutionStep(
        step_id="1",
        description="t",
        agent_id="qa",
        method="ok",
    )
    result = _execute_step(step, max_retries=2)
    assert result.success
    assert result.retries >= 1
    assert "fail#" in str(result.result.get("saw") or "")


def test_workflow_retryable_then_ok(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from services import workflow_engine as we
    from services.workflow_engine_catalog import RECIPE_CATALOG
    from services.workflow_engine_handlers import _STEP_HANDLERS
    from services.workflow_engine_models import WorkflowRecipe, WorkflowStepDef
    from services.workflow_engine_run import run_workflow

    runs = tmp_path / "workflow_runs"
    runs.mkdir()
    monkeypatch.setattr(we, "_RUNS_DIR", runs)

    state = {"n": 0}

    def flaky(ctx):
        state["n"] += 1
        if state["n"] < 2:
            return {
                "status": "RETRYABLE",
                "detail": "transient",
                "feedback": "network blip",
                "gaps": ["transient"],
            }
        return {"status": "OK", "detail": "done", "gaps": []}

    recipe = WorkflowRecipe(
        id="test_loop_retry",
        name="Test loop",
        description="retry",
        head_agent="coo",
        steps=[WorkflowStepDef(id="flaky_step", label="Flaky", head_agent="coo")],
    )
    RECIPE_CATALOG.append(recipe)
    _STEP_HANDLERS["flaky_step"] = flaky
    try:
        out = run_workflow("test_loop_retry", {})
        assert out["success"] is True
        assert state["n"] == 2
        step = out["steps"][0]
        assert step["status"] == "OK"
        assert step["result"]["_loop_iterations"] == 2
    finally:
        RECIPE_CATALOG[:] = [r for r in RECIPE_CATALOG if r.id != "test_loop_retry"]
        _STEP_HANDLERS.pop("flaky_step", None)


def test_is_strict_loop_and_resolve_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.loop_engine import is_strict_loop, resolve_max_iterations

    monkeypatch.setenv("LOOP_MAX_ITERATIONS", "5")
    monkeypatch.setenv("LOOP_STRICT_MAX_ITERATIONS", "2")
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass

    assert is_strict_loop(method="merge_pr")
    assert is_strict_loop(agent_id="dev_integrator")
    assert is_strict_loop(recipe_id="ship_hub")
    assert is_strict_loop(kwargs={"auto_merge": True})
    assert not is_strict_loop(method="analyze", agent_id="qa")

    assert resolve_max_iterations(strict=True) == 2
    assert resolve_max_iterations(strict=True, override=5) == 2
    assert resolve_max_iterations(strict=False, override=5) == 5


def test_plan_merge_step_uses_strict_ceiling(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.plan_executor_models import ExecutionStep
    from services.plan_executor_run import _execute_step

    monkeypatch.setenv("ISOLATION_ENABLED", "0")
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    monkeypatch.setenv("LOOP_STRICT_MAX_ITERATIONS", "2")
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass

    calls = {"n": 0}

    def always_fail(**kwargs):
        calls["n"] += 1
        raise RuntimeError(f"merge fail #{calls['n']}")

    monkeypatch.setattr(
        "services.parallel_runner._get_agent_method",
        lambda agent_id, method: always_fail,
    )
    step = ExecutionStep(
        step_id="m1",
        description="merge staging",
        agent_id="dev_integrator",
        method="merge_branch",
    )
    result = _execute_step(step, max_retries=5)
    assert not result.success
    assert calls["n"] == 2  # strict ceiling, not legacy 6
    assert result.retries == 1
