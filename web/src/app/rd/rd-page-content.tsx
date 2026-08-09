"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { BureauPage } from "@/components/shared/bureau-page";
import { PoleOverview } from "@/components/shared/pole-overview";
import { ChevronDown, ChevronUp, Lightbulb, Beaker, FolderOpen, TreePine, LayoutDashboard } from "lucide-react";

const BrainstormView = dynamic(
  () =>
    import("@/components/brainstorm/brainstorm-view").then((m) => ({
      default: m.BrainstormView,
    })),
  { loading: () => <TabSkeleton /> },
);

const RndCenterView = dynamic(
  () =>
    import("@/components/rnd/rnd-center-view").then((m) => ({
      default: m.RndCenterView,
    })),
  { loading: () => <TabSkeleton /> },
);

const RndHypothesisTreePanel = dynamic(
  () =>
    import("@/components/rnd/rnd-hypothesis-tree-panel").then((m) => ({
      default: m.RndHypothesisTreePanel,
    })),
  { loading: () => <TabSkeleton /> },
);

const RndDossiersView = dynamic(
  () =>
    import("@/components/rnd/rnd-dossiers-view").then((m) => ({
      default: m.RndDossiersView,
    })),
  { loading: () => <TabSkeleton /> },
);

function TabSkeleton() {
  return (
    <div className="flex min-h-[200px] items-center justify-center text-sm text-titanium/50">
      Chargement…
    </div>
  );
}

type Tab = "overview" | "brainstorm" | "rnd" | "trees" | "dossiers";

const CEO_VIEWS = new Set(["ceo", "committee", "deck", "visuals", "social", "product", "pipeline"]);

export function RdPageContent() {
  const searchParams = useSearchParams();
  const dossierFromUrl = searchParams.get("dossier");
  const viewFromUrl = searchParams.get("view");
  const tabFromUrl = searchParams.get("tab");

  const treeFromUrl = searchParams.get("tree");

  const resolveInitialTab = (): Tab => {
    if (dossierFromUrl) return "dossiers";
    if (treeFromUrl || tabFromUrl === "trees") return "trees";
    if (tabFromUrl === "rnd") return "rnd";
    if (tabFromUrl === "dossiers") return "dossiers";
    if (tabFromUrl === "brainstorm") return "brainstorm";
    return "overview";
  };

  const [tab, setTab] = useState<Tab>(resolveInitialTab);
  const [dossierFocusId, setDossierFocusId] = useState<string | null>(dossierFromUrl);
  const [dossiersReloadKey, setDossiersReloadKey] = useState(0);
  // Collapsed by default — the agent cards + library shelf were eating most
  // of a 15" viewport before any tab content became visible at all.
  const [agentsOpen, setAgentsOpen] = useState(false);

  useEffect(() => {
    setAgentsOpen(sessionStorage.getItem("rd_agents_open") === "1");
  }, []);

  function toggleAgents() {
    setAgentsOpen((prev) => {
      const next = !prev;
      sessionStorage.setItem("rd_agents_open", next ? "1" : "0");
      return next;
    });
  }
  const initialPitchView =
    viewFromUrl && CEO_VIEWS.has(viewFromUrl) ? viewFromUrl : undefined;

  function handleDossierCreated(dossierId: string) {
    setDossierFocusId(dossierId);
    setDossiersReloadKey((k) => k + 1);
    setTab("dossiers");
  }

  return (
    <BureauPage
      dept="rd"
      title="R&D"
      subtitle="Nova · Mira · Brainstorm · Dossiers · Comité"
      flush
    >
      <div>
        <button
          type="button"
          onClick={toggleAgents}
          className="mb-3 flex items-center gap-1.5 text-xs font-medium text-titane/60 transition hover:text-bronze-bright"
        >
          {agentsOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          Agents &amp; bibliothèque R&amp;D
        </button>
        {agentsOpen ? (
          <BureauAgentsSection bureau="rd" className="mb-4 grid gap-4 sm:grid-cols-2" />
        ) : null}
      </div>

      <div className="mb-4 flex w-fit flex-wrap gap-1 rounded-2xl border border-bronze-faint bg-obsidian/70 p-1">
        <button
          onClick={() => setTab("overview")}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition ${
            tab === "overview"
              ? "bg-bronze text-obsidian shadow-glow"
              : "text-titane/70 hover:text-ivoire"
          }`}
        >
          <LayoutDashboard className="h-4 w-4" />
          Vue d&apos;ensemble
        </button>
        <button
          onClick={() => setTab("brainstorm")}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition ${
            tab === "brainstorm"
              ? "bg-bronze text-obsidian shadow-glow"
              : "text-titane/70 hover:text-ivoire"
          }`}
        >
          <Lightbulb className="h-4 w-4" />
          Brainstorm
        </button>
        <button
          onClick={() => setTab("rnd")}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition ${
            tab === "rnd"
              ? "bg-bronze text-obsidian shadow-glow"
              : "text-titane/70 hover:text-ivoire"
          }`}
        >
          <Beaker className="h-4 w-4" />
          Centre R&D
        </button>
        <button
          onClick={() => setTab("trees")}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition ${
            tab === "trees"
              ? "bg-bronze text-obsidian shadow-glow"
              : "text-titane/70 hover:text-ivoire"
          }`}
        >
          <TreePine className="h-4 w-4" />
          Arbres
        </button>
        <button
          onClick={() => {
            setDossiersReloadKey((k) => k + 1);
            setTab("dossiers");
          }}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition ${
            tab === "dossiers"
              ? "bg-bronze text-obsidian shadow-glow"
              : "text-titane/70 hover:text-ivoire"
          }`}
        >
          <FolderOpen className="h-4 w-4" />
          Dossiers
        </button>
      </div>

      <div>
        {tab === "overview" ? (
          <PoleOverview bureau="rd" dept="rd" />
        ) : tab === "brainstorm" ? (
          <BrainstormView />
        ) : tab === "rnd" ? (
          <RndCenterView onDossierCreated={handleDossierCreated} />
        ) : tab === "trees" ? (
          <RndHypothesisTreePanel
            initialSlug={treeFromUrl}
            onDossierCreated={handleDossierCreated}
          />
        ) : (
          <RndDossiersView
            initialDossierId={dossierFocusId ?? dossierFromUrl}
            initialPitchView={initialPitchView}
            reloadKey={dossiersReloadKey}
          />
        )}
      </div>
    </BureauPage>
  );
}
