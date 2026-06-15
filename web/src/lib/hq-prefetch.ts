import {
  HQ_HUB_IMAGE_WEBP,
  HQ_MAP_OFFICES,
} from "@/lib/hq-hub-offices";
import { DEPARTMENT_ROUTES } from "@/lib/routes";

type PrefetchRouter = { prefetch: (href: string) => void };

/** Unique bureau routes shown on the HQ floor plan. */
export const HQ_OFFICE_ROUTES = Array.from(
  new Set(HQ_MAP_OFFICES.map((office) => office.href)),
);

const prefetched = new Set<string>();
let lobbyMapWarmed = false;

/** Prefetch a single office route (idempotent). */
export function prefetchOfficeRoute(router: PrefetchRouter, href: string): void {
  if (href === "/" || prefetched.has(href)) return;
  prefetched.add(href);
  router.prefetch(href);
}

/** Call on pointerdown / touchstart — warms chunk before click completes. */
export function prefetchOfficeRouteOnIntent(
  router: PrefetchRouter,
  href: string,
): void {
  prefetchOfficeRoute(router, href);
}

/** Decode the HQ map into the browser image cache for instant lobby return. */
export function warmLobbyMapCache(): void {
  if (lobbyMapWarmed || typeof window === "undefined") return;
  lobbyMapWarmed = true;
  const img = new window.Image();
  img.src = HQ_HUB_IMAGE_WEBP;
}

/** Prefetch lobby route + map asset together. */
export function prefetchLobby(router: PrefetchRouter): void {
  router.prefetch("/");
  warmLobbyMapCache();
}

/** Wave 1: all map destinations immediately (user may click within seconds). */
export function prefetchMapOfficeRoutes(router: PrefetchRouter): void {
  HQ_OFFICE_ROUTES.forEach((href) => prefetchOfficeRoute(router, href));
}

/** Wave 2: other department pages when the browser is idle. */
export function prefetchSecondaryDepartmentRoutes(router: PrefetchRouter): void {
  const secondary = DEPARTMENT_ROUTES.filter(
    (route) => route !== "/" && !HQ_OFFICE_ROUTES.includes(route),
  );
  secondary.forEach((href, index) => {
    const run = () => prefetchOfficeRoute(router, href);
    if (typeof requestIdleCallback !== "undefined") {
      requestIdleCallback(run, { timeout: 800 + index * 100 });
    } else {
      setTimeout(run, index * 60);
    }
  });
}

/** Warm all bureau destinations from the lobby. */
export function prefetchAllOfficeRoutes(router: PrefetchRouter): void {
  prefetchMapOfficeRoutes(router);
  prefetchSecondaryDepartmentRoutes(router);
}
