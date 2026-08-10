"""Parallel runner — pre-configured ALNUA usage patterns."""

from __future__ import annotations

from typing import Any

from services.parallel_runner_exec import run_agents_parallel_sync
from services.parallel_runner_types import AgentTask


def run_analytics_room(
    product: str,
    business_question: str,
    sql_question: str,
    schema_context: str,
) -> dict[str, Any]:
    """Lance Layla (Business Analyst) et Axel (Data Analyst) en parallèle."""
    tasks = [
        AgentTask(
            agent_id="analyst_business",
            method="strategic_brief",
            kwargs={
                "topic": product,
                "context": business_question,
                "decision_needed": "Quelle action prendre ?",
            },
            task_label="Layla — brief stratégique",
        ),
        AgentTask(
            agent_id="analyst_data",
            method="sql_query",
            kwargs={
                "question": sql_question,
                "schema_context": schema_context,
            },
            task_label="Axel — requête SQL",
        ),
    ]
    return run_agents_parallel_sync(tasks)


def run_content_sprint(
    topic: str,
    product: str,
    target: str,
) -> dict[str, Any]:
    """Lance marketing et les rédacteurs secteur en parallèle sur un même brief."""
    tasks = [
        AgentTask(
            agent_id="marketing",
            method="handle_instruction",
            kwargs={"instruction": f"Stratégie de lancement pour {product} sur le sujet : {topic}. Cible : {target}"},
            task_label="Camille — stratégie marketing",
        ),
        AgentTask(
            agent_id="content_app",
            method="handle_instruction",
            kwargs={"instruction": f"Rédige du contenu app pour {product} sur : {topic}. Ton : engageant, cible : {target}"},
            task_label="Content App — posts produit",
        ),
        AgentTask(
            agent_id="content_gaming",
            method="handle_instruction",
            kwargs={"instruction": f"Rédige du contenu gaming pour {product} sur : {topic}. Ton : engageant, cible : {target}"},
            task_label="Content Gaming — devlogs",
        ),
        AgentTask(
            agent_id="content_robo",
            method="handle_instruction",
            kwargs={"instruction": f"Rédige du contenu robotique pour {product} sur : {topic}. Ton : engageant, cible : {target}"},
            task_label="Content Robo — updates hardware",
        ),
        AgentTask(
            agent_id="content_company",
            method="handle_instruction",
            kwargs={"instruction": f"Rédige du contenu corporate ALNUA pour {product} sur : {topic}. Ton : aligné marque, cible : {target}"},
            task_label="Content Company — posts corporate",
        ),
    ]
    return run_agents_parallel_sync(tasks)
