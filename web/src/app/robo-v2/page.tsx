"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { RoboConsole } from "@/components/robo/robo-console";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { useConsoleData, ConsoleProvider } from "@/components/console/console-provider";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { getAgentsForBureau, type BureauAgentDef } from "@/lib/agent-bureau";
import { CONSOLE_POLES } from "@/lib/console/departments";
import { HUB_CHIEF, HUB_OWNER } from "@/lib/console/owner";
import { fetchProjects } from "@/lib/api";
import { fetchLatestRoboBuild } from "@/lib/robo-builds";
import { ROUTES } from "@/lib/routes";
import type { Project, RoboBuild } from "@/lib/types";
import type { TicketWithProject } from "@/lib/tickets";
import type { ConsoleActivityItem } from "@/lib/console/types";
import { cn } from "@/lib/utils";
import { C, STATUS_LOAD, STATUS_TEXT, STATUS_COLOR, KIND_META } from "../app-v2/shared";
import { useBureauTickets } from "../app-v2/tabs";
import { MissionBox, ChatPanel, RecentTasksPanel, ApercuPanel } from "../app-v2/team";
import { useCooStore } from "@/store/coo-store";
import { CooDrawer } from "@/components/shared/coo-drawer";
import { ProjetsTab } from "./projects-tab";
import { MissionsTab } from "./missions-tab";
import { LaboratoireTab } from "./laboratoire-tab";
import { BacklogTab } from "./backlog-tab";
import { DocumentationTab } from "./documentation-tab";
import { AnalyticsTab } from "./analytics-tab";
import { SettingsTab } from "./settings-tab";

/* ────────────────────────────────────────────────────────────────────────────
   Département Robotique — même socle que /app-v2 et /gaming-v2 (header,
   sidebar, onglets), contenu spécialisé, plus un onglet propre (Laboratoire).
   Décision du 2026-07-31 (plan Gaming/Robotique) : roster visuel pour
   l'instant (2 agents réels + 8 postes vacants), pas de faux agents créés.
   DA "laboratoire" — plus épurée/clinique (accents titane plutôt que cuivre
   sur la grille de fond) tout en restant Obsidian / Titane / Cuivre. */

const TABS = ["Équipe", "Projets", "Missions", "Laboratoire", "Backlog", "Documentation", "Analytics", "Paramètres"] as const;
type Tab = (typeof TABS)[number];

const TAB_ICON: Record<Tab, string> = {
  Équipe: "👥",
  Projets: "▤",
  Missions: "◈",
  Laboratoire: "⚗",
  Backlog: "☰",
  Documentation: "📄",
  Analytics: "📈",
  Paramètres: "⚙",
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
  { icon: "＋", label: "Nouvelle mission" },
  { icon: "▤", label: "Rapport d'équipe" },
  { icon: "◎", label: "Analyse prototype" },
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
  { icon: "▦", label: "Départements", href: ROUTES.robo, active: true },
  { icon: "◈", label: "Missions", href: ROUTES.tickets },
  { icon: "📈", label: "Analytics", href: ROUTES.analytics },
  { icon: "🗂", label: "Ressources", href: ROUTES.library },
];

/* Les 10 rôles du plan Robotique ont désormais tous un agent réel (Phase 13,
   ROADMAP.md, 2026-07-30) — plus de postes vacants. Le tableau reste en
   place (vide) pour ne pas retoucher le rendu ci-dessous si un nouveau rôle
   venait à manquer plus tard. */
const VACANT_ROLES: string[] = [];

function SectionBox({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[10px] border p-2" style={{ borderColor: "rgba(200,127,78,.14)", background: "rgba(16,13,11,.5)" }}>
      <p className="mb-2 ml-2 mt-0.5 text-[8.5px] tracking-[0.2em]" style={{ color: C.faint }}>
        {title}
      </p>
      {children}
    </div>
  );
}

function RoboDepartmentView() {
  const agents = getAgentsForBureau("robo");
  const statuses = useAgentStatuses();
  const { activityFeed, stats } = useConsoleData();
  const [tab, setTab] = useState<Tab>("Équipe");
  const [projects, setProjects] = useState<Project[]>([]);
  const { tickets } = useBureauTickets(projects);

  useEffect(() => {
    let cancelled = false;
    void fetchProjects()
      .then((all) => {
        if (!cancelled) setProjects(all.filter((p) => p.branch === "robotics"));
      })
      .catch(() => {
        if (!cancelled) setProjects([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const openDrawer = useCooStore((s) => s.openDrawer);
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);

  function requestRole(role?: string) {
    setPrefillMessage(
      role
        ? `Je veux ouvrir un poste "${role}" au workshop Robotique. Comment le créer ?`
        : "Je veux ajouter un agent au workshop Robotique. Quel rôle manque-t-il et comment le créer ?",
    );
    openDrawer();
  }

  const activeCount = agents.filter((a) => {
    const s = statuses[a.id]?.status;
    return s === "working" || s === "waiting";
  }).length;

  return (
    <div
      className="alnua-scroll flex h-full w-full flex-col overflow-x-auto overflow-y-auto"
      style={{
        background:
          "radial-gradient(1100px 600px at 15% -10%, rgba(200,127,78,.07), transparent 55%), radial-gradient(900px 700px at 90% 110%, rgba(167,173,181,.05), transparent 60%), #07080A",
        color: C.ivory,
      }}
    >
      {/* Grille façon labo/PCB — décorative, accents titane plutôt que cuivre. */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(167,173,181,.6) 1px, transparent 1px), linear-gradient(90deg, rgba(167,173,181,.6) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* ══ HEADER ══ */}
      <header className="relative z-10 flex h-[clamp(56px,6vh,64px)] shrink-0 items-stretch border-b" style={{ borderColor: C.line }}>
        <Link href={ROUTES.home} className="flex w-[clamp(178px,13.7vw,210px)] shrink-0 items-center gap-[11px] border-r pl-[18px]" style={{ borderColor: C.line }}>
          <span
            className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-full border"
            style={{ borderColor: "rgba(200,127,78,.45)", background: "radial-gradient(circle,rgba(200,127,78,.28),transparent 70%)", boxShadow: "0 0 18px rgba(200,127,78,.25)" }}
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
                style={t.active ? { borderColor: "rgba(200,127,78,.4)", background: "rgba(200,127,78,.12)", color: C.copperLight } : { color: C.warm }}
              >
                <span className="text-[12px] opacity-90">{t.icon}</span>
                <span className="hidden xl:inline">{t.label}</span>
              </Link>
            ))}
          </nav>

          <div className="flex shrink-0 items-center gap-[18px]">
            <span className="relative flex h-[34px] w-[34px] items-center justify-center rounded-full border text-[13px]" style={{ borderColor: "rgba(200,127,78,.22)" }}>
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
              <Link key={it.label} href={it.href} className="flex items-center justify-between gap-1 whitespace-nowrap rounded-[7px] px-2 py-[7px] text-[12px] transition-colors hover:bg-white/[0.03]" style={{ color: C.warm }}>
                <span className="flex min-w-0 items-center gap-2">
                  <span className="w-[15px] shrink-0 text-center text-[12px]" style={{ color: C.copper }}>
                    {it.icon}
                  </span>
                  {it.label}
                </span>
                {it.badge && stats.ceoNotifications > 0 ? (
                  <span className="rounded-lg border px-1.5 text-[9px]" style={{ borderColor: "rgba(200,127,78,.5)", color: C.copperLight }}>
                    {stats.ceoNotifications}
                  </span>
                ) : null}
              </Link>
            ))}
          </SectionBox>

          <SectionBox title="DÉPARTEMENTS">
            {CONSOLE_POLES.filter((pole) => pole.id !== "ceo").map((pole, i) => {
              const active = pole.id === "robo";
              const icon = DEPT_ICON[pole.id] ?? "◈";
              return (
                <Link
                  key={pole.id}
                  href={pole.href}
                  className="flex items-center justify-between rounded-[7px] px-2 py-[7px] transition-colors hover:bg-white/[0.03]"
                  style={active ? { background: "rgba(200,127,78,.12)", color: C.copperLight } : { color: C.warm }}
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
              <Link key={t.label} href={t.href} className="flex items-center justify-between gap-1 whitespace-nowrap rounded-[7px] px-2 py-[7px] text-[12px] transition-colors hover:bg-white/[0.03]" style={{ color: C.warm }}>
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
            style={{ borderColor: "rgba(200,127,78,.2)", background: "radial-gradient(120% 90% at 50% 45%, rgba(200,127,78,.13), rgba(8,7,9,.92) 70%)" }}
          >
            <div className="flex items-center justify-center gap-2">
              <span className="h-px w-4" style={{ background: "linear-gradient(90deg,transparent,rgba(200,127,78,.6))" }} />
              <span className="text-[10px] tracking-[2.4px]" style={{ color: C.copperLight }}>
                ALNUA CORE
              </span>
              <span className="h-px w-4" style={{ background: "linear-gradient(90deg,rgba(200,127,78,.6),transparent)" }} />
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
                style={{ borderColor: "rgba(200,127,78,.4)", background: "radial-gradient(circle at 30% 20%, rgba(200,127,78,.25), rgba(10,9,10,.9))", color: C.copperLight }}
              >
                🤖
              </span>
              <div className="min-w-0">
                <h1 className="truncate text-[23px] leading-[1.1] tracking-[1px]">
                  <span className="font-bold">ROBOTIQUE</span>{" "}
                  <span className="font-light tracking-[4px]" style={{ color: "#D8CFC4" }}>
                    WORKSHOP
                  </span>
                </h1>
                <p className="mt-0.5 truncate text-[11px]" style={{ color: C.dim }}>
                  Eve · Hardware &amp; IA embarquée
                </p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-[9px]">
              <span
                className="hidden items-center gap-[7px] rounded-[18px] border px-[13px] py-1.5 text-[11.5px] sm:flex"
                style={{ borderColor: "rgba(200,127,78,.22)", background: "rgba(16,13,11,.6)", color: C.warm }}
              >
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: C.online, boxShadow: `0 0 6px ${C.online}` }} />
                {activeCount} agent{activeCount !== 1 ? "s" : ""} actif{activeCount !== 1 ? "s" : ""}
              </span>
              <button
                type="button"
                onClick={() => requestRole()}
                className="flex items-center gap-1.5 rounded-[18px] border px-[13px] py-1.5 text-[11.5px]"
                style={{ borderColor: "rgba(200,127,78,.45)", background: "rgba(200,127,78,.08)", color: C.copperLight }}
              >
                ＋ <span className="hidden sm:inline">Ajouter un agent</span>
              </button>
            </div>
          </div>

          <div className="flex gap-5 overflow-x-auto border-b" style={{ borderColor: "rgba(200,127,78,.15)" }}>
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
          </div>

          <div className="flex min-h-0 flex-1 flex-col">
            {tab === "Équipe" ? (
              <EquipeTab
                agents={agents}
                statuses={statuses}
                onRequestRole={requestRole}
                tickets={tickets}
                activityFeed={activityFeed}
                projects={projects}
              />
            ) : tab === "Projets" ? (
              <ProjetsTab projects={projects} agents={agents} onProjectCreated={(p) => setProjects((prev) => [...prev, p])} />
            ) : tab === "Missions" ? (
              <MissionsTab projects={projects} agents={agents} statuses={statuses} activityFeed={activityFeed} />
            ) : tab === "Laboratoire" ? (
              <LaboratoireTab projects={projects} />
            ) : tab === "Backlog" ? (
              <BacklogTab projects={projects} agents={agents} activityFeed={activityFeed} />
            ) : tab === "Documentation" ? (
              <DocumentationTab projects={projects} />
            ) : tab === "Analytics" ? (
              <AnalyticsTab projects={projects} />
            ) : (
              <SettingsTab />
            )}
          </div>

          {/* ══ COMMAND BAR ══ */}
          <div className="relative flex h-[clamp(54px,7vh,62px)] shrink-0 items-center">
            <span
              className="absolute inset-0 rounded-[34px] border"
              style={{ borderColor: "rgba(200,127,78,.28)", background: "radial-gradient(60% 220% at 50% 50%, rgba(200,127,78,.14), rgba(14,11,9,.7) 70%)" }}
            />
            <div className="relative flex flex-1 items-center justify-between px-7">
              <span className="hidden text-[12px] sm:inline" style={{ color: C.muted }}>
                Que souhaitez-vous faire aujourd&apos;hui ?
              </span>
              <div className="ml-auto flex items-center gap-3 text-[11.5px]" style={{ color: C.warm }}>
                {QUICK_ACTIONS.map((qa) => (
                  <span key={qa.label} className="flex items-center gap-[7px]">
                    <span className="flex h-[22px] w-[22px] items-center justify-center rounded-md border text-[10px]" style={{ borderColor: "rgba(200,127,78,.28)", color: C.copperLight }}>
                      {qa.icon}
                    </span>
                    <span className="hidden xl:inline">{qa.label}</span>
                  </span>
                ))}
              </div>
            </div>
            <span
              className="absolute left-1/2 top-1/2 flex h-[88px] w-[88px] -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full"
              style={{ background: "radial-gradient(circle, rgba(200,127,78,.30) 0%, rgba(200,127,78,.10) 45%, transparent 70%)" }}
            >
              <span className="absolute h-[76px] w-[76px] rounded-full border" style={{ borderColor: "rgba(200,127,78,.35)" }} />
              <AlnuaStar size={60} glow sparkMid="#E8A87C" sparkOuter="#C87F4E" glowColorRgb="200,127,78" />
            </span>
          </div>

          {/* Console agents Robotique — repliée par défaut, fonctionnalité
              réelle de l'ancienne /robo (statut Eve, Looking Glass, BOM,
              instructions Hardware/Embedded), préservée mais pas visible
              sans défiler volontairement. */}
          <details className="group shrink-0 rounded-xl border" style={{ borderColor: C.line }}>
            <summary className="flex cursor-pointer items-center gap-2 px-4 py-2.5 text-[10.5px]" style={{ color: C.dim }}>
              <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
              Console agents Robotique — instructions directes
            </summary>
            <div className="alnua-scroll max-h-[46vh] overflow-y-auto border-t p-4" style={{ borderColor: C.line }}>
              <RoboConsole />
            </div>
          </details>
        </div>
      </div>
    </div>
  );
}

function EquipeTab({
  agents,
  statuses,
  onRequestRole,
  tickets,
  activityFeed,
  projects,
}: {
  agents: BureauAgentDef[];
  statuses: ReturnType<typeof useAgentStatuses>;
  onRequestRole: (role?: string) => void;
  tickets: TicketWithProject[];
  activityFeed: ConsoleActivityItem[];
  projects: Project[];
}) {
  const [selectedId, setSelectedId] = useState(agents[0]?.id ?? "");
  const selected = agents.find((a) => a.id === selectedId);
  const selStatus = selected ? statuses[selected.id]?.status ?? "idle" : "idle";
  const selLoad = STATUS_LOAD[selStatus];

  /* Dernier build hardware réel (Phase 19, ROADMAP.md, 2026-07-30) — partagé
   * par toutes les cartes agent, comme pour Gaming (pas de vrai suivi Git
   * par personne). null tant qu'aucun build n'a été rapporté. */
  const [latestBuild, setLatestBuild] = useState<RoboBuild | null>(null);
  useEffect(() => {
    const firstProjectId = projects[0]?.id;
    if (!firstProjectId) return;
    let cancelled = false;
    fetchLatestRoboBuild(firstProjectId).then((b) => {
      if (!cancelled) setLatestBuild(b);
    });
    return () => {
      cancelled = true;
    };
  }, [projects]);

  const agentTasks = useMemo(
    () => (selected ? activityFeed.filter((e) => e.agent === selected.name).slice(0, 6) : []),
    [activityFeed, selected],
  );

  const activeCount = agents.filter((a) => {
    const s = statuses[a.id]?.status;
    return s === "working" || s === "waiting";
  }).length;

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-2">
      <div className="flex shrink-0 gap-3">
        {/* Ligne scrollable horizontalement plutôt qu'une grille qui empile les
            10 cartes (2 réelles + 8 postes vacants) sur plusieurs rangées. */}
        <div className="alnua-scroll flex min-w-0 flex-1 gap-3 overflow-x-auto pb-1">
          {agents.map((agent) => {
            const s = statuses[agent.id]?.status ?? "idle";
            const load = STATUS_LOAD[s];
            const active = agent.id === selectedId;
            return (
              <button
                key={agent.id}
                type="button"
                onClick={() => setSelectedId(agent.id)}
                className="flex w-[230px] shrink-0 flex-col gap-2.5 rounded-xl border p-3 text-left transition-colors"
                style={{
                  borderColor: active ? C.copper : C.line,
                  background: active
                    ? "radial-gradient(120% 120% at 0% 0%, rgba(200,127,78,.12), rgba(16,13,11,.6) 60%)"
                    : "rgba(16,13,11,.55)",
                  boxShadow: active ? "0 0 22px rgba(200,127,78,.12)" : undefined,
                }}
              >
                <div className="flex items-center gap-2.5">
                  <AgentAvatar agentId={agent.id} name={agent.name} size={40} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[12.5px] font-semibold">{agent.name}</span>
                    <span className="block truncate text-[9.5px]" style={{ color: C.dim }}>
                      {agent.role}
                    </span>
                  </span>
                  <span className="h-[6px] w-[6px] shrink-0 rounded-full" style={{ background: STATUS_COLOR[s] }} title={STATUS_TEXT[s]} />
                </div>
                <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[9px]" style={{ color: C.faint }}>
                  <span className="truncate">
                    Branche <b style={{ color: C.warm }}>{latestBuild?.branch ?? "—"}</b>
                  </span>
                  <span className="truncate">
                    Stage <b style={{ color: C.warm }}>{latestBuild?.stage ?? "—"}</b>
                  </span>
                  <span className="truncate">
                    PCB <b style={{ color: C.warm }}>{latestBuild?.pcb_revision ?? "—"}</b>
                  </span>
                  <span className="truncate">
                    Firmware <b style={{ color: C.warm }}>{latestBuild?.firmware_version ?? "—"}</b>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-1 flex-1 overflow-hidden rounded-full" style={{ background: "rgba(200,127,78,.15)" }}>
                    <span className="block h-full rounded-full" style={{ width: `${load}%`, background: C.copper }} />
                  </span>
                  <span className="text-[9.5px]" style={{ color: C.ivory }}>
                    {load}%
                  </span>
                </div>
                {!latestBuild ? (
                  <span className="text-[9px]" style={{ color: C.faint }}>
                    Aucun build rapporté
                  </span>
                ) : null}
              </button>
            );
          })}

          {VACANT_ROLES.map((role) => (
            <button
              key={role}
              type="button"
              onClick={() => onRequestRole(role)}
              className="flex w-[230px] shrink-0 flex-col items-center justify-center gap-1.5 rounded-xl border border-dashed p-3 text-center transition-colors hover:opacity-80"
              style={{ borderColor: "rgba(200,127,78,.28)", background: "rgba(16,13,11,.3)", minHeight: 150 }}
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full border text-[13px]" style={{ borderColor: "rgba(200,127,78,.35)", color: C.copperLight }}>
                ＋
              </span>
              <span className="text-[10.5px] font-medium" style={{ color: C.warm }}>
                {role}
              </span>
              <span className="text-[9px]" style={{ color: C.faint }}>
                Poste vacant
              </span>
            </button>
          ))}
        </div>

        {/* Activité en temps réel — même panneau que App/Gaming. */}
        <div
          className="flex h-[268px] w-[clamp(226px,18vw,276px)] shrink-0 flex-col rounded-xl border px-3 py-[11px]"
          style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
        >
          <div className="flex items-center justify-between border-b pb-[9px]" style={{ borderColor: C.lineSoft }}>
            <span className="text-[9.5px] tracking-[1.6px]" style={{ color: "#D8CFC4" }}>
              ACTIVITÉ EN TEMPS RÉEL
            </span>
            <Link href={ROUTES.activity} className="text-[9.5px]" style={{ color: C.copper }}>
              Tout voir
            </Link>
          </div>
          <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-[11px] overflow-y-auto py-2.5">
            {activityFeed.length === 0 ? (
              <p className="py-6 text-center text-[10px]" style={{ color: C.faint }}>
                Aucune activité récente.
              </p>
            ) : (
              activityFeed.slice(0, 12).map((ev) => (
                <div key={ev.id} className="flex items-start gap-2">
                  <span className="w-[29px] shrink-0 pt-[3px] text-[9.5px]" style={{ color: C.faint }}>
                    {ev.time}
                  </span>
                  <AgentAvatar agentId={ev.agent} name={ev.agent} size={24} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[11px] font-semibold" style={{ color: "#E8DFD4" }}>
                      {ev.agent}
                    </span>
                    <span className="block text-[10px] leading-[1.35]" style={{ color: C.muted }}>
                      {ev.action}
                    </span>
                    <span className="mt-px block text-[9px]" style={{ color: C.faint }}>
                      {ev.dept}
                    </span>
                  </span>
                  <span className="mt-[5px] h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: (KIND_META[ev.kind] ?? KIND_META.create).color }} />
                </div>
              ))
            )}
          </div>
          <Link href={ROUTES.activity} className="rounded-lg border py-[7px] text-center text-[10.5px]" style={{ borderColor: "rgba(200,127,78,.22)", color: C.warm }}>
            Voir toute l&apos;activité
          </Link>
        </div>
      </div>

      {selected ? (
        <div className="flex min-h-[clamp(340px,44vh,420px)] flex-1 gap-3">
          {/* Roster — dimensionné à l'équipe réelle, pas étiré (self-start). */}
          <div
            className="flex w-[clamp(176px,13.4vw,206px)] shrink-0 flex-col self-start rounded-xl border px-2.5 py-[11px]"
            style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
          >
            <div className="flex items-center justify-between border-b pb-[9px]" style={{ borderColor: C.lineSoft }}>
              <span className="text-[9.5px] tracking-[1.5px]" style={{ color: "#D8CFC4" }}>
                ÉQUIPE ROBOTIQUE
              </span>
              <span className="flex items-center gap-1 rounded-[10px] border px-[6px] py-px text-[9px]" style={{ borderColor: "rgba(140,200,150,.3)", color: C.onlineSoft }}>
                <span className="h-[5px] w-[5px] rounded-full" style={{ background: C.online }} />
                {activeCount > 0 ? "En ligne" : "En veille"} ▾
              </span>
            </div>
            <div className="alnua-scroll max-h-[240px] space-y-1 overflow-y-auto py-2">
              {agents.map((agent) => {
                const s = statuses[agent.id]?.status ?? "idle";
                const active = agent.id === selected.id;
                return (
                  <button
                    key={agent.id}
                    type="button"
                    onClick={() => setSelectedId(agent.id)}
                    className="flex w-full items-center gap-2 rounded-lg px-1.5 py-1.5 text-left transition-colors"
                    style={active ? { background: "rgba(200,127,78,.12)" } : undefined}
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
            <Link href={ROUTES.agents} className="rounded-lg border py-[6px] text-center text-[10px]" style={{ borderColor: "rgba(200,127,78,.22)", color: C.warm }}>
              Voir toute l&apos;équipe
            </Link>
          </div>

          {/* Detail */}
          <div
            className="flex min-w-0 flex-1 flex-col gap-[11px] rounded-xl border px-[13px] py-3"
            style={{
              borderColor: C.lineStrong,
              background: "radial-gradient(120% 120% at 0% 0%, rgba(200,127,78,.08), rgba(16,13,11,.6) 55%)",
              boxShadow: "0 0 24px rgba(200,127,78,.07)",
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
                  <span>⊕ Workshop Robotique</span>
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

          <ApercuPanel agent={selected} selLoad={selLoad} selStatus={selStatus} projects={projects} tickets={tickets} bureau="robo" />
        </div>
      ) : null}
    </div>
  );
}

export default function RoboDepartmentV2Page() {
  return (
    <ConsoleProvider>
      <RoboDepartmentView />
      <CooDrawer />
    </ConsoleProvider>
  );
}
