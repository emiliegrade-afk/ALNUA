"""Robo Academy program config — Eve Paper Build (SPEC_STUDIO_ACADEMIES / DEC-036).

Curriculum data lives in ``academy_curriculum_robo.py``; this module wires it
into an ``AcademyProgram`` for the generic studio_academy engine. QA is done
by qa_robot (Bilal) via the engine's default DoD review (AgentBase
``run_json_task``) — no agent-side method needed.
"""

from __future__ import annotations

import os

from services.academy_curriculum_robo import LEVEL_META, POLE, SLUG, SUBJECT, all_exercises
from services.studio_academy_program import AcademyProgram

# Local dispatch — hardware workshop only (same ripple rationale as gaming).
_AGENT_CLASSES: dict[str, tuple[str, str]] = {
    "hardware": ("agents.hardware_agent", "HardwareAgent"),
    "embedded_dev": ("agents.embedded_dev_agent", "EmbeddedDevAgent"),
    "vision_ai": ("agents.vision_ai_agent", "VisionAiAgent"),
    "electronics": ("agents.electronics_agent", "ElectronicsAgent"),
    "firmware": ("agents.firmware_agent", "FirmwareAgent"),
    "mechanical": ("agents.mechanical_agent", "MechanicalAgent"),
    "industrial_design": ("agents.industrial_design_agent", "IndustrialDesignAgent"),
    "qa_robot": ("agents.qa_robot_agent", "QaRobotAgent"),
    "safety": ("agents.safety_agent", "SafetyAgent"),
    "simulation": ("agents.simulation_agent", "SimulationAgent"),
}

# Where each agent method can absorb cross-deliverable context (N2+ refs).
_CONTEXT_PARAM: dict[str, str] = {
    "design_circuit": "constraints",
    "design_form_factor": "constraints",
    "design_part": "load_requirements",
    "design_driver": "constraints",
    "build_test_protocol": "prior_issues",
    "assess_risk": "context",
    "run_simulation_plan": "constraints",
    "design_detection_pipeline": "constraints",
}

_STUDIO_ROLES = tuple(_AGENT_CLASSES)


def _v2_prereq() -> tuple[str, bool]:
    # V2 = real prototype work in the Eve lab (Pi reachable over SSH).
    return "v2_prereq_pi_host", bool(os.getenv("PI_HOST", "").strip())


ROBO_PROGRAM = AcademyProgram(
    program_id="robo",
    title="Eve Paper Build",
    subject=SUBJECT,
    subject_kwarg=None,  # robo agent prompts already embed "Eve robot"
    pole=POLE,
    slug=SLUG,
    qa_agent_id="qa_robot",
    agent_classes=_AGENT_CLASSES,
    context_params=_CONTEXT_PARAM,
    level_meta=LEVEL_META,
    progress_env="ROBO_ACADEMY_PROGRESS_PATH",
    progress_filename="robo_academy_progress.json",
    notes="Robo Academy — Eve Paper Build, specs de pré-production du compagnon de bureau Eve",
    runner_module="services.robo_academy_runner",
    exercises=all_exercises,
    studio_roles=_STUDIO_ROLES,
    gate_n3_check="n3_prototype_complete",
    gate_extra=_v2_prereq,
)
