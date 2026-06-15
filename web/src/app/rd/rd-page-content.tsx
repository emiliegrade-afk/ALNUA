"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { BrainstormView } from "@/components/brainstorm/brainstorm-view";
import { RndCenterView } from "@/components/rnd/rnd-center-view";
import { RndDossiersView } from "@/components/rnd/rnd-dossiers-view";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { DepartmentHeader } from "@/components/shared/department-header";
import { Lightbulb, Beaker, FolderOpen } from "lucide-react";

type Tab = "brainstorm" | "rnd" | "dossiers";

const CEO_VIEWS = new Set(["ceo", "committee", "deck", "visuals", "social", "product", "pipeline"]);

export function RdPageContent() {
  const searchParams = useSearchParams();
  const dossierFromUrl = searchParams.get("dossier");
  const viewFromUrl = searchParams.get("view");
  const tabFromUrl = searchParams.get("tab");

  const resolveInitialTab = (): Tab => {
    if (dossierFromUrl) return "dossiers";
    if (tabFromUrl === "rnd") return "rnd";
    if (tabFromUrl === "dossiers") return "dossiers";
    if (tabFromUrl === "brainstorm") return "brainstorm";
    return "brainstorm";
  };

  const [tab, setTab] = useState<Tab>(resolveInitialTab);
  const [dossierFocusId, setDossierFocusId] = useState<string | null>(dossierFromUrl);
  const [dossiersReloadKey, setDossiersReloadKey] = useState(0);
  const initialPitchView =
    viewFromUrl && CEO_VIEWS.has(viewFromUrl) ? viewFromUrl : undefined;

  function handleDossierCreated(dossierId: string) {
    setDossierFocusId(dossierId);
    setDossiersReloadKey((k) => k + 1);
    setTab("dossiers");
  }

  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="rd"
        title="R&D"
        subtitle="Nova · Mira · Brainstorm · Dossiers · Comité"
      />

      <BureauAgentsSection bureau="rd" className="mb-6 grid gap-4 sm:grid-cols-2" />

      <div className="mb-4 flex w-fit flex-wrap gap-1 rounded-xl border border-white/10 bg-white/[0.02] p-1">
        <button
          onClick={() => setTab("brainstorm")}
          className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition ${
            tab === "brainstorm"
              ? "bg-copper text-obsidian shadow"
              : "text-titanium/70 hover:text-ivory/80"
          }`}
        >
          <Lightbulb className="h-4 w-4" />
          Brainstorm
        </button>
        <button
          onClick={() => setTab("rnd")}
          className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition ${
            tab === "rnd"
              ? "bg-copper text-obsidian shadow"
              : "text-titanium/70 hover:text-ivory/80"
          }`}
        >
          <Beaker className="h-4 w-4" />
          Centre R&D
        </button>
        <button
          onClick={() => {
            setDossiersReloadKey((k) => k + 1);
            setTab("dossiers");
          }}
          className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition ${
            tab === "dossiers"
              ? "bg-copper text-obsidian shadow"
              : "text-titanium/70 hover:text-ivory/80"
          }`}
        >
          <FolderOpen className="h-4 w-4" />
          Dossiers
        </button>
      </div>

      <div className="-mx-6 flex h-[calc(100dvh-15rem)] flex-col overflow-hidden px-6">
        {tab === "brainstorm" ? (
          <BrainstormView />
        ) : tab === "rnd" ? (
          <RndCenterView onDossierCreated={handleDossierCreated} />
        ) : (
          <RndDossiersView
            initialDossierId={dossierFocusId ?? dossierFromUrl}
            initialPitchView={initialPitchView}
            reloadKey={dossiersReloadKey}
          />
        )}
      </div>
    </>
  );
}
