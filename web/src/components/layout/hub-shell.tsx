"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ConsoleShell } from "@/components/console/console-shell";
import { ConsoleProvider } from "@/components/console/console-provider";
import { HubAuthBanner } from "@/components/shared/hub-auth-banner";
import { HubNavigationProvider } from "@/components/layout/hub-navigation";
import { prefetchLobby } from "@/lib/hq-prefetch";
import { dynamicWithChunkRetry } from "@/lib/dynamic-chunk-retry";
import { CONSOLE_IDE, CONSOLE_HQ } from "@/lib/console/nav";
import { isPublicPortalRoute } from "@/lib/routes";
import { Toaster } from "@/components/ui/sonner";
import { PROTO_SHELL_PATHS } from "@/components/mockup/prototype/proto-dept-routes";

const HubStatusMonitor = dynamicWithChunkRetry(() =>
  import("@/components/shared/hub-status-monitor").then((m) => ({
    default: m.HubStatusMonitor,
  })),
);

const CooDrawer = dynamicWithChunkRetry(() =>
  import("@/components/shared/coo-drawer").then((m) => ({
    default: m.CooDrawer,
  })),
);

const QuickCaptureButton = dynamicWithChunkRetry(() =>
  import("@/components/shared/quick-capture-button").then((m) => ({
    default: m.QuickCaptureButton,
  })),
);

/** Canonical dept routes re-export *-v2 (AGENTIC OS maquettes) + alias *-v2. */
const LIVE_V2_CANONICAL = [
  "/app",
  "/gaming",
  "/robo",
  "/marketing",
  "/finances",
  "/rd",
] as const;

/** Self-contained live shells (DeptV2 / BrandView) — no ConsoleShell wrap. */
const SELF_CONTAINED_V2_ROUTES = [
  ...LIVE_V2_CANONICAL,
  "/app-v2",
  "/gaming-v2",
  "/robo-v2",
  "/rnd-v2",
  "/marketing-v2",
  "/finances-v2",
  "/ceo",
  "/secretary",
  "/legal",
  "/hq",
  "/brand",
  "/hub",
  "/analytics",
];

/** Residual mockup ProtoFullShell — none for primary dept routes (clean 2026-08-09). */
const DEPT_SHELL_ROUTES = PROTO_SHELL_PATHS.filter(
  (route) =>
    !(LIVE_V2_CANONICAL as readonly string[]).includes(route) &&
    !(SELF_CONTAINED_V2_ROUTES as readonly string[]).includes(route),
);

function isSelfContainedV2(pathname: string): boolean {
  return SELF_CONTAINED_V2_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );
}

function isDeptShellRoute(pathname: string): boolean {
  return DEPT_SHELL_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );
}

export function HubShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = isPublicPortalRoute(pathname);
  const isHqImmersive = pathname === CONSOLE_HQ;
  const isIdeImmersive = pathname === CONSOLE_IDE;
  const isProjectDetail = pathname?.startsWith("/projects/") ?? false;
  const isSelfContainedV2Page = isSelfContainedV2(pathname);
  const isDeptShell = isDeptShellRoute(pathname);
  const isImmersive =
    isHqImmersive || isIdeImmersive || isProjectDetail || isSelfContainedV2Page;
  const showAuthBanner = !isPublic && !isImmersive && !isDeptShell;

  useEffect(() => {
    if (!isPublic && !isImmersive && !isDeptShell) {
      prefetchLobby(router);
    }
  }, [isImmersive, isDeptShell, isPublic, router]);

  if (isPublic) {
    return (
      <>
        {children}
        <Toaster
          theme="dark"
          position="bottom-center"
          toastOptions={{
            classNames: {
              toast: "bg-surface border-copper/15 text-ivory/90",
            },
          }}
        />
      </>
    );
  }

  if (isImmersive) {
    return (
      <HubNavigationProvider>
        {isHqImmersive ? <HubStatusMonitor /> : null}
        <main className="fixed inset-0 z-0 flex h-[100dvh] w-full flex-col overflow-hidden p-0">
          {children}
        </main>
        <Toaster
          theme="dark"
          position="bottom-left"
          toastOptions={{
            classNames: {
              toast: "bg-surface border-copper/15 text-ivory/90",
            },
          }}
        />
        <CooDrawer />
      </HubNavigationProvider>
    );
  }

  // Pôles : pages auto-contenues (shell maquette ChatGPT dans MockupDepartmentPage)
  if (isDeptShell) {
    return (
      <HubNavigationProvider>
        <ConsoleProvider>
          {children}
          <Toaster
            theme="dark"
            position="bottom-left"
            toastOptions={{
              classNames: {
                toast: "bg-surface border-copper/15 text-ivory/90",
              },
            }}
          />
        </ConsoleProvider>
      </HubNavigationProvider>
    );
  }

  // Vue générale + reste console — shell d'origine, non touché
  return (
    <HubNavigationProvider>
      {showAuthBanner ? <HubAuthBanner /> : null}
      <ConsoleShell>{children}</ConsoleShell>
      <QuickCaptureButton />
      <CooDrawer />
      <Toaster
        theme="dark"
        position="bottom-left"
        toastOptions={{
          classNames: {
            toast: "bg-surface border-copper/15 text-ivory/90",
          },
        }}
      />
    </HubNavigationProvider>
  );
}
