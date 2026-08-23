"""
seed_knowledge.py — Nourrit Mem0 avec la connaissance structurée de tous les projets ALNUA.

Usage :
    python scripts/seed_knowledge.py

À relancer chaque fois que la situation d'un projet change significativement.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from skills.skill_mem0 import remember

# ---------------------------------------------------------------------------
# Connaissance globale ALNUA — COO + tous les agents
# ---------------------------------------------------------------------------

GLOBAL_KNOWLEDGE = [
    # Emilie & contexte
    "Emilie est CEO et seule humaine de la société virtuelle ALNUA (solopreneuse). Elle pilote plusieurs branches en parallèle : App (NUAWAY), Gaming (Wyrdheim), Robotique (Eve), plus le Hub IA.",
    "Emilie est débutante en code mais apprend très vite. Elle utilise Cursor et Claude comme co-pilotes. Toujours aller droit au but, pas de blabla.",
    "Objectif principal d'Emilie : que le Hub gère sa société de façon autonome pour qu'elle n'ait pas à s'inquiéter de la gestion au quotidien. Ne pas centrer les décisions ou le ton sur un mode de vie personnel.",

    # Architecture Hub
    "Le ALNUA Hub est une plateforme multi-agent : Next.js 14 (frontend port 3000) + FastAPI (API port 8000) + 12 agents spécialisés via CrewAI.",
    "Stack technique Hub : CrewAI, Supabase, Mem0 (mémoire persistante), Langfuse (monitoring), Composio (OAuth 250+ APIs), OpenHands (coding autonome), Chroma (base vectorielle).",
    "Le Hub tourne sur localhost en dev. Repo GitHub : emiliegrade-afk/ALNUA.",
]

# ---------------------------------------------------------------------------
# Projets par agent spécialisé
# ---------------------------------------------------------------------------

NUAWAY_KNOWLEDGE = [
    "NUAWAY (anciennement NOMAD) est un produit de la branche App ALNUA — pas l'identité de toute la société. Mix Park4Night + Signal pour voyageurs / vanlifers.",
    "NUAWAY est un produit App parmi d'autres priorités ALNUA (gaming, robotique, Hub) — arbitrage via la roadmap CEO.",
    "Repo GitHub NUAWAY : emiliegrade-afk/NUAWAY. Branche App ALNUA.",
    "Audience produit NUAWAY : voyageurs, vanlifers, roadtrippers. Fonctionnalités : spots, communauté, messagerie. Ne pas confondre avec le positionnement corporate ALNUA.",
    "Le local repo NUAWAY est à C:/Dev/nomad sur la machine d'Emilie (chemin historique du clone).",
]

NAIA_KNOWLEDGE = [
    "Naïa World est le projet Gaming/Monde 3D d'ALNUA. Un monde ouvert où Naïa est un personnage IA autonome dans un village médiéval.",
    "Naïa fonctionne avec des agents émergents — les PNJs apprennent et évoluent. Inspiré de Stanford Smallville.",
    "Repo GitHub Naïa : emiliegrade-afk/naia. Local : C:/Dev/naia.",
    "Naïa World est un nouveau projet, moins avancé que NUAWAY. Priorité secondaire après la beta NUAWAY.",
]

WYRDHEIM_KNOWLEDGE = [
    "Wyrdheim Online est un mod MMORPG de la branche Gaming ALNUA. Univers fantastique/mythologique.",
    "Wyrdheim a une communauté Discord. Le Discord bot n'est pas encore configuré (DISCORD_BOT_TOKEN vide).",
    "Wyrdheim utilise UE5 (Unreal Engine 5) et Nwiro pour la logique de mod. Toutes les tâches UE5 → dev_gaming agent uniquement.",
    "Le lore Wyrdheim est riche — écriture créative, game design, quêtes, personnages mythologiques.",
]

EVE_KNOWLEDGE = [
    "Eve est le projet Robotique d'ALNUA. Un agent embarqué sur Raspberry Pi.",
    "Eve est l'agent physique de la société — elle tourne sur un Pi et peut interagir avec le monde réel.",
    "Le Pi Eve n'est pas encore configuré (PI_HOST vide dans .env). Priorité après NUAWAY beta.",
    "BOM (Bill of Materials) Eve est géré dans Supabase (table bom_eve). Catégories : compute, motion, sensing, power, structure, communication.",
]

HUB_KNOWLEDGE = [
    "Le Hub a 12 agents : COO (orchestrateur), pm_agent, qa_agent, content_agent, brainstorm_agent, spec_agent, game_director, dev_gaming, dev_app, hardware, embedded, marketing.",
    "Les skills réutilisables sont dans api/skills/ : mem0, github, composio, supabase, chroma, langfuse, openhands, playwright, etc.",
    "Sécurité Hub : X-Hub-Key middleware sur toutes les routes sauf /health et /beta/*. RLS Supabase anon = SELECT only.",
    "Le COO peut créer des GitHub Issues via Composio. Les tickets sont aussi stockés dans Supabase.",
    "Auto-skill generation : depuis juin 2026, le Hub peut générer de nouveaux skills Python automatiquement via le SkillSynthesizer après chaque instruction réussie.",
]

ROADMAP_KNOWLEDGE = [
    "Roadmap Q2-Q3 2026 : 1) NUAWAY beta test (urgent), 2) Naïa World MVP, 3) Eve Raspberry Pi setup, 4) Wyrdheim Discord bot, 5) Auto-skill generation Hub.",
    "Priorités actuelles (juin 2026) : NUAWAY beta > Hub amélioration > Naïa > Eve > Wyrdheim Discord.",
    "Dette technique Hub : api/main.py est un monolithe 3500 lignes (P4). CORS/nginx/Docker prod non configuré (P3).",
]

# ---------------------------------------------------------------------------
# Mapping agent_id → knowledge à injecter
# ---------------------------------------------------------------------------

AGENT_KNOWLEDGE: dict[str, list[str]] = {
    "coo": GLOBAL_KNOWLEDGE + NUAWAY_KNOWLEDGE + NAIA_KNOWLEDGE + WYRDHEIM_KNOWLEDGE + EVE_KNOWLEDGE + HUB_KNOWLEDGE + ROADMAP_KNOWLEDGE,
    "pm_agent": GLOBAL_KNOWLEDGE + NUAWAY_KNOWLEDGE + NAIA_KNOWLEDGE + ROADMAP_KNOWLEDGE,
    "dev_app": GLOBAL_KNOWLEDGE + NUAWAY_KNOWLEDGE,
    "dev_gaming": GLOBAL_KNOWLEDGE + WYRDHEIM_KNOWLEDGE + NAIA_KNOWLEDGE,
    "hardware": GLOBAL_KNOWLEDGE + EVE_KNOWLEDGE,
    "embedded": GLOBAL_KNOWLEDGE + EVE_KNOWLEDGE,
    "game_director": GLOBAL_KNOWLEDGE + WYRDHEIM_KNOWLEDGE + NAIA_KNOWLEDGE,
    "content_agent": GLOBAL_KNOWLEDGE + NUAWAY_KNOWLEDGE + WYRDHEIM_KNOWLEDGE,
    "marketing": GLOBAL_KNOWLEDGE + NUAWAY_KNOWLEDGE,
    "qa_agent": GLOBAL_KNOWLEDGE + NUAWAY_KNOWLEDGE + HUB_KNOWLEDGE,
    "brainstorm_agent": GLOBAL_KNOWLEDGE + ROADMAP_KNOWLEDGE,
    "spec_agent": GLOBAL_KNOWLEDGE + HUB_KNOWLEDGE + NUAWAY_KNOWLEDGE,
}

# ---------------------------------------------------------------------------
# Injection
# ---------------------------------------------------------------------------

def seed_agent(agent_id: str, facts: list[str], user_id: str = "emilie") -> int:
    """Pousse une liste de faits dans Mem0 pour un agent donné. Retourne le nb injecté."""
    count = 0
    for fact in facts:
        try:
            remember(fact, agent_id=agent_id, user_id=user_id)
            count += 1
        except Exception as exc:
            print(f"  ⚠️  [{agent_id}] Erreur sur : {fact[:60]}... → {exc}")
    return count


def main() -> None:
    print("🧠 ALNUA Knowledge Seeder — injection dans Mem0\n")

    total = 0
    for agent_id, facts in AGENT_KNOWLEDGE.items():
        print(f"  → {agent_id} ({len(facts)} faits)...", end=" ", flush=True)
        n = seed_agent(agent_id, facts)
        print(f"✅ {n} injectés")
        total += n

    print(f"\n✅ Terminé — {total} faits injectés au total.")
    print("Les agents ont maintenant connaissance de tous les projets ALNUA.\n")


if __name__ == "__main__":
    main()
