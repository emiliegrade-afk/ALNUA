"""Gaming studio specialist agent routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.agents_pole_helpers import clean_agent_text

router = APIRouter()


@router.post("/agents/level-designer/quest")
def level_designer_quest(body: LevelDesignerQuestRequest) -> dict[str, Any]:
    return LevelDesignerAgent().design_quest(
        body.quest_name,
        body.game,
        clean_agent_text(body.lore_context),
        body.player_level_range,
        body.quest_type,
    )


@router.post("/agents/level-designer/level")
def level_designer_level(body: LevelDesignerLevelRequest) -> dict[str, Any]:
    return LevelDesignerAgent().design_level(
        body.level_name,
        body.game,
        body.biome,
        body.difficulty,
        clean_agent_text(body.special_mechanics),
    )


@router.post("/agents/level-designer/lore")
def level_designer_lore(body: LevelDesignerLoreRequest) -> dict[str, Any]:
    return LevelDesignerAgent().write_lore_entry(
        clean_agent_text(body.subject, max_length=500), body.game, body.lore_type, body.length
    )


@router.post("/agents/level-designer/balance")
def level_designer_balance(body: LevelDesignerBalanceRequest) -> dict[str, Any]:
    return LevelDesignerAgent().balance_review(
        body.system, body.current_values, clean_agent_text(body.player_feedback)
    )


@router.post("/agents/ai-programmer/behavior")
def ai_programmer_behavior(body: AiProgrammerBehaviorRequest) -> dict[str, Any]:
    return AiProgrammerAgent().design_behavior(
        body.entity_name, body.game, body.behavior_type, body.difficulty
    )


@router.post("/agents/ai-programmer/nwiro-probe")
def ai_programmer_nwiro_probe() -> dict[str, Any]:
    """Phase 21 — Kenji probes Nwiro BT tools (explicit offline if UE5 down)."""
    return AiProgrammerAgent().probe_nwiro_tools()


@router.post("/agents/environment-artist/environment")
def environment_artist_environment(body: EnvironmentArtistRequest) -> dict[str, Any]:
    return EnvironmentArtistAgent().design_environment(
        body.zone_name, body.game, body.biome, clean_agent_text(body.mood, max_length=500)
    )


@router.post("/agents/environment-artist/ue58-probe")
def environment_artist_ue58_probe() -> dict[str, Any]:
    return EnvironmentArtistAgent().probe_ue58()


@router.post("/agents/technical-artist/render-budget")
def technical_artist_render_budget(body: TechnicalArtistRenderRequest) -> dict[str, Any]:
    return TechnicalArtistAgent().optimize_render_budget(
        body.scene_name, body.game, body.target_fps, clean_agent_text(body.current_issues)
    )


@router.post("/agents/narrative-designer/dialogue")
def narrative_designer_dialogue(body: NarrativeDesignerDialogueRequest) -> dict[str, Any]:
    return NarrativeDesignerAgent().write_dialogue(
        body.npc_name, body.game, clean_agent_text(body.context), body.tone
    )


@router.post("/agents/narrative-designer/canon-search")
def narrative_designer_canon_search(body: NarrativeCanonSearchRequest) -> dict[str, Any]:
    return NarrativeDesignerAgent().search_canon(
        clean_agent_text(body.query, max_length=500), body.game
    )


@router.post("/agents/narrative-designer/ue58-probe")
def narrative_designer_ue58_probe() -> dict[str, Any]:
    return NarrativeDesignerAgent().probe_ue58()


@router.post("/agents/vfx-artist/vfx")
def vfx_artist_vfx(body: VfxArtistRequest) -> dict[str, Any]:
    return VfxArtistAgent().design_vfx(body.effect_name, body.game, body.trigger, body.style)


@router.post("/agents/sound-designer/soundscape")
def sound_designer_soundscape(body: SoundDesignerRequest) -> dict[str, Any]:
    return SoundDesignerAgent().design_soundscape(
        body.scene_name, body.game, body.mood, clean_agent_text(body.key_sfx, max_length=500)
    )


@router.post("/agents/sound-designer/ue58-probe")
def sound_designer_ue58_probe() -> dict[str, Any]:
    return SoundDesignerAgent().probe_ue58()


@router.post("/agents/qa-gaming/test-plan")
def qa_gaming_test_plan(body: QaGamingTestPlanRequest) -> dict[str, Any]:
    return QaGamingAgent().build_test_plan(
        body.feature_name, body.game, body.build_version, clean_agent_text(body.risk_areas)
    )


@router.post("/agents/qa-gaming/ue58-probe")
def qa_gaming_ue58_probe() -> dict[str, Any]:
    return QaGamingAgent().probe_ue58()


@router.get("/agents/qa-gaming/builds")
def qa_gaming_builds(limit: int = 5) -> dict[str, Any]:
    return QaGamingAgent().list_recent_builds(limit=limit)
