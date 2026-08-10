"""Pydantic models — split from schemas.py (debt paydown)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

class SecretaryDraftEmailRequest(BaseModel):
    subject: str
    context: str
    recipient: str
    tone: str = "professionnel"
    language: str = "fr"


class SecretaryTriageRequest(BaseModel):
    emails: list[dict[str, str]]


class SecretaryDraftContractRequest(BaseModel):
    contract_type: str
    party_name: str
    scope: str
    duration: str
    compensation: str = ""
    special_clauses: str = ""


class SecretaryPlanMeetingRequest(BaseModel):
    participants: list[str]
    topic: str
    duration_minutes: int = 60
    constraints: str = ""


class SecretaryMeetingNotesRequest(BaseModel):
    meeting_title: str
    raw_notes: str
    participants: list[str]


class MilestoneCreateRequest(BaseModel):
    title: str
    date_iso: str
    pole: str = ""
    description: str = ""


class MilestoneUpdateRequest(BaseModel):
    title: str | None = None
    date_iso: str
    pole: str | None = None
    description: str | None = None


class MilestoneValidateRequest(BaseModel):
    validated: bool = True


class ScoreAddRequest(BaseModel):
    agent_id: str
    action: str = Field(
        pattern="^(task_completed|task_validated|feature_shipped|bug_found_critical|bug_fixed|review_approved|document_produced|insight_actioned|custom)$"
    )
    points: int | None = Field(default=None, ge=1, le=500)
    note: str = ""


class DevBackendDesignAPIRequest(BaseModel):
    feature: str
    project: str
    constraints: str = ""


class DevBackendImplementRequest(BaseModel):
    feature: str
    project: str
    api_spec: str = ""
    tech_stack: str = "FastAPI + Supabase"


class DevBackendReviewRequest(BaseModel):
    code: str
    context: str = ""


class DevBackendDebugRequest(BaseModel):
    error: str
    context: str
    code_snippet: str = ""


class DevFrontendImplementRequest(BaseModel):
    feature: str
    project: str = "Hub ALNUA"
    context: str = ""
    design_notes: str = ""


class DevFrontendFixLayoutRequest(BaseModel):
    issue: str
    context: str = ""
    code_snippet: str = ""


class DevFrontendReviewRequest(BaseModel):
    code: str
    context: str = ""


class DevIntegratorIntegrateRequest(BaseModel):
    repo_path: str
    branch: str
    worktrees: list[str] | None = None
    base_branch: str = ""


class DevIntegratorOpenPrRequest(BaseModel):
    repo_path: str
    branch: str
    title: str
    body: str = ""
    qa_verdict: dict | None = None


class DevIntegratorReviewDiffRequest(BaseModel):
    diff_summary: str
    context: str = ""


class LevelDesignerQuestRequest(BaseModel):
    quest_name: str
    game: str
    lore_context: str = ""
    player_level_range: str = "1-10"
    quest_type: str = "main"


class LevelDesignerLevelRequest(BaseModel):
    level_name: str
    game: str
    biome: str = ""
    difficulty: str = "medium"
    special_mechanics: str = ""


class LevelDesignerLoreRequest(BaseModel):
    subject: str
    game: str
    lore_type: str = "history"
    length: str = "medium"


class LevelDesignerBalanceRequest(BaseModel):
    system: str
    current_values: dict[str, Any]
    player_feedback: str = ""


class AiProgrammerBehaviorRequest(BaseModel):
    entity_name: str
    game: str
    behavior_type: str = "hostile"
    difficulty: str = "medium"


class EnvironmentArtistRequest(BaseModel):
    zone_name: str
    game: str
    biome: str = ""
    mood: str = ""


class TechnicalArtistRenderRequest(BaseModel):
    scene_name: str
    game: str
    target_fps: int = 60
    current_issues: str = ""


class NarrativeCanonSearchRequest(BaseModel):
    query: str
    game: str = "Wyrdheim"


class NarrativeDesignerDialogueRequest(BaseModel):
    npc_name: str
    game: str
    context: str = ""
    tone: str = "neutre"


class VfxArtistRequest(BaseModel):
    effect_name: str
    game: str
    trigger: str = ""
    style: str = ""


class SoundDesignerRequest(BaseModel):
    scene_name: str
    game: str
    mood: str = ""
    key_sfx: str = ""


class QaGamingTestPlanRequest(BaseModel):
    feature_name: str
    game: str
    build_version: str = ""
    risk_areas: str = ""


class VisionAiDetectionRequest(BaseModel):
    task_name: str
    target_objects: str = ""
    constraints: str = ""


class ElectronicsCircuitRequest(BaseModel):
    circuit_name: str
    function: str = ""
    constraints: str = ""


class FirmwareDriverRequest(BaseModel):
    component_name: str
    timing_requirement: str = ""
    constraints: str = ""


class MechanicalPartRequest(BaseModel):
    part_name: str
    function: str = ""
    load_requirements: str = ""


class IndustrialDesignRequest(BaseModel):
    product_name: str
    constraints: str = ""
    brand_notes: str = ""


class QaRobotProtocolRequest(BaseModel):
    subsystem_name: str
    risk_level: str = "medium"
    prior_issues: str = ""


class SafetyRiskRequest(BaseModel):
    subsystem_name: str
    hazard_type: str = ""
    context: str = ""


class SimulationPlanRequest(BaseModel):
    subsystem_name: str
    scenario: str = ""
    constraints: str = ""


class AgentInstructionRequest(BaseModel):
    instruction: str


class GameDirectorLoreSearchRequest(BaseModel):
    query: str
    project: str | None = None
    limit: int = 5


class RndAgentResearchRequest(BaseModel):
    query: str
    context: str = ""


class RndAgentPrototypeRequest(BaseModel):
    idea: str
    context: str = ""


class CodingCoachTeachRequest(BaseModel):
    message: str
    workspace: str = "sandbox"
    file_path: str | None = None
    file_content: str | None = None


class CodingCoachExerciseRequest(BaseModel):
    topic: str
    level: str = "débutant"


