"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="font-title text-2xl text-ivory">Une erreur est survenue</h1>
      <p className="max-w-md font-body text-sm text-titanium/80">
        {error.message || "Impossible de charger cette page."}
      </p>
      <div className="flex gap-3">
        <Button onClick={reset} variant="outline" className="border-copper/30">
          Réessayer
        </Button>
        <Button asChild className="bg-copper text-obsidian hover:bg-copper-light">
          <Link href="/">Retour au lobby</Link>
        </Button>
      </div>
    </div>
  );
}
