"""

skill_agent_learning.py — Boucle d'apprentissage universel ALNUA.



Chaque agent appelle learn_from_outcome() après chaque tâche.

Le LLM distille 1-2 leçons spécifiques au domaine de l'agent.

Les leçons sont écrites dans Mem0 sous l'agent_id concerné uniquement.



Usage :

    from skills.skill_agent_learning import learn_from_outcome

    learn_from_outcome(

        agent_id="marketing_agent",

        task="Rédiger post LinkedIn NUAWAY",

        outcome="Publié — 340 impressions, 12 likes, 2 partages",

        success=True,

    )

"""

from __future__ import annotations



from config.agent_models import memory_agent_id  # noqa: F401 — re-export façade



from skills.skill_agent_learning_compress import (  # noqa: F401 — re-export

    auto_compress_if_needed,

    compress_agent_memory,

)

from skills.skill_agent_learning_constants import LEARNING_LENS  # noqa: F401 — re-export

from skills.skill_agent_learning_context import (  # noqa: F401 — re-export

    get_learning_context,

    get_library_context,

    inject_learning_context,

)

from skills.skill_agent_learning_outcome import (  # noqa: F401 — re-export

    _distill_lessons,

    is_task_failure,

    learn_from_failure,

    learn_from_outcome,

    record_task_learning,

)



__all__ = [

    "LEARNING_LENS",

    "_distill_lessons",

    "auto_compress_if_needed",

    "compress_agent_memory",

    "get_learning_context",

    "get_library_context",

    "inject_learning_context",

    "is_task_failure",

    "learn_from_failure",

    "learn_from_outcome",

    "memory_agent_id",

    "record_task_learning",

]


