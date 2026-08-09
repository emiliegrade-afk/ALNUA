"""Phase 21 Vague B — thin robotics skill endpoints (keep agents_pole lean)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.input_sanitizer import sanitize_user_input

router = APIRouter(tags=["robo-phase21"])


class BomContextBody(BaseModel):
    category: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class LabContextBody(BaseModel):
    project_id: str | None = None
    category: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class PiProbeBody(BaseModel):
    command: str = Field(default="uname -a", max_length=200)


@router.post("/agents/mechanical/bom-context")
def mechanical_bom_context(body: BomContextBody) -> dict[str, Any]:
    from agents.mechanical_agent import MechanicalAgent

    return MechanicalAgent().bom_context(category=body.category, limit=body.limit)


@router.post("/agents/industrial-design/bom-context")
def industrial_design_bom_context(body: BomContextBody) -> dict[str, Any]:
    from agents.industrial_design_agent import IndustrialDesignAgent

    return IndustrialDesignAgent().bom_context(category=body.category, limit=body.limit)


@router.post("/agents/qa-robot/lab-context")
def qa_robot_lab_context(body: LabContextBody) -> dict[str, Any]:
    from agents.qa_robot_agent import QaRobotAgent

    return QaRobotAgent().lab_context(
        project_id=body.project_id, category=body.category, limit=body.limit
    )


@router.post("/agents/safety/lab-context")
def safety_lab_context(body: LabContextBody) -> dict[str, Any]:
    from agents.safety_agent import SafetyAgent

    return SafetyAgent().lab_context(project_id=body.project_id, category=body.category)


@router.post("/agents/vision-ai/pi-probe")
def vision_ai_pi_probe(body: PiProbeBody) -> dict[str, Any]:
    from agents.vision_ai_agent import VisionAiAgent

    cmd = sanitize_user_input(body.command, max_length=200) or "uname -a"
    return VisionAiAgent().probe_pi(cmd)


@router.post("/agents/simulation/lab-context")
def simulation_lab_context(body: LabContextBody) -> dict[str, Any]:
    from agents.simulation_agent import SimulationAgent

    return SimulationAgent().lab_context(project_id=body.project_id)
