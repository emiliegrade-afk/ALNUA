"""
agents/embedded_dev_agent.py

Agent CrewAI — Embedded Dev (Pôle Robotique)

Robot : Eve (Raspberry Pi + Python/C)
Responsabilités :
- Scripts Python/C pour Eve (mouvement, audio, capteurs)
- Intégration naia-embodied ↔ Eve hardware
- Looking Glass HoloPlay SDK
- Raspberry Pi management (SSH, déploiement)
- Firmware updates

Tools (max 5) : pi_ssh, naia_embodied_api, deploy_to_pi, eve_coding_agent
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from collections.abc import Callable

from crewai import Agent, Crew, LLM, Task
from crewai.tools import tool

from skills.skill_coding_agent import execute_coding_task
from config.llm_runtime import CREWAI_MAX_ITER_DEFAULT
from config.agent_operating_spec import crew_backstory
from skills.skill_langfuse import trace_agent
from skills.skill_pi_ssh import PI_NOT_CONFIGURED, pi_is_configured, run_pi_command
from skills.skill_retry_loop import retry_with_learning

logger = logging.getLogger(__name__)

_telegram_notify: Callable[[str], None] | None = None


def execute_pi_ssh_with_retry(
    command: str,
    timeout: int = 30,
    telegram_notify_fn: Callable[[str], None] | None = None,
) -> dict:
    """Run an SSH command on Eve Pi with retry on unstable connections."""
    if not pi_is_configured():
        return {
            "success": False,
            "error": PI_NOT_CONFIGURED,
            "result": {
                "success": False,
                "output": PI_NOT_CONFIGURED,
                "host": "",
                "command": command,
            },
        }

    def _attempt(learning_context: str) -> dict:
        result = run_pi_command(command, timeout)
        if not result["success"]:
            detail = result.get("output", "SSH command failed")
            if learning_context:
                detail = f"{detail}\n{learning_context[:200]}"
            raise ConnectionError(detail)
        return result

    return retry_with_learning(
        agent_name="embedded_dev",
        task_fn=_attempt,
        task_id=command[:80],
        task_context=f"SSH: {command}",
        max_attempts=3,
        telegram_notify_fn=telegram_notify_fn,
    )


def _build_llm() -> LLM:
    from agents.base import build_crewai_llm

    return build_crewai_llm("embedded_dev", temperature=0.3)


@tool("pi_ssh_command")
def pi_ssh_tool(command_json: str) -> str:
    """
    Exécute une commande sur le Raspberry Pi Eve via SSH.
    Input JSON : {"command": "...", "timeout": 30}
    Utilise les variables d'env PI_HOST, PI_USER, PI_SSH_KEY.
    """
    try:
        if not pi_is_configured():
            return PI_NOT_CONFIGURED

        data = json.loads(command_json)
        retry_result = execute_pi_ssh_with_retry(
            data["command"],
            data.get("timeout", 30),
            telegram_notify_fn=_telegram_notify,
        )
        if not retry_result["success"]:
            return f"[ERREUR] SSH échoué après 3 tentatives : {retry_result['error']}"
        result = retry_result["result"]
        if not result["success"] and result["host"] == "":
            return f"[ERREUR] {result['output']}"
        return f"Pi [{result['host']}] $ {result['command']}\n{result['output']}"
    except Exception as e:
        return f"[ERREUR] Erreur SSH : {e}"


@tool("robotics_edge_call")
def robotics_edge_tool(action_json: str) -> str:
    """
    Placeholder — edge robotics API (configure when hardware project is registered).
    Input JSON : {"action": "speak|move|status", "params": {...}}
    """
    try:
        json.loads(action_json)
        return (
            "Robotics edge API non configurée — enregistrez le projet dans le registry "
            "quand le hardware sera prêt."
        )
    except Exception as e:
        return f"[ERREUR] JSON invalide : {e}"


@tool("deploy_to_pi")
def deploy_pi_tool(deploy_json: str) -> str:
    """
    Déploie du code Python sur le Raspberry Pi via rsync + SSH.
    Input JSON : {"source_path": "...", "restart_service": true}
    """
    try:
        data = json.loads(deploy_json)
        pi_host = os.getenv("PI_HOST")
        pi_user = os.getenv("PI_USER", "pi")
        pi_key = os.path.expanduser(os.getenv("PI_SSH_KEY", "~/.ssh/id_ed25519"))
        source = data.get("source_path", "./eve/")

        if not pi_host:
            return PI_NOT_CONFIGURED

        result = subprocess.run(
            [
                "rsync",
                "-avz",
                "--exclude",
                "__pycache__",
                "-e",
                f"ssh -i {pi_key} -o StrictHostKeyChecking=no",
                source,
                f"{pi_user}@{pi_host}:/home/{pi_user}/eve/",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            return f"[ERREUR] rsync échoué : {result.stderr}"

        output = f"[OK] Code déployé sur Pi ({pi_host})"

        if data.get("restart_service"):
            restart = subprocess.run(
                [
                    "ssh",
                    "-i",
                    pi_key,
                    f"{pi_user}@{pi_host}",
                    "sudo systemctl restart eve.service",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            output += f"\n🔄 Service Eve redémarré : {'OK' if restart.returncode == 0 else 'ERREUR'}"

        return output
    except Exception as e:
        return f"[ERREUR] Erreur déploiement : {e}"


@tool("eve_coding_agent")
def eve_code_tool(spec_json: str) -> str:
    """
    Lance le pipeline de codage pour les scripts Eve (Python/C).
    Input JSON : même format que skill_coding_agent
    """
    try:
        spec = json.loads(spec_json)
        spec["description"] = (
            f"[Eve Robot — Raspberry Pi]\n{spec['description']}\n\n"
            "CONTRAINTES :\n"
            "- Code Python 3.11 compatible Raspberry Pi OS\n"
            "- Gestion GPIO via RPi.GPIO ou gpiozero\n"
            "- Servomoteurs via PCA9685 (adafruit-circuitpython-pca9685)\n"
            "- Audio via pygame.mixer ou subprocess aplay\n"
            "- Logging via logging module (pas print)\n"
            "- Gestion des exceptions hardware (GPIO busy, disconnected)"
        )
        result = execute_coding_task(spec, telegram_notify_fn=_telegram_notify)
        if result["success"]:
            return f"[OK] PR Eve créée : {result['pr_url']}"
        return f"[ERREUR] Échec : {result['error']}"
    except Exception as e:
        return f"[ERREUR] Erreur : {e}"


class EmbeddedDevAgent:
    def __init__(self, telegram_notify_fn: Callable[[str], None] | None = None):
        global _telegram_notify
        _telegram_notify = telegram_notify_fn
        self.agent = Agent(
            role="Embedded Dev — Eve Robot",
            goal=(
                "Écrire et déployer les scripts Python/C qui font fonctionner Eve robot. "
                "Assurer la connexion fiable entre Eve, naia-embodied et le Hub ALNUA."
            ),
            backstory=crew_backstory("embedded_dev"),
            tools=[
                pi_ssh_tool,
                robotics_edge_tool,
                deploy_pi_tool,
                eve_code_tool,
            ],
            llm=_build_llm(),
            max_iter=CREWAI_MAX_ITER_DEFAULT,
            verbose=True,
        )

    @trace_agent("embedded_dev_agent")
    def handle_instruction(self, instruction: str) -> str:
        from skills.skill_agent_learning import get_learning_context, record_task_learning

        memory_block = get_learning_context("embedded_dev", instruction)
        task = Task(
            description=instruction + memory_block,
            agent=self.agent,
            expected_output="Code déployé sur Pi, PR créée, ou rapport de statut Eve.",
        )
        crew = Crew(agents=[self.agent], tasks=[task])
        _result = str(crew.kickoff())
        try:
            record_task_learning(agent_id="embedded_dev", task=instruction, outcome=_result)
        except Exception:
            pass
        return _result
