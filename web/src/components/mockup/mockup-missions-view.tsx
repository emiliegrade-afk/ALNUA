"use client";

import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { ConsoleDepartment } from "@/lib/console/types";
import { MockCard, ProgressBar, StatusBadge } from "./mockup-widgets";

interface MockupMissionsViewProps {
  department: ConsoleDepartment;
}

const COLUMNS = ["À FAIRE", "EN COURS", "EN ATTENTE", "EN TEST", "TERMINÉES"];

function idForName(name: string): string {
  return name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
}

const MISSIONS = [
  { title: "Module auth SSO", col: 1, progress: 45, assignee: "Théo Laurent", priority: "Haute" },
  { title: "Landing page v3", col: 0, progress: 0, assignee: "Inès Moreau", priority: "Moyenne" },
  { title: "Pipeline CI/CD", col: 2, progress: 70, assignee: "Hao Chen", priority: "Haute" },
  { title: "Tests E2E", col: 3, progress: 90, assignee: "Alex Okafor", priority: "Moyenne" },
  { title: "Refactor stores", col: 4, progress: 100, assignee: "Rayan Kone", priority: "Basse" },
  { title: "API marketing", col: 1, progress: 30, assignee: "Léo Morel", priority: "Moyenne" },
];

const PRIORITY_COLORS: Record<string, "active" | "warning" | "neutral"> = {
  Haute: "active",
  Moyenne: "warning",
  Basse: "neutral",
};

export function MockupMissionsView({ department }: MockupMissionsViewProps) {
  const counts = COLUMNS.map((_, i) => MISSIONS.filter((m) => m.col === i).length);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
        {[
          { label: "Total", value: MISSIONS.length },
          { label: "En cours", value: counts[1] },
          { label: "En attente", value: counts[2] },
          { label: "En test", value: counts[3] },
          { label: "Terminées", value: counts[4] },
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

      <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
        {COLUMNS.map((col, i) => (
          <div key={col} className="rounded-xl border border-bronze-faint bg-obsidian/40 p-2">
            <div className="mb-2 flex items-center justify-between px-2 py-1">
              <p className="text-[10px] uppercase tracking-wider text-titane/55">{col}</p>
              <span className="rounded-full bg-obsidian-2 px-1.5 py-0.5 text-[10px] text-titane/60">
                {counts[i]}
              </span>
            </div>
            <div className="space-y-2">
              {MISSIONS.filter((m) => m.col === i).map((m, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-bronze-faint bg-obsidian/60 p-2.5"
                >
                  <p className="text-[12px] font-medium text-ivoire/90">{m.title}</p>
                  <div className="mt-2 flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <AgentAvatar agentId={idForName(m.assignee)} name={m.assignee} size={18} />
                      <span className="text-[10px] text-titane/55">{m.assignee.split(" ")[0]}</span>
                    </div>
                    <StatusBadge status={PRIORITY_COLORS[m.priority]}>{m.priority}</StatusBadge>
                  </div>
                  <div className="mt-2">
                    <ProgressBar value={m.progress} />
                  </div>
                </div>
              ))}
              <button className="w-full rounded-lg border border-dashed border-bronze-faint py-1.5 text-[10px] text-titane/45 hover:text-titane/70">
                + Ajouter
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <MockCard title="Vue par priorité">
          <div className="grid grid-cols-2 gap-2">
            {["Haute", "Moyenne", "Basse", "À venir"].map((p) => (
              <div key={p} className="rounded-lg border border-bronze-faint bg-obsidian/50 p-2">
                <p className="text-[10px] uppercase tracking-wider text-titane/50">{p}</p>
                <p className="mt-1 font-title text-lg font-semibold text-ivoire">
                  {MISSIONS.filter((m) => (p === "À venir" ? m.col === 0 : m.priority === p)).length}
                </p>
              </div>
            ))}
          </div>
        </MockCard>

        <MockCard title="Performance globale">
          <div className="flex items-center gap-4">
            <div className="relative h-20 w-20">
              <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#1A1E24" strokeWidth="12" />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#C08A72"
                  strokeWidth="12"
                  strokeDasharray="196 251.2"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <p className="font-title text-base font-semibold text-ivoire">78%</p>
              </div>
            </div>
            <div className="flex-1 space-y-2">
              <MetricRow label="Agents impliqués" value={String(department.agents.length)} />
              <MetricRow label="Temps estimé" value="124h" />
              <MetricRow label="Temps passé" value="98h" />
              <MetricRow label="Efficacité" value="+12%" />
            </div>
          </div>
        </MockCard>
      </div>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[11px] text-titane/60">{label}</span>
      <span className="font-title text-sm font-semibold text-ivoire">{value}</span>
    </div>
  );
}
