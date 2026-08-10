"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { DeptV2CommandBar, DeptV2PageShell } from "@/components/dept-v2";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { useConsoleData, ConsoleProvider } from "@/components/console/console-provider";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { getAgentsForBureau, type BureauAgentDef } from "@/lib/agent-bureau";
import { fetchProjects } from "@/lib/api";
import { fetchLatestGamingBuild } from "@/lib/gaming-builds";
import { ROUTES } from "@/lib/routes";
import type { GamingBuild, Project } from "@/lib/types";
import type { TicketWithProject } from "@/lib/tickets";
import type { ConsoleActivityItem } from "@/lib/console/types";
import { C, STATUS_TEXT, STATUS_COLOR, KIND_META, resolveAgentLoad, agentLoadChip } from "../app-v2/shared";
import { useBureauTickets } from "../app-v2/tabs";
import { MissionBox, ChatPanel, RecentTasksPanel, ApercuPanel } from "../app-v2/team";
import { useCooStore } from "@/store/coo-store";
import { CooDrawer } from "@/components/shared/coo-drawer";
import { UE5_VERSION } from "./mock-data";
import { ProjetsTab } from "./projects-tab";
import { MissionsTab } from "./missions-tab";
import { AssetsTab } from "./assets-tab";
import { BacklogTab } from "./backlog-tab";
import { DocumentationTab } from "./documentation-tab";
import { AnalyticsTab } from "./analytics-tab";
import { SettingsTab } from "./settings-tab";

/* ────────────────────────────────────────────────────────────────────────────
   Département Gaming — même socle que /app-v2 (header, sidebar, onglets),
   contenu spécialisé Gaming, plus un onglet propre (Assets). Décision du
   2026-07-31 (plan Gaming/Robotique) : roster visuel pour l'instant (3 agents
   réels + 7 postes vacants), pas de faux agents créés. DA légèrement plus
   "cinématique" (fond plus profond, grille façon viewport) tout en restant
   Obsidian / Titane / Cuivre — aucune teinte bleue ajoutée. */

const TABS = ["Équipe", "Projets", "Missions", "Assets", "Backlog", "Documentation", "Analytics", "Paramètres"] as const;
type Tab = (typeof TABS)[number];

const TAB_ICON: Record<Tab, string> = {
  Équipe: "👥",
  Projets: "▤",
  Missions: "◈",
  Assets: "◆",
  Backlog: "☰",
  Documentation: "📄",
  Analytics: "📈",
  Paramètres: "⚙",
};

const QUICK_ACTIONS = [
  { icon: "＋", label: "Nouvelle mission" },
  { icon: "▤", label: "Rapport d'équipe" },
  { icon: "◎", label: "Analyse build" },
  { icon: "⚙", label: "Automatisation" },
] as const;

/* Les 10 rôles du plan Gaming ont désormais tous un agent réel (Phase 13,
   ROADMAP.md, 2026-07-30) — plus de postes vacants. Le tableau reste en
   place (vide) pour ne pas retoucher le rendu ci-dessous si un nouveau rôle
   venait à manquer plus tard. */
const VACANT_ROLES: string[] = [];

function GamingDepartmentView() {
  const agents = getAgentsForBureau("gaming");
  const statuses = useAgentStatuses();
  const { activityFeed } = useConsoleData();
  const [tab, setTab] = useState<Tab>("Équipe");
  const [projects, setProjects] = useState<Project[]>([]);
  const { tickets } = useBureauTickets(projects);

  useEffect(() => {
    let cancelled = false;
    void fetchProjects()
      .then((all) => {
        if (!cancelled) setProjects(all.filter((p) => p.branch === "gaming"));
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
        ? `Je veux ouvrir un poste "${role}" au studio Gaming. Comment le créer ?`
        : "Je veux ajouter un agent au studio Gaming. Quel rôle manque-t-il et comment le créer ?",
    );
    openDrawer();
  }

  const activeCount = agents.filter((a) => {
    const s = statuses[a.id]?.status;
    return s === "working" || s === "waiting";
  }).length;

  return (
    <DeptV2PageShell deptHref={ROUTES.gaming} activeDeptId="gaming" coreSubtitle="Studio opérationnel">
        <div className="dept-hud flex min-w-0 flex-1 flex-col gap-4 px-5 pb-4 pt-4">
          <div className="flex shrink-0 items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <span
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] border text-[15px]"
                style={{ borderColor: "rgba(224,155,106,.4)", background: "radial-gradient(circle at 30% 20%, rgba(224,155,106,.25), #000000)", color: C.copperLight }}
              >
                🎮
              </span>
              <div className="min-w-0">
                <h1 className="truncate text-[23px] leading-[1.1] tracking-[1px]">
                  <span className="font-bold">GAMING</span>{" "}
                  <span className="font-light tracking-[4px]" style={{ color: "#A7ADB5" }}>
                    STUDIO
                  </span>
                </h1>
                <p className="mt-0.5 truncate text-[11px]" style={{ color: C.dim }}>
                  Wyrdheim Online · Unreal Engine 5 · Lore &amp; gameplay
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
                onClick={() => requestRole()}
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
                onRequestRole={requestRole}
                tickets={tickets}
                activityFeed={activityFeed}
                projects={projects}
              />
            ) : tab === "Projets" ? (
              <ProjetsTab projects={projects} agents={agents} onProjectCreated={(p) => setProjects((prev) => [...prev, p])} />
            ) : tab === "Missions" ? (
              <MissionsTab projects={projects} agents={agents} statuses={statuses} activityFeed={activityFeed} />
            ) : tab === "Assets" ? (
              <AssetsTab projects={projects} />
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

          <DeptV2CommandBar
            actions={QUICK_ACTIONS.map((qa) => ({
              icon: qa.icon,
              label: qa.label,
            }))}
          />
        </div>
    </DeptV2PageShell>
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
  const selLoad = selected
    ? resolveAgentLoad(statuses[selected.id] ?? { status: selStatus })
    : 0;

  /* Dernier build réel du studio (Phase 16, ROADMAP.md, 2026-07-30) — partagé
   * par toutes les cartes agent (pas de vrai suivi par-personne de branche/
   * commit Git ; le seul signal réel disponible est le build le plus récent
   * du studio). null tant qu'aucun build n'a été rapporté. */
  const [latestBuild, setLatestBuild] = useState<GamingBuild | null>(null);
  useEffect(() => {
    const firstProjectId = projects[0]?.id;
    if (!firstProjectId) return;
    let cancelled = false;
    fetchLatestGamingBuild(firstProjectId).then((b) => {
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
          10 cartes (3 réelles + 7 postes vacants) sur plusieurs rangées —
          garde le panneau détail visible sans avoir à faire défiler la page. */}
      <div className="alnua-scroll flex min-w-0 flex-1 gap-3 overflow-x-auto pb-1">
        {agents.map((agent) => {
          const s = statuses[agent.id]?.status ?? "idle";
          const load = resolveAgentLoad(statuses[agent.id] ?? { status: s });
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
                  ? "radial-gradient(120% 120% at 0% 0%, rgba(224,155,106,.12), #000000 60%)"
                  : "#000000",
                boxShadow: active ? "0 0 22px rgba(224,155,106,.12)" : undefined,
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
                  Build <b style={{ color: C.warm }}>{latestBuild ? `#${latestBuild.build_number}` : "—"}</b>
                </span>
                <span className="truncate">
                  UE5 <b style={{ color: C.warm }}>{latestBuild?.engine_version ?? UE5_VERSION}</b>
                </span>
                <span className="truncate">
                  FPS <b style={{ color: C.warm }}>{latestBuild?.fps_avg ?? "—"}</b>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-1 flex-1 overflow-hidden rounded-full" style={{ background: "rgba(224,155,106,.15)" }}>
                  <span className="block h-full rounded-full" style={{ width: `${load}%`, background: C.copper }} />
                </span>
                <span className="text-[9.5px]" style={{ color: C.ivory }}>
                  {load}%
                </span>
              </div>
              {latestBuild?.status === "running" ? (
                <span className="text-metal-copper flex items-center gap-1.5 text-[9px]">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full" style={{ background: C.copperLight }} />
                  Build en cours…
                </span>
              ) : !latestBuild ? (
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
          style={{ borderColor: "rgba(224,155,106,.28)", background: "#000000", minHeight: 150 }}
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-full border text-[13px]" style={{ borderColor: "rgba(224,155,106,.35)", color: C.copperLight }}>
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

      {/* Activité en temps réel — même panneau que App, propre à Équipe. */}
      <div
        className="flex h-[268px] w-[clamp(226px,18vw,276px)] shrink-0 flex-col rounded-xl border px-3 py-[11px]"
        style={{ borderColor: C.line, background: "#000000" }}
      >
        <div className="flex items-center justify-between border-b pb-[9px]" style={{ borderColor: C.lineSoft }}>
          <span className="text-[9.5px] tracking-[1.6px]" style={{ color: "#A7ADB5" }}>
            ACTIVITÉ EN TEMPS RÉEL
          </span>
          <Link href={ROUTES.activity} className="text-metal-copper text-[9.5px]">
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
        <Link href={ROUTES.activity} className="rounded-lg border py-[7px] text-center text-[10.5px]" style={{ borderColor: "rgba(224,155,106,.22)", color: C.warm }}>
          Voir toute l&apos;activité
        </Link>
      </div>
      </div>

      {selected ? (
        <div className="flex min-h-[clamp(340px,44vh,420px)] flex-1 gap-3">
          {/* Roster — dimensionné à l'équipe réelle, pas étiré (self-start). */}
          <div
            className="flex w-[clamp(176px,13.4vw,206px)] shrink-0 flex-col self-start dept-instrument px-2.5 py-[11px]"
          >
            <div className="flex items-center justify-between border-b pb-[9px]" style={{ borderColor: C.lineSoft }}>
              <span className="text-[9.5px] tracking-[1.5px]" style={{ color: "#A7ADB5" }}>
                ÉQUIPE GAMING
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
                  <span>⊕ Studio Gaming</span>
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

          <ApercuPanel agent={selected} selLoad={selLoad} selStatus={selStatus} projects={projects} tickets={tickets} bureau="gaming" />
        </div>
      ) : null}
    </div>
  );
}

export default function GamingDepartmentV2Page() {
  return (
    <ConsoleProvider>
      <GamingDepartmentView />
      <CooDrawer />
    </ConsoleProvider>
  );
}
