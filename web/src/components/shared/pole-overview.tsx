"use client";

import { useMemo } from "react";
import {
  Activity,
  CircleDot,
  Clock,
} from "lucide-react";
import {
  getAgentsForBureau,
  type BureauKey,
} from "@/lib/agent-bureau";
import { CONSOLE_POLES } from "@/lib/console/departments";
import { useConsoleData } from "@/components/console/console-provider";
import { Donut, LevelBar, Sparkline } from "@/components/console/charts";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { DeptKey } from "@/lib/dept-colors";
import { cn } from "@/lib/utils";

interface PoleMetric { label: string; value: string; delta?: string }
interface PoleBudget { allocated: number; spent: number; unit: string }
interface PoleCapteur { label: string; value: string; hint?: string }
interface PoleSkill { label: string; value: number }
interface PoleMilestone { label: string; date: string }

interface PoleOverviewConfig {
  metrics: PoleMetric[];
  budget: PoleBudget;
  performance: number[];
  performanceMeta?: { min: number; avg: number; max: number };
  capteurs: PoleCapteur[];
  skills: PoleSkill[];
  milestones: PoleMilestone[];
}

const POLE_OVERVIEW_CONFIG: Partial<Record<BureauKey, PoleOverviewConfig>> = {
  rd: {
    metrics: [
      { label: "Expériences actives", value: "27", delta: "+3" },
      { label: "Papers / mois", value: "6", delta: "+1" },
      { label: "Prototypes", value: "14", delta: "+2" },
    ],
    budget: { allocated: 1260, spent: 718, unit: "k€" },
    performance: [82, 84, 83, 86, 85, 87, 88, 89],
    performanceMeta: { min: 82, avg: 86, max: 89 },
    capteurs: [
      { label: "GPU cluster", value: "81%", hint: "6 nœuds" },
      { label: "Expériences actives", value: "27" },
      { label: "Précision modèle", value: "94.2%" },
    ],
    skills: [
      { label: "Recherche fondamentale", value: 93 },
      { label: "Prototypage", value: 88 },
      { label: "Éthique & alignement", value: 91 },
      { label: "Multimodal", value: 85 },
    ],
    milestones: [
      { label: "POC NOMAD embarqué", date: "15 août" },
      { label: "Audit multi-modal EVE", date: "28 août" },
    ],
  },
};

const CARD = "rounded-xl border border-bronze-faint bg-obsidian/60 p-4 sm:p-5";
const CARD_TITLE = "text-[10px] uppercase tracking-[0.18em] text-titane/55";

function findPole(bureau: BureauKey) {
  return CONSOLE_POLES.find((p) => p.bureau === bureau);
}

function statusLabel(kind: string | undefined): { label: string; tone: string } {
  switch (kind) {
    case "working": return { label: "Actif", tone: "text-emerald-300" };
    case "waiting": return { label: "Réflexion", tone: "text-bronze-bright" };
    case "idle": return { label: "Veille", tone: "text-titane/55" };
    default: return { label: "Hors ligne", tone: "text-titane/40" };
  }
}

function Row({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-titane/55">{label}</span>
      <span className={cn("font-mono tabular-nums text-ivoire", tone)}>{value}</span>
    </div>
  );
}

interface PoleOverviewProps {
  bureau: BureauKey;
  dept: DeptKey;
  className?: string;
}

export function PoleOverview({ bureau, dept, className }: PoleOverviewProps) {
  const { liveAgents, activityFeed, activeAgents, totalAgents } = useConsoleData();
  const cfg = POLE_OVERVIEW_CONFIG[bureau];
  const pole = findPole(bureau);
  const agents = useMemo(() => getAgentsForBureau(bureau), [bureau]);

  if (!pole || !cfg) {
    return (
      <div className={cn(CARD, "text-sm text-titane/60", className)}>
        Vue d&apos;ensemble non configurée pour ce pôle.
      </div>
    );
  }

  const PoleIcon = pole.icon;
  const budgetRemaining = cfg.budget.allocated - cfg.budget.spent;
  const budgetPct = Math.round((cfg.budget.spent / cfg.budget.allocated) * 100);
  const poleActivity = activityFeed
    .filter((a) => a.dept === dept)
    .slice(0, 6);

  return (
    <div className={cn("space-y-4", className)}>
      {/* Hero */}
      <section className={cn(CARD, "relative overflow-hidden")}>
        <div className="pointer-events-none absolute -right-12 -top-12 opacity-[0.07]">
          <PoleIcon className="h-44 w-44 text-copper" />
        </div>
        <div className="relative flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-titane/55">
              <span className="font-mono text-copper/70">{pole.code}</span>
              <span>Pôle</span>
            </div>
            <h2 className="mt-1 font-title text-2xl font-semibold text-ivoire">
              {pole.name.replace("Bureau ", "").replace("Pôle ", "")}
            </h2>
            <p className="mt-1 text-sm text-titane/65">{pole.tagline}</p>
            <p className="mt-3 max-w-xl text-xs leading-relaxed text-titane/55">
              {pole.description}
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 lg:gap-4">
            {cfg.metrics.map((m) => (
              <div key={m.label} className="rounded-lg border border-bronze-faint bg-obsidian-deep/60 px-3 py-2.5">
                <p className="text-[9px] uppercase tracking-wide text-titane/50">{m.label}</p>
                <p className="mt-1 font-title text-xl font-semibold text-ivoire tabular-nums">{m.value}</p>
                {m.delta ? <p className="mt-0.5 text-[10px] text-emerald-300/80">{m.delta}</p> : null}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Budget · Performance · Capteurs */}
      <section className="grid gap-4 lg:grid-cols-3">
        <div className={CARD}>
          <p className={CARD_TITLE}>Budget pôle</p>
          <div className="mt-3 flex items-center gap-4">
            <Donut
              segments={[
                { value: cfg.budget.spent, color: "#E09B6A" },
                { value: budgetRemaining, color: "#2a2a30" },
              ]}
              size={104}
              thickness={10}
              centerValue={`${budgetPct}%`}
              centerLabel="utilisé"
            />
            <div className="flex-1 space-y-1.5 text-xs">
              <Row label="Alloué" value={`${cfg.budget.allocated} ${cfg.budget.unit}`} />
              <Row label="Dépensé" value={`${cfg.budget.spent} ${cfg.budget.unit}`} tone="text-copper" />
              <Row label="Restant" value={`${budgetRemaining} ${cfg.budget.unit}`} />
            </div>
          </div>
        </div>

        <div className={CARD}>
          <p className={CARD_TITLE}>Performance · 8 semaines</p>
          <div className="mt-3">
            <Sparkline data={cfg.performance} width={260} height={64} stroke="#E09B6A" idSeed={`pole-${bureau}-perf`} />
            <div className="mt-2 flex justify-between text-[10px] text-titane/50">
              <span>Min {cfg.performanceMeta?.min ?? ""}</span>
              <span>Moy {cfg.performanceMeta?.avg ?? ""}</span>
              <span>Max {cfg.performanceMeta?.max ?? ""}</span>
            </div>
          </div>
        </div>

        <div className={CARD}>
          <p className={CARD_TITLE}>Capteurs · temps réel</p>
          <ul className="mt-3 space-y-2.5">
            {cfg.capteurs.map((c) => (
              <li key={c.label} className="flex items-center gap-2.5 text-xs">
                <CircleDot className="h-3.5 w-3.5 shrink-0 text-copper/70" />
                <span className="flex-1 text-titane/70">{c.label}</span>
                <span className="font-mono tabular-nums text-ivoire">{c.value}</span>
                {c.hint ? <span className="text-[10px] text-titane/40">{c.hint}</span> : null}
              </li>
            ))}
            <li className="flex items-center gap-2.5 border-t border-bronze-faint pt-2.5 text-xs">
              <Activity className="h-3.5 w-3.5 shrink-0 text-copper/70" />
              <span className="flex-1 text-titane/70">Agents actifs</span>
              <span className="font-mono tabular-nums text-ivoire">{activeAgents}/{totalAgents}</span>
            </li>
          </ul>
        </div>
      </section>

      {/* Compétences · Jalons */}
      <section className="grid gap-4 lg:grid-cols-3">
        <div className={cn(CARD, "lg:col-span-2")}>
          <p className={CARD_TITLE}>Matrice de compétences</p>
          <div className="mt-4 grid gap-x-8 gap-y-3 sm:grid-cols-2">
            {cfg.skills.map((s) => (
              <div key={s.label}>
                <div className="mb-1.5 flex items-center justify-between text-xs">
                  <span className="text-titane/70">{s.label}</span>
                  <span className="font-mono tabular-nums text-ivoire">{s.value}</span>
                </div>
                <LevelBar value={s.value} />
              </div>
            ))}
          </div>
        </div>

        <div className={CARD}>
          <p className={CARD_TITLE}>Jalons du pôle</p>
          <ul className="mt-3 space-y-3">
            {cfg.milestones.map((ms) => (
              <li key={ms.label} className="flex items-start gap-3">
                <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-copper shadow-glow" />
                <div className="min-w-0">
                  <p className="text-xs text-ivoire">{ms.label}</p>
                  <p className="mt-0.5 flex items-center gap-1 text-[10px] text-titane/55">
                    <Clock className="h-3 w-3" />{ms.date}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Métriques détaillées des agents — table */}
      <section className={CARD}>
        <p className={CARD_TITLE}>Métriques détaillées des agents</p>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-xs">
            <thead>
              <tr className="border-b border-bronze-faint text-[10px] uppercase tracking-wide text-titane/50">
                <th className="py-2 pr-3 font-medium">Agent</th>
                <th className="py-2 pr-3 font-medium">Rôle</th>
                <th className="py-2 pr-3 font-medium">Statut</th>
                <th className="py-2 pr-3 text-right font-medium">Tâches</th>
                <th className="py-2 pr-3 text-right font-medium">Réponse moy.</th>
                <th className="py-2 pr-3 text-right font-medium">Précision</th>
                <th className="py-2 pr-3 font-medium">Charge</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((a) => {
                const live = liveAgents[a.id];
                const st = statusLabel(live?.status);
                const load = live?.progress ?? 0;
                return (
                  <tr key={a.id} className="border-b border-bronze-faint/60 last:border-0">
                    <td className="py-2.5 pr-3">
                      <div className="flex items-center gap-2.5">
                        <AgentAvatar agentId={a.id} name={a.name} size={26} />
                        <span className="font-medium text-ivoire">{a.name}</span>
                      </div>
                    </td>
                    <td className="py-2.5 pr-3 text-titane/65">{a.role}</td>
                    <td className="py-2.5 pr-3">
                      <span className="inline-flex items-center gap-1.5">
                        <span className={cn("h-1.5 w-1.5 rounded-full", live?.status === "working" ? "bg-emerald-400" : live?.status === "waiting" ? "bg-copper" : "bg-titane/30")} />
                        <span className={st.tone}>{st.label}</span>
                      </span>
                    </td>
                    <td className="py-2.5 pr-3 text-right font-mono tabular-nums text-titane/70">—</td>
                    <td className="py-2.5 pr-3 text-right font-mono tabular-nums text-titane/70">—</td>
                    <td className="py-2.5 pr-3 text-right font-mono tabular-nums text-titane/70">—</td>
                    <td className="py-2.5 pr-3 w-28">
                      <LevelBar value={load} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Cartes profil agents + activité du pôle */}
      <section className="grid gap-4 lg:grid-cols-3">
        <div className={cn(CARD, "lg:col-span-2")}>
          <p className={CARD_TITLE}>Agents du pôle</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {agents.map((a) => {
              const live = liveAgents[a.id];
              const st = statusLabel(live?.status);
              const load = live?.progress ?? 0;
              return (
                <div key={a.id} className="rounded-lg border border-bronze-faint bg-obsidian-deep/50 p-3.5">
                  <div className="flex items-center gap-3">
                    <AgentAvatar agentId={a.id} name={a.name} size={36} ring />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-ivoire">{a.name}</p>
                      <p className="truncate text-[11px] text-titane/55">{a.role}</p>
                    </div>
                    <span className={cn("rounded-full border px-2 py-0.5 text-[9px] uppercase tracking-wide", live?.status === "working" ? "border-emerald-500/40 text-emerald-300" : "border-bronze-faint text-titane/60")}>
                      {st.label}
                    </span>
                  </div>
                  <p className="mt-3 text-[10px] uppercase tracking-wide text-titane/45">Tâche courante</p>
                  <p className="mt-1 text-xs leading-relaxed text-titane/75">
                    {live?.currentTask ?? a.description}
                  </p>
                  <div className="mt-3 flex items-center justify-between text-[10px] text-titane/50">
                    <span>{a.skills.join(" · ")}</span>
                    <span className="font-mono tabular-nums">{load}%</span>
                  </div>
                  <div className="mt-1.5">
                    <LevelBar value={load} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className={CARD}>
          <p className={CARD_TITLE}>Activité du pôle</p>
          <ul className="mt-3 space-y-3">
            {poleActivity.length === 0 ? (
              <li className="text-xs text-titane/45">Aucune activité récente.</li>
            ) : (
              poleActivity.map((a, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-copper/60" />
                  <div className="min-w-0">
                    <p className="text-xs leading-snug text-titane/80">{a.action}</p>
                    {a.time ? (
                      <p className="mt-0.5 text-[10px] text-titane/45">{a.time}</p>
                    ) : null}
                  </div>
                </li>
              ))
            )}
          </ul>
        </div>
      </section>
    </div>
  );
}
