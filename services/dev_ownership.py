"""Lightweight ownership resolver for autonomous coding dispatch."""

from __future__ import annotations

from typing import Any

from config.agent_models import normalize_agent_id

CODING_AGENT_IDS: frozenset[str] = frozenset(
    {"dev_app", "dev_backend", "dev_gaming", "embedded_dev", "dev_frontend", "dev_integrator"}
)


class OwnershipRule:
    agent_id: str = "dev_backend"
    label: str = "Backend"
    description: str = "Fallback general"
    path_markers: tuple[str, ...] = ()
    title_markers: tuple[str, ...] = ()
    text_markers: tuple[str, ...] = ()

    def matches(self, paths: list[str] | tuple[str, ...], title: str, description: str) -> bool:
        paths = [str(p).lower() for p in paths if p]
        text_blob = " ".join([title or "", description or "", *paths]).lower()

        for path in paths:
            for marker in self.path_markers:
                if marker and marker in path:
                    return True

        for marker in self.title_markers + self.text_markers:
            if marker and marker in text_blob:
                return True

        return False


class DevFrontendOwnershipRule(OwnershipRule):
    agent_id = "dev_frontend"
    label = "Frontend"
    description = "Hub web, React/Next, components and layouts"
    path_markers = ("/web/", "/frontend/", "/src/", "/components/", "/pages/", ".tsx", ".jsx", ".css", ".html")
    title_markers = ("ui", "frontend", "layout", "page", "component", "screen", "web")
    text_markers = ("react", "next", "frontend", "component", "layout", "design system")


class DevBackendOwnershipRule(OwnershipRule):
    agent_id = "dev_backend"
    label = "Backend"
    description = "API, services, database and backend logic"
    path_markers = ("/api/", "/services/", "/database/", "/bots/", "/models/", ".py", ".sql")
    title_markers = ("api", "backend", "service", "endpoint", "schema", "database", "migration")
    text_markers = ("fastapi", "router", "sql", "supabase", "migration", "backend")


class DevAppOwnershipRule(OwnershipRule):
    agent_id = "dev_app"
    label = "App"
    description = "Mobile app and Expo-style product work"
    path_markers = ("/mobile/", "/expo/", ".swift", ".kt", ".java", "/ios/", "/android/")
    title_markers = ("mobile", "ios", "android", "expo", "native")
    text_markers = ("expo", "react native", "mobile", "ios", "android", "native app")


class DevGamingOwnershipRule(OwnershipRule):
    agent_id = "dev_gaming"
    label = "Gaming"
    description = "Gameplay, levels and engine implementation"
    path_markers = ("godot", "unreal", "ue5", "/levels/", "/gameplay/", ".gd", ".cs", ".cpp")
    title_markers = ("gameplay", "level", "quest", "blueprint", "godot", "ue5")
    text_markers = ("gameplay", "unreal", "blueprint", "level design", "npc", "quest")


class EmbeddedDevOwnershipRule(OwnershipRule):
    agent_id = "embedded_dev"
    label = "Embedded"
    description = "Robotics, firmware and IoT implementation"
    path_markers = ("firmware", "arduino", "raspberry", "iot", "embedded", "robot", "esp32", "stm32")
    title_markers = ("robot", "embedded", "firmware", "iot", "microcontroller", "sensor")
    text_markers = ("robotics", "firmware", "iot", "arduino", "sensor", "motor")


OWNERSHIP_RULES: tuple[type[OwnershipRule], ...] = (
    DevAppOwnershipRule,
    DevFrontendOwnershipRule,
    DevBackendOwnershipRule,
    DevGamingOwnershipRule,
    EmbeddedDevOwnershipRule,
)


def resolve_coding_agent(
    *,
    paths: list[str] | tuple[str, ...] | None = None,
    title: str = "",
    description: str = "",
    agent_id: str | None = None,
    branch: str = "",
) -> str:
    if agent_id:
        normalized = normalize_agent_id(agent_id)
        if normalized in CODING_AGENT_IDS:
            return normalized

    branch_text = (branch or "").lower()
    if any(token in branch_text for token in ("gaming", "game", "godot", "ue5")):
        return "dev_gaming"
    if any(token in branch_text for token in ("robot", "embedded", "firmware", "iot")):
        return "embedded_dev"

    candidate_paths = [str(p) for p in (paths or []) if p]
    for rule_cls in OWNERSHIP_RULES:
        rule = rule_cls()
        if rule.matches(candidate_paths, title, description):
            return rule.agent_id

    text = " ".join([title or "", description or "", *candidate_paths]).lower()
    if any(token in text for token in ("api", "backend", "service", "router", "database", "schema")):
        return "dev_backend"
    return "dev_frontend"


def describe_coding_agent(agent_id: str) -> dict[str, Any]:
    normalized = normalize_agent_id(agent_id)
    if normalized == "dev_integrator":
        return {
            "agent_id": "dev_integrator",
            "available": True,
            "label": "Intégrateur",
            "description": "Merge les worktrees des autres devs vers la branche commune ; ne possède aucun fichier en propre",
        }
    for rule_cls in OWNERSHIP_RULES:
        rule = rule_cls()
        if rule.agent_id == normalized:
            return {"agent_id": normalized, "available": True, "label": rule.label, "description": rule.description}
    return {"agent_id": normalized, "available": False}
