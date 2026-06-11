"""
agents/hardware_agent.py

Agent CrewAI — Hardware (Pôle Robotique)

Robot : Eve (Raspberry Pi + Python/C + caméras + micros + servomoteurs)
Responsabilités :
- Architecture hardware Eve robot
- Sélection composants (Pi, Arduino, caméras, micros, moteurs)
- BOM (Bill of Materials) avec fournisseurs et prix
- Design produit et contraintes mécaniques
- Connexion avec Embedded Dev pour l'implémentation

Tools (max 5) : supplier_search, bom_manager, hardware_docs, component_specs, budget_tracker
Règle : Toujours fournir alternatives budget (AliExpress) et pro (Mouser/Farnell).
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from typing import Any

from crewai import Agent, Crew, LLM, Task
from crewai.tools import tool

from database.supabase_client import get_supabase

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


@tool("component_search")
def component_search_tool(query: str) -> str:
    """
    Recherche et compare des composants hardware pour Eve robot.
    Input : description du composant (ex: "caméra HD basse latence Raspberry Pi")
    """
    return f"""Recherche composant : {query}

**Options recommandées :**

Option Pro (fiable, rapide) :
- [Composant X] — Mouser/Farnell — ~[prix]€
- Avantages : [specs], [garantie]
- Lien : https://www.mouser.fr/

Option Budget (délai 2-4 semaines) :
- [Composant Y] — AliExpress — ~[prix]€
- Avantages : économique pour prototype
- Lien : https://www.aliexpress.com/

Compatibilité Raspberry Pi 4/5 : ✅/⚠️/❌
GPIO requis : [liste pins]
Alimentation : [voltage/amperage]

Documentation : [lien datasheet]
Bibliothèque Python : [pip install ...]"""


@tool("bom_manager")
def bom_manager_tool(action_json: str) -> str:
    """
    Gère le BOM (Bill of Materials) d'Eve robot dans Supabase.
    Input JSON : action (add|list|update|total), component, category, quantity, etc.
    """
    try:
        data = json.loads(action_json)
        action = data.get("action", "list")
        sb = get_supabase()

        if action == "total":
            rows = sb.select("bom_eve")
            total = sum(
                float(r.get("total_price") or 0)
                for r in rows
                if r.get("total_price") is not None
            )
            return f"💰 BOM Eve Robot — Total estimé : {total:.2f}€ ({len(rows)} composants)"

        if action == "add":
            row = {
                "component": data["component"],
                "category": data.get("category", "autre"),
                "quantity": data.get("quantity", 1),
                "unit_price": data.get("unit_price"),
                "supplier": data.get("supplier"),
                "url": data.get("url"),
                "status": data.get("status", "a_commander"),
                "notes": data.get("notes"),
            }
            sb.insert("bom_eve", row)
            return (
                f"✅ Composant ajouté au BOM : {data.get('component')} "
                f"x{data.get('quantity', 1)} — {data.get('unit_price', '?')}€ "
                f"chez {data.get('supplier', '?')}"
            )

        if action == "list":
            rows = sb.select("bom_eve", order_by="created_at", ascending=False)
            if not rows:
                return "BOM Eve Robot vide — utilise action=add pour ajouter des composants."
            lines = [
                "| Composant | Qté | Prix unit | Fournisseur | Statut |",
                "|---|---|---|---|---|",
            ]
            for r in rows:
                lines.append(
                    f"| {r['component']} | {r.get('quantity', 1)} | "
                    f"{r.get('unit_price', '?')}€ | {r.get('supplier', '?')} | "
                    f"{r.get('status', '?')} |"
                )
            return "\n".join(lines)

        if action == "update" and data.get("id"):
            updates: dict[str, Any] = {
                k: data[k]
                for k in (
                    "component",
                    "category",
                    "quantity",
                    "unit_price",
                    "supplier",
                    "url",
                    "status",
                    "notes",
                )
                if k in data
            }
            sb.update("bom_eve", data["id"], updates)
            return f"✅ Composant BOM mis à jour : {data['id']}"

        return f"Action BOM '{action}' exécutée."
    except Exception as e:
        return f"❌ Erreur BOM : {e}"


@tool("hardware_architecture")
def hardware_arch_tool(request: str) -> str:
    """
    Génère ou consulte l'architecture hardware d'Eve robot.
    Input : question ou demande de spec (ex: "schéma connexion servomoteurs Pi")
    """
    return f"""Architecture Hardware Eve Robot — {request}

**Cerveau :** Raspberry Pi 5 (8GB RAM)
- OS : Raspberry Pi OS Lite (64-bit)
- Connexion : WiFi + Ethernet
- Interface naia-embodied : HTTP/WebSocket vers Supabase Edge Function

**Vision :**
- OAK-D Lite (depth + RGB, DepthAI/OpenCV)
- Grounding DINO (déjà intégré dans Hub) pour détection objets

**Audio :**
- Micro : ReSpeaker 2-Mics HAT ou USB mic
- Speaker : USB DAC + ampli PAM8403

**Mobilité :**
- 4x Servomoteurs MG996R (tête + bras)
- Contrôleur : PCA9685 via I2C (16 canaux PWM)
- Alimentation servo : 5-6V séparé du Pi

**Alimentation :**
- Pi 5 : USB-C 5V/5A (officiel)
- Servos : LiPo 2S (7.4V) + régulateur 5V

**Communication :**
- Pi → Hub : HTTP POST vers API ALNUA
- Hub → Pi : WebSocket ou SSH tunnel
- Pi → Supabase : Edge Function naia-embodied

**GPIO Map (à détailler selon design final) :**
- I2C : SDA=GPIO2, SCL=GPIO3 → PCA9685
- SPI : réservé si capteurs additionnels
- UART : réservé debug

Note : Consulte Embedded Dev pour l'implémentation Python/C."""


class HardwareAgent:
    def __init__(self, telegram_notify_fn: Callable[[str], None] | None = None):
        self.agent = Agent(
            role="Hardware Engineer",
            goal=(
                "Concevoir l'architecture hardware d'Eve robot. "
                "Sélectionner les meilleurs composants (rapport qualité/prix). "
                "Fournir des specs claires à Embedded Dev pour l'implémentation."
            ),
            backstory=(
                "Tu es le Lead Hardware Engineer d'ALNUA, spécialiste robotique embarquée. "
                "Tu maîtrises Raspberry Pi, Arduino, électronique (I2C, SPI, UART, PWM), "
                "impression 3D et supply chain composants. "
                "Tu connais les fournisseurs : Mouser, Farnell, RS, Pimoroni, AliExpress. "
                "Tu proposes toujours une option pro ET une option budget."
            ),
            tools=[
                component_search_tool,
                bom_manager_tool,
                hardware_arch_tool,
            ],
            llm=_build_llm(),
            max_iter=6,
            verbose=True,
        )

    def handle_instruction(self, instruction: str) -> str:
        task = Task(
            description=instruction,
            agent=self.agent,
            expected_output="Spec hardware, BOM mis à jour, ou recommandations composants.",
        )
        crew = Crew(agents=[self.agent], tasks=[task])
        return str(crew.kickoff())
