"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  fetchAdminFlags,
  isAdminPageEnabled,
  type AdminFlags,
} from "@/lib/admin-flags-api";

const FLAG_HINTS: Record<string, string> = {
  costs: "ADMIN_COSTS_PAGE_ENABLED=1",
  events: "ADMIN_EVENTS_PAGE_ENABLED=1",
  "ab-test": "ADMIN_AB_TEST_PAGE_ENABLED=1",
};

export function AdminGate({
  page,
  title,
  children,
}: {
  page: "costs" | "events" | "ab-test";
  title: string;
  children: React.ReactNode;
}) {
  const [flags, setFlags] = useState<AdminFlags | null>(null);
  const [preview, setPreview] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Read preview and flags in one pass — avoids race where flags resolve before
    // the separate preview effect runs (breaks ?preview=1 when flags are off).
    const previewMode =
      new URLSearchParams(window.location.search).get("preview") === "1";

    fetchAdminFlags()
      .then((f) => {
        setPreview(previewMode);
        setFlags(f);
      })
      .catch(() => {
        setPreview(previewMode);
        setFlags(null);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-copper/60" />
      </div>
    );
  }

  const enabled = isAdminPageEnabled(flags, page, preview);

  if (!enabled) {
    return (
      <Card className="mx-auto mt-24 max-w-lg border-copper/20 bg-obsidian-2/90">
        <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
          <Lock className="h-10 w-10 text-copper/50" />
          <h1 className="font-title text-lg text-ivory">{title}</h1>
          <p className="font-body text-sm text-titanium/80">
            Cette page admin est désactivée. Active le flag dans{" "}
            <code className="rounded bg-obsidian px-1.5 py-0.5 text-copper-light">
              {FLAG_HINTS[page]}
            </code>{" "}
            puis redémarre l&apos;API.
          </p>
          {flags?.preview_allowed && (
            <p className="font-body text-xs text-titanium/60">
              Dev : ajoute{" "}
              <code className="text-copper-light">?preview=1</code> à l&apos;URL pour
              prévisualiser sans activer le flag.
            </p>
          )}
          <Button asChild variant="outline" className="border-copper/30">
            <Link href="/">Retour au lobby</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return <>{children}</>;
}
