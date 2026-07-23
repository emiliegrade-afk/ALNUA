"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { BackToLobby } from "@/components/shared/back-to-lobby";

/**
 * Bureau-scoped error boundary — re-exported as-is by each department route's
 * error.tsx (same pattern as DepartmentRouteLoading). Catching the error here
 * instead of only at the root keeps a failure in one bureau from reading as
 * "the whole Hub is down", and keeps the user in context instead of bouncing
 * them to the generic app-wide boundary.
 */
export default function DepartmentRouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const pathname = usePathname();

  useEffect(() => {
    console.error(`[bureau:${pathname}]`, error);
  }, [error, pathname]);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 px-6 pt-16 text-center">
      <BackToLobby />
      <h1 className="font-title text-2xl text-ivory">Ce bureau a rencontré un problème</h1>
      <p className="max-w-md font-body text-sm text-titanium/80">
        {error.message || "Impossible de charger cette section."}
      </p>
      {pathname ? (
        <p className="font-mono text-[11px] uppercase tracking-[0.12em] text-titanium/40">
          {pathname}
        </p>
      ) : null}
      <Button onClick={reset} variant="outline" className="border-copper/30">
        Réessayer
      </Button>
    </div>
  );
}
