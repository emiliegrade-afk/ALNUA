"""Robotics / hardware / Eve BOM / Pi bridge routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.agents_pole_helpers import clean_agent_text
from services.input_sanitizer import sanitize_user_input

router = APIRouter()


@router.post("/agents/vision-ai/detection-pipeline")
def vision_ai_detection_pipeline(body: VisionAiDetectionRequest) -> dict[str, Any]:
    return VisionAiAgent().design_detection_pipeline(
        body.task_name, body.target_objects, clean_agent_text(body.constraints)
    )


@router.post("/agents/electronics/circuit")
def electronics_circuit(body: ElectronicsCircuitRequest) -> dict[str, Any]:
    return ElectronicsAgent().design_circuit(
        body.circuit_name, body.function, clean_agent_text(body.constraints)
    )


@router.post("/agents/electronics/bom-context")
def electronics_bom_context(body: ElectronicsBomContextRequest) -> dict[str, Any]:
    """Phase 21 — Marco reads Eve BOM via skill_bom (no fabricated lines)."""
    return ElectronicsAgent().bom_context(category=body.category, limit=body.limit)


@router.post("/agents/electronics/alternatives")
def electronics_alternatives(body: EveAlternativesRequest) -> dict[str, Any]:
    """Sourcing expert — pro vs budget options (estimates, no auto-buy)."""
    try:
        return ElectronicsAgent().suggest_alternatives(
            sanitize_user_input(body.need, max_length=400),
            category=sanitize_user_input(body.category or "", max_length=40) or None,
            max_options=body.max_options,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/agents/firmware/driver")
def firmware_driver(body: FirmwareDriverRequest) -> dict[str, Any]:
    return FirmwareAgent().design_driver(
        body.component_name, body.timing_requirement, clean_agent_text(body.constraints)
    )


@router.post("/agents/firmware/pi-probe")
def firmware_pi_probe(body: FirmwarePiProbeRequest) -> dict[str, Any]:
    """Phase 21 — Petra probes Eve Pi via SSH (denylist + PI_NOT_CONFIGURED)."""
    cmd = sanitize_user_input(body.command or "uname -a", max_length=200)
    return FirmwareAgent().probe_pi(cmd)


@router.post("/agents/mechanical/part")
def mechanical_part(body: MechanicalPartRequest) -> dict[str, Any]:
    return MechanicalAgent().design_part(
        body.part_name, body.function, clean_agent_text(body.load_requirements)
    )


@router.post("/agents/mechanical/assembly-plan")
def mechanical_assembly_plan(body: EveAssemblyPlanRequest) -> dict[str, Any]:
    """Plan de montage Eve — basé sur le BOM courant."""
    return MechanicalAgent().assembly_plan(
        sanitize_user_input(body.goal or "", max_length=500)
    )


@router.post("/agents/industrial-design/form-factor")
def industrial_design_form_factor(body: IndustrialDesignRequest) -> dict[str, Any]:
    return IndustrialDesignAgent().design_form_factor(
        body.product_name, clean_agent_text(body.constraints), clean_agent_text(body.brand_notes)
    )


@router.post("/agents/qa-robot/protocol")
def qa_robot_protocol(body: QaRobotProtocolRequest) -> dict[str, Any]:
    return QaRobotAgent().build_test_protocol(
        body.subsystem_name, body.risk_level, clean_agent_text(body.prior_issues)
    )


@router.post("/agents/safety/risk-assessment")
def safety_risk_assessment(body: SafetyRiskRequest) -> dict[str, Any]:
    return SafetyAgent().assess_risk(
        body.subsystem_name, body.hazard_type, clean_agent_text(body.context)
    )


@router.post("/agents/simulation/plan")
def simulation_plan(body: SimulationPlanRequest) -> dict[str, Any]:
    return SimulationAgent().run_simulation_plan(
        body.subsystem_name, body.scenario, clean_agent_text(body.constraints)
    )


@router.post("/agents/hardware/instruction")
def hardware_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = HardwareAgent().handle_instruction(clean_agent_text(body.instruction))
    return {"result": result}


@router.post("/agents/hardware/infra-blueprint")
def hardware_infra_blueprint(body: EveInfraBlueprintRequest) -> dict[str, Any]:
    """Qui build le robot vs l'app compagnon (comme Naïa) — Yuki."""
    return HardwareAgent().infra_blueprint(
        sanitize_user_input(body.focus or "full", max_length=80)
    )


@router.get("/robo/pi-bridge")
def robo_pi_bridge_status() -> dict[str, Any]:
    """SSH bridge status — Hub replaces WinSCP for agent commands when PI_HOST set."""
    import os

    from skills.skill_pi_ssh import PI_NOT_CONFIGURED, pi_is_configured

    configured = pi_is_configured()
    return {
        "configured": configured,
        "host": (os.getenv("PI_HOST") or "").strip() or None,
        "tooling": {
            "agents": "POST /agents/embedded/pi-command (denylist + SSH)",
            "human_files": "WinSCP optional for manual file copy; not used by agents",
        },
        "message": (
            "Pi prêt pour commandes agents via Hub."
            if configured
            else PI_NOT_CONFIGURED
        ),
        "pi_deferred_ok": True,
    }


@router.post("/agents/embedded/instruction")
def embedded_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = EmbeddedDevAgent().handle_instruction(clean_agent_text(body.instruction))
    return {"result": result}


@router.post("/agents/embedded/pi-command")
def embedded_pi_command(body: EmbeddedPiCommandRequest) -> dict[str, Any]:
    from agents.embedded_dev_agent import execute_pi_ssh_with_retry

    result = execute_pi_ssh_with_retry(body.command)
    return result


@router.get("/bom/eve")
def bom_eve_list() -> dict[str, Any]:
    items = list_bom_items()
    return {"items": items, "totals": bom_totals(items), "categories": list(BOM_CATEGORIES)}


@router.post("/bom/eve")
def bom_eve_create(body: BomCreateRequest) -> dict[str, Any]:
    try:
        return create_bom_item(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/bom/eve/{item_id}")
def bom_eve_update(item_id: str, body: BomUpdateRequest) -> dict[str, Any]:
    try:
        return update_bom_item(item_id, body.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/bom/eve/{item_id}")
def bom_eve_delete(item_id: str) -> dict[str, Any]:
    return delete_bom_item(item_id)


@router.get("/looking-glass/status")
def looking_glass_status() -> dict[str, Any]:
    """Check HoloPlay / Looking Glass availability via Pi SSH or local host."""
    import os

    host = os.getenv("LOOKING_GLASS_HOST", "").strip()
    if host:
        try:
            import httpx

            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{host.rstrip('/')}/health")
                if res.is_success:
                    return {
                        "connected": True,
                        "holoplay_running": True,
                        "message": "Looking Glass host reachable",
                    }
        except Exception:
            pass

    from skills.skill_pi_ssh import pi_is_configured, run_pi_command

    if pi_is_configured():
        try:
            out = run_pi_command("pgrep -f holoplay || pgrep -f LookingGlass")
            running = out.get("success") and bool(out.get("output", "").strip())
            return {
                "connected": True,
                "holoplay_running": running,
                "message": "HoloPlay actif sur Pi" if running else "Pi online, HoloPlay inactif",
            }
        except Exception:
            return {
                "connected": False,
                "holoplay_running": False,
                "message": "Pi configuré mais injoignable",
            }

    return {
        "connected": False,
        "holoplay_running": False,
        "message": "Configurer LOOKING_GLASS_HOST ou PI_HOST dans .env",
    }
