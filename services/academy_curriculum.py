"""ALNUA Academy curriculum — 52 exercices N1→N4 (Super Plan Phase 2)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AcademyExercise:
    exercise_id: str
    level: int
    title: str
    description: str
    files_to_create: list[str] = field(default_factory=list)
    files_to_modify: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    stack: str = "react_native_expo"

    def github_title(self) -> str:
        return f"[ACADEMY {self.exercise_id}] {self.title}"

    def issue_body(self) -> str:
        create = "\n".join(f"- {p}" for p in self.files_to_create) or "- (déterminer selon le repo)"
        modify = "\n".join(f"- {p}" for p in self.files_to_modify) or "- (aucun)"
        tests = "\n".join(f"- {p}" for p in self.tests) or "- npm test (si configuré)"
        return f"""## Stack
{self.stack}

## Description
{self.description}

## Fichiers à créer
{create}

## Fichiers à modifier
{modify}

## Tests
{tests}

## Contexte additionnel
Exercice Académie ALNUA — Niveau {self.level} ({self.exercise_id}). Repo jamais publié.
"""


def _n1() -> list[AcademyExercise]:
    return [
        AcademyExercise(
            "N1.1",
            1,
            "Scaffold Expo + TypeScript + navigation tabs",
            "Initialiser ou compléter un projet Expo Router avec 3 tabs (Home, Map, Profile). "
            "Structure propre, TypeScript strict.",
            files_to_create=["app/(tabs)/_layout.tsx", "app/(tabs)/index.tsx", "app/(tabs)/map.tsx", "app/(tabs)/profile.tsx"],
            tests=["npx expo export --platform web (smoke) ou npm test"],
        ),
        AcademyExercise(
            "N1.2",
            1,
            "Client Supabase + variables d'environnement",
            "Configurer @supabase/supabase-js avec EXPO_PUBLIC_SUPABASE_URL et EXPO_PUBLIC_SUPABASE_ANON_KEY. "
            "Exporter un client singleton depuis lib/supabase.ts.",
            files_to_create=["lib/supabase.ts", ".env.example"],
            tests=["lib/supabase.ts compile sans erreur"],
        ),
        AcademyExercise(
            "N1.3",
            1,
            "Auth email/password — inscription",
            "Écran signup : email, password, confirmation. Appel supabase.auth.signUp. "
            "Gestion erreurs utilisateur (toast ou Text).",
            files_to_create=["app/(auth)/signup.tsx"],
            files_to_modify=["app/_layout.tsx"],
            tests=["Parcours signup mocké ou test composant"],
        ),
        AcademyExercise(
            "N1.4",
            1,
            "Auth email/password — connexion + session",
            "Écran login + persistance session (auto refresh). Redirection vers tabs si session active.",
            files_to_create=["app/(auth)/login.tsx"],
            files_to_modify=["app/_layout.tsx", "lib/supabase.ts"],
            tests=["Session restaurée au reload"],
        ),
        AcademyExercise(
            "N1.5",
            1,
            "Routes protégées (redirect si non-auth)",
            "Guard : utilisateur non connecté → /login. Utilisateur connecté sur /login → /(tabs).",
            files_to_create=["hooks/useAuth.ts"],
            files_to_modify=["app/_layout.tsx"],
            tests=["Navigation guard manuelle documentée"],
        ),
        AcademyExercise(
            "N1.6",
            1,
            "Profil utilisateur CRUD (table profiles)",
            "Table profiles liée à auth.users. Écran édition display_name + avatar_url. RLS : user lit/écrit son profil.",
            files_to_create=["app/(tabs)/profile/edit.tsx", "supabase/migrations/001_profiles.sql"],
            files_to_modify=["app/(tabs)/profile.tsx"],
            tests=["Migration SQL valide", "Update profil"],
        ),
        AcademyExercise(
            "N1.7",
            1,
            "Logout + nettoyage session",
            "Bouton logout sur Profile. supabase.auth.signOut + reset navigation vers login.",
            files_to_modify=["app/(tabs)/profile.tsx", "hooks/useAuth.ts"],
            tests=["Logout remet sur login"],
        ),
        AcademyExercise(
            "N1.8",
            1,
            "Error boundaries + affichage erreurs réseau",
            "Composant ErrorBoundary + helper formatApiError pour messages utilisateur clairs.",
            files_to_create=["components/ErrorBoundary.tsx", "lib/errors.ts"],
            tests=["ErrorBoundary capture erreur enfant"],
        ),
        AcademyExercise(
            "N1.9",
            1,
            "Tests smoke auth (Jest)",
            "Configurer Jest/Testing Library si absent. 1 test : rendu écran login sans crash.",
            files_to_create=["__tests__/login.test.tsx", "jest.config.js"],
            tests=["npm test -- --passWithNoTests"],
        ),
        AcademyExercise(
            "N1.10",
            1,
            "CI GitHub Actions (lint + test)",
            "Workflow .github/workflows/ci.yml : install, typecheck, npm test sur PR.",
            files_to_create=[".github/workflows/ci.yml"],
            tests=["Workflow YAML valide"],
        ),
    ]


def _n2() -> list[AcademyExercise]:
    return [
        AcademyExercise("N2.1", 2, "Permission géolocalisation + fallback", "Demander permission location. Message si refusé.", files_to_create=["hooks/useLocation.ts"], files_to_modify=["app/(tabs)/map.tsx"]),
        AcademyExercise("N2.2", 2, "Intégration Mapbox + token env", "Carte Mapbox ou react-native-maps selon deps. Token via EXPO_PUBLIC_MAPBOX_TOKEN.", files_to_create=["components/MapView.tsx", "lib/mapConfig.ts"], files_to_modify=[".env.example"]),
        AcademyExercise("N2.3", 2, "Afficher position utilisateur", "Blue dot / marker position actuelle centrée sur la carte.", files_to_modify=["components/MapView.tsx", "hooks/useLocation.ts"]),
        AcademyExercise("N2.4", 2, "Pins statiques (5 spots démo)", "5 markers hardcodés avec titre. Tap → bottom sheet résumé.", files_to_create=["data/demoSpots.ts", "components/SpotMarker.tsx"], files_to_modify=["components/MapView.tsx"]),
        AcademyExercise("N2.5", 2, "Fiche spot (bottom sheet)", "Composant SpotSheet : nom, description, distance.", files_to_create=["components/SpotSheet.tsx"]),
        AcademyExercise("N2.6", 2, "CRUD spots Supabase", "Table spots (name, lat, lng, type, owner_id). Insert depuis formulaire.", files_to_create=["supabase/migrations/002_spots.sql", "app/spot/new.tsx"], files_to_modify=["lib/supabase.ts"]),
        AcademyExercise("N2.7", 2, "Filtres spots (type, distance)", "Filtres UI + query Supabase filtrée.", files_to_create=["components/SpotFilters.tsx"], files_to_modify=["app/(tabs)/map.tsx"]),
        AcademyExercise("N2.8", 2, "Recherche texte spots", "Barre recherche + ilike sur name/description.", files_to_create=["components/SpotSearch.tsx"], files_to_modify=["app/(tabs)/map.tsx"]),
        AcademyExercise("N2.9", 2, "Upload photo spot → Storage", "Picker image + upload bucket spots + URL publique.", files_to_create=["lib/storage.ts"], files_to_modify=["app/spot/new.tsx"]),
        AcademyExercise("N2.10", 2, "Liste spots triée par distance", "FlatList spots proches, tri haversine.", files_to_create=["lib/geo.ts", "app/spots/index.tsx"]),
        AcademyExercise("N2.11", 2, "Tests carte + CRUD", "Test unitaire geo.ts + mock Supabase insert.", files_to_create=["__tests__/geo.test.ts"]),
        AcademyExercise("N2.12", 2, "Cache offline spots récents", "AsyncStorage cache 20 derniers spots consultés.", files_to_create=["lib/spotCache.ts"], files_to_modify=["app/(tabs)/map.tsx"]),
    ]


def _n3() -> list[AcademyExercise]:
    return [
        AcademyExercise("N3.1", 3, "Liste profils publics", "Écran communauté : liste profiles (display_name, avatar).", files_to_create=["app/(tabs)/community.tsx"]),
        AcademyExercise("N3.2", 3, "Chat 1-to-1 Supabase Realtime", "Tables messages + subscription channel par conversation.", files_to_create=["supabase/migrations/003_messages.sql", "app/chat/[id].tsx", "lib/chat.ts"]),
        AcademyExercise("N3.3", 3, "Liste conversations + unread", "Inbox avec dernier message et badge non-lu.", files_to_create=["app/(tabs)/messages.tsx", "hooks/useConversations.ts"]),
        AcademyExercise("N3.4", 3, "Notification in-app nouveau message", "Listener Realtime → toast ou badge tab Messages.", files_to_modify=["hooks/useConversations.ts", "app/(tabs)/_layout.tsx"]),
        AcademyExercise("N3.5", 3, "Blocage / signalement utilisateur", "Table reports + action block sur profil.", files_to_create=["supabase/migrations/004_reports.sql"], files_to_modify=["app/(tabs)/community.tsx"]),
        AcademyExercise("N3.6", 3, "Favoris spots (bookmark)", "Table favorites user_id + spot_id. Toggle sur fiche spot.", files_to_create=["supabase/migrations/005_favorites.sql"], files_to_modify=["components/SpotSheet.tsx"]),
        AcademyExercise("N3.7", 3, "Feed activité communauté", "Feed agrégé : nouveaux spots + messages récents (mock ou view SQL).", files_to_create=["components/ActivityFeed.tsx"], files_to_modify=["app/(tabs)/community.tsx"]),
        AcademyExercise("N3.8", 3, "Push notifications Expo", "Enregistrer Expo push token en base, handler réception.", files_to_create=["lib/push.ts"], files_to_modify=["app/_layout.tsx"]),
        AcademyExercise("N3.9", 3, "Tests chat Realtime", "Test mock subscription + format message.", files_to_create=["__tests__/chat.test.ts"]),
        AcademyExercise("N3.10", 3, "Rate limiting messages", "Max 10 messages/minute côté client + message d'attente.", files_to_modify=["lib/chat.ts", "app/chat/[id].tsx"]),
    ]


def _n4() -> list[AcademyExercise]:
    items: list[tuple[str, str, str]] = [
        ("N4.1", "Onboarding 3 écrans", "Flow onboarding : bienvenue, permissions, profil minimal."),
        ("N4.2", "Home = carte + spots proches", "Tab Home affiche carte centrée + 5 spots les plus proches."),
        ("N4.3", "Tab Map plein écran", "Refactor map en expérience plein écran avec filtres."),
        ("N4.4", "Tab Communauté intégrée", "Fusion feed + liste profils."),
        ("N4.5", "Tab Messages intégré", "Inbox + navigation vers chat."),
        ("N4.6", "Tab Profil + settings", "Profil, edit, logout, préférences notifications."),
        ("N4.7", "Empty states cohérents", "Composant EmptyState réutilisable sur listes vides."),
        ("N4.8", "Loading skeletons", "Skeletons carte, liste, chat."),
        ("N4.9", "Gestion erreurs réseau globale", "Retry banner + offline indicator."),
        ("N4.10", "Deep linking routes", "Liens spot/:id et chat/:id depuis notifications."),
        ("N4.11", "Thème couleurs nomade", "Palette tokens (sand, night, copper) dans theme.ts."),
        ("N4.12", "Accessibilité labels", "accessibilityLabel sur boutons principaux."),
        ("N4.13", "Perf images lazy", "expo-image avec placeholder sur avatars et spots."),
        ("N4.14", "Memo composants liste", "React.memo sur SpotRow et MessageRow."),
        ("N4.15", "EAS build config", "eas.json profils preview + env staging."),
        ("N4.16", "Test E2E parcours auth", "Test Detox ou Maestro : login → tabs."),
        ("N4.17", "Test E2E parcours carte", "Ouvrir map → voir pin → ouvrir fiche."),
        ("N4.18", "Test E2E parcours chat", "Ouvrir conversation → envoyer message."),
        ("N4.19", "README Academy complet", "Documenter setup, env, scripts, architecture."),
        ("N4.20", "Manifest build staging", "Script ou doc deploy EAS preview + checklist."),
    ]
    return [
        AcademyExercise(
            eid,
            4,
            title,
            desc + " Intégration mini-app NomadSpot — assembler les modules des niveaux précédents.",
            files_to_modify=["app/(tabs)/_layout.tsx"],
            tests=["npm test", "npx expo doctor"],
        )
        for eid, title, desc in items
    ]


def all_exercises() -> list[AcademyExercise]:
    return _n1() + _n2() + _n3() + _n4()


def exercises_for_level(level: int) -> list[AcademyExercise]:
    return [e for e in all_exercises() if e.level == level]


def exercise_by_id(exercise_id: str) -> AcademyExercise | None:
    for e in all_exercises():
        if e.exercise_id == exercise_id:
            return e
    return None


LEVEL_META: dict[int, dict[str, str | int]] = {
    1: {"name": "Fondations", "focus": "Auth, navigation, CRUD profil", "issues": 10},
    2: {"name": "Géoloc & carte", "focus": "Map, spots, filtres, cache", "issues": 12},
    3: {"name": "Social & Realtime", "focus": "Chat, communauté, push", "issues": 10},
    4: {"name": "NomadSpot intégré", "focus": "Assemblage + E2E + deploy", "issues": 20},
}
