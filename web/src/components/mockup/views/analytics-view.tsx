"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp } from "lucide-react";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { ConsoleDepartment } from "@/lib/console/types";
import { cn } from "@/lib/utils";
import { MockCard, ProgressBar, StatusBadge } from "../mockup-widgets";
import { poleFadeUp } from "../pole-page-shell";
import { PoleKpiRow, SeeAllLink } from "../pole-kpi-row";
import {
  PoleFilledPanel,
  PoleListCard,
  PoleProtoTabs,
  PoleStatStrip,
} from "../pole-proto-tabs";

interface AnalyticsViewProps {
  department: ConsoleDepartment;
}

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "rapports", label: "Rapports" },
  { id: "insights", label: "Insights" },
  { id: "sources", label: "Sources" },
];

type ListRow = { primary: string; secondary?: string; meta?: string; tone?: "ok" | "warn" | "muted" };
type PanelDef = {
  title: string;
  subtitle: string;
  stats: { label: string; value: string }[];
  left: { title: string; rows: ListRow[] };
  right: { title: string; rows: ListRow[] };
};

const CHART_DATA = [35, 42, 38, 50, 55, 62, 58, 70, 75, 82, 78, 88];

const INSIGHTS = [
  { title: "Pic d'activité R&D", desc: "+32% de requêtes LLM cette semaine", impact: "Haute" },
  { title: "Conversion marketing", desc: "Taux de conversion x1.8 sur TikTok", impact: "Moyenne" },
  { title: "Coût par projet", desc: "APP dépasse le budget de 12%", impact: "Haute" },
];

const REPORTS = [
  { title: "Analyse coûts Q3", author: "Axel Roux", status: "Publié" },
  { title: "Usage modèles par pôle", author: "Layla Hassan", status: "Brouillon" },
  { title: "Satisfaction agents 2026", author: "Axel Roux", status: "Publié" },
];

const POLE_USAGE = [
  { name: "APP", value: 32 },
  { name: "R&D", value: 28 },
  { name: "Marketing", value: 18 },
  { name: "Gaming", value: 12 },
  { name: "Robotique", value: 10 },
];

const SECONDARY: Record<string, PanelDef> = {
  rapports: {
    title: "Rapports",
    subtitle: "Analyses publiées et brouillons en cours",
    stats: [
      { label: "Publiés", value: "64" },
      { label: "Brouillons", value: "12" },
      { label: "En revue", value: "8" },
      { label: "Ce mois", value: "+14" },
      { label: "Lectures", value: "2.1K" },
    ],
    left: {
      title: "RAPPORTS RÉCENTS",
      rows: [
        { primary: "Analyse coûts Q3", secondary: "Axel Roux · Finance", meta: "Publié", tone: "ok" },
        { primary: "Usage modèles par pôle", secondary: "Layla Hassan · Ops", meta: "Brouillon", tone: "warn" },
        { primary: "Satisfaction agents 2026", secondary: "Axel Roux · RH", meta: "Publié", tone: "ok" },
        { primary: "Latence OpenRouter", secondary: "Layla Hassan · Infra", meta: "En revue", tone: "muted" },
      ],
    },
    right: {
      title: "PLANIFIÉS",
      rows: [
        { primary: "Forecast budget Q4", secondary: "Échéance 15 août", meta: "Priorité", tone: "warn" },
        { primary: "Benchmark LLM tiers", secondary: "Échéance 22 août", meta: "Standard", tone: "muted" },
        { primary: "Rapport adoption Mem0", secondary: "Échéance 29 août", meta: "Standard", tone: "muted" },
      ],
    },
  },
  insights: {
    title: "Insights",
    subtitle: "Signaux détectés sur l'activité multi-pôles",
    stats: [
      { label: "Actifs", value: "11" },
      { label: "Haute priorité", value: "3" },
      { label: "Résolus 7j", value: "7" },
      { label: "Précision", value: "94%" },
      { label: "Alertes", value: "3" },
    ],
    left: {
      title: "INSIGHTS PRIORITAIRES",
      rows: [
        { primary: "Pic d'activité R&D", secondary: "+32% requêtes LLM cette semaine", meta: "Haute", tone: "warn" },
        { primary: "Coût par projet APP", secondary: "Budget dépassé de 12%", meta: "Haute", tone: "warn" },
        { primary: "Conversion TikTok", secondary: "Taux x1.8 vs moyenne", meta: "Moyenne", tone: "ok" },
        { primary: "Churn Mem0 embeddings", secondary: "Latence +180 ms le soir", meta: "Moyenne", tone: "muted" },
      ],
    },
    right: {
      title: "TENDANCES",
      rows: [
        { primary: "Volume Gaming Studio", secondary: "Stable sur 14 jours", meta: "+2%", tone: "ok" },
        { primary: "Coût token premium", secondary: "Hausse modèles Claude", meta: "+9%", tone: "warn" },
        { primary: "Adoption skills vault", secondary: "Learn-on-demand actif", meta: "+21%", tone: "ok" },
      ],
    },
  },
  sources: {
    title: "Sources",
    subtitle: "Connecteurs data et santé des pipelines",
    stats: [
      { label: "Connectées", value: "8" },
      { label: "Saines", value: "7" },
      { label: "Dégradées", value: "1" },
      { label: "Sync /h", value: "24" },
      { label: "Uptime", value: "99.4%" },
    ],
    left: {
      title: "SOURCES CONNECTÉES",
      rows: [
        { primary: "Supabase", secondary: "Postgres · agent_logs, costs", meta: "Online", tone: "ok" },
        { primary: "Langfuse", secondary: "Traces LLM · latence & tokens", meta: "Online", tone: "ok" },
        { primary: "Mem0", secondary: "Mémoire agents · digests", meta: "Online", tone: "ok" },
        { primary: "GitHub", secondary: "Repos · PRs & commits", meta: "Online", tone: "ok" },
      ],
    },
    right: {
      title: "PIPELINES",
      rows: [
        { primary: "Cost monitor → JSON", secondary: "Dernière sync il y a 4 min", meta: "OK", tone: "ok" },
        { primary: "Trend radar HN/Reddit", secondary: "Dernière sync il y a 28 min", meta: "OK", tone: "ok" },
        { primary: "OpenRouter usage", secondary: "Quota API proche limite", meta: "Attention", tone: "warn" },
      ],
    },
  },
};

export function MockupAnalyticsView({ department }: AnalyticsViewProps) {
  const [tab, setTab] = useState("dashboard");
  const panel = SECONDARY[tab];

  return (
    <div className="pb-8">
      <PoleProtoTabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "dashboard" ? (
        <AnalyticsDashboard department={department} onNavigateTab={setTab} />
      ) : panel ? (
        <PoleFilledPanel title={panel.title} subtitle={panel.subtitle} onBack={() => setTab("dashboard")}>
          <PoleStatStrip items={panel.stats} />
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            <PoleListCard title={panel.left.title} rows={panel.left.rows} />
            <PoleListCard title={panel.right.title} rows={panel.right.rows} />
          </div>
        </PoleFilledPanel>
      ) : null}
    </div>
  );
}

function AnalyticsDashboard({
  department,
  onNavigateTab,
}: {
  department: ConsoleDepartment;
  onNavigateTab: (id: string) => void;
}) {
  const max = Math.max(...CHART_DATA);
  const min = Math.min(...CHART_DATA);
  const range = max - min || 1;
  const points = CHART_DATA.map(
    (v, i) => `${(i / (CHART_DATA.length - 1)) * 100},${100 - ((v - min) / range) * 80 - 10}`,
  ).join(" ");

  return (
    <div className="space-y-3">
      <PoleKpiRow
        kpis={[
          { label: "REQUÊTES/J", value: "12.4K", delta: "+18%", deltaType: "up", trend: [8, 9, 10, 11, 11.5, 12.4], color: "#C08A72" },
          { label: "RAPPORTS", value: "86", delta: "+12", deltaType: "up", trend: [60, 68, 72, 75, 80, 86], color: "#22c55e", onClick: () => onNavigateTab("rapports") },
          { label: "ALERTES", value: "3", delta: "-2", deltaType: "down", trend: [5, 5, 4, 4, 3, 3], color: "#f97316", onClick: () => onNavigateTab("insights") },
          { label: "PRÉCISION", value: "94%", delta: "+1.2%", deltaType: "up", trend: [91, 92, 92.5, 93, 93.5, 94], color: "#60a5fa" },
        ]}
      />

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-8" custom={4} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="VOLUME DE REQUÊTES — 30 JOURS" action={<TrendingUp className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="relative h-40 w-full">
              <svg className="h-full w-full overflow-visible" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="anaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#C08A72" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#C08A72" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <polygon points={`0,100 ${points} 100,100`} fill="url(#anaGrad)" />
                <polyline points={points} fill="none" stroke="#C08A72" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
              </svg>
            </div>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {[
                { label: "Moyenne", value: "9.8K" },
                { label: "Pic", value: "14.2K" },
                { label: "Total", value: "294K" },
              ].map((m) => (
                <div key={m.label} className="rounded-lg border border-bronze-faint bg-obsidian/50 p-2 text-center">
                  <p className="font-title text-base font-semibold text-ivoire">{m.value}</p>
                  <p className="text-[9px] text-titane/50">{m.label}</p>
                </div>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-4" custom={5} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="USAGE PAR PÔLE" action={<BarChart3 className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="space-y-2">
              {POLE_USAGE.map((d) => (
                <div key={d.name} className="space-y-0.5">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-ivoire/80">{d.name}</span>
                    <span className="text-copper">{d.value}%</span>
                  </div>
                  <ProgressBar value={d.value} />
                </div>
              ))}
            </div>
          </MockCard>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-4" custom={6} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="INSIGHTS GÉNÉRÉS" action={<SeeAllLink onClick={() => onNavigateTab("insights")} label="Tous" />}>
            <div className="space-y-2">
              {INSIGHTS.map((ins) => (
                <button key={ins.title} type="button" onClick={() => onNavigateTab("insights")} className="w-full rounded-xl border border-bronze-faint bg-obsidian/50 p-3 text-left transition-all hover:border-copper/40">
                  <div className="flex items-center justify-between">
                    <p className="text-[11px] font-medium text-ivoire/90">{ins.title}</p>
                    <span className={cn("rounded px-1.5 py-0.5 text-[9px]", ins.impact === "Haute" ? "bg-copper/10 text-copper" : "bg-obsidian-2 text-titane/70")}>{ins.impact}</span>
                  </div>
                  <p className="mt-1 text-[10px] text-titane/55">{ins.desc}</p>
                </button>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-4" custom={7} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="RAPPORTS RÉCENTS" action={<SeeAllLink onClick={() => onNavigateTab("rapports")} label="Rapports" />}>
            <div className="space-y-2">
              {REPORTS.map((r) => (
                <button key={r.title} type="button" onClick={() => onNavigateTab("rapports")} className="w-full rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2 text-left hover:border-copper/40">
                  <p className="text-[11px] font-medium text-ivoire/90">{r.title}</p>
                  <div className="mt-1 flex items-center justify-between">
                    <span className="text-[10px] text-titane/50">{r.author}</span>
                    <StatusBadge status={r.status === "Publié" ? "success" : "warning"}>{r.status}</StatusBadge>
                  </div>
                </button>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-4" custom={8} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="ÉQUIPE & SOURCES">
            <div className="mb-3 space-y-2">
              {department.agents.map((a) => (
                <div key={a.id} className="flex items-center gap-2">
                  <AgentAvatar agentId={a.id} name={a.name} size={32} />
                  <div className="min-w-0 flex-1">
                    <p className="text-[11px] font-medium text-ivoire/90">{a.name}</p>
                    <p className="text-[9px] text-titane/55">{a.role}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="border-t border-bronze-faint pt-2">
              <p className="mb-2 text-[9px] uppercase tracking-wider text-titane/50">Sources connectées</p>
              <div className="space-y-1.5">
                {["Supabase", "Langfuse", "Mem0", "GitHub"].map((src) => (
                  <button key={src} type="button" onClick={() => onNavigateTab("sources")} className="flex w-full items-center justify-between rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-1.5 text-left hover:border-copper/40">
                    <span className="text-[10px] text-ivoire/80">{src}</span>
                    <div className="h-2 w-2 rounded-full bg-online" />
                  </button>
                ))}
              </div>
            </div>
          </MockCard>
        </motion.div>
      </div>
    </div>
  );
}
