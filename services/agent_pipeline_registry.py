"""
services/agent_pipeline_registry.py — Registre unique agents → pipeline.

Utilisé par parallel_runner, plan_executor et les audits de connectivité.
Les clés agent_id correspondent à config/agent_personas.py et web/agent-bureau.ts.
"""
from __future__ import annotations

import importlib
from typing import Any, Callable

# agent_id → (module, class_name)
AGENT_CLASSES: dict[str, tuple[str, str]] = {
    "coo": ("agents.coo_agent", "COOAgent"),
    "spec": ("agents.spec_agent", "SpecAgent"),
    "qa": ("agents.qa_agent", "QAAgent"),
    "pm": ("agents.pm_agent", "PMAgent"),
    "dev_app": ("agents.dev_app_agent", "DevAppAgent"),
    "dev_backend": ("agents.dev_backend_agent", "DevBackendAgent"),
    "game_director": ("agents.game_director_agent", "GameDirectorAgent"),
    "dev_gaming": ("agents.dev_gaming_agent", "DevGamingAgent"),
    "brainstorm": ("agents.brainstorm_agent", "BrainstormAgent"),
    "rnd_agent": ("agents.rnd_agent", "RndAgent"),
    "marketing": ("agents.marketing_agent", "MarketingAgent"),
    "content": ("agents.content_agent", "ContentAgent"),
    "accounting": ("agents.accountant_agent", "AccountantAgent"),
    "hardware": ("agents.hardware_agent", "HardwareAgent"),
    "embedded_dev": ("agents.embedded_dev_agent", "EmbeddedDevAgent"),
    "secretary": ("agents.secretary_agent", "SecretaryAgent"),
    "level_designer": ("agents.level_designer_agent", "LevelDesignerAgent"),
    "controller": ("agents.controller_agent", "ControllerAgent"),
    "analyst_business": ("agents.analyst_business_agent", "BusinessAnalystAgent"),
    "analyst_data": ("agents.analyst_data_agent", "DataAnalystAgent"),
}

# Méthodes exposées au plan_executor (noms réels vérifiés sur les classes)
PIPELINE_METHODS: dict[str, list[str]] = {
    "coo": ["get_daily_briefing", "run_daily_briefing", "handle_instruction"],
    "spec": [
        "generate_cursor_prompt",
        "generate_from_ticket",
        "generate_and_write_dispatch",
        "batch_generate_for_open_tickets",
    ],
    "qa": ["analyze_feedback_batch", "create_ticket_from_report"],
    "pm": ["handle_instruction", "triage_project", "add_roadmap_item"],
    "dev_app": ["handle_instruction"],
    "dev_backend": ["design_api", "implement_feature", "review_code", "debug"],
    "dev_gaming": ["handle_instruction"],
    "game_director": ["handle_instruction"],
    "brainstorm": ["brainstorm", "chat", "summarize_session"],
    "rnd_agent": ["research_topic", "prototype_spec"],
    "marketing": ["handle_instruction"],
    "content": ["generate_posts", "generate_from_dev_logs"],
    "accounting": ["financial_advice", "estimate_for_dossier"],
    "hardware": ["handle_instruction"],
    "embedded_dev": ["handle_instruction"],
    "secretary": ["draft_email", "triage_emails", "draft_contract", "plan_meeting", "write_meeting_notes"],
    "level_designer": ["design_quest", "design_level", "write_lore_entry", "balance_review"],
    "controller": ["analyze_costs", "build_forecast", "llm_cost_alert", "monthly_report"],
    "analyst_business": ["market_analysis", "define_kpis", "user_research", "strategic_brief"],
    "analyst_data": ["sql_query", "funnel_analysis", "anomaly_report", "dashboard_spec"],
}

# agent_logs.agent_name / alias → agent_id OpenRoom (IDs bureau)
LOG_NAME_TO_AGENT_ID: dict[str, str] = {
    "coo_agent": "coo",
    "coo": "coo",
    "pm_agent": "pm",
    "qa_agent": "qa",
    "spec_agent": "spec",
    "content_agent": "content",
    "marketing_agent": "marketing",
    "marketing": "marketing",
    "dev_app_agent": "dev_app",
    "DevApp": "dev_app",
    "dev_backend": "dev_backend",
    "dev_backend_agent": "dev_backend",
    "game_director": "game_director",
    "GameDirector": "game_director",
    "dev_gaming": "dev_gaming",
    "DevGaming": "dev_gaming",
    "hardware": "hardware",
    "Hardware": "hardware",
    "HardwareAgent": "hardware",
    "embedded_dev": "embedded_dev",
    "EmbeddedDev": "embedded_dev",
    "brainstorm_agent": "brainstorm",
    "Brainstorm": "brainstorm",
    "rnd_agent": "rnd_agent",
    "RndAgent": "rnd_agent",
    "secretary": "secretary",
    "accounting": "accounting",
    "accountant_agent": "accounting",
    "controller": "controller",
    "controller_agent": "controller",
    "level_designer": "level_designer",
    "analyst_business": "analyst_business",
    "analyst_business_agent": "analyst_business",
    "analyst_data": "analyst_data",
    "analyst_data_agent": "analyst_data",
}

OPENROOM_DISPLAY: dict[str, str] = {
    "coo": "COO",
    "pm": "PM",
    "qa": "QA",
    "spec": "SPEC",
    "secretary": "SECRETARY",
    "dev_app": "DEV",
    "dev_backend": "BACKEND",
    "dev_gaming": "DEV-G",
    "game_director": "GAME",
    "level_designer": "LEVEL",
    "brainstorm": "IDEA",
    "rnd_agent": "R&D",
    "content": "CONTENT",
    "marketing": "MKT",
    "hardware": "HW",
    "embedded_dev": "EMB",
    "accounting": "COMPTA",
    "controller": "CTRL",
    "analyst_business": "BIZ",
    "analyst_data": "DATA",
}

# Tous les agents du bureau (20) — IDs alignés web/src/lib/agent-bureau.ts
ALL_BUREAU_AGENT_IDS: tuple[str, ...] = tuple(AGENT_CLASSES.keys())


def get_agent_method(agent_id: str, method_name: str) -> Callable[..., Any]:
    """Instancie l'agent et retourne la méthode pipeline demandée."""
    if agent_id not in AGENT_CLASSES:
        raise ValueError(
            f"Agent inconnu: {agent_id!r}. Disponibles: {list(AGENT_CLASSES)}"
        )
    module_path, class_name = AGENT_CLASSES[agent_id]
    module = importlib.import_module(module_path)
    agent_class = getattr(module, class_name)
    instance = agent_class()
    method = getattr(instance, method_name, None)
    if method is None:
        raise AttributeError(
            f"L'agent {agent_id!r} n'a pas de méthode {method_name!r}. "
            f"Pipeline: {PIPELINE_METHODS.get(agent_id, [])}"
        )
    return method


def format_plan_executor_catalog() -> str:
    """Texte injecté dans le prompt COO plan_executor."""
    lines = ["AGENTS DISPONIBLES (méthodes réelles) :"]
    for agent_id, methods in PIPELINE_METHODS.items():
        lines.append(f"- {agent_id} → {', '.join(methods)}")
    return "\n".join(lines)


def audit_pipeline() -> dict[str, Any]:
    """Vérifie import, instanciation et méthodes pipeline pour chaque agent."""
    report: dict[str, Any] = {
        "agents_ok": [],
        "agents_fail": [],
        "methods_ok": [],
        "methods_fail": [],
    }

    for agent_id, (module_path, class_name) in AGENT_CLASSES.items():
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            cls()
            report["agents_ok"].append(agent_id)
        except Exception as exc:
            report["agents_fail"].append({"agent_id": agent_id, "error": str(exc)})

    for agent_id, methods in PIPELINE_METHODS.items():
        for method in methods:
            try:
                get_agent_method(agent_id, method)
                report["methods_ok"].append(f"{agent_id}.{method}")
            except Exception as exc:
                report["methods_fail"].append(
                    {"agent_id": agent_id, "method": method, "error": str(exc)}
                )

    report["summary"] = {
        "agents_total": len(AGENT_CLASSES),
        "agents_ok": len(report["agents_ok"]),
        "methods_total": sum(len(m) for m in PIPELINE_METHODS.values()),
        "methods_ok": len(report["methods_ok"]),
        "all_connected": not report["agents_fail"] and not report["methods_fail"],
    }
    return report
