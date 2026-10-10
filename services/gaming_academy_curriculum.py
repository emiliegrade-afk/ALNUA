"""Gaming Academy curriculum — compat wrapper (DEC-036).

Data moved to ``academy_curriculum_gaming.py``; generic types live in
``studio_academy_program.py``. This module only re-exports the historical API
so existing imports (router, tests, recipes) keep working unchanged.
"""

from services.academy_curriculum_gaming import GAME, LEVEL_META, POLE, SLUG, all_exercises, get_exercise
from services.studio_academy_program import StudioExercise, exercise_sort_key

__all__ = [
    "GAME",
    "LEVEL_META",
    "POLE",
    "SLUG",
    "StudioExercise",
    "all_exercises",
    "exercise_sort_key",
    "get_exercise",
]
