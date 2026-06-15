/** Department portal routes — lobby-style navigation with their own BackToLobby. */
export const DEPARTMENT_ROUTES = [
  "/",
  "/briefing",
  "/openroom",
  "/ceo",
  "/secretary",
  "/hub",
  "/app",
  "/gaming",
  "/robo",
  "/finances",
  "/marketing",
  "/rd",
  "/brand",
  "/analytics",
  "/connections",
  "/academy",
  "/settings",
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
