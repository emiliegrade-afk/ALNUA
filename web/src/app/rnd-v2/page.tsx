"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { useConsoleData, ConsoleProvider } from "@/components/console/console-provider";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { getAgentsForBureau, type BureauAgentDef } from "@/lib/agent-bureau";
import { CONSOLE_POLES } from "@/lib/console/departments";
import { HUB_CHIEF, HUB_OWNER } from "@/lib/console/owner";
import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { C, STATUS_LOAD, STATUS_TEXT, STATUS_COLOR } from "../app-v2/shared";
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
   dossiers-tab.tsx) livrés. Explorer reste à venir (Phase 28). /rd reste
   la page de référence pour l'édition complète d'un dossier (sections,
   comité, finance, deck...) — la table Dossiers y renvoie via "Ouvrir ↗"
   plutôt que de porter toute cette UI en v2 (hors périmètre Phase 27), et
   reste plus généralement la page réelle jusqu'à bascule finale — cette
   route n'est pas encore liée à la nav principale (CONSOLE_POLES pointe
   toujours vers /rd), accessible seulement en URL directe pour l'instant.
   ──────────────────────────────────────────────────────────────────────────── */

const TABS = ["Équipe", "Pipeline", "Incubateur", "Conseil", "Arbres", "Dossiers"] as const;
type Tab = (typeof TABS)[number];

const TAB_ICON: Record<Tab, string> = {
  Équipe: "👥",
  Pipeline: "💡",
  Incubateur: "🧪",
  Conseil: "🏛",
  Arbres: "🌳",
  Dossiers: "📚",
};

const DASHBOARD_NAV = [
  { icon: "◉", label: "Command Center", href: ROUTES.home },
  { icon: "〰", label: "Activité en direct", href: ROUTES.activity },
  { icon: "▤", label: "Décisions", href: ROUTES.ceo, badge: true },
];

const DEPT_ICON: Record<string, string> = {
  hub: "◎",
  secretary: "🗂",
  rd: "◇",
  app: "▦",
  marketing: "📣",
  gaming: "🎮",
  robo: "🤖",
  finances: "💠",
  analytics: "📈",
  brand: "🎨",
};

const QUICK_ACTIONS = [
  { icon: "＋", label: "Nouvelle idée" },
  { icon: "▤", label: "Rapport R&D" },
  { icon: "◎", label: "Lancer un brainstorm" },
  { icon: "⚙", label: "Automatisation" },
] as const;

const TOOLS_NAV = [
  { icon: "📄", label: "Documents", href: "/docs" },
  { icon: "📖", label: "Connaissances", href: ROUTES.library },
  { icon: "🗒", label: "Modèles", href: ROUTES.settings },
  { icon: "⚙", label: "Automatisations", href: ROUTES.settings },
] as const;

const TOP_TABS: { icon: string; label: string; href: string; active?: boolean }[] = [
  { icon: "☰", label: "Vue générale", href: ROUTES.home },
  { icon: "▦", label: "Départements", href: ROUTES.rndV2, active: true },
  { icon: "◈", label: "Missions", href: ROUTES.tickets },
  { icon: "📈", label: "Analytics", href: ROUTES.analytics },
  { icon: "🗂", label: "Ressources", href: ROUTES.library },
];

function SectionBox({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[10px] border p-2" style={{ borderColor: "rgba(192,138,114,.14)", background: "rgba(16,13,11,.5)" }}>
      <p className="mb-2 ml-2 mt-0.5 text-[8.5px] tracking-[0.2em]" style={{ color: C.faint }}>
        {title}
      </p>
      {children}
    </div>
  );
}

function RndDepartmentView() {
  const agents = getAgentsForBureau("rd");
  const statuses = useAgentStatuses();
  const { activityFeed, stats } = useConsoleData();
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
  const selLoad = STATUS_LOAD[selStatus];

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
    <div
      className="alnua-scroll flex h-full w-full flex-col overflow-x-auto overflow-y-auto"
      style={{
        background:
          "radial-gradient(900px 500px at 12% -5%, rgba(192,138,114,.10), transparent 60%), radial-gradient(1000px 600px at 88% 105%, rgba(192,138,114,.09), transparent 62%), #08090B",
        color: C.ivory,
      }}
    >
      {/* ══ HEADER ══ */}
      <header className="flex h-[clamp(56px,6vh,64px)] shrink-0 items-stretch border-b" style={{ borderColor: C.line }}>
        <Link href={ROUTES.home} className="flex w-[clamp(178px,13.7vw,210px)] shrink-0 items-center gap-[11px] border-r pl-[18px]" style={{ borderColor: C.line }}>
          <span
            className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-full border"
            style={{ borderColor: "rgba(192,138,114,.45)", background: "radial-gradient(circle,rgba(192,138,114,.28),transparent 70%)", boxShadow: "0 0 18px rgba(192,138,114,.25)" }}
          >
            <AlnuaStar size={24} animated={false} sparkMid="#E8A87C" sparkOuter="#C87F4E" glowColorRgb="200,127,78" />
          </span>
          <span>
            <span className="block font-title text-[21px] leading-none tracking-[4px]" style={{ color: C.copperLight }}>
              ALNUA
            </span>
            <span className="mt-[3px] block text-[8px] tracking-[3.4px]" style={{ color: C.dim }}>
              AGENTIC OS
            </span>
          </span>
        </Link>

        <div className="flex flex-1 items-center justify-between gap-4 px-5">
          <div className="flex min-w-0 items-center gap-[11px]">
            <AgentAvatar agentId={HUB_CHIEF.agentId} name={HUB_CHIEF.name} size={38} ring />
            <span className="min-w-0">
              <span className="block truncate text-[12.5px] font-medium">
                {HUB_CHIEF.shortRole} : {HUB_CHIEF.name}
              </span>
              <span className="mt-[3px] flex items-center gap-2">
                <span className="flex items-center gap-1 rounded-[10px] border px-[7px] py-px" style={{ borderColor: "rgba(140,200,150,.3)" }}>
                  <span className="h-[5px] w-[5px] rounded-full" style={{ background: C.online }} />
                  <span className="text-[9px]" style={{ color: C.onlineSoft }}>
                    {STATUS_TEXT[statuses[HUB_CHIEF.agentId]?.status ?? "idle"]}
                  </span>
                </span>
              </span>
            </span>
          </div>

          <nav className="hidden items-center gap-1 lg:flex">
            {TOP_TABS.map((t) => (
              <Link
                key={t.label}
                href={t.href}
                className={cn("flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] transition-colors", t.active ? "border" : "border border-transparent hover:opacity-80")}
                style={t.active ? { borderColor: "rgba(192,138,114,.4)", background: "rgba(192,138,114,.12)", color: C.copperLight } : { color: C.warm }}
              >
                <span className="text-[12px] opacity-90">{t.icon}</span>
                <span className="hidden xl:inline">{t.label}</span>
              </Link>
            ))}
          </nav>

          <div className="flex shrink-0 items-center gap-[18px]">
            <span className="relative flex h-[34px] w-[34px] items-center justify-center rounded-full border text-[13px]" style={{ borderColor: "rgba(192,138,114,.22)" }}>
              🔔
              {stats.ceoNotifications > 0 ? <span className="absolute right-[3px] top-[2px] h-[6px] w-[6px] rounded-full" style={{ background: C.copper, boxShadow: `0 0 6px ${C.copper}` }} /> : null}
            </span>
            <span className="flex items-center gap-[9px]">
              <AgentAvatar agentId={HUB_OWNER.id} name={HUB_OWNER.name} size={36} />
              <span className="hidden xl:block">
                <span className="block text-[12px] font-medium">{HUB_OWNER.name}</span>
                <span className="block text-[9.5px]" style={{ color: C.dim }}>
                  {HUB_OWNER.role}
                </span>
              </span>
              <span className="text-[9px]" style={{ color: C.dim }}>
                ▾
              </span>
            </span>
          </div>
        </div>
      </header>

      {/* ══ BODY ══ */}
      <div className="relative z-10 flex min-h-[600px] flex-1">
        <aside className="flex w-[clamp(178px,13.7vw,210px)] shrink-0 flex-col gap-3 overflow-y-auto border-r px-3 py-4" style={{ borderColor: C.line }}>
          <SectionBox title="TABLEAU DE BORD">
            {DASHBOARD_NAV.map((it) => (
              <Link key={it.label} href={it.href} className="flex items-center justify-between gap-1 whitespace-nowrap rounded-[7px] px-2 py-[7px] text-[12px] transition-colors hover:bg-obsidian-deep/50" style={{ color: C.warm }}>
                <span className="flex min-w-0 items-center gap-2">
                  <span className="w-[15px] shrink-0 text-center text-[12px]" style={{ color: C.copper }}>
                    {it.icon}
                  </span>
                  {it.label}
                </span>
                {it.badge && stats.ceoNotifications > 0 ? (
                  <span className="rounded-lg border px-1.5 text-[9px]" style={{ borderColor: "rgba(192,138,114,.5)", color: C.copperLight }}>
                    {stats.ceoNotifications}
                  </span>
                ) : null}
              </Link>
            ))}
          </SectionBox>

          <SectionBox title="DÉPARTEMENTS">
            {CONSOLE_POLES.filter((pole) => pole.id !== "ceo").map((pole, i) => {
              const active = pole.id === "rd";
              const icon = DEPT_ICON[pole.id] ?? "◈";
              return (
                <Link
                  key={pole.id}
                  href={pole.href}
                  className="flex items-center justify-between rounded-[7px] px-2 py-[7px] transition-colors hover:bg-obsidian-deep/50"
                  style={active ? { background: "rgba(192,138,114,.12)", color: C.copperLight } : { color: C.warm }}
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <span className="w-[16px] shrink-0 text-center text-[11px]" style={{ color: C.copper }}>
                      {icon}
                    </span>
                    <span className="text-[10.5px]" style={{ color: C.faint }}>
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="truncate text-[12px]">{pole.name.replace("Bureau ", "").replace("Pôle ", "")}</span>
                  </span>
                  <span className="text-[10px]" style={{ color: "#6E655E" }}>
                    ›
                  </span>
                </Link>
              );
            })}
          </SectionBox>

          <SectionBox title="OUTILS">
            {TOOLS_NAV.map((t) => (
              <Link key={t.label} href={t.href} className="flex items-center justify-between gap-1 whitespace-nowrap rounded-[7px] px-2 py-[7px] text-[12px] transition-colors hover:bg-obsidian-deep/50" style={{ color: C.warm }}>
                <span className="flex min-w-0 items-center gap-2">
                  <span className="w-[15px] shrink-0 text-center text-[11px]" style={{ color: C.copper }}>
                    {t.icon}
                  </span>
                  {t.label}
                </span>
                <span className="text-[10px]" style={{ color: "#6E655E" }}>
                  ›
                </span>
              </Link>
            ))}
          </SectionBox>

          <div
            className="relative mt-auto overflow-hidden rounded-xl border p-3 pb-3.5"
            style={{ borderColor: "rgba(192,138,114,.2)", background: "radial-gradient(120% 90% at 50% 45%, rgba(192,138,114,.13), rgba(8,7,9,.92) 70%)" }}
          >
            <div className="flex items-center justify-center gap-2">
              <span className="h-px w-4" style={{ background: "linear-gradient(90deg,transparent,rgba(192,138,114,.6))" }} />
              <span className="text-[10px] tracking-[2.4px]" style={{ color: C.copperLight }}>
                ALNUA CORE
              </span>
              <span className="h-px w-4" style={{ background: "linear-gradient(90deg,rgba(192,138,114,.6),transparent)" }} />
            </div>
            <p className="mt-[3px] text-center text-[9.5px]" style={{ color: C.dim }}>
              Laboratoire opérationnel
            </p>
            <div className="relative mt-1.5 flex h-[100px] items-center justify-center">
              <AlnuaStar size={48} glow className="relative" sparkMid="#E8A87C" sparkOuter="#C87F4E" glowColorRgb="200,127,78" />
            </div>
            <div className="mt-0.5 flex items-center justify-center gap-2">
              <span className="h-[7px] w-[7px] shrink-0 rounded-full" style={{ background: C.online, boxShadow: `0 0 7px ${C.online}` }} />
              <p className="text-left text-[9.5px] leading-tight" style={{ color: "#9A9089" }}>
                Tous les systèmes
                <br />
                opérationnels
              </p>
            </div>
          </div>
        </aside>

        {/* MAIN */}
        <div className="flex min-w-0 flex-1 flex-col gap-3 px-4 pb-3 pt-3.5">
          <div className="flex shrink-0 items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <span
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] border text-[15px]"
                style={{ borderColor: "rgba(192,138,114,.4)", background: "radial-gradient(circle at 30% 20%, rgba(192,138,114,.25), rgba(10,9,10,.9))", color: C.copperLight }}
              >
                🔬
              </span>
              <div className="min-w-0">
                <h1 className="truncate text-[23px] leading-[1.1] tracking-[1px]">
                  <span className="font-bold">R&D</span>{" "}
                  <span className="font-light tracking-[4px]" style={{ color: "#D8CFC4" }}>
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
                className="hidden items-center gap-[7px] rounded-[18px] border px-[13px] py-1.5 text-[11.5px] sm:flex"
                style={{ borderColor: "rgba(192,138,114,.22)", background: "rgba(16,13,11,.6)", color: C.warm }}
              >
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: C.online, boxShadow: `0 0 6px ${C.online}` }} />
                {activeCount} agent{activeCount !== 1 ? "s" : ""} actif{activeCount !== 1 ? "s" : ""}
              </span>
              <button
                type="button"
                onClick={requestNewAgent}
                className="flex items-center gap-1.5 rounded-[18px] border px-[13px] py-1.5 text-[11.5px]"
                style={{ borderColor: "rgba(192,138,114,.45)", background: "rgba(192,138,114,.08)", color: C.copperLight }}
              >
                ＋ <span className="hidden sm:inline">Ajouter un agent</span>
              </button>
            </div>
          </div>

          <div className="flex gap-5 overflow-x-auto border-b" style={{ borderColor: "rgba(192,138,114,.15)" }}>
            {TABS.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className="flex shrink-0 items-center gap-[7px] whitespace-nowrap border-b-2 pb-2 pt-1 text-[10.5px] tracking-[1.2px]"
                style={{ borderColor: tab === t ? C.copper : "transparent", color: tab === t ? "#F2E9DE" : C.faint }}
              >
                <span className="text-[11px]">{TAB_ICON[t]}</span>
                {t.toUpperCase()}
              </button>
            ))}
            {/* Explorer arrive Phase 28 — pas d'onglet désactivé fantôme
                ici, juste absent tant que le contenu réel n'existe pas. */}
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
            ) : (
              <DossiersTab />
            )}
          </div>

          {/* ══ COMMAND BAR ══ */}
          <div className="relative flex h-[clamp(54px,7vh,62px)] shrink-0 items-center">
            <span
              className="absolute inset-0 rounded-[34px] border"
              style={{ borderColor: "rgba(192,138,114,.28)", background: "radial-gradient(60% 220% at 50% 50%, rgba(192,138,114,.14), rgba(14,11,9,.7) 70%)" }}
            />
            <div className="relative flex flex-1 items-center justify-between px-7">
              <span className="hidden text-[12px] sm:inline" style={{ color: C.muted }}>
                Que souhaitez-vous faire aujourd&apos;hui ?
              </span>
              <div className="ml-auto flex items-center gap-3 text-[11.5px]" style={{ color: C.warm }}>
                {QUICK_ACTIONS.map((qa) =>
                  qa.label === "Nouvelle idée" ? (
                    // Seule action réellement câblée du groupe (les 3 autres
                    // sont décoratives, même pattern que app-v2/gaming-v2) —
                    // label toujours visible (pas de hidden xl:inline) et
                    // fond distinct pour qu'elle ne se confonde pas avec les
                    // 3 icônes inertes sous ~1280px de large (signalé par
                    // Emilie, 2026-07-31 : boutons introuvables une fois les
                    // libellés masqués en dessous de ce seuil).
                    <button
                      key={qa.label}
                      type="button"
                      onClick={() => setNewIdeaOpen(true)}
                      title={qa.label}
                      className="flex items-center gap-[7px] rounded-full border px-2.5 py-1"
                      style={{ borderColor: "rgba(192,138,114,.4)", background: "rgba(192,138,114,.1)" }}
                    >
                      <span className="flex h-[22px] w-[22px] items-center justify-center rounded-md border text-[10px]" style={{ borderColor: "rgba(192,138,114,.28)", color: C.copperLight }}>
                        {qa.icon}
                      </span>
                      <span style={{ color: C.copperLight }}>{qa.label}</span>
                    </button>
                  ) : (
                    <span key={qa.label} title={qa.label} className="flex items-center gap-[7px]">
                      <span className="flex h-[22px] w-[22px] items-center justify-center rounded-md border text-[10px]" style={{ borderColor: "rgba(192,138,114,.28)", color: C.copperLight }}>
                        {qa.icon}
                      </span>
                      <span className="hidden xl:inline">{qa.label}</span>
                    </span>
                  ),
                )}
              </div>
            </div>
            <span
              className="absolute left-1/2 top-1/2 flex h-[88px] w-[88px] -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full"
              style={{ background: "radial-gradient(circle, rgba(192,138,114,.30) 0%, rgba(192,138,114,.10) 45%, transparent 70%)" }}
            >
              <span className="absolute h-[76px] w-[76px] rounded-full border" style={{ borderColor: "rgba(192,138,114,.35)" }} />
              <AlnuaStar size={60} glow sparkMid="#E8A87C" sparkOuter="#C87F4E" glowColorRgb="200,127,78" />
            </span>
          </div>
        </div>
      </div>

      <NewIdeaModal open={newIdeaOpen} onClose={() => setNewIdeaOpen(false)} />
    </div>
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
        style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
      >
        <div className="flex items-center justify-between border-b pb-[9px]" style={{ borderColor: C.lineSoft }}>
          <span className="text-[9.5px] tracking-[1.5px]" style={{ color: "#D8CFC4" }}>
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
                style={active ? { background: "rgba(192,138,114,.12)" } : undefined}
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
                    {STATUS_LOAD[s]}%
                  </span>
                  <span className="h-[5px] w-[5px] rounded-full" style={{ background: STATUS_COLOR[s] }} />
                </span>
              </button>
            );
          })}
        </div>
        <Link href={ROUTES.agents} className="rounded-lg border py-[6px] text-center text-[10px]" style={{ borderColor: "rgba(192,138,114,.22)", color: C.warm }}>
          Voir toute l&apos;équipe
        </Link>
      </div>

      {/* Detail */}
      <div
        className="flex min-w-0 flex-1 flex-col gap-[11px] rounded-xl border px-[13px] py-3"
        style={{
          borderColor: C.lineStrong,
          background: "radial-gradient(120% 120% at 0% 0%, rgba(192,138,114,.08), rgba(16,13,11,.6) 55%)",
          boxShadow: "0 0 24px rgba(192,138,114,.07)",
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <AgentAvatar agentId={selected.id} name={selected.name} size={56} ring />
            <div className="min-w-0">
              <div className="flex items-center gap-[7px]">
                <span className="truncate text-[19px] font-semibold">{selected.name}</span>
                <span className="text-[13px]" style={{ color: C.copperLight }}>
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
