/** Agent Lounge — labels + assets calés sur la maquette. */

export type LoungeActivityId =
  | "arcade"
  | "strategy"
  | "puzzle"
  | "code_challenge"
  | "simulation"
  | "exploration"
  | "creative";

export type LoungeActivity = {
  id: LoungeActivityId;
  label: string;
  blurb: string;
  image?: string;
  accent: string;
  status: "soon" | "live";
};

export const LOUNGE_ACTIVITIES: LoungeActivity[] = [
  {
    id: "arcade",
    label: "Arcade",
    blurb: "Jeux d’arcade rétro-futuristes — Action, Course, Shooter…",
    image: "/lounge/act-arcade.png?v=9",
    accent: "rgba(168, 85, 247, 0.35)",
    status: "live",
  },
  {
    id: "strategy",
    label: "Stratégie",
    blurb: "Échecs, Go, stratégie temps réel — défis tactiques.",
    image: "/lounge/act-strategy.png?v=9",
    accent: "rgba(224, 155, 106, 0.35)",
    status: "live",
  },
  {
    id: "puzzle",
    label: "Puzzles",
    blurb: "Casse-têtes, Sudoku, labyrinthes — exerce ta logique.",
    image: "/lounge/act-puzzle.png?v=9",
    accent: "rgba(96, 165, 250, 0.3)",
    status: "live",
  },
  {
    id: "code_challenge",
    label: "Code Challenge",
    blurb: "Compétitions de code — algorithmique, optimisation.",
    image: "/lounge/act-code_challenge.png?v=9",
    accent: "rgba(45, 212, 191, 0.3)",
    status: "live",
  },
  {
    id: "simulation",
    label: "Simulations",
    blurb: "Simulateurs & scénarios — robots, villes, écosystèmes.",
    image: "/lounge/act-simulation.png?v=9",
    accent: "rgba(56, 189, 248, 0.3)",
    status: "live",
  },
  {
    id: "exploration",
    label: "Exploration",
    blurb: "Exploration libre & recherche — découvertes.",
    image: "/lounge/act-exploration.png?v=9",
    accent: "rgba(99, 102, 241, 0.3)",
    status: "live",
  },
  {
    id: "creative",
    label: "Creative Lab",
    blurb: "Écriture, concepts, storytelling, idées.",
    image: "/lounge/act-creative.png?v=1",
    accent: "rgba(244, 114, 182, 0.28)",
    status: "live",
  },
];

export const ACTIVITY_LABELS: Record<LoungeActivityId, string> = {
  arcade: "Arcade",
  strategy: "Stratégie",
  puzzle: "Puzzle",
  code_challenge: "Code Duel",
  simulation: "Simulation",
  exploration: "Exploration",
  creative: "Creative",
};
