import type { BetaFeedbackType, BetaSeverity } from "@/lib/beta-api";

export const BETA_FEEDBACK_TYPES: {
  id: BetaFeedbackType;
  label: string;
  icon: string;
  titlePlaceholder: string;
  descriptionPlaceholder: string;
}[] = [
  {
    id: "bug",
    label: "Bug",
    icon: "🐛",
    titlePlaceholder: "Ex : le bouton Enregistrer ne répond pas",
    descriptionPlaceholder:
      "Décris ce qui s'est passé, ce que tu attendais, et comment reproduire le bug.",
  },
  {
    id: "suggestion",
    label: "Suggestion",
    icon: "💡",
    titlePlaceholder: "Ex : ajouter un rappel quotidien",
    descriptionPlaceholder:
      "Partage ton idée et pourquoi elle t'aiderait dans ton usage de l'app.",
  },
  {
    id: "crash",
    label: "Crash",
    icon: "💥",
    titlePlaceholder: "Ex : l'app se ferme sur l'écran d'accueil",
    descriptionPlaceholder:
      "Décris à quel moment l'app plante et si tu as un message d'erreur.",
  },
  {
    id: "ux",
    label: "UX / Design",
    icon: "🎨",
    titlePlaceholder: "Ex : le texte est difficile à lire en mode sombre",
    descriptionPlaceholder:
      "Explique ce qui te gêne visuellement ou dans la navigation.",
  },
];

export const BETA_SEVERITIES: {
  id: BetaSeverity;
  label: string;
  className: string;
}[] = [
  {
    id: "bloquant",
    label: "Bloquant",
    className: "border-red-500/50 bg-red-500/15 text-red-300",
  },
  {
    id: "majeur",
    label: "Majeur",
    className: "border-orange-500/50 bg-orange-500/15 text-orange-300",
  },
  {
    id: "mineur",
    label: "Mineur",
    className: "border-amber-500/50 bg-amber-500/15 text-amber-300",
  },
  {
    id: "cosmétique",
    label: "Cosmétique",
    className: "border-slate-500/50 bg-slate-500/15 text-slate-300",
  },
];

export const BETA_TYPE_LABELS: Record<string, string> = {
  bug: "Bug",
  suggestion: "Suggestion",
  crash: "Crash",
  ux: "UX / Design",
  autre: "Autre",
};

export function severityStyle(severity: string | null | undefined): string {
  return (
    BETA_SEVERITIES.find((s) => s.id === severity)?.className ??
    "border-copper/15 bg-obsidian/50 text-titanium"
  );
}
