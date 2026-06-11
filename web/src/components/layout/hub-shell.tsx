"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { QuickCaptureButton } from "@/components/shared/quick-capture-button";
import { Toaster } from "@/components/ui/sonner";
import { isDepartmentRoute, isPublicPortalRoute } from "@/lib/routes";

export function HubShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublic = isPublicPortalRoute(pathname);
  const isDepartment = isDepartmentRoute(pathname);
  const isLobby = pathname === "/";

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

  if (isDepartment) {
    return (
      <>
        <main
          className={
            isLobby
              ? "relative min-h-screen"
              : "relative mx-auto min-h-screen max-w-7xl px-6 py-8"
          }
        >
          {children}
        </main>
        {!isLobby ? <QuickCaptureButton /> : null}
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

  return (
    <>
      <Sidebar />
      <main className="relative min-h-screen pl-64">
        <div className="mx-auto max-w-7xl px-6 py-8">{children}</div>
      </main>
      <QuickCaptureButton />
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
