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
from skills.skill_naia_embodied import call_naia_embodied
from skills.skill_pi_ssh import run_pi_command

logger = logging.getLogger(__name__)


def _build_llm() -> LLM:
    from config.settings import get_settings

    settings = get_settings()
    model = os.getenv("AGENT_MODEL", "openrouter/minimax/minimax-m1")
    if not model.startswith("openrouter/"):
        model = f"openrouter/{model}"
    return LLM(
        model=model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=0.3,
    )


@tool("pi_ssh_command")
def pi_ssh_tool(command_json: str) -> str:
    """
    Exécute une commande sur le Raspberry Pi Eve via SSH.
    Input JSON : {"command": "...", "timeout": 30}
    Utilise les variables d'env PI_HOST, PI_USER, PI_SSH_KEY.
    """
    try:
        data = json.loads(command_json)
        result = run_pi_command(data["command"], data.get("timeout", 30))
        if not result["success"] and result["host"] == "":
            return f"❌ {result['output']}"
        return f"Pi [{result['host']}] $ {result['command']}\n{result['output']}"
    except Exception as e:
        return f"❌ Erreur SSH : {e}"


@tool("naia_embodied_call")
def naia_embodied_tool(action_json: str) -> str:
    """
    Appelle la Edge Function naia-embodied sur Supabase.
    Input JSON : {"action": "speak|move|look|gesture|status", "params": {...}}
    """
    try:
        data = json.loads(action_json)
        result = call_naia_embodied(data["action"], data.get("params", {}))
        return f"naia-embodied → {result['status_code']} : {result['body'][:200]}"
    except Exception as e:
        return f"❌ Erreur naia-embodied : {e}"


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
            return "❌ PI_HOST non configuré"

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
            return f"❌ rsync échoué : {result.stderr}"

        output = f"✅ Code déployé sur Pi ({pi_host})"

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
        return f"❌ Erreur déploiement : {e}"


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
        result = execute_coding_task(spec)
        if result["success"]:
            return f"✅ PR Eve créée : {result['pr_url']}"
        return f"❌ Échec : {result['error']}"
    except Exception as e:
        return f"❌ Erreur : {e}"


class EmbeddedDevAgent:
    def __init__(self, telegram_notify_fn: Callable[[str], None] | None = None):
        self.agent = Agent(
            role="Embedded Dev — Eve Robot",
            goal=(
                "Écrire et déployer les scripts Python/C qui font fonctionner Eve robot. "
                "Assurer la connexion fiable entre Eve, naia-embodied et le Hub ALNUA."
            ),
            backstory=(
                "Tu es le développeur embarqué d'ALNUA, expert Raspberry Pi et robotique. "
                "Tu maîtrises Python pour Pi (RPi.GPIO, gpiozero, PCA9685, DepthAI), "
                "C/C++ pour firmware, et les protocoles I2C/SPI/UART/PWM. "
                "Tu sais déployer du code sur Pi via SSH/rsync. "
                "Tu connais le SDK HoloPlay pour Looking Glass. "
                "Tu penses toujours à la gestion des erreurs hardware (déconnexion, surchauffe)."
            ),
            tools=[
                pi_ssh_tool,
                naia_embodied_tool,
                deploy_pi_tool,
                eve_code_tool,
            ],
            llm=_build_llm(),
            max_iter=8,
            verbose=True,
        )

    def handle_instruction(self, instruction: str) -> str:
        task = Task(
            description=instruction,
            agent=self.agent,
            expected_output="Code déployé sur Pi, PR créée, ou rapport de statut Eve.",
        )
        crew = Crew(agents=[self.agent], tasks=[task])
        return str(crew.kickoff())
