"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ConsoleShell } from "@/components/console/console-shell";
import { HubAuthBanner } from "@/components/shared/hub-auth-banner";
import { HubNavigationProvider } from "@/components/layout/hub-navigation";
import { prefetchLobby } from "@/lib/hq-prefetch";
import { CONSOLE_HQ, CONSOLE_IDE } from "@/lib/console/nav";
import { isPublicPortalRoute } from "@/lib/routes";
import { Toaster } from "@/components/ui/sonner";

const HubStatusMonitor = dynamic(
  () =>
    import("@/components/shared/hub-status-monitor").then((m) => ({
      default: m.HubStatusMonitor,
    })),
  { ssr: false },
);

const CooDrawer = dynamic(
  () =>
    import("@/components/shared/coo-drawer").then((m) => ({
      default: m.CooDrawer,
    })),
  { ssr: false },
);

const QuickCaptureButton = dynamic(
  () =>
    import("@/components/shared/quick-capture-button").then((m) => ({
      default: m.QuickCaptureButton,
    })),
  { ssr: false },
);

export function HubShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = isPublicPortalRoute(pathname);
  const isHqImmersive = pathname === CONSOLE_HQ;
  const isIdeImmersive = pathname === CONSOLE_IDE;
  // Département App : rend son propre chrome (en-tête, sidebar, barre de
  // commande) pour être un calque fidèle de la maquette source — elle ne
  // doit donc pas être enveloppée par ConsoleShell. /app-v2 reste un alias
  // de la même page pendant la transition.
  const isAppV2 = pathname === "/app-v2" || pathname === "/app";
  // Détail projet : plein écran avec un simple bouton retour, pas de sidebar
  // ni de chrome ConsoleShell (maquette dédiée "clic sur un projet").
  const isProjectDetail = pathname?.startsWith("/projects/") ?? false;
  // Département Gaming (nouvelle DA, validée le 2026-07-31) — /gaming est
  // désormais la vraie route ; /gaming-v2 reste un alias.
  const isGamingV2 = pathname === "/gaming-v2" || pathname === "/gaming";
  // Département Robotique — même bascule, /robo est la vraie route.
  const isRoboV2 = pathname === "/robo-v2" || pathname === "/robo";
  const isImmersive = isHqImmersive || isIdeImmersive || isAppV2 || isProjectDetail || isGamingV2 || isRoboV2;
  const showAuthBanner = !isPublic && !isImmersive;
  const isRdRoute = pathname === "/rd";

  useEffect(() => {
    if (!isPublic && !isImmersive) {
      prefetchLobby(router);
    }
  }, [isImmersive, isPublic, router]);

  if (isPublic) {
    return (
      <>
        {children}
        <Toaster
          theme="dark"
          position="bottom-center"
          toastOptions={{
            classNames: {
              toast: "bg-surface border-white/10 text-ivory/90",
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
              toast: "bg-surface border-white/10 text-ivory/90",
            },
          }}
        />
      </HubNavigationProvider>
    );
  }

  return (
    <HubNavigationProvider>
      {showAuthBanner ? <HubAuthBanner /> : null}
      <ConsoleShell>{children}</ConsoleShell>
      {!isRdRoute ? <QuickCaptureButton /> : null}
      {!isRdRoute ? <CooDrawer /> : null}
      <Toaster
        theme="dark"
        position="bottom-left"
        toastOptions={{
          classNames: {
            toast: "bg-surface border-white/10 text-ivory/90",
          },
        }}
      />
    </HubNavigationProvider>
  );
}
