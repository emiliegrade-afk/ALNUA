"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Compass, Play, TrendingUp } from "lucide-react";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { AlnuaStar } from "@/components/brand/alnua-star";
import type { ConsoleDepartment } from "@/lib/console/types";
import { MockCard, ProgressBar, StatusBadge } from "../mockup-widgets";
import { poleFadeUp } from "../pole-page-shell";
import { PoleKpiRow, SeeAllLink } from "../pole-kpi-row";
import {
  PoleFilledPanel,
  PoleListCard,
  PoleProtoTabs,
  PoleStatStrip,
} from "../pole-proto-tabs";

interface HubViewProps {
  department: ConsoleDepartment;
}

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "sante", label: "Santé pôles" },
  { id: "pipeline", label: "Pipeline" },
  { id: "couts", label: "Coûts" },
  { id: "workflows", label: "Workflows" },
];

const POLES_HEALTH = [
  { name: "APP", score: 88 },
  { name: "R&D", score: 91 },
  { name: "Marketing", score: 82 },
  { name: "Gaming", score: 78 },
  { name: "Robotique", score: 75 },
  { name: "Comptabilité", score: 85 },
  { name: "CEO", score: 87 },
  { name: "Secrétariat", score: 80 },
];

const PIPELINE_ISSUES = [
  { repo: "alnua-hub", number: 142, title: "Auth SSO multi-produits" },
  { repo: "alnua-core", number: 89, title: "Event bus cross-département" },
  { repo: "nomad-mobile", number: 56, title: "Offline mode" },
];

const COSTS = [
  { day: "Lun", value: 12.4 },
  { day: "Mar", value: 18.2 },
  { day: "Mer", value: 15.6 },
  { day: "Jeu", value: 22.1 },
  { day: "Ven", value: 19.8 },
  { day: "Sam", value: 8.4 },
  { day: "Dim", value: 7.2 },
];

const WORKFLOWS = ["Daily briefing", "Review PRs", "R&D dispatch", "Marketing planning"];

export function MockupHubView({ department }: HubViewProps) {
  const [tab, setTab] = useState("dashboard");
  const back = () => setTab("dashboard");
  const totalCost = COSTS.reduce((sum, d) => sum + d.value, 0).toFixed(2);

  return (
    <div className="space-y-3 pb-24">
      <PoleProtoTabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "dashboard" ? <HubDashboard department={department} onNavigateTab={setTab} /> : null}
      {tab === "sante" ? (
        <PoleFilledPanel title="Santé des pôles" subtitle="Score opérationnel par département" onBack={back}>
          <PoleStatStrip
            items={[
              { label: "Moyenne", value: "83%" },
              { label: "Top pôle", value: "R&D" },
              { label: "À surveiller", value: "Robotique" },
              { label: "Agents actifs", value: "26" },
              { label: "Alertes", value: "2" },
            ]}
          />
          <PoleListCard
            title="SCORES & SIGNALS"
            rows={[
              ...POLES_HEALTH.map((p) => ({
                primary: p.name,
                secondary: "Santé opérationnelle",
                meta: `${p.score}%`,
                tone: (p.score >= 85 ? "ok" : p.score >= 78 ? "warn" : "muted") as "ok" | "warn" | "muted",
              })),
            ]}
          />
        </PoleFilledPanel>
      ) : null}
      {tab === "pipeline" ? (
        <PoleFilledPanel title="Pipeline codage" subtitle="Issues & jobs cross-repos" onBack={back}>
          <PoleStatStrip
            items={[
              { label: "Ouvertes", value: "12" },
              { label: "En cours", value: "5" },
              { label: "Bloquées", value: "1" },
              { label: "Reposes / sem.", value: "9" },
              { label: "Reposos", value: "3" },
            ]}
          />
          <PoleListCard
            title="ISSUES & FILES"
            rows={[
              ...PIPELINE_ISSUES.map((i) => ({
                primary: `#${i.number} — ${i.title}`,
                secondary: i.repo,
                meta: "Ready",
                tone: "warn" as const,
              })),
              { primary: "dev_app — Auth SSO", secondary: "alnua-hub #142", meta: "En cours", tone: "ok" },
              { primary: "dev_backend — Event bus", secondary: "alnua-core #89", meta: "Queue", tone: "muted" },
            ]}
          />
        </PoleFilledPanel>
      ) : null}
      {tab === "couts" ? (
        <PoleFilledPanel title="Coûts LLM" subtitle={`7 derniers jours — $${totalCost}`} onBack={back}>
          <PoleStatStrip
            items={[
              { label: "Total 7j", value: `$${totalCost}` },
              { label: "Pic", value: "$22.1" },
              { label: "Moy. / jour", value: `$${(Number(totalCost) / 7).toFixed(1)}` },
              { label: "vs sem. -1", value: "+8%" },
              { label: "Budget mois", value: "62%" },
            ]}
          />
          <PoleListCard
            title="RÉPARTITION 7J"
            rows={[
              ...COSTS.map((d) => ({
                primary: d.day,
                secondary: "OpenRouter + providers",
                meta: `$${d.value.toFixed(1)}`,
                tone: (d.value > 20 ? "warn" : "ok") as "ok" | "warn",
              })),
              { primary: "Direction (COO + Spec)", secondary: "Premium tier", meta: "$28.4", tone: "warn" },
              { primary: "R&D Lab", secondary: "Premium + standard", meta: "$34.2", tone: "warn" },
            ]}
          />
        </PoleFilledPanel>
      ) : null}
      {tab === "workflows" ? (
        <PoleFilledPanel title="Workflows actifs" subtitle="Automatisations n8n & hub" onBack={back}>
          <PoleStatStrip
            items={[
              { label: "Actifs", value: "4" },
              { label: "Runs / j", value: "48" },
              { label: "Échecs 24h", value: "1" },
              { label: "Latence moy.", value: "2.1s" },
              { label: "Planifiés", value: "6" },
            ]}
          />
          <PoleListCard
            title="WORKFLOWS & RUNS"
            rows={[
              ...WORKFLOWS.map((w) => ({
                primary: w,
                secondary: "n8n cloud",
                meta: "Actif",
                tone: "ok" as const,
              })),
              { primary: "Daily briefing — 08:00", secondary: "Succès", meta: "OK", tone: "ok" },
              { primary: "R&D dispatch — 11:02", secondary: "Retry 1×", meta: "Warn", tone: "warn" },
            ]}
          />
        </PoleFilledPanel>
      ) : null}
    </div>
  );
}

function HubDashboard({
  department,
  onNavigateTab,
}: {
  department: ConsoleDepartment;
  onNavigateTab: (id: string) => void;
}) {
  const totalCost = COSTS.reduce((sum, d) => sum + d.value, 0).toFixed(2);

  return (
    <div className="space-y-3">
      <PoleKpiRow
        kpis={[
          { label: "AGENTS", value: "26", delta: "+12%", deltaType: "up", trend: [20, 22, 23, 24, 25, 26], color: "#E09B6A" },
          { label: "PROJETS", value: "38", delta: "+5%", deltaType: "up", trend: [30, 32, 34, 35, 36, 38], color: "#22c55e" },
          { label: "DÉCISIONS/J", value: "184", delta: "+8%", deltaType: "up", trend: [150, 162, 168, 175, 178, 184], color: "#60a5fa" },
          { label: "UPTIME", value: "99.98%", delta: "stable", deltaType: "neutral", trend: [99.9, 99.95, 99.97, 99.98, 99.98, 99.99], color: "#A7ADB5" },
        ]}
      />

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-5" custom={4} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard
            title="CARTE ORGANISATIONNELLE"
            action={<Compass className="h-3.5 w-3.5 text-copper/70" />}
          >
            <div className="relative flex h-48 items-center justify-center">
              <div className="absolute inset-0 rounded-full border border-dashed border-bronze-faint" />
              <div className="absolute inset-8 rounded-full border border-dashed border-bronze-faint/50" />
              <div className="relative z-10 flex h-14 w-14 items-center justify-center rounded-full bg-obsidian-2">
                <AlnuaStar className="h-7 w-7 text-copper" />
              </div>
              {POLES_HEALTH.slice(0, 8).map((p, i) => {
                const angle = (i * 45 - 90) * (Math.PI / 180);
                const radius = i % 2 === 0 ? 42 : 30;
                const x = 50 + radius * Math.cos(angle);
                const y = 50 + radius * Math.sin(angle);
                return (
                  <button
                    key={p.name}
                    type="button"
                    onClick={() => onNavigateTab("sante")}
                    className="absolute flex h-8 w-8 items-center justify-center rounded-full border border-copper/30 bg-obsidian text-[9px] text-copper transition-colors hover:border-copper"
                    style={{ left: `${x}%`, top: `${y}%`, transform: "translate(-50%, -50%)" }}
                  >
                    {p.name.slice(0, 2)}
                  </button>
                );
              })}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-4" custom={5} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard
            title="SANTÉ DES PÔLES"
            action={<SeeAllLink onClick={() => onNavigateTab("sante")} label="Détail" />}
          >
            <div className="space-y-2">
              {POLES_HEALTH.slice(0, 6).map((p) => (
                <div key={p.name} className="space-y-0.5">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-ivoire/80">{p.name}</span>
                    <span className="text-copper">{p.score}%</span>
                  </div>
                  <ProgressBar value={p.score} />
                </div>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-3" custom={6} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="COÛTS LLM — 7J" action={<TrendingUp className="h-3.5 w-3.5 text-copper/70" />}>
            <p className="font-title text-xl font-semibold text-ivoire">${totalCost}</p>
            <div className="mt-2 flex items-end gap-1" style={{ height: 64 }}>
              {COSTS.map((d) => (
                <div
                  key={d.day}
                  className="flex-1 rounded-sm bg-copper/50"
                  style={{ height: `${(d.value / 25) * 100}%` }}
                />
              ))}
            </div>
            <div className="mt-1 flex justify-between text-[8px] text-titane/40">
              {COSTS.map((d) => (
                <span key={d.day}>{d.day}</span>
              ))}
            </div>
            <button type="button" onClick={() => onNavigateTab("couts")} className="mt-2 text-[10px] text-copper hover:underline">
              Rapport coûts →
            </button>
          </MockCard>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-6" custom={7} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="PIPELINE CODAGE" action={<SeeAllLink onClick={() => onNavigateTab("pipeline")} label="Pipeline" />}>
            <div className="space-y-2">
              {PIPELINE_ISSUES.map((issue) => (
                <div
                  key={issue.number}
                  className="flex items-center justify-between rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2"
                >
                  <span className="text-[11px] text-ivoire/80">
                    [{issue.repo}] #{issue.number} — {issue.title}
                  </span>
                  <button
                    type="button"
                    className="rounded border border-copper/30 p-1 text-copper hover:bg-copper/10"
                  >
                    <Play className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-3" custom={8} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="WORKFLOWS ACTIFS">
            <div className="space-y-2">
              {WORKFLOWS.map((w) => (
                <button
                  key={w}
                  type="button"
                  onClick={() => onNavigateTab("workflows")}
                  className="flex w-full items-center justify-between rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2 text-left hover:border-copper/40"
                >
                  <span className="text-[11px] text-ivoire/80">{w}</span>
                  <StatusBadge status="active">Actif</StatusBadge>
                </button>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-3" custom={9} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="AGENTS DIRECTION">
            <div className="space-y-2">
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
          </MockCard>
        </motion.div>
      </div>
    </div>
  );
}
