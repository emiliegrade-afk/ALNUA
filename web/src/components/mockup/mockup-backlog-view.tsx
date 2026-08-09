"use client";

import type { ConsoleDepartment } from "@/lib/console/types";
import { MockCard, StatusBadge } from "./mockup-widgets";

interface MockupBacklogViewProps {
  department: ConsoleDepartment;
}

const COLUMNS = ["NOUVELLES", "À PRIORISER", "EN ATTENTE", "VALIDÉES", "PLANIFIÉES", "REJETÉES"];

const ITEMS = [
  { title: "Dark mode charts", col: 0, type: "Amélioration", author: "Théo" },
  { title: "Export PDF rapports", col: 0, type: "Fonctionnalité", author: "Inès" },
  { title: "WebSocket retries", col: 1, type: "Correction", author: "Hao" },
  { title: "API rate limiting", col: 2, type: "Recherche", author: "Alex" },
  { title: "Mobile offline mode", col: 3, type: "Fonctionnalité", author: "Rayan" },
  { title: "Legacy lobby cleanup", col: 4, type: "Dette", author: "Aria" },
  { title: "3D avatar system", col: 5, type: "Recherche", author: "Mira" },
];

const TYPE_STATUS: Record<string, "active" | "warning" | "neutral" | "success"> = {
  Amélioration: "active",
  Fonctionnalité: "success",
  Correction: "warning",
  Recherche: "neutral",
  Dette: "neutral",
};

export function MockupBacklogView({ department }: MockupBacklogViewProps) {
  const counts = COLUMNS.map((_, i) => ITEMS.filter((m) => m.col === i).length);
  const total = ITEMS.length;
  const distribution = [
    { label: "Fonctionnalité", value: 60 },
    { label: "Corrections", value: 25 },
    { label: "Recherche", value: 15 },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 md:grid-cols-7">
          {[
            { label: "Total", value: total },
            { label: "Agents", value: department.agents.length },
            { label: "Nouvelles", value: counts[0] },
            { label: "Priorisées", value: counts[1] },
            { label: "Validées", value: counts[3] },
            { label: "Planifiées", value: counts[4] },
            { label: "Rejetées", value: counts[5] },
          ].map((k) => (
          <div
            key={k.label}
            className="rounded-xl border border-bronze-faint bg-obsidian/60 p-3 text-center"
          >
            <p className="font-title text-xl font-semibold text-ivoire">{k.value}</p>
            <p className="text-[9px] uppercase tracking-wider text-titane/45">{k.label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-2">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            {COLUMNS.slice(0, 3).map((col, i) => (
              <div key={col} className="rounded-xl border border-bronze-faint bg-obsidian/40 p-2">
                <div className="mb-2 flex items-center justify-between px-2 py-1">
                  <p className="text-[10px] uppercase tracking-wider text-titane/55">{col}</p>
                  <span className="rounded-full bg-obsidian-2 px-1.5 py-0.5 text-[10px] text-titane/60">
                    {counts[i]}
                  </span>
                </div>
                <div className="space-y-2">
                  {ITEMS.filter((m) => m.col === i).map((m, idx) => (
                    <div key={idx} className="rounded-lg border border-bronze-faint bg-obsidian/60 p-2.5">
                      <p className="text-[12px] font-medium text-ivoire/90">{m.title}</p>
                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-[10px] text-titane/50">{m.author}</span>
                        <StatusBadge status={TYPE_STATUS[m.type]}>{m.type}</StatusBadge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            {COLUMNS.slice(3).map((col, i) => (
              <div key={col} className="rounded-xl border border-bronze-faint bg-obsidian/40 p-2">
                <div className="mb-2 flex items-center justify-between px-2 py-1">
                  <p className="text-[10px] uppercase tracking-wider text-titane/55">{col}</p>
                  <span className="rounded-full bg-obsidian-2 px-1.5 py-0.5 text-[10px] text-titane/60">
                    {counts[i + 3]}
                  </span>
                </div>
                <div className="space-y-2">
                  {ITEMS.filter((m) => m.col === i + 3).map((m, idx) => (
                    <div key={idx} className="rounded-lg border border-bronze-faint bg-obsidian/60 p-2.5">
                      <p className="text-[12px] font-medium text-ivoire/90">{m.title}</p>
                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-[10px] text-titane/50">{m.author}</span>
                        <StatusBadge status={TYPE_STATUS[m.type]}>{m.type}</StatusBadge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <MockCard title="Répartition par type">
            <div className="flex items-center justify-center py-2">
              <div className="relative h-28 w-28">
                <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
                  {distribution.reduce(
                    (acc, seg, i) => {
                      const dash = (seg.value / 100) * 251.2;
                      const el = (
                        <circle
                          key={i}
                          cx="50"
                          cy="50"
                          r="40"
                          fill="none"
                          stroke={["#C08A72", "#D9A88F", "#8A6050"][i]}
                          strokeWidth="12"
                          strokeDasharray={`${dash} 251.2`}
                          strokeDashoffset={-acc.offset}
                        />
                      );
                      acc.offset += dash;
                      acc.nodes.push(el);
                      return acc;
                    },
                    { offset: 0, nodes: [] as React.ReactNode[] },
                  ).nodes}
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <p className="font-title text-lg font-semibold text-ivoire">{total}</p>
                  <p className="text-[9px] text-titane/50">items</p>
                </div>
              </div>
            </div>
            <div className="mt-2 space-y-1">
              {distribution.map((d, i) => (
                <div key={d.label} className="flex items-center justify-between text-[11px]">
                  <span className="flex items-center gap-1.5 text-titane/65">
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ background: ["#C08A72", "#D9A88F", "#8A6050"][i] }}
                    />
                    {d.label}
                  </span>
                  <span className="text-ivoire/80">{d.value}%</span>
                </div>
              ))}
            </div>
          </MockCard>
        </div>
      </div>
    </div>
  );
}
