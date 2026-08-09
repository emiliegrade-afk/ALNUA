"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import RndV2Page from "../rnd-v2/page";
import { RdPageContent } from "./rd-page-content";

/**
 * Canonical /rd = R&D v2 shell (maquette AGENTIC OS). Deep-links dossier /
 * brainstorm / trees → RdPageContent (éditeur legacy).
 */
function RdRoute() {
  const sp = useSearchParams();
  const useLegacyEditor =
    Boolean(sp.get("dossier")) ||
    Boolean(sp.get("tree")) ||
    Boolean(sp.get("view")) ||
    ["dossiers", "trees", "brainstorm", "rnd"].includes(sp.get("tab") ?? "");

  if (useLegacyEditor) return <RdPageContent />;
  return <RndV2Page />;
}

export default function RdPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[40vh] items-center justify-center text-sm text-titanium/50">
          Chargement R&D…
        </div>
      }
    >
      <RdRoute />
    </Suspense>
  );
}
