"""COO Agent — orchestrateur central ALNUA (CrewAI + Supabase)."""

from __future__ import annotations

import logging

from database.supabase_client import SupabaseClient, get_supabase

from agents.coo_briefing import COOBriefingMixin
from agents.coo_composio_tools import (  # noqa: F401 — re-export façade
    connect_app_oauth,
    create_calendar_event,
    create_github_issue_via_composio,
    search_knowledge_base,
    send_email_via_gmail,
)
from agents.coo_constants import (  # noqa: F401 — re-export façade
    COO_SYSTEM_PROMPT,
    IRREVERSIBLE_KEYWORDS,
    PROJECT_ALIASES,
    PROJECT_SCOPED_KEYWORDS,
)
from agents.coo_conversation import COOConversationMixin
from agents.coo_crew import COOCrewMixin
from agents.coo_delegates import COODelegatesMixin
from agents.coo_instruction import COOInstructionMixin
from agents.coo_intents import (  # noqa: F401 — re-export façade
    CODING_KEYWORDS,
    RND_KEYWORDS,
    RESEARCH_KEYWORDS,
    TEACH_KEYWORDS,
    _detect_research_intent,
    _detect_teach_intent,
    _extract_research_topic,
    _format_plan_execution_result,
    _is_standalone_rnd_research,
    _needs_plan_execution,
    detect_coding_intent,
    detect_target_repo,
)
from agents.coo_plan import COOPlanMixin
from agents.coo_project import COOProjectMixin
from agents.coo_routing import AGENT_KEYWORDS, route_to_agent  # noqa: F401

logger = logging.getLogger(__name__)


class COOAgent(
    COOProjectMixin,
    COOBriefingMixin,
    COODelegatesMixin,
    COOPlanMixin,
    COOCrewMixin,
    COOConversationMixin,
    COOInstructionMixin,
):
    """Agent COO — point d'entrée unique d'Emilie vers le système ALNUA."""

    AGENT_NAME = "coo_agent"

    def __init__(
        self,
        db: SupabaseClient | None = None,
        verbose: bool = False,
    ) -> None:
        self.db = db or get_supabase()
        self.verbose = verbose
        self._llm = None
        self._tools = None
        self._crew_agent = None


def main() -> None:
    """Boucle interactive pour tester le COO depuis le terminal."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    print("=" * 50)
    print("  ALNUA Hub — Agent COO")
    print("  Parle-moi en langage naturel.")
    print("  Commandes : briefing | exit")
    print("=" * 50)

    try:
        coo = COOAgent(verbose=True)
    except Exception as exc:
        print(f"\n[ERREUR] Impossible d'initialiser le COO : {exc}")
        print("Vérifie ton fichier .env (SUPABASE_URL, SUPABASE_KEY, OPENROUTER_API_KEY).")
        return

    while True:
        try:
            user_input = input("\nEmilie > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nÀ plus.")
            break

        if not user_input:
            continue

        lowered = user_input.lower()
        if lowered in ("exit", "quit", "q"):
            print("COO > Bonne session. À demain.")
            break

        if lowered == "briefing":
            try:
                print(f"\nCOO >\n{coo.run_daily_briefing()}")
            except Exception as exc:
                print(f"\nCOO > Erreur briefing : {exc}")
            continue

        try:
            response = coo.handle_instruction(user_input)
            print(f"\nCOO > {response}")
        except Exception as exc:
            print(f"\nCOO > Erreur : {exc}")


if __name__ == "__main__":
    main()
