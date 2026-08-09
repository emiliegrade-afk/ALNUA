"use client";

import { Activity, CheckCircle, Shield, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { useConsoleData } from "@/components/console/console-provider";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { MockCard, KpiCard } from "../mockup-widgets";

const WORLD_CLOCKS = [
  { city: "Paris", offset: 0 },
  { city: "New York", offset: -6 },
  { city: "Tokyo", offset: 7 },
  { city: "Dubai", offset: 2 },
];

const DEPARTMENT_PERFS = [
  { name: "Gaming", value: 78 },
  { name: "Robotique", value: 75 },
  { name: "Marketing", value: 82 },
  { name: "APP", value: 88 },
  { name: "R&D", value: 91 },
  { name: "Comptabilité", value: 85 },
];

const ALERTS = [
  { icon: Shield, text: "Tentative d&apos;intrusion neutralisée", time: "à l&apos;instant" },
  { icon: CheckCircle, text: "Sauvegarde Q2 terminée", time: "il y a 3 min" },
  { icon: Zap, text: "GPU cluster à 81%", time: "il y a 7 min" },
  { icon: Activity, text: "Latence Edge < 12ms", time: "il y a 12 min" },
];

const MILESTONES = [
  { label: "Lancement teaser NAÏA", date: "15 août" },
  { label: "POC NOMAD embarqué", date: "28 août" },
  { label: "Release Wyrdheim α", date: "5 septembre" },
  { label: "Audit EVE sécurité", date: "18 septembre" },
];

const HEATMAP_VALUES = [
  0, 0, 1, 2, 2, 1, 0, 0, 0, 1, 2, 2, 2, 1, 0, 0, 1, 1, 2, 2, 1, 0, 0, 0,
  0, 1, 1, 2, 2, 2, 1, 0, 0, 0, 1, 2, 2, 2, 1, 0, 0, 1, 2, 2, 1, 0, 0, 0,
  0, 0, 1, 2, 2, 1, 1, 0, 0, 1, 2, 2, 2, 1, 0, 0, 0, 1, 2, 2, 1, 0, 0, 0,
  0, 1, 1, 2, 2, 2, 1, 0, 0, 0, 1, 2, 2, 1, 0, 0, 1, 2, 2, 1, 0, 0, 0, 0,
  0, 0, 1, 2, 2, 1, 0, 0, 0, 1, 2, 2, 2, 1, 0, 0, 0, 1, 2, 1, 0, 0, 0, 0,
  0, 0, 0, 1, 1, 2, 1, 0, 0, 0, 1, 2, 2, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0,
  0, 0, 0, 1, 2, 2, 1, 0, 0, 0, 1, 2, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0,
];

export function MockupDashboardView() {
  const { activityFeed, globalKpis, activeAgents } = useConsoleData();

  const kpis = globalKpis ?? [
    { label: "Agents actifs", value: String(activeAgents), delta: "+12%", trend: [45, 52, 48, 60, 55, 68] },
    { label: "Projets en cours", value: "38", delta: "+5%", trend: [30, 32, 35, 34, 38, 40] },
    { label: "Décisions / Jour", value: "184", delta: "+8%", trend: [120, 135, 150, 162, 175, 184] },
    { label: "Revenu mensuel", value: "472 k€", delta: "+18%", trend: [380, 410, 425, 440, 460, 472] },
    { label: "Uptime infra", value: "99.98%", delta: "stable", trend: [99.9, 99.95, 99.97, 99.98, 99.98, 99.99] },
    { label: "Satisfaction", value: "9.4/10", delta: "+0.2", trend: [8.8, 8.9, 9.0, 9.1, 9.3, 9.4] },
  ];

  const gauges = [
    { label: "CPU", value: 47 },
    { label: "Mémoire", value: 63 },
    { label: "Réseau", value: 28, suffix: "Gb/s" },
    { label: "Latence Edge", value: 12, suffix: "ms" },
    { label: "GPU Cluster", value: 81 },
    { label: "Stockage", value: 38 },
  ];

  return (
    <div className="space-y-4 pb-20">
      <header>
        <p className="text-[9px] uppercase tracking-[0.2em] text-titane/50">ALNUA / Vue d&apos;ensemble</p>
        <h1 className="font-title text-xl font-semibold tracking-wide text-ivoire sm:text-2xl">
          Console opérationnelle
        </h1>
      </header>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {kpis.map((k, i) => (
          <KpiCard key={i} label={k.label} value={k.value} delta={k.delta} sparkline={k.trend} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <MockCard title="Santé système — Temps réel">
            <div className="grid grid-cols-3 gap-4 sm:grid-cols-6">
              {gauges.map((g) => (
                <div key={g.label} className="flex flex-col items-center">
                  <div className="relative h-16 w-16">
                    <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="40" fill="none" stroke="#1A1E24" strokeWidth="10" />
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        fill="none"
                        stroke="#C08A72"
                        strokeWidth="10"
                        strokeDasharray={`${(g.value / 100) * 251.2} 251.2`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <p className="font-title text-sm font-semibold text-ivoire">
                        {g.value}
                        {g.suffix ? <span className="text-[9px]">{g.suffix}</span> : null}
                      </p>
                    </div>
                  </div>
                  <p className="mt-1 text-[9px] uppercase tracking-wider text-titane/50">{g.label}</p>
                </div>
              ))}
            </div>
            <div className="mt-4">
              <p className="mb-2 text-[10px] uppercase tracking-wider text-titane/50">Activité 24h — Agents actifs</p>
              <AreaChart data={[30, 45, 38, 52, 48, 60, 55, 68, 72, 66, 75, 80]} />
            </div>
          </MockCard>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <MockCard title="Alertes & logs">
              <div className="space-y-3">
                {ALERTS.map((a, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <a.icon className="mt-0.5 h-4 w-4 text-copper" />
                    <div className="min-w-0 flex-1">
                      <p className="text-[11px] text-ivoire/80">{a.text}</p>
                      <p className="text-[10px] text-titane/50">{a.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </MockCard>

            <MockCard title="Performance par département">
              <div className="space-y-3">
                {DEPARTMENT_PERFS.map((d) => (
                  <div key={d.name} className="space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-ivoire/80">{d.name}</span>
                      <span className="text-copper">{d.value}%</span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-obsidian-2">
                      <div className="h-full rounded-full bg-copper" style={{ width: `${d.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </MockCard>
          </div>

          <MockCard title="Densité d&apos;activité — 7 jours x 24h">
            <div className="grid grid-cols-7 gap-0.5">
              {HEATMAP_VALUES.map((intensity, i) => (
                <div
                  key={i}
                  className={cn(
                    "h-2 rounded-sm",
                    intensity === 2 ? "bg-copper/60" : intensity === 1 ? "bg-copper/30" : "bg-obsidian-2",
                  )}
                />
              ))}
            </div>
            <div className="mt-2 flex justify-between text-[9px] text-titane/40">
              <span>Lun</span>
              <span>Mar</span>
              <span>Mer</span>
              <span>Jeu</span>
              <span>Ven</span>
              <span>Sam</span>
              <span>Dim</span>
            </div>
          </MockCard>
        </div>

        <div className="space-y-4">
          <MockCard title="Horloges mondiales">
            <div className="grid grid-cols-2 gap-2">
              {WORLD_CLOCKS.map((c) => (
                <div key={c.city} className="rounded-lg border border-bronze-faint bg-obsidian/50 p-2 text-center">
                  <p className="text-[10px] text-titane/50">{c.city}</p>
                  <p className="font-title text-sm font-semibold text-ivoire">
                    {new Date(Date.now() + c.offset * 3600000).toLocaleTimeString("fr-FR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              ))}
            </div>
            <div className="mt-3 space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-titane/65">Uptime cumulé</span>
                <span className="text-online">99.98%</span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-titane/65">Disponibilité</span>
                <span className="text-ivoire/80">24/7/365</span>
              </div>
            </div>
          </MockCard>

          <MockCard title="Carte organisationnelle">
            <div className="relative flex h-48 items-center justify-center">
              <div className="absolute inset-0 rounded-full border border-dashed border-bronze-faint" />
              <div className="absolute inset-6 rounded-full border border-dashed border-bronze-faint/50" />
              <div className="relative z-10 flex h-14 w-14 items-center justify-center rounded-full bg-obsidian-2">
                <AlnuaStar className="h-7 w-7 text-copper" />
              </div>
              {["CEO", "R&D", "APP", "Marketing", "Gaming", "Robotique"].map((d, i) => {
                const angle = (i * 60 * Math.PI) / 180;
                const x = 50 + 38 * Math.cos(angle);
                const y = 50 + 38 * Math.sin(angle);
                return (
                  <div
                    key={d}
                    className="absolute flex h-8 w-8 items-center justify-center rounded-full border border-copper/30 bg-obsidian text-[8px] text-copper"
                    style={{ left: `${x}%`, top: `${y}%`, transform: "translate(-50%, -50%)" }}
                  >
                    {d.slice(0, 2)}
                  </div>
                );
              })}
            </div>
          </MockCard>

          <MockCard title="Activité live">
            <div className="space-y-3">
              {activityFeed.slice(0, 5).map((item, i) => (
                <div key={i} className="flex gap-2.5">
                  <div className="mt-0.5">
                    <AgentAvatar agentId={item.agent.toLowerCase().replace(/\s+/g, "-")} name={item.agent} size={22} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-[11px] text-ivoire/90">
                      <span className="font-medium text-copper">{item.agent}</span> {item.action}
                    </p>
                    <p className="text-[10px] text-titane/50">{item.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </MockCard>

          <MockCard title="Jalons à venir">
            <div className="space-y-2">
              {MILESTONES.map((m) => (
                <div key={m.label} className="flex items-center justify-between rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2">
                  <span className="text-[11px] text-ivoire/80">{m.label}</span>
                  <span className="text-[10px] text-copper">{m.date}</span>
                </div>
              ))}
            </div>
          </MockCard>
        </div>
      </div>
    </div>
  );
}

function AreaChart({ data }: { data: number[] }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * 100;
      const y = 100 - ((v - min) / range) * 80 - 10;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="relative h-24 w-full">
      <svg className="h-full w-full overflow-visible" preserveAspectRatio="none">
        <defs>
          <linearGradient id="dashGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#C08A72" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#C08A72" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={`0,100 ${points} 100,100`} fill="url(#dashGrad)" />
        <polyline
          points={points}
          fill="none"
          stroke="#C08A72"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    </div>
  );
}
