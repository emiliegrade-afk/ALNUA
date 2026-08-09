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
  openroom: "/openroom",
  ceo: "/ceo",
  secretary: "/secretary",
  hub: "/hub",
  app: "/app",
  gaming: "/gaming",
  robo: "/robo",
  finances: "/finances",
  marketing: "/marketing",
  rd: "/rd",
  // Nouvelle DA R&D (Phase 22, ROADMAP.md) — coexiste avec /rd le temps de
  // la refonte multi-phases ; pas encore la route canonique (contrairement
  // à /app, /gaming, /robo qui sont déjà des alias vers leur -v2).
  rndV2: "/rnd-v2",
  // Marketing/Finances Command Center (Phase 29, ROADMAP.md) — même pattern
  // de coexistence que rndV2 : pas encore des alias de /marketing et
  // /finances pendant la refonte.
  marketingV2: "/marketing-v2",
  financesV2: "/finances-v2",
  brand: "/brand",
  analytics: "/analytics",
  connections: "/connections",
  ide: "/ide",
  academy: "/academy",
  library: "/library",
  settings: "/settings",
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

export function openroomAgentHref(agentId: string): string {
  return `${ROUTES.openroom}?agent=${encodeURIComponent(agentId)}`;
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
  ROUTES.openroom,
  ROUTES.ceo,
  ROUTES.secretary,
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
