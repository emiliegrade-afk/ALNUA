/** Console navigation — maps export UI labels to Hub routes. */
export const CONSOLE_HOME = "/";
export const CONSOLE_AGENTS = "/agents";
export const CONSOLE_ACTIVITY = "/activity";
export const CONSOLE_HQ = "/hq";
export const CONSOLE_IDE = "/ide";
export const CONSOLE_ACADEMY = "/academy";
export const CONSOLE_LIBRARY = "/library";
export const CONSOLE_DOCS = "/docs";
export const CONSOLE_DECISIONS = "/ceo";

/**
 * Section « Tableau de bord » de la sidebar. `badge` désigne le compteur live
 * à afficher (résolu dans la sidebar depuis `useConsoleData()`), pas une
 * valeur figée — la maquette montre un « 2 » sur Décisions qui doit refléter
 * les arbitrages réellement en attente.
 */
export const TOP_NAV = [
  { id: "dashboard", label: "Command Center", href: CONSOLE_HOME },
  { id: "activity", label: "Activité en direct", href: CONSOLE_ACTIVITY },
  { id: "decisions", label: "Décisions", href: CONSOLE_DECISIONS, badge: "decisions" },
  { id: "agents", label: "Tous les agents", href: CONSOLE_AGENTS },
] as const;

/**
 * Section « Outils ». Les libellés suivent la maquette là où une vue réelle
 * existe derrière ; « Modèles »/« Automatisations » de la maquette n'ont pas
 * de page dédiée dans le Hub (les réglages modèles vivent dans Paramètres,
 * les automatisations dans n8n) — on ne crée pas d'entrées mortes pour eux.
 */
export const TOOL_NAV = [
  { id: "docs", label: "Documents", href: CONSOLE_DOCS },
  { id: "library", label: "Connaissances", href: CONSOLE_LIBRARY },
  { id: "ide", label: "IDE Hub", href: CONSOLE_IDE },
  { id: "academy", label: "Academy", href: CONSOLE_ACADEMY },
] as const;

export function consolePathTitle(pathname: string): {
  crumb: string;
  title: string;
  sub: string;
} {
  if (pathname === CONSOLE_HOME) {
    return {
      crumb: "ALNUA",
      title: "Vue d'ensemble",
      sub: "Console opérationnelle",
    };
  }
  if (pathname === CONSOLE_AGENTS) {
    return {
      crumb: "ALNUA",
      title: "Tous les agents",
      sub: "Équipe IA · pôles ALNUA",
    };
  }
  if (pathname === CONSOLE_ACTIVITY) {
    return { crumb: "ALNUA", title: "Activité", sub: "Flux temps réel" };
  }
  if (pathname === CONSOLE_HQ) {
    return { crumb: "ALNUA", title: "Départements", sub: "Annuaire des 11 pôles" };
  }
  if (pathname === CONSOLE_IDE) {
    return { crumb: "ALNUA / Outils", title: "IDE Hub", sub: "Code · Bac à sable · Agent live" };
  }
  if (pathname === CONSOLE_ACADEMY) {
    return {
      crumb: "ALNUA / Formation",
      title: "ALNUA Academy",
      sub: "Niveaux · Sprints · Validation agents",
    };
  }
  if (pathname === CONSOLE_LIBRARY) {
    return {
      crumb: "ALNUA / Archives",
      title: "Bibliothèque",
      sub: "Recherche · archives · rapport CEO",
    };
  }
  if (pathname === "/settings") {
    return { crumb: "ALNUA / Système", title: "Paramètres", sub: "Configuration Hub" };
  }
  return {
    crumb: "ALNUA / Pôles",
    title: pathname.replace("/", "").toUpperCase(),
    sub: "Espace département",
  };
}

export function isConsoleChromeRoute(pathname: string | null): boolean {
  if (!pathname) return false;
  if (pathname === CONSOLE_IDE) return false;
  return true;
}
