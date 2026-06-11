"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { QuickCaptureButton } from "@/components/shared/quick-capture-button";
import { Toaster } from "@/components/ui/sonner";

/** Public portal routes skip the Hub chrome (sidebar, quick capture). */
function isPublicPortalRoute(pathname: string | null): boolean {
  if (!pathname) return false;
  return (
    /^\/beta\/[^/]+$/.test(pathname) ||
    /^\/waitlist\/[^/]+$/.test(pathname) ||
    pathname === "/partnerships"
  );
}

export function HubShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublic = isPublicPortalRoute(pathname);

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
