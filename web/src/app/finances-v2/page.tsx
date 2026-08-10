"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { DeptV2CommandBar, DeptV2PageShell } from "@/components/dept-v2";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { useConsoleData, ConsoleProvider } from "@/components/console/console-provider";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { getAgentsForBureau, type BureauAgentDef } from "@/lib/agent-bureau";
import { fetchProjects } from "@/lib/api";
import { ROUTES } from "@/lib/routes";
import { C, STATUS_TEXT, STATUS_COLOR, resolveAgentLoad, agentLoadChip } from "../app-v2/shared";
import { MissionBox, ChatPanel, RecentTasksPanel, ApercuPanel } from "../app-v2/team";
import { useCooStore } from "@/store/coo-store";
import { CooDrawer } from "@/components/shared/coo-drawer";
import { FinancesTransactionModal } from "@/components/finances/finances-transaction-modal";
import {
  currentMonthKey,
  fetchFinanceDashboard,
  type FinanceDashboard,
  type FinanceTransaction,
} from "@/lib/finances-api";
import type { TicketWithProject } from "@/lib/tickets";
import type { Project } from "@/lib/types";
import { VueGlobaleTab } from "./vue-globale-tab";
import { TransactionsTab } from "./transactions-tab";
import { CoutsTab } from "./couts-tab";
import { BudgetsFiscalTab } from "./budgets-fiscal-tab";

/* Département Finances — chrome void / Jarvis (DEC-016). */

const TABS = ["Équipe", "Vue globale", "Transactions", "Coûts & Factures", "Budgets & Fiscal"] as const;
type Tab = (typeof TABS)[number];

const QUICK_ACTIONS = [
  { icon: "+", label: "Nouvelle transaction" },
  { icon: "≡", label: "Rapport mensuel" },
  { icon: "◎", label: "Analyse des coûts" },
  { icon: "⚙", label: "Automatisation" },
] as const;

function useLiveClock(): string {
  const [now, setNow] = useState("--:--:--");
  useEffect(() => {
    const tick = () =>
      setNow(new Date().toLocaleTimeString("fr-FR", { hour12: false }));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

function FinancesDepartmentView() {
  const agents = getAgentsForBureau("finances");
  const statuses = useAgentStatuses();
  const { activityFeed } = useConsoleData();
  const clock = useLiveClock();
  const [tab, setTab] = useState<Tab>("Vue globale");
  const [selectedId, setSelectedId] = useState(agents[0]?.id ?? "");

  const [projects, setProjects] = useState<Project[]>([]);
  const [month, setMonth] = useState(currentMonthKey());
  const [dashboard, setDashboard] = useState<FinanceDashboard | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);
  const [txModalOpen, setTxModalOpen] = useState(false);
  const [editingTx, setEditingTx] = useState<FinanceTransaction | null>(null);

  const openDrawer = useCooStore((s) => s.openDrawer);
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);

  function requestNewAgent() {
    setPrefillMessage(
      "Je veux ajouter un agent à la comptabilité. Quel rôle manque-t-il et comment le créer ? ",
    );
    openDrawer();
  }

  function openNewTransaction() {
    setEditingTx(null);
    setTxModalOpen(true);
  }
  function openEditTransaction(tx: FinanceTransaction) {
    setEditingTx(tx);
    setTxModalOpen(true);
  }

  useEffect(() => {
    let cancelled = false;
    void fetchProjects()
      .then((all) => {
        if (!cancelled) setProjects(all);
      })
      .catch(() => {
        if (!cancelled) setProjects([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setDashboardLoading(true);
    fetchFinanceDashboard(month)
      .then((d) => {
        if (!cancelled) setDashboard(d);
      })
      .catch(() => {
        if (!cancelled) setDashboard(null);
      })
      .finally(() => {
        if (!cancelled) setDashboardLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [month, refreshKey]);

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

  const tickets: TicketWithProject[] = [];

  if (!selected) {
    return (
      <p className="p-8 text-sm text-titanium">
        Aucun agent dans le bureau Comptabilité.
      </p>
    );
  }

  return (
    <DeptV2PageShell
      deptHref={ROUTES.finances}
      activeDeptId="finances"
      coreSubtitle="Cockpit opérationnel"
    >
      <div className="dept-hud flex min-w-0 flex-1 flex-col gap-4 px-5 pb-4 pt-4">
        <div className="flex shrink-0 items-end justify-between gap-3 border-b border-titanium/15 pb-3">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <p className="text-[9px] font-medium uppercase tracking-[0.28em] text-titanium/70">
                Département 09
              </p>
              <span className="hidden items-center gap-1.5 text-[9px] tracking-[0.18em] text-teal sm:flex">
                <span className="finance-live-dot" />
                SYSTEMS ONLINE
              </span>
            </div>
            <h1 className="mt-1 truncate font-display text-[26px] font-light leading-none tracking-[0.08em] text-metal-titanium">
              COMPTABILITÉ
            </h1>
            <p className="mt-1.5 truncate text-[11px] tracking-wide text-titanium/60">
              Finance · Budget · Reporting · Conformité
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <span className="hidden font-mono text-[11px] tabular-nums tracking-wider text-titanium/70 sm:inline">
              {clock}
            </span>
            <span className="hidden items-center gap-2 border border-titanium/20 px-3 py-1.5 text-[10px] text-titanium sm:flex">
              <span className="finance-live-dot" />
              {activeCount} actif{activeCount !== 1 ? "s" : ""}
            </span>
            <button
              type="button"
              onClick={requestNewAgent}
              className="bg-metal-copper px-3 py-1.5 text-[10px] tracking-wide transition-opacity hover:opacity-90"
            >
              + Agent
            </button>
          </div>
        </div>

        <div className="flex gap-6 overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={
                tab === t
                  ? "shrink-0 border-b border-copper pb-2 text-[10px] uppercase tracking-[0.16em] text-metal-copper"
                  : "shrink-0 border-b border-transparent pb-2 text-[10px] uppercase tracking-[0.16em] text-titanium/55 transition-colors hover:text-titanium"
              }
              style={
                tab === t ? { boxShadow: `0 1px 14px ${C.copperGlow}` } : undefined
              }
            >
              {t}
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
          ) : tab === "Vue globale" ? (
            <VueGlobaleTab
              month={month}
              dashboard={dashboard}
              dashboardLoading={dashboardLoading}
              onMonthChange={setMonth}
              projects={projects}
            />
          ) : tab === "Transactions" ? (
            <TransactionsTab
              month={month}
              refreshKey={refreshKey}
              onAdd={openNewTransaction}
              onEdit={openEditTransaction}
            />
          ) : tab === "Coûts & Factures" ? (
            <CoutsTab />
          ) : (
            <BudgetsFiscalTab />
          )}
        </div>

        <DeptV2CommandBar
          actions={QUICK_ACTIONS.map((qa) => ({
            icon: qa.icon,
            label: qa.label,
            onClick: qa.label === "Nouvelle transaction" ? openNewTransaction : undefined,
          }))}
        />

      </div>

      <FinancesTransactionModal
        open={txModalOpen}
        onOpenChange={setTxModalOpen}
        projects={projects}
        transaction={editingTx}
        defaultMonth={month}
        onSaved={() => setRefreshKey((k) => k + 1)}
      />
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
      {/* Roster */}
      <div className="finance-instrument flex w-[clamp(176px,13.4vw,206px)] shrink-0 flex-col self-start px-2.5 py-3">
        <div className="flex items-center justify-between border-b border-titanium/15 pb-2">
          <span className="text-[9px] font-medium uppercase tracking-[0.2em] text-titanium">
            Équipe
          </span>
          <span className="flex items-center gap-1.5 text-[9px] text-titanium/70">
            <span
              className="h-1 w-1 rounded-full"
              style={{ background: C.online, boxShadow: `0 0 6px ${C.online}` }}
            />
            {activeCount > 0 ? "Live" : "Veille"}
          </span>
        </div>
        <div className="alnua-scroll max-h-[260px] space-y-0.5 overflow-y-auto py-2">
          {agents.map((agent) => {
            const s = statuses[agent.id]?.status ?? "idle";
            const active = agent.id === selectedId;
            return (
              <button
                key={agent.id}
                type="button"
                onClick={() => setSelectedId(agent.id)}
                className="flex w-full items-center gap-2 px-1.5 py-1.5 text-left transition-colors hover:bg-white/[0.03]"
                style={
                  active
                    ? {
                        background: "rgba(224,155,106,0.08)",
                        boxShadow: `inset 2px 0 0 ${C.copper}`,
                      }
                    : undefined
                }
              >
                <AgentAvatar agentId={agent.id} name={agent.name} size={32} />
                <span className="min-w-0 flex-1">
                  <span
                    className="block truncate text-[11px] font-medium"
                    style={{ color: active ? C.copperLight : C.ivory }}
                  >
                    {agent.name}
                  </span>
                  <span className="block truncate text-[9px] text-titanium/55">
                    {agent.role}
                  </span>
                </span>
                <span className="flex shrink-0 flex-col items-end gap-[3px]">
                  <span className="text-[9px] text-titanium/50">
                    {agentLoadChip(statuses[agent.id], s)}
                  </span>
                  <span
                    className="h-1 w-1 rounded-full"
                    style={{ background: STATUS_COLOR[s] }}
                  />
                </span>
              </button>
            );
          })}
        </div>
        <Link
          href={ROUTES.agents}
          className="mt-1 border border-titanium/20 py-1.5 text-center text-[10px] text-titanium transition-colors hover:border-copper/40 hover:text-copper-light"
        >
          Voir toute l&apos;équipe
        </Link>
      </div>

      {/* Agent detail */}
      <div className="finance-instrument flex min-w-0 flex-1 flex-col gap-3 px-3.5 py-3">
        <div className="flex items-start justify-between gap-3 border-b border-titanium/15 pb-3">
          <div className="flex min-w-0 items-center gap-3">
            <AgentAvatar agentId={selected.id} name={selected.name} size={52} ring />
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="truncate font-display text-[18px] font-light tracking-wide text-ivoire">
                  {selected.name}
                </span>
                <span className="text-[11px] text-copper-light">✓</span>
              </div>
              <p className="truncate text-[12px] text-titanium">{selected.role}</p>
              <p className="mt-1 truncate text-[9.5px] text-titanium/50">
                {selected.skills.join(" · ")}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1.5">
            <div className="flex items-center gap-3 text-[10px]">
              <span
                className="flex items-center gap-1.5"
                style={{ color: STATUS_COLOR[selStatus] }}
              >
                <span
                  className="h-1 w-1 rounded-full"
                  style={{ background: STATUS_COLOR[selStatus] }}
                />
                {STATUS_TEXT[selStatus]}
              </span>
              <Link
                href={`${ROUTES.openroom}?agent=${encodeURIComponent(selected.id)}`}
                className="border border-titanium/25 px-2.5 py-1 text-[10px] text-titanium transition-colors hover:border-copper/40 hover:text-copper-light"
              >
                Profil ↗
              </Link>
            </div>
            <div className="flex gap-3 text-[10px] text-titanium/45">
              <span>Comptabilité</span>
              <span>{selected.skills.length} skills</span>
            </div>
          </div>
        </div>

        <div className="flex min-h-0 flex-1 flex-col gap-3 min-[1240px]:flex-row">
          <MissionBox agent={selected} status={statuses[selected.id]} tickets={tickets} />
          <ChatPanel agent={selected} />
          <RecentTasksPanel tasks={agentTasks} />
        </div>
      </div>

      <ApercuPanel
        agent={selected}
        selLoad={selLoad}
        selStatus={selStatus}
        projects={projects}
        tickets={tickets}
        bureau="finances"
      />
    </div>
  );
}

export default function FinancesDepartmentV2Page() {
  return (
    <ConsoleProvider>
      <FinancesDepartmentView />
      <CooDrawer />
    </ConsoleProvider>
  );
}
