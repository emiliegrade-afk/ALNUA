/** Console navigation — maps export UI labels to Hub routes. */
export const CONSOLE_HOME = "/";
export const CONSOLE_AGENTS = "/agents";
export const CONSOLE_ACTIVITY = "/activity";
export const CONSOLE_HQ = "/hq";
export const CONSOLE_IDE = "/ide";
export const CONSOLE_ACADEMY = "/academy";
export const CONSOLE_LIBRARY = "/library";

export const TOP_NAV = [
  { id: "dashboard", label: "Vue d'ensemble", href: CONSOLE_HOME },
  { id: "agents", label: "Tous les agents", href: CONSOLE_AGENTS },
  { id: "activity", label: "Activité", href: CONSOLE_ACTIVITY },
  { id: "hq", label: "Vue HQ", href: CONSOLE_HQ },
] as const;

export const TOOL_NAV = [
  { id: "ide", label: "IDE Hub", href: CONSOLE_IDE },
  { id: "academy", label: "Academy", href: CONSOLE_ACADEMY },
  { id: "library", label: "Bibliothèque", href: CONSOLE_LIBRARY },
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
    return { crumb: "ALNUA", title: "Vue HQ", sub: "Plan interactif des bureaux" };
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
  if (pathname === CONSOLE_HQ || pathname === CONSOLE_IDE) return false;
  return true;
}
