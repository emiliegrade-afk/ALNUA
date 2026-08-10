"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { DeptV2CommandBar, DeptV2PageShell } from "@/components/dept-v2";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { useConsoleData, ConsoleProvider } from "@/components/console/console-provider";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { getAgentsForBureau, type BureauAgentDef } from "@/lib/agent-bureau";
import { ROUTES } from "@/lib/routes";
import { C, STATUS_TEXT, STATUS_COLOR, resolveAgentLoad, agentLoadChip } from "../app-v2/shared";
import { MissionBox, ChatPanel, RecentTasksPanel, ApercuPanel } from "../app-v2/team";
import { useCooStore } from "@/store/coo-store";
import { CooDrawer } from "@/components/shared/coo-drawer";
import type { TicketWithProject } from "@/lib/tickets";
import type { Project } from "@/lib/types";
import { PipelineTab } from "./pipeline-tab";
import { IncubateurTab } from "./incubateur-tab";
import { ConseilTab } from "./conseil-tab";
import { ArbresTab } from "./arbres-tab";
import { DossiersTab } from "./dossiers-tab";
import { ExplorerTab } from "./explorer-tab";
import { NewIdeaModal } from "./new-idea-modal";

/* ────────────────────────────────────────────────────────────────────────────
   Département R&D v2 — Phase 22, ROADMAP.md (refonte "laboratoire" du Centre
   R&D). Même socle que /app-v2, /gaming-v2, /robo-v2 : coquille bespoke
   autonome (en-tête, sidebar, barre de commandes), pas de ConsoleShell.

   Phase 22 : socle + onglet Équipe, en test de fumée sur les vraies données
   du bureau R&D (2 agents réels : Idris/Brainstorm, Alex/R&D — voir
   web/src/lib/agent-bureau.ts). Phase 23 : onglet Pipeline (pipeline-tab.tsx
   + dossier-detail-view.tsx) — cartes idées scorées + vue détail dossier.
   Incubateur, Conseil (Phases 24-25), Arbres (Phase 26 — canvas mindmap
   glissable, arbres-tab.tsx), Dossiers (Phase 27 — vue table,
   dossiers-tab.tsx) + Explorer (Phase 28 — veille externe) livrés. /rd reste
   la page de référence pour l'édition complète d'un dossier (sections,
   comité, finance, deck...) — la table Dossiers y renvoie via "Ouvrir ↗"
   plutôt que de porter toute cette UI en v2 (hors périmètre Phase 27), et
   reste plus généralement la page réelle jusqu'à bascule finale — cette
   route n'est pas encore liée à la nav principale (CONSOLE_POLES pointe
   toujours vers /rd), accessible seulement en URL directe pour l'instant.
   ──────────────────────────────────────────────────────────────────────────── */

const TABS = ["Équipe", "Pipeline", "Incubateur", "Conseil", "Arbres", "Dossiers", "Explorer"] as const;
type Tab = (typeof TABS)[number];

const TAB_ICON: Record<Tab, string> = {
  Équipe: "👥",
  Pipeline: "💡",
  Incubateur: "🧪",
  Conseil: "🏛",
  Arbres: "🌳",
  Dossiers: "📚",
  Explorer: "📡",
};

const QUICK_ACTIONS = [
  { icon: "＋", label: "Nouvelle idée" },
  { icon: "▤", label: "Rapport R&D" },
  { icon: "◎", label: "Lancer un brainstorm" },
  { icon: "⚙", label: "Automatisation" },
] as const;

function RndDepartmentView() {
  const agents = getAgentsForBureau("rd");
  const statuses = useAgentStatuses();
  const { activityFeed } = useConsoleData();
  const [tab, setTab] = useState<Tab>("Équipe");
  const [selectedId, setSelectedId] = useState(agents[0]?.id ?? "");
  const [newIdeaOpen, setNewIdeaOpen] = useState(false);

  const openDrawer = useCooStore((s) => s.openDrawer);
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);

  /** Créer un agent passe par du code (checklist 7 étapes, CLAUDE.md), pas
   * par une UI — le bouton ouvre donc une vraie conversation avec Aria
   * plutôt que de mentir sur une action qui n'existe pas. */
  function requestNewAgent() {
    setPrefillMessage(
      "Je veux ajouter un agent au laboratoire R&D. Quel rôle manque-t-il et comment le créer ? ",
    );
    openDrawer();
  }

  const selected: BureauAgentDef | undefined = agents.find((a) => a.id === selectedId) ?? agents[0];
  const selStatus = selected ? statuses[selected.id]?.status ?? "idle" : "idle";
  const selLoad = selected
    ? resolveAgentLoad(statuses[selected.id] ?? { status: selStatus })
    : 0;

  const activeCount = agents.filter((a) => {
    const s = statuses[a.id]?.status;
    return s === "working" || s === "waiting";
  }).length;

  const agentTasks = useMemo(
    () => (selected ? activityFeed.filter((e) => e.agent === selected.name).slice(0, 6) : []),
    [activityFeed, selected],
  );

  // Onglets Pipeline/Incubateur/Conseil n'existent pas encore (Phases 23-25)
  // — pas de vrais projets/tickets R&D à filtrer pour l'instant, tableaux
  // vides plutôt que de brancher un filtre `branch === "rd"` inutilisé.
  const projects: Project[] = [];
  const tickets: TicketWithProject[] = [];

  if (!selected) {
    return (
      <p className="p-8 text-sm" style={{ color: C.dim }}>
        Aucun agent dans le bureau R&D.
      </p>
    );
  }

  return (
    <DeptV2PageShell deptHref={ROUTES.rd} activeDeptId="rd" coreSubtitle="Laboratoire opérationnel">
        <div className="dept-hud flex min-w-0 flex-1 flex-col gap-4 px-5 pb-4 pt-4">
          <div className="flex shrink-0 items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <span
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] border text-[15px]"
                style={{ borderColor: "rgba(224,155,106,.4)", background: "radial-gradient(circle at 30% 20%, rgba(224,155,106,.25), #000000)", color: C.copperLight }}
              >
                🔬
              </span>
              <div className="min-w-0">
                <h1 className="truncate text-[23px] leading-[1.1] tracking-[1px]">
                  <span className="font-bold">R&D</span>{" "}
                  <span className="font-light tracking-[4px]" style={{ color: "#A7ADB5" }}>
                    LABORATOIRE
                  </span>
                </h1>
                <p className="mt-0.5 truncate text-[11px]" style={{ color: C.dim }}>
                  Recherche · Idéation · Prototypes
                </p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-[9px]">
              <span
                className="hidden items-center gap-[7px] border border-titanium/20 px-3 py-1.5 text-[10px] text-titanium sm:flex"
              >
                <span className="dept-live-dot" />
                {activeCount} agent{activeCount !== 1 ? "s" : ""} actif{activeCount !== 1 ? "s" : ""}
              </span>
              <button
                type="button"
                onClick={requestNewAgent}
                className="flex items-center gap-1.5 bg-metal-copper px-3 py-1.5 text-[10px] tracking-wide"
              >
                ＋ <span className="hidden sm:inline">Ajouter un agent</span>
              </button>
            </div>
          </div>

          <div className="flex gap-5 overflow-x-auto border-b" style={{ borderColor: "rgba(224,155,106,.15)" }}>
            {TABS.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={`flex shrink-0 items-center gap-[7px] whitespace-nowrap border-b-2 pb-2 pt-1 text-[10.5px] tracking-[1.2px] ${tab === t ? "border-copper text-metal-copper" : "border-transparent text-titanium/45"}`}
              >
                <span className="text-[11px]">{TAB_ICON[t]}</span>
                {t.toUpperCase()}
              </button>
            ))}
          </div>

          <div className="flex min-h-0 flex-1 flex-col">
            {tab === "Équipe" ? (
              <EquipeTab
                agents={agents}
                statuses={statuses}
                selected={selected}
                selectedId={selectedId}
                setSelectedId={setSelectedId}
                selStatus={selStatus}
                selLoad={selLoad}
                activeCount={activeCount}
                tickets={tickets}
                projects={projects}
                agentTasks={agentTasks}
              />
            ) : tab === "Pipeline" ? (
              <PipelineTab />
            ) : tab === "Incubateur" ? (
              <IncubateurTab />
            ) : tab === "Conseil" ? (
              <ConseilTab />
            ) : tab === "Arbres" ? (
              <ArbresTab />
            ) : tab === "Dossiers" ? (
              <DossiersTab />
            ) : (
              <ExplorerTab />
            )}
          </div>

          <DeptV2CommandBar
            actions={QUICK_ACTIONS.map((qa) => ({
              icon: qa.icon,
              label: qa.label,
              onClick: qa.label === "Nouvelle idée" ? () => setNewIdeaOpen(true) : undefined,
            }))}
          />

        </div>

      <NewIdeaModal open={newIdeaOpen} onClose={() => setNewIdeaOpen(false)} />
    </DeptV2PageShell>
  );
}

function EquipeTab({
  agents,
  statuses,
  selected,
  selectedId,
  setSelectedId,
  selStatus,
  selLoad,
  activeCount,
  tickets,
  projects,
  agentTasks,
}: {
  agents: BureauAgentDef[];
  statuses: ReturnType<typeof useAgentStatuses>;
  selected: BureauAgentDef;
  selectedId: string;
  setSelectedId: (id: string) => void;
  selStatus: ReturnType<typeof useAgentStatuses>[string]["status"];
  selLoad: number;
  activeCount: number;
  tickets: TicketWithProject[];
  projects: Project[];
  agentTasks: ReturnType<typeof useConsoleData>["activityFeed"];
}) {
  return (
    <div className="flex min-h-[clamp(340px,44vh,420px)] flex-1 gap-3">
      {/* Roster — équipe de 2 agents aujourd'hui, `self-start` pour ne pas
          s'étirer à la hauteur du panneau détail (même pattern que App). */}
      <div
        className="flex w-[clamp(176px,13.4vw,206px)] shrink-0 flex-col self-start rounded-xl border px-2.5 py-[11px]"
        style={{ borderColor: C.line, background: "#000000" }}
      >
        <div className="flex items-center justify-between border-b pb-[9px]" style={{ borderColor: C.lineSoft }}>
          <span className="text-[9.5px] tracking-[1.5px]" style={{ color: "#A7ADB5" }}>
            ÉQUIPE R&D
          </span>
          <span className="flex items-center gap-1 rounded-[10px] border px-[6px] py-px text-[9px]" style={{ borderColor: "rgba(140,200,150,.3)", color: C.onlineSoft }}>
            <span className="h-[5px] w-[5px] rounded-full" style={{ background: C.online }} />
            {activeCount > 0 ? "En ligne" : "En veille"} ▾
          </span>
        </div>
        <div className="alnua-scroll max-h-[240px] space-y-1 overflow-y-auto py-2">
          {agents.map((agent) => {
            const s = statuses[agent.id]?.status ?? "idle";
            const active = agent.id === selectedId;
            return (
              <button
                key={agent.id}
                type="button"
                onClick={() => setSelectedId(agent.id)}
                className="flex w-full items-center gap-2 rounded-lg px-1.5 py-1.5 text-left transition-colors"
                style={active ? { background: "rgba(224,155,106,.12)" } : undefined}
              >
                <AgentAvatar agentId={agent.id} name={agent.name} size={32} />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[11px] font-medium" style={{ color: active ? C.copperLight : C.ivory }}>
                    {agent.name}
                  </span>
                  <span className="block truncate text-[9px]" style={{ color: C.faint }}>
                    {agent.role}
                  </span>
                </span>
                <span className="flex shrink-0 flex-col items-end gap-[3px]">
                  <span className="text-[9.5px]" style={{ color: C.dim }}>
                    {agentLoadChip(statuses[agent.id], s)}
                  </span>
                  <span className="h-[5px] w-[5px] rounded-full" style={{ background: STATUS_COLOR[s] }} />
                </span>
              </button>
            );
          })}
        </div>
        <Link href={ROUTES.agents} className="rounded-lg border py-[6px] text-center text-[10px]" style={{ borderColor: "rgba(224,155,106,.22)", color: C.warm }}>
          Voir toute l&apos;équipe
        </Link>
      </div>

      {/* Detail */}
      <div
        className="flex min-w-0 flex-1 flex-col gap-[11px] rounded-xl border px-[13px] py-3"
        style={{
          borderColor: C.lineStrong,
          background: "radial-gradient(120% 120% at 0% 0%, rgba(224,155,106,.08), #000000 55%)",
          boxShadow: "0 0 24px rgba(224,155,106,.07)",
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <AgentAvatar agentId={selected.id} name={selected.name} size={56} ring />
            <div className="min-w-0">
              <div className="flex items-center gap-[7px]">
                <span className="truncate text-[19px] font-semibold">{selected.name}</span>
                <span className="text-metal-copper text-[13px]">
                  ✔
                </span>
              </div>
              <p className="truncate text-[12px]" style={{ color: C.muted }}>
                {selected.role}
              </p>
              <p className="mt-1 truncate text-[9.5px]" style={{ color: C.faint }}>
                Spécialités : {selected.skills.join(" · ")}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1.5">
            <div className="flex items-center gap-3.5 text-[10px]">
              <span className="flex items-center gap-1.5" style={{ color: STATUS_COLOR[selStatus] }}>
                <span className="h-[5px] w-[5px] rounded-full" style={{ background: STATUS_COLOR[selStatus] }} />
                {STATUS_TEXT[selStatus]}
              </span>
              <Link
                href={`${ROUTES.openroom}?agent=${encodeURIComponent(selected.id)}`}
                className="rounded-[16px] border px-3 py-[5px] text-[10.5px]"
                style={{ borderColor: C.lineStrong, color: "#E8DFD4" }}
              >
                Ouvrir le profil complet ↗
              </Link>
            </div>
            <div className="flex gap-3.5 text-[10px]" style={{ color: C.dim }}>
              <span>⊕ Laboratoire R&D</span>
              <span>⏱ {selected.skills.length} compétences</span>
            </div>
          </div>
        </div>

        <div className="flex min-h-0 flex-1 flex-col gap-[11px] min-[1240px]:flex-row">
          <MissionBox agent={selected} status={statuses[selected.id]} tickets={tickets} />
          <ChatPanel agent={selected} />
          <RecentTasksPanel tasks={agentTasks} />
        </div>
      </div>

      <ApercuPanel agent={selected} selLoad={selLoad} selStatus={selStatus} projects={projects} tickets={tickets} bureau="rd" />
    </div>
  );
}

export default function RndDepartmentV2Page() {
  return (
    <ConsoleProvider>
      <RndDepartmentView />
      <CooDrawer />
    </ConsoleProvider>
  );
}
