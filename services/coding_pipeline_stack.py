"""Stack detection and prompt rules for the coding pipeline."""

from __future__ import annotations

from services.coding_pipeline import DevStack

_STACK_HINTS: dict[DevStack, tuple[str, ...]] = {
    DevStack.REACT_NATIVE_EXPO: (
        "expo",
        "react-native",
        "react native",
        "app.tsx",
        "app.json",
        "eas.json",
        "detox",
        "securestore",
        "mapbox",
    ),
    DevStack.NEXTJS: (
        "next.js",
        "nextjs",
        "next.config",
        "app/page.tsx",
        "app router",
        "shadcn",
    ),
    DevStack.PYTHON_FASTAPI: (
        "fastapi",
        "pydantic",
        "api/main.py",
        "uvicorn",
        "pytest",
        "api/schemas",
    ),
    DevStack.TYPESCRIPT: ("typescript", "package.json"),
}

_REPO_DEFAULT_STACK: dict[str, DevStack] = {
    "academy": DevStack.REACT_NATIVE_EXPO,
    "hub": DevStack.PYTHON_FASTAPI,
}


def detect_stack(spec: dict) -> DevStack:
    """Infer target stack from issue spec (files, description, repo slug)."""
    explicit = (spec.get("stack") or "").strip().lower()
    if explicit:
        for stack in DevStack:
            if stack.value == explicit or explicit in stack.value:
                return stack
        if explicit in ("rn", "expo", "react-native"):
            return DevStack.REACT_NATIVE_EXPO
        if explicit in ("next", "nextjs"):
            return DevStack.NEXTJS
        if explicit in ("python", "fastapi", "api"):
            return DevStack.PYTHON_FASTAPI

    blob_parts = [
        spec.get("description") or "",
        spec.get("title") or "",
        " ".join(spec.get("files_to_create") or []),
        " ".join(spec.get("files_to_modify") or []),
        " ".join(spec.get("tests_to_pass") or []),
    ]
    blob = " ".join(blob_parts).lower()

    scores: dict[DevStack, int] = {s: 0 for s in DevStack}
    for stack, hints in _STACK_HINTS.items():
        for hint in hints:
            if hint in blob:
                scores[stack] += 1

    file_blob = " ".join(
        (spec.get("files_to_create") or [])
        + (spec.get("files_to_modify") or [])
    ).lower()
    if file_blob.endswith(".tsx") or ".tsx" in file_blob:
        scores[DevStack.REACT_NATIVE_EXPO] += 2
        scores[DevStack.NEXTJS] += 1
    elif file_blob.endswith(".ts") or ".ts" in file_blob:
        scores[DevStack.TYPESCRIPT] += 1

    best_score = max(scores.values())
    if best_score > 0:
        for stack in (
            DevStack.REACT_NATIVE_EXPO,
            DevStack.NEXTJS,
            DevStack.PYTHON_FASTAPI,
            DevStack.TYPESCRIPT,
        ):
            if scores[stack] == best_score:
                return stack

    slug = (spec.get("repo_slug") or spec.get("_repo_slug") or "").lower()
    return _REPO_DEFAULT_STACK.get(slug, DevStack.PYTHON_FASTAPI)


_STACK_PROMPTS: dict[DevStack, str] = {
    DevStack.PYTHON_FASTAPI: """STACK : Python 3.12 + FastAPI + Pydantic + Supabase.
- Logging via logger = logging.getLogger(__name__), jamais print()
- Variables d'env via os.getenv() + valeur par défaut
- Nouvelles deps → requirements.txt
- Tests : pytest dans tests/""",
    DevStack.REACT_NATIVE_EXPO: """STACK : React Native + Expo SDK 56 + TypeScript + Supabase JS.
- Pas de print() — utiliser console.warn en dev seulement si nécessaire
- Secrets dans .env / app.config — jamais hardcodés
- Navigation : Expo Router (app/ directory)
- Nouvelles deps Expo : versions ~56.x uniquement — jamais ~12.x (utiliser `npx expo install <pkg>`)
- Auth : @supabase/supabase-js ; session via supabase.auth
- Ne jamais créer de fichier vide ni de fichier hors arborescence app/lib/hooks/components
- Ne pas ajouter CLAUDE.md, AGENTS.md, .aider.* (réservés au Hub ALNUA, pas Academy)
- Tab bar : MaterialIcons (TabBarIcon) — jamais expo-symbols/SymbolView (crash web)
- Supprimer boilerplate Expo (EditScreenInfo, « Tab One ») — écran Accueil réel
- Géoloc : fallback coords par défaut si permission refusée (surtout web)
- UI : Pressable + StyleSheet — éviter Button RN brut sur web
- Tests : `npx tsc --noEmit` ET `npm test` doivent passer avant PR""",
    DevStack.NEXTJS: """STACK : Next.js 14+ App Router + TypeScript + Tailwind + shadcn/ui.
- Server Components par défaut ; 'use client' seulement si requis
- Appels API via web/src/lib/* — pas de fetch dans les composants UI
- Env : NEXT_PUBLIC_* pour le client, secrets côté serveur uniquement
- Tests : pytest backend OU playwright/jest selon le repo""",
    DevStack.TYPESCRIPT: """STACK : TypeScript strict (no any).
- Suivre la structure et les conventions du repo existant
- Tests selon le framework déjà configuré""",
}


def stack_expert_role(stack: DevStack) -> str:
    roles = {
        DevStack.PYTHON_FASTAPI: "expert Python/FastAPI backend",
        DevStack.REACT_NATIVE_EXPO: "expert React Native / Expo mobile",
        DevStack.NEXTJS: "expert Next.js App Router frontend",
        DevStack.TYPESCRIPT: "expert TypeScript fullstack",
    }
    return roles.get(stack, "expert développeur ALNUA")


def stack_rules_block(stack: DevStack) -> str:
    return _STACK_PROMPTS.get(stack, _STACK_PROMPTS[DevStack.PYTHON_FASTAPI])
