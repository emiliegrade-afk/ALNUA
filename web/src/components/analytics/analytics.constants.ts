import type { AnalyticsPeriod } from "@/lib/analytics";
import type { Project } from "@/lib/types";

export const PERIOD_OPTIONS: { id: AnalyticsPeriod; label: string }[] = [
  { id: "7d", label: "7 jours" },
  { id: "30d", label: "30 jours" },
  { id: "3m", label: "3 mois" },
  { id: "6m", label: "6 mois" },
  { id: "1y", label: "1 an" },
];

export const CHART_COLORS = {
  naia: "#22c55e",
  wyrdheim: "#f59e0b",
  eve: "#06b6d4",
  alnua: "#8b5cf6",
  revenue: "#22c55e",
  expense: "#f87171",
  mrr: "#c084fc",
  ivory: "#e8e4df",
  copper: "#c08a72",
} as const;

export const METRIC_OPTIONS = [
  { id: "downloads", label: "Téléchargements" },
  { id: "subscriptions", label: "Abonnements actifs" },
  { id: "mrr", label: "MRR" },
  { id: "churn", label: "Churn (%)" },
  { id: "web_visitors", label: "Visiteurs web" },
  { id: "active_users", label: "Utilisateurs actifs" },
] as const;

export const METRIC_SOURCES = [
  { id: "app_store", label: "App Store" },
  { id: "google_play", label: "Google Play" },
  { id: "stripe", label: "Stripe" },
  { id: "revenuecat", label: "RevenueCat" },
  { id: "plausible", label: "Plausible" },
] as const;

export const FEEDBACK_SOURCE_LABELS: Record<string, string> = {
  beta_portal: "Beta portal",
  discord: "Discord",
  app_store: "App Store",
  google_play: "Google Play",
  reddit: "Reddit",
  sav: "SAV",
};

export const EMPTY_STATE_MESSAGE =
  "Pas encore de données — les bots rempliront ça automatiquement quand tes apps seront en ligne. Tu peux aussi saisir des données manuellement.";

export function getProjectChartColor(project: Project): string {
  const name = project.name.toLowerCase();
  if (name.includes("naïa") || name.includes("naia")) return CHART_COLORS.naia;
  if (name.includes("wyrdheim")) return CHART_COLORS.wyrdheim;
  if (name.includes("eve")) return CHART_COLORS.eve;
  if (name.includes("alnua")) return CHART_COLORS.alnua;

  switch (project.branch) {
    case "app":
      return CHART_COLORS.naia;
    case "gaming":
      return CHART_COLORS.wyrdheim;
    case "robotics":
      return CHART_COLORS.eve;
    default:
      return CHART_COLORS.alnua;
  }
}

export function isActiveProject(project: Project): boolean {
  return project.status !== "paused";
}

export function formatChartDate(iso: string): string {
  const d = new Date(iso.slice(0, 10));
  return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

export function formatMonthLabel(ym: string): string {
  const [y, m] = ym.split("-");
  const d = new Date(Number(y), Number(m) - 1, 1);
  return d.toLocaleDateString("fr-FR", { month: "short", year: "2-digit" });
}
