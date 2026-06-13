/** Department portal routes — lobby-style navigation with their own BackToLobby. */
export const DEPARTMENT_ROUTES = [
  "/",
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
  "/settings",
] as const;

export function isDepartmentRoute(pathname: string | null): boolean {
  if (!pathname) return false;
  return (DEPARTMENT_ROUTES as readonly string[]).includes(pathname);
}

export function isPublicPortalRoute(pathname: string | null): boolean {
  if (!pathname) return false;
  return (
    /^\/beta\/[^/]+$/.test(pathname) ||
    /^\/waitlist\/[^/]+$/.test(pathname) ||
    /^\/p\/[^/]+$/.test(pathname) ||
    pathname === "/partnerships"
  );
}
