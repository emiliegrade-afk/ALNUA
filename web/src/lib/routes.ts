/** Department portal routes — lobby-style navigation with their own BackToLobby. */
export const DEPARTMENT_ROUTES = [
  "/",
  "/openroom",
  "/ceo",
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
    pathname === "/partnerships"
  );
}
