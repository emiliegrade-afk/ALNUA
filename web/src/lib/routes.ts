/**
 * Canonical path constants — import these instead of hardcoding `href="/foo"`
 * in components. A renamed route only needs updating here; grep for the old
 * string elsewhere would otherwise miss any literal that slipped through.
 */
export const ROUTES = {
  home: "/",
  agents: "/agents",
  activity: "/activity",
  hq: "/hq",
  briefing: "/briefing",
  /** Agent Lounge — remplace OpenRoom / repas (DEC-031). */
  lounge: "/lounge",
  /** @deprecated Alias → `/lounge` (bookmarks & liens historiques). */
  openroom: "/lounge",
  competition: "/competition",
  ceo: "/ceo",
  secretary: "/secretary",
  /** Cockpit Nadia Live - taches en arriere-plan (DEC-038). */
  live: "/live",
  legal: "/legal",
  hub: "/hub",
  app: "/app",
  gaming: "/gaming",
  robo: "/robo",
  finances: "/finances",
  marketing: "/marketing",
  rd: "/rd",
  // Alias historiques — les pages /finances, /marketing, /rd, /app, /gaming,
  // /robo ré-exportent désormais les shells *-v2 (Phase B, 2026-08-09). Les
  // constantes *-V2 restent pour les liens absolus / bookmarks.
  rndV2: "/rnd-v2",
  marketingV2: "/marketing-v2",
  financesV2: "/finances-v2",
  brand: "/brand",
  analytics: "/analytics",
  connections: "/connections",
  ide: "/ide",
  academy: "/academy",
  library: "/library",
  docs: "/docs",
  userManual: "/docs/guides/user-manual",
  settings: "/settings",
  trust: "/trust",
  // Non-department utility routes also referenced from bureau components.
  tickets: "/tickets",
  content: "/content",
  roadmap: "/roadmap",
  apps: "/apps",
  beta: "/beta",
} as const;

export function ticketHref(id: string): string {
  return `${ROUTES.tickets}?id=${encodeURIComponent(id)}`;
}

export function loungeAgentHref(agentId: string): string {
  return `${ROUTES.lounge}?agent=${encodeURIComponent(agentId)}`;
}

/** @deprecated Prefer `loungeAgentHref`. */
export function openroomAgentHref(agentId: string): string {
  return loungeAgentHref(agentId);
}

export function rdDossierHref(dossierId: string): string {
  return `${ROUTES.rd}?tab=dossiers&dossier=${encodeURIComponent(dossierId)}`;
}

/** Department portal routes — console chrome + bureau pages. */
export const DEPARTMENT_ROUTES = [
  ROUTES.home,
  ROUTES.agents,
  ROUTES.activity,
  ROUTES.hq,
  ROUTES.briefing,
  ROUTES.lounge,
  ROUTES.competition,
  ROUTES.ceo,
  ROUTES.secretary,
  ROUTES.legal,
  ROUTES.hub,
  ROUTES.app,
  ROUTES.gaming,
  ROUTES.robo,
  ROUTES.finances,
  ROUTES.marketing,
  ROUTES.rd,
  ROUTES.brand,
  ROUTES.analytics,
  ROUTES.connections,
  ROUTES.ide,
  ROUTES.academy,
  ROUTES.library,
  ROUTES.settings,
  ROUTES.trust,
] as const;

export function isDepartmentRoute(pathname: string | null): boolean {
  if (!pathname) return false;
  return (DEPARTMENT_ROUTES as readonly string[]).includes(pathname);
}

/** Admin hub + tier-3 tools — BackToLobby provided by HubShell, not page shells. */
export function isAdminRoute(pathname: string | null): boolean {
  if (!pathname) return false;
  return pathname === "/admin" || pathname.startsWith("/admin/");
}

/** Legacy URL — brainstorm UI lives under /rd (tab brainstorm). */
export const BRAINSTORM_LEGACY_PATH = "/brainstorm";

export function isPublicPortalRoute(pathname: string | null): boolean {
  if (!pathname) return false;
  return (
    /^\/beta\/[^/]+$/.test(pathname) ||
    /^\/waitlist\/[^/]+$/.test(pathname) ||
    /^\/p\/[^/]+$/.test(pathname) ||
    pathname === "/partnerships"
  );
}
