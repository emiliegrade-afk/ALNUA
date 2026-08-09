"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { DeptV2PageShell } from "@/components/dept-v2";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { useConsoleData, ConsoleProvider } from "@/components/console/console-provider";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { getAgentsForBureau, type BureauAgentDef } from "@/lib/agent-bureau";
import { fetchProjects } from "@/lib/api";
import { ROUTES } from "@/lib/routes";
import { C, STATUS_LOAD, STATUS_TEXT, STATUS_COLOR } from "../app-v2/shared";
import { MissionBox, ChatPanel, RecentTasksPanel, ApercuPanel } from "../app-v2/team";
import { useCooStore } from "@/store/coo-store";
import { CooDrawer } from "@/components/shared/coo-drawer";
import { FinancesAccountingPanel } from "@/components/finances/finances-accounting-panel";
import { FinancesControllerPanel } from "@/components/finances/finances-controller-panel";
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

/* ────────────────────────────────────────────────────────────────────────────
   Département Finances v2 — Phase 29 + DEC-016. Socle autonome (en-tête,
   sidebar, barre de commandes). Données réelles via finances-api /
   costs-api. Onglet « Coûts & Factures » = API costs + SaaS + ledger
   factures + statut Revolut (`SaasInvoicesPanel`). Depuis Phase B
   (2026-08-09), `/finances` ré-exporte cette page (plus de MockupShell).
   ──────────────────────────────────────────────────────────────────────────── */

const TABS = ["Équipe", "Vue globale", "Transactions", "Coûts & Factures"] as const;
type Tab = (typeof TABS)[number];

const TAB_ICON: Record<Tab, string> = {
  Équipe: "👥",
  "Vue globale": "◉",
  Transactions: "💳",
  "Coûts & Factures": "📡",
};

const QUICK_ACTIONS = [
  { icon: "＋", label: "Nouvelle transaction" },
  { icon: "▤", label: "Rapport mensuel" },
  { icon: "◎", label: "Analyse des coûts" },
  { icon: "⚙", label: "Automatisation" },
] as const;

function FinancesDepartmentView() {
  const agents = getAgentsForBureau("finances");
  const statuses = useAgentStatuses();
  const { activityFeed } = useConsoleData();
  const [tab, setTab] = useState<Tab>("Équipe");
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
  const selLoad = STATUS_LOAD[selStatus];

  const activeCount = agents.filter((a) => {
    const s = statuses[a.id]?.status;
    return s === "working" || s === "waiting";
  }).length;

  const agentTasks = useMemo(
    () => (selected ? activityFeed.filter((e) => e.agent === selected.name).slice(0, 6) : []),
    [activityFeed, selected],
  );

  // Pas de concept de ticket propre à la Comptabilité (comme /finances legacy,
  // projectBranch: null) — tableau honnêtement vide plutôt qu'un filtre
  // inutilisé sur une branche qui n'existe pas pour ce bureau.
  const tickets: TicketWithProject[] = [];

  const dashboardData = dashboard
    ? {
        total_income: dashboard.current_month.total_income,
        total_expenses: dashboard.current_month.total_expenses,
        balance: dashboard.current_month.balance,
        by_category: dashboard.current_month.by_category,
      }
    : undefined;

  if (!selected) {
    return (
      <p className="p-8 text-sm" style={{ color: C.dim }}>
        Aucun agent dans le bureau Comptabilité.
      </p>
    );
  }

  return (
    <DeptV2PageShell deptHref={ROUTES.finances} activeDeptId="finances" coreSubtitle="Cockpit opérationnel">
        <div className="flex min-w-0 flex-1 flex-col gap-3 px-4 pb-3 pt-3.5">
          <div className="flex shrink-0 items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <span
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] border text-[15px]"
                style={{ borderColor: "rgba(192,138,114,.4)", background: "radial-gradient(circle at 30% 20%, rgba(192,138,114,.25), rgba(14,16,20,.9))", color: C.copperLight }}
              >
                💠
              </span>
              <div className="min-w-0">
                <h1 className="truncate text-[23px] leading-[1.1] tracking-[1px]">
                  <span className="font-bold">FINANCE</span>{" "}
                  <span className="font-light tracking-[4px]" style={{ color: "#A7ADB5" }}>
                    COCKPIT
                  </span>
                </h1>
                <p className="mt-0.5 truncate text-[11px]" style={{ color: C.dim }}>
                  Trésorerie · Coûts IA · Prévisions
                </p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-[9px]">
              <span
                className="hidden items-center gap-[7px] rounded-[18px] border px-[13px] py-1.5 text-[11.5px] sm:flex"
                style={{ borderColor: "rgba(192,138,114,.22)", background: "rgba(19,22,27,.6)", color: C.warm }}
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
                style={{ borderColor: tab === t ? C.copper : "transparent", color: tab === t ? "#F5F2EA" : C.faint }}
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
            ) : tab === "Vue globale" ? (
              <VueGlobaleTab month={month} dashboard={dashboard} dashboardLoading={dashboardLoading} onMonthChange={setMonth} projects={projects} />
            ) : tab === "Transactions" ? (
              <TransactionsTab month={month} refreshKey={refreshKey} onAdd={openNewTransaction} onEdit={openEditTransaction} />
            ) : (
              <CoutsTab />
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
                  qa.label === "Nouvelle transaction" ? (
                    // Seule action réellement câblée du groupe (label toujours
                    // visible, fond distinct — précédent rnd-v2, signalé par
                    // Emilie : boutons introuvables sous ~1280px si le libellé
                    // se masque comme les icônes décoratives).
                    <button
                      key={qa.label}
                      type="button"
                      onClick={openNewTransaction}
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
              <AlnuaStar size={60} glow sparkMid="#D9A88F" sparkOuter="#C08A72" glowColorRgb="192,138,114" />
            </span>
          </div>

          {/* Outils IA Jules/Rémi — repliés par défaut, fonctionnalité réelle
              de l'ancien /finances, préservée mais pas visible sans défiler
              volontairement (même pattern que gaming-v2). */}
          <details className="group shrink-0 rounded-xl border" style={{ borderColor: C.line }}>
            <summary className="flex cursor-pointer items-center gap-2 px-4 py-2.5 text-[10.5px]" style={{ color: C.dim }}>
              <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
              Jules — Comptabilité
            </summary>
            <div className="alnua-scroll max-h-[46vh] overflow-y-auto border-t p-4" style={{ borderColor: C.line }}>
              <FinancesAccountingPanel month={month} dashboardData={dashboardData} />
            </div>
          </details>
          <details className="group shrink-0 rounded-xl border" style={{ borderColor: C.line }}>
            <summary className="flex cursor-pointer items-center gap-2 px-4 py-2.5 text-[10.5px]" style={{ color: C.dim }}>
              <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
              Rémi — Contrôle de gestion
            </summary>
            <div className="alnua-scroll max-h-[46vh] overflow-y-auto border-t p-4" style={{ borderColor: C.line }}>
              <FinancesControllerPanel month={month} dashboardData={dashboardData} />
            </div>
          </details>
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
      <div
        className="flex w-[clamp(176px,13.4vw,206px)] shrink-0 flex-col self-start rounded-xl border px-2.5 py-[11px]"
        style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}
      >
        <div className="flex items-center justify-between border-b pb-[9px]" style={{ borderColor: C.lineSoft }}>
          <span className="text-[9.5px] tracking-[1.5px]" style={{ color: "#A7ADB5" }}>
            ÉQUIPE FINANCE
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

      <div
        className="flex min-w-0 flex-1 flex-col gap-[11px] rounded-xl border px-[13px] py-3"
        style={{
          borderColor: C.lineStrong,
          background: "radial-gradient(120% 120% at 0% 0%, rgba(192,138,114,.08), rgba(19,22,27,.6) 55%)",
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
              <span>⊕ Comptabilité</span>
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

      <ApercuPanel agent={selected} selLoad={selLoad} selStatus={selStatus} projects={projects} tickets={tickets} bureau="finances" />
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
