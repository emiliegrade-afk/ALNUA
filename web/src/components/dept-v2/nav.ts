import { ROUTES } from "@/lib/routes";

export const DEPT_V2_DASHBOARD_NAV = [
  { icon: "◉", label: "Command Center", href: ROUTES.home },
  { icon: "〰", label: "Activité en direct", href: ROUTES.activity },
  { icon: "▤", label: "Décisions", href: ROUTES.ceo, badge: true as const },
] as const;

export const DEPT_V2_TOOLS_NAV = [
  { icon: "📄", label: "Documents", href: "/docs" },
  { icon: "📖", label: "Connaissances", href: ROUTES.library },
  { icon: "🗒", label: "Modèles", href: ROUTES.settings },
  { icon: "⚙", label: "Automatisations", href: ROUTES.settings },
] as const;

export const DEPT_V2_ICONS: Record<string, string> = {
  hub: "◎",
  secretary: "🗂",
  legal: "⚖",
  rd: "◇",
  app: "▦",
  marketing: "📣",
  gaming: "🎮",
  robo: "🤖",
  finances: "💠",
  analytics: "📈",
  brand: "🎨",
};

/** Onglets header — `deptHref` = route canonique du département courant. */
export function deptV2TopTabs(
  deptHref: string,
  activeTab: "overview" | "dept" | "missions" | "analytics" | "resources" = "dept",
) {
  return [
    {
      icon: "☰",
      label: "Vue générale",
      href: ROUTES.home,
      active: activeTab === "overview",
    },
    {
      icon: "▦",
      label: "Départements",
      href: deptHref,
      active: activeTab === "dept",
    },
    {
      icon: "◈",
      label: "Missions",
      href: ROUTES.tickets,
      active: activeTab === "missions",
    },
    {
      icon: "📈",
      label: "Analytics",
      href: ROUTES.analytics,
      active: activeTab === "analytics",
    },
    {
      icon: "🗂",
      label: "Ressources",
      href: ROUTES.library,
      active: activeTab === "resources",
    },
  ] as const;
}
