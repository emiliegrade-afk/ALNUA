"use client";

import { ArrowUpRight, BarChart3, TrendingUp } from "lucide-react";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { ConsoleDepartment } from "@/lib/console/types";
import { KpiCard, MockCard, ProgressBar } from "./mockup-widgets";

interface MockupOverviewProps {
  department: ConsoleDepartment;
}

export function MockupOverview({ department }: MockupOverviewProps) {
  const kpis = department.kpis;
  const agents = department.agents.slice(0, 4);
  const projects = department.projects;

  const spark1 = [45, 52, 48, 60, 55, 68, 72, 66, 75, 80];
  const spark2 = [30, 35, 42, 38, 45, 50, 48, 55, 60, 58];

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <div className="space-y-4 xl:col-span-2">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {kpis.slice(0, 3).map((k, i) => (
            <KpiCard
              key={i}
              label={k.label}
              value={k.value}
              delta={i === 0 ? "+12%" : undefined}
              deltaType={i === 0 ? "positive" : "neutral"}
              sparkline={i === 0 ? spark1 : i === 1 ? spark2 : undefined}
            />
          ))}
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <MockCard title="Performance" action={<TrendingUp className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="space-y-4">
              <div className="flex items-end justify-between">
                <span className="font-title text-2xl font-semibold text-ivoire">86%</span>
                <span className="text-[11px] text-online">+4.2%</span>
              </div>
              <LineChart data={[62, 68, 65, 72, 74, 78, 82, 80, 84, 86]} />
              <div className="grid grid-cols-3 gap-2 text-center">
                <Metric label="Min" value="62%" />
                <Metric label="Moy" value="76%" />
                <Metric label="Max" value="86%" />
              </div>
            </div>
          </MockCard>

          <MockCard title="Répartition" action={<BarChart3 className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="flex items-center justify-center py-2">
              <DonutChart segments={[42, 28, 18, 12]} labels={["A", "B", "C", "D"]} />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <Metric label="Segment A" value="42%" />
              <Metric label="Segment B" value="28%" />
              <Metric label="Segment C" value="18%" />
              <Metric label="Segment D" value="12%" />
            </div>
          </MockCard>
        </div>

        <MockCard title="Agents actifs" action={<ArrowUpRight className="h-3.5 w-3.5 text-copper/70" />}>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="flex items-center gap-3 rounded-lg border border-bronze-faint bg-obsidian/50 p-3"
              >
                <AgentAvatar agentId={agent.id} name={agent.name} size={36} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[12px] font-medium text-ivoire">{agent.name}</p>
                  <p className="truncate text-[10px] text-titane/55">{agent.role}</p>
                </div>
                <div className="text-right">
                  <p className="font-title text-sm font-semibold text-copper">{agent.utilization}%</p>
                  <p className="text-[9px] text-titane/50">Charge</p>
                </div>
              </div>
            ))}
          </div>
        </MockCard>
      </div>

      <div className="space-y-4">
        <MockCard title="Jalons">
          <div className="space-y-3">
            {projects.map((p, i) => (
              <div key={i} className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-ivoire/80">{p.name}</span>
                  <span className="text-copper">{p.progress}%</span>
                </div>
                <ProgressBar value={p.progress} />
              </div>
            ))}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-ivoire/80">Livraison globale</span>
                <span className="text-copper">68%</span>
              </div>
              <ProgressBar value={68} />
            </div>
          </div>
        </MockCard>

        <MockCard title="Capteurs">
          <div className="space-y-2">
            <Sensor label="GPU cluster" value="81%" />
            <Sensor label="Expériences actives" value={department.agents.length.toString()} />
            <Sensor label="Précision modèle" value="94.2%" />
            <Sensor label="Latence API" value="120ms" />
          </div>
        </MockCard>

        <MockCard title="Compétences clés">
          <div className="space-y-3">
            {departmentSkills(department.id).map((skill) => (
              <div key={skill.label} className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-titane/70">{skill.label}</span>
                  <span className="text-ivoire/80">{skill.value}%</span>
                </div>
                <ProgressBar value={skill.value} />
              </div>
            ))}
          </div>
        </MockCard>
      </div>
    </div>
  );
}

function Sensor({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2">
      <span className="text-[11px] text-titane/70">{label}</span>
      <span className="font-title text-xs font-semibold text-copper">{value}</span>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-bronze-faint bg-obsidian/50 p-2 text-center">
      <p className="font-title text-sm font-semibold text-ivoire">{value}</p>
      <p className="text-[9px] uppercase tracking-wider text-titane/45">{label}</p>
    </div>
  );
}

function LineChart({ data }: { data: number[] }) {
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
          <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#C08A72" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#C08A72" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={`0,100 ${points} 100,100`} fill="url(#lineGrad)" />
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

function DonutChart({ segments, labels }: { segments: number[]; labels: string[] }) {
  const total = segments.reduce((a, b) => a + b, 0);
  let offset = 0;

  return (
    <div className="relative h-32 w-32">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
        {segments.map((seg, i) => {
          const dash = (seg / total) * 251.2;
          const el = (
            <circle
              key={i}
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke={["#C08A72", "#D9A88F", "#8A6050", "#A7ADB5"][i]}
              strokeWidth="12"
              strokeDasharray={`${dash} 251.2`}
              strokeDashoffset={-offset}
            />
          );
          offset += dash;
          return el;
        })}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <p className="font-title text-lg font-semibold text-ivoire">{total}%</p>
      </div>
      <div className="absolute -bottom-4 left-0 right-0 flex justify-center gap-2">
        {labels.map((l, i) => (
          <span
            key={l}
            className="text-[9px] font-medium"
            style={{ color: ["#C08A72", "#D9A88F", "#8A6050", "#A7ADB5"][i] }}
          >
            {l}
          </span>
        ))}
      </div>
    </div>
  );
}

function departmentSkills(id: string): { label: string; value: number }[] {
  switch (id) {
    case "rd":
      return [
        { label: "Recherche fondamentale", value: 93 },
        { label: "Prototypage", value: 88 },
        { label: "Éthique & alignement", value: 91 },
        { label: "Multimodal", value: 85 },
      ];
    case "app":
      return [
        { label: "Full-stack", value: 92 },
        { label: "Mobile", value: 86 },
        { label: "DevOps", value: 80 },
        { label: "UX", value: 84 },
      ];
    case "marketing":
      return [
        { label: "Content", value: 90 },
        { label: "SEO", value: 82 },
        { label: "Paid Ads", value: 78 },
        { label: "Social", value: 88 },
      ];
    case "finances":
      return [
        { label: "Comptabilité", value: 94 },
        { label: "Forecast", value: 86 },
        { label: "Reporting", value: 90 },
        { label: "Conformité", value: 88 },
      ];
    case "gaming":
      return [
        { label: "Gameplay", value: 89 },
        { label: "Level Design", value: 85 },
        { label: "Narrative", value: 82 },
        { label: "Tech Art", value: 80 },
      ];
    case "robo":
      return [
        { label: "Hardware", value: 88 },
        { label: "Firmware", value: 86 },
        { label: "Vision", value: 84 },
        { label: "Safety", value: 90 },
      ];
    default:
      return [
        { label: "Stratégie", value: 88 },
        { label: "Exécution", value: 84 },
        { label: "Analyse", value: 86 },
        { label: "Communication", value: 82 },
      ];
  }
}
