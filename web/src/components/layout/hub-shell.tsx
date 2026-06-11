"use client";

import { usePathname } from "next/navigation";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { CooDrawer } from "@/components/shared/coo-drawer";
import { QuickCaptureButton } from "@/components/shared/quick-capture-button";
import { Toaster } from "@/components/ui/sonner";
import { isDepartmentRoute, isPublicPortalRoute } from "@/lib/routes";
import { cn } from "@/lib/utils";

export function HubShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublic = isPublicPortalRoute(pathname);
  const isLobby = pathname === "/";
  const showBackToLobby = !isPublic && !isLobby && !isDepartmentRoute(pathname);

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
    <>
      {showBackToLobby ? <BackToLobby /> : null}
      <main
        className={
          isLobby
            ? "relative min-h-screen"
            : cn(
                "relative mx-auto min-h-screen max-w-7xl px-6 py-8",
                showBackToLobby && "pt-16"
              )
        }
      >
        {children}
      </main>
      {!isLobby ? <QuickCaptureButton /> : null}
      {!isLobby ? <CooDrawer /> : null}
      <Toaster
        theme="dark"
        position="bottom-left"
        toastOptions={{
          classNames: {
            toast: "bg-surface border-white/10 text-ivory/90",
          },
        }}
      />
    </>
  );
}
