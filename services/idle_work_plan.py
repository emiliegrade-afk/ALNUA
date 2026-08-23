"""Idle day plan builder — split from idle_work_queue (Vague 5 / DEC-032)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any


def _item(
    *,
    level: int,
    kind: str,
    agent_id: str,
    title: str,
    family: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from services.idle_work_queue import _now_iso

    return {
        "id": f"idle_{uuid.uuid4().hex[:12]}",
        "level": level,
        "kind": kind,
        "agent_id": agent_id,
        "title": title,
        "family": family,
        "status": "pending",
        "payload": payload or {},
        "run_id": None,
        "created_at": _now_iso(),
        "finished_at": None,
    }


def build_day_plan(*, autonomy_level: int = 1) -> dict[str, Any]:
    """Build / refresh today's idle file (does not require CEO validation)."""
    from services.idle_work_queue import (
        _now_iso,
        clamp_autonomy,
        max_idle_level_for_autonomy,
        save_queue,
    )

    max_lvl = max_idle_level_for_autonomy(autonomy_level)
    items: list[dict[str, Any]] = []

    if max_lvl >= 0:
        items.append(
            _item(
                level=0,
                kind="ops_snapshot",
                agent_id="coo",
                title="Snapshot ops multi-repo",
                family="ops",
            )
        )
        items.append(
            _item(
                level=0,
                kind="cost_snapshot",
                agent_id="accounting",
                title="Alerte budget LLM du jour",
                family="finance",
            )
        )

    if max_lvl >= 1:
        items.append(
            _item(
                level=1,
                kind="company_draft",
                agent_id="content_company",
                title="Brouillon initiative marque / process ALNUA",
                family="company",
                payload={"theme": "cohérence marque + process interne"},
            )
        )
        items.append(
            _item(
                level=1,
                kind="product_triage",
                agent_id="pm",
                title="Triage backlog → proposition tickets idle-ok",
                family="product",
            )
        )

    if max_lvl >= 2:
        items.append(
            _item(
                level=2,
                kind="academy_wake",
                agent_id="dev_app",
                title="Academy wake si pipeline libre",
                family="code",
            )
        )

    if max_lvl >= 1:
        for aid in ("coo", "marketing", "dev_app", "rnd_agent"):
            items.append(
                _item(
                    level=1,
                    kind="self_dev",
                    agent_id=aid,
                    title=f"Self-dev Mem0 compress — {aid}",
                    family="self_dev",
                )
            )

    if max_lvl >= 0:
        roster = (
            "dev_app",
            "dev_backend",
            "qa",
            "brainstorm",
            "dev_gaming",
            "analyst_data",
        )
        aid = roster[date.today().toordinal() % len(roster)]
        items.append(
            _item(
                level=0,
                kind="lounge_session",
                agent_id=aid,
                title=f"Lounge puzzle filler — {aid}",
                family="lounge",
                payload={"activity": "puzzle"},
            )
        )

    queue = {
        "date": date.today().isoformat(),
        "ceo_validated": False,
        "validated_at": None,
        "autonomy_level": clamp_autonomy(autonomy_level),
        "items": items,
        "updated_at": _now_iso(),
    }
    save_queue(queue)
    return queue
