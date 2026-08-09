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
export function deptV2TopTabs(deptHref: string) {
  return [
    { icon: "☰", label: "Vue générale", href: ROUTES.home, active: false },
    { icon: "▦", label: "Départements", href: deptHref, active: true },
    { icon: "◈", label: "Missions", href: ROUTES.tickets, active: false },
    { icon: "📈", label: "Analytics", href: ROUTES.analytics, active: false },
    { icon: "🗂", label: "Ressources", href: ROUTES.library, active: false },
  ] as const;
}
