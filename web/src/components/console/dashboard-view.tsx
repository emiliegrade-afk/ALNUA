"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useConsoleData } from "./console-provider";
import { timezones, milestones, agentComm, activityHeatmapDays } from "@/lib/console/rich-data";
import { CONSOLE_ACTIVITY } from "@/lib/console/nav";
import { Widget, LiveDot } from "./widget";
import { SyncBadge } from "./sync-badge";
import { OrgNetwork } from "./org-network";
import { ActivityFeed } from "./activity-feed";
import { Sparkline, Bars, Gauge, Heatmap, CommGraph } from "./charts";
import { cn } from "@/lib/utils";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Banknote,
  Boxes,
  Calendar,
  CheckCircle2,
  Gauge as GaugeIcon,
  GitBranch,
  Globe2,
  Grid3x3,
  Network,
  Rocket,
  ShieldAlert,
  XCircle,
  Loader2,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const SEVERITY_META: Record<string, { icon: LucideIcon; color: string; bg: string; label: string }> = {
  info: { icon: CheckCircle2, color: "text-bronze-bright", bg: "bg-bronze/15", label: "Info" },
  warning: { icon: AlertTriangle, color: "text-glow", bg: "bg-glow/15", label: "Alerte" },
  critical: { icon: ShieldAlert, color: "text-red-400", bg: "bg-red-500/15", label: "Critique" },
};

const DEPLOY_META: Record<string, { icon: LucideIcon; color: string; label: string }> = {
  success: { icon: CheckCircle2, color: "text-bronze-bright", label: "Réussi" },
  running: { icon: Loader2, color: "text-glow", label: "En cours" },
  failed: { icon: XCircle, color: "text-red-400", label: "Échec" },
};

const DECISION_META: Record<string, { color: string; label: string; dot: string }> = {
  approved: { color: "text-bronze-bright", label: "Approuvée", dot: "bg-bronze-bright" },
  review: { color: "text-glow", label: "Revue", dot: "bg-glow" },
  pending: { color: "text-titane", label: "En attente", dot: "bg-titane" },
};

/** Hauteur fixe des rangées ops (org + live alignées). */
const OPS_ROW_H = "h-[28rem]";

export function DashboardView() {
  const router = useRouter();
  const {
    departments,
    globalKpis,
    systemMetrics,
    stats,
    activityFeed,
    activity24h,
    activityHeatmap,
    decisions7d,
    incidents,
    deployments,
    decisionsToday,
    activeAgents,
  } = useConsoleData();

  const decisionsTotal = decisions7d.reduce((n, d) => n + d.value, 0);
  const activityPeak = activity24h.length > 0 ? Math.max(...activity24h) : 0;

  const navigateToDept = (id: string) => {
    const pole = departments.find((d) => d.id === id);
    if (pole) router.push(pole.href);
  };

  return (
    <div className="grid grid-cols-12 gap-4">
      {/* ─── KPI strip ─── */}
      <div className="col-span-12 grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
        {globalKpis.map((k) => (
          <div
            key={k.label}
            className="rounded-xl border border-bronze-faint bg-obsidian/70 p-3.5 relative overflow-hidden group"
          >
            <div className="flex items-start justify-between gap-1 mb-2">
              <span className="text-[9px] uppercase tracking-[0.15em] text-titane/55 leading-tight">
                {k.label}
              </span>
              <span className="text-[9px] text-bronze-bright shrink-0">{k.delta}</span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-xl font-bold text-gradient-bronze">{k.value}</span>
              {k.unit && <span className="text-[10px] text-titane/50">{k.unit}</span>}
            </div>
            <div className="mt-2 -mb-1 opacity-70">
              <Sparkline data={k.trend} width={140} height={24} stroke="#B87333" />
            </div>
          </div>
        ))}
      </div>

      {/* ─── System health (gauges) ─── */}
      <Widget
        title="Santé système — temps réel"
        icon={GaugeIcon}
        span="lg:col-span-8"
        action={<SyncBadge className="text-[9px] text-titane/45" />}
        delay={0.05}
      >
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
          {Object.values(systemMetrics).map((m) => (
            <Gauge
              key={m.label}
              value={m.value}
              label={m.label}
              unit={m.unit}
              size={84}
              color={m.tone === "titanium" ? "#A7ADB5" : "#B87333"}
            />
          ))}
        </div>
        <div className="mt-4 pt-4 border-t border-bronze-faint">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] uppercase tracking-wide text-titane/55">Activité 24h — flux agents</span>
            <span className="text-[10px] text-bronze">
              {activityFeed.length} events · pic {activityPeak}
            </span>
          </div>
          <Sparkline data={activity24h} width={640} height={48} stroke="#B87333" className="w-full h-12" />
        </div>
      </Widget>

      {/* ─── World clocks ─── */}
      <Widget title="Horloges mondiales" icon={Globe2} span="lg:col-span-4" delay={0.08}>
        <WorldClocks />
        <div className="mt-4 pt-4 border-t border-bronze-faint grid grid-cols-2 gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-wide text-titane/55">Uptime cumulé</div>
            <div className="text-lg font-bold text-bronze-bright">99.98%</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wide text-titane/55">Disponibilité</div>
            <div className="text-lg font-bold text-ivoire">24/7/365</div>
          </div>
        </div>
      </Widget>

      {/* ─── Org + Activité live (même hauteur) ─── */}
      <div className={cn("col-span-12 grid grid-cols-12 gap-4 items-stretch", OPS_ROW_H)}>
        <Widget
          title="Carte organisationnelle"
          icon={Network}
          span="lg:col-span-8"
          fill
          action={
            <div className="flex items-center gap-2">
              <SyncBadge className="text-[9px] text-titane/45" />
              <LiveDot label="11 pôles" />
            </div>
          }
          delay={0.1}
          bodyClassName="!p-3 sm:!p-4 flex flex-1 min-h-0"
        >
          <div className="flex h-full min-h-0 flex-1 items-center justify-center bg-radial-glow/30">
            <OrgNetwork onSelect={navigateToDept} />
          </div>
        </Widget>

        <Widget
          title="Activité live"
          icon={Activity}
          span="lg:col-span-4"
          fill
          action={
            <div className="flex items-center gap-2">
              <SyncBadge className="text-[9px] text-titane/45" />
              <Link
                href={CONSOLE_ACTIVITY}
                className="inline-flex items-center gap-1 text-[10px] text-bronze hover:text-bronze-bright"
              >
                Tout voir <ArrowUpRight className="h-3 w-3" />
              </Link>
            </div>
          }
          delay={0.12}
          bodyClassName="!p-0 flex flex-1 min-h-0 flex-col"
        >
          <ActivityFeed compact className="flex h-full min-h-0 flex-1 flex-col" />
        </Widget>
      </div>

      {/* ─── État produit (pas de revenu fictif) ─── */}
      <Widget title="État produit" icon={Banknote} span="lg:col-span-4" delay={0.14}>
        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-2xl font-bold text-titane/70">—</span>
          <span className="text-xs text-titane/55">revenu · pré-lancement</span>
        </div>
        <p className="text-sm text-titane/65 leading-relaxed">
          Aucun revenu enregistré pour l&apos;instant. Les métriques financières
          apparaîtront ici une fois les premiers produits monétisés.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-3 border-t border-bronze-faint pt-4">
          <div>
            <p className="text-[10px] uppercase tracking-wide text-titane/50">Coût LLM / jour</p>
            <p className="text-lg font-bold text-gradient-bronze">
              ${stats.costTodayUsd.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wide text-titane/50">Agents actifs</p>
            <p className="text-lg font-bold text-ivoire">{activeAgents}</p>
          </div>
        </div>
      </Widget>

      {/* ─── Décisions 7j (données live) ─── */}
      <Widget title="Décisions — 7 jours" icon={GitBranch} span="lg:col-span-4" delay={0.16}>
        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-2xl font-bold text-gradient-bronze">{decisionsTotal}</span>
          <span className="text-xs text-titane/55">événements / sem.</span>
          <span className="text-[10px] text-titane/45 ml-auto">depuis flux live</span>
        </div>
        <Bars data={decisions7d} height={120} color="#b87333" />
      </Widget>

      {/* ─── Decisions pipeline today ─── */}
      <Widget
        title="Décisions du jour"
        icon={GitBranch}
        span="lg:col-span-4"
        action={<SyncBadge className="text-[9px] text-titane/45" />}
        delay={0.18}
      >
        <ul className="space-y-2">
          {decisionsToday.slice(0, 5).map((d) => {
            const meta = DECISION_META[d.status];
            return (
              <li key={d.id} className="flex items-center gap-2.5 rounded-lg bg-obsidian-deep/50 border border-bronze-faint px-3 py-2">
                <span className={cn("h-1.5 w-1.5 rounded-full shrink-0", meta.dot, d.status === "approved" && "animate-alnua-pulse")} />
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-ivoire/90 leading-snug truncate">{d.title}</p>
                  <p className="text-[10px] text-titane/50">
                    {d.agent} · {d.time}
                  </p>
                </div>
                <span className={cn("text-[9px] uppercase tracking-wide shrink-0", meta.color)}>{meta.label}</span>
              </li>
            );
          })}
        </ul>
      </Widget>

      {/* ─── Incidents · Déploiements · Charge (même hauteur) ─── */}
      <div className={cn("col-span-12 grid grid-cols-12 gap-4 items-stretch", OPS_ROW_H)}>
        <Widget
          title="Incidents & alertes"
          icon={AlertTriangle}
          span="lg:col-span-4"
          fill
          action={
            <div className="flex items-center gap-2">
              <SyncBadge className="text-[9px] text-titane/45" />
              <span className="text-[10px] text-titane/50">{incidents.length}</span>
            </div>
          }
          delay={0.2}
          bodyClassName="flex flex-1 min-h-0 flex-col"
        >
          <ul className="flex-1 space-y-2 overflow-y-auto alnua-scroll">
            {incidents.slice(0, 6).map((inc) => {
            const meta = SEVERITY_META[inc.severity];
            const Icon = meta.icon;
            return (
              <li key={inc.id} className="flex items-start gap-2.5 rounded-lg bg-obsidian-deep/50 border border-bronze-faint px-3 py-2">
                <div className={cn("flex h-6 w-6 items-center justify-center rounded shrink-0", meta.bg)}>
                  <Icon className={cn("h-3 w-3", meta.color, inc.severity === "critical" && "animate-alnua-pulse")} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-ivoire/90 leading-snug">{inc.title}</p>
                  <p className="text-[10px] text-titane/50">
                    {inc.pôle} · {inc.time}
                    {inc.resolved && <span className="text-bronze-bright ml-1">· résolu</span>}
                  </p>
                </div>
              </li>
            );
            })}
          </ul>
        </Widget>

        <Widget
          title="Déploiements récents"
          icon={Rocket}
          span="lg:col-span-4"
          fill
          action={
            <div className="flex items-center gap-2">
              <SyncBadge className="text-[9px] text-titane/45" />
              <LiveDot />
            </div>
          }
          delay={0.24}
          bodyClassName="!p-0 flex flex-1 min-h-0 flex-col"
        >
          <ul className="flex-1 divide-y divide-bronze-faint overflow-y-auto alnua-scroll">
            {deployments.map((dep) => {
              const meta = DEPLOY_META[dep.status];
              const Icon = meta.icon;
              return (
                <li key={dep.id} className="flex items-center gap-3 px-4 py-2.5">
                  <div className={cn("flex h-7 w-7 items-center justify-center rounded shrink-0", "bg-obsidian-deep border border-bronze-faint")}>
                    <Icon className={cn("h-3.5 w-3.5", meta.color, dep.status === "running" && "animate-spin")} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-ivoire font-medium truncate">
                      {dep.service} <span className="text-titane/50 font-normal">{dep.version}</span>
                    </p>
                    <p className="text-[10px] text-titane/50">{dep.by} · {dep.time}</p>
                  </div>
                  <span className={cn("text-[9px] uppercase tracking-wide shrink-0", meta.color)}>{meta.label}</span>
                </li>
              );
            })}
          </ul>
        </Widget>

        <Widget
          title="Charge par pôle"
          icon={Boxes}
          span="lg:col-span-4"
          fill
          action={
            <div className="flex items-center gap-2">
              <SyncBadge className="text-[9px] text-titane/45" />
              <LiveDot />
            </div>
          }
          delay={0.22}
          bodyClassName="flex flex-1 min-h-0 flex-col"
        >
          <div className="flex-1 space-y-2 overflow-y-auto alnua-scroll">
            {departments.map((d) => {
              const load = Math.round(d.agents.reduce((s, a) => s + a.utilization, 0) / Math.max(d.agents.length, 1));
              return (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => navigateToDept(d.id)}
                  className="flex w-full items-center gap-2.5 group"
                >
                  <span className="w-16 truncate text-left text-[10px] text-titane/70 transition-colors group-hover:text-bronze-bright">
                    {d.name.replace("Bureau ", "").replace("Pôle ", "")}
                  </span>
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-obsidian-deep">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${load}%`, background: `linear-gradient(90deg, ${d.glow}, ${d.glow}99)` }}
                    />
                  </div>
                  <span className="w-8 text-right text-[10px] tabular-nums text-titane/60">{load}%</span>
                </button>
              );
            })}
          </div>
        </Widget>
      </div>

      {/* ─── Activity heatmap ─── */}
      <Widget
        title="Densité d'activité — aujourd'hui, par heure"
        icon={Grid3x3}
        span="lg:col-span-8"
        delay={0.26}
      >
        <Heatmap data={activityHeatmap} days={activityHeatmapDays} color="#B87333" />
        <div className="mt-4 pt-3 border-t border-bronze-faint flex items-center justify-between">
          <span className="text-[10px] text-titane/55">Intensité</span>
          <div className="flex items-center gap-1">
            <span className="text-[9px] text-titane/45">faible</span>
            {[0.1, 0.3, 0.5, 0.7, 1].map((o) => (
              <span key={o} className="h-3 w-3 rounded-sm" style={{ background: "#B87333", opacity: o }} />
            ))}
            <span className="text-[9px] text-titane/45 ml-1">élevée</span>
          </div>
        </div>
      </Widget>

      {/* ─── Agent communication graph ─── */}
      <Widget
        title="Communications inter-agents"
        icon={Network}
        span="lg:col-span-4"
        action={<LiveDot />}
        delay={0.28}
      >
        <CommGraph edges={agentComm} size={300} className="w-full" />
        <p className="text-[10px] text-titane/50 text-center mt-2">
          {agentComm.length} flux actifs entre {new Set(agentComm.flatMap((e) => [e.from, e.to])).size} agents
        </p>
      </Widget>

      {/* ─── Milestones ─── */}
      <Widget
        title="Jalons à venir"
        icon={Calendar}
        span="lg:col-span-12"
        delay={0.3}
        bodyClassName="!p-0"
      >
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 divide-y md:divide-y-0 md:divide-x divide-bronze-faint">
          {milestones.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => {
                const pole = departments.find((x) =>
                  x.name.toLowerCase().includes(m.pôle.toLowerCase().slice(0, 4)),
                );
                if (pole) navigateToDept(pole.id);
              }}
              className="group text-left p-4 hover:bg-obsidian-deep/40 transition-colors"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-bronze/10 text-bronze text-[10px] font-bold">
                  J{m.days}
                </span>
                <span className="text-[9px] uppercase tracking-wide text-titane/50">{m.pôle}</span>
              </div>
              <p className="text-xs font-medium text-ivoire leading-snug mb-1 group-hover:text-bronze-bright transition-colors">
                {m.title}
              </p>
              <p className="text-[10px] text-titane/50">{m.date}</p>
            </button>
          ))}
        </div>
      </Widget>
    </div>
  );
}

// ─── World clocks (live) ────────────────────────────────────────────────────
function WorldClocks() {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    const tick = () => setNow(new Date());
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="grid grid-cols-2 gap-2.5">
      {timezones.map((tz) => {
        const time = now
          ? now.toLocaleTimeString("fr-FR", {
              timeZone: tz.tz,
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            })
          : "--:--:--";
        return (
          <div key={tz.city} className="rounded-lg bg-obsidian-deep/50 border border-bronze-faint px-3 py-2.5">
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-[11px] text-ivoire font-medium">{tz.city}</span>
              <span className="text-[9px] text-titane/45">{tz.code}</span>
            </div>
            <span
              className="text-sm font-mono tabular-nums text-bronze-bright"
              suppressHydrationWarning
            >
              {time}
            </span>
          </div>
        );
      })}
    </div>
  );
}
