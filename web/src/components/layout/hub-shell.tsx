"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { HubAuthBanner } from "@/components/shared/hub-auth-banner";
import { HubNavigationProvider } from "@/components/layout/hub-navigation";
import { prefetchLobby } from "@/lib/hq-prefetch";
import { isDepartmentRoute, isPublicPortalRoute } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { Toaster } from "@/components/ui/sonner";

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
  const isLobby = pathname === "/";
  const showBackToLobby = !isPublic && !isLobby && !isDepartmentRoute(pathname);
  const showAuthBanner = !isPublic;
  const isRdRoute = pathname === "/rd";

  useEffect(() => {
    if (!isPublic && !isLobby) {
      prefetchLobby(router);
    }
  }, [isLobby, isPublic, router]);

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

  return (
    <HubNavigationProvider>
      {showAuthBanner && !isLobby ? <HubAuthBanner /> : null}
      {showBackToLobby ? <BackToLobby /> : null}
      <main
        className={
          isLobby
            ? "relative h-[100dvh] w-full overflow-hidden p-0"
            : cn(
                "relative mx-auto min-h-screen max-w-7xl px-6 py-8",
                showBackToLobby && "pt-16"
              )
        }
      >
        {children}
      </main>
      {!isLobby && !isRdRoute ? <QuickCaptureButton /> : null}
      {!isLobby && !isRdRoute ? <CooDrawer /> : null}
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
