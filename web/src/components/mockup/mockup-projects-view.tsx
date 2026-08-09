"use client";

import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { ConsoleDepartment } from "@/lib/console/types";
import { cn } from "@/lib/utils";
import { MockCard, StatusBadge } from "./mockup-widgets";

interface MockupProjectsViewProps {
  department: ConsoleDepartment;
}

const PROJECTS: { name: string; phase: string; progress: number; status: "active" | "warning" | "success" }[] = [
  { name: "NAÏA", phase: "Design", progress: 83, status: "active" },
  { name: "NUAWAY", phase: "Dev", progress: 64, status: "active" },
  { name: "RESONANCE", phase: "QA", progress: 47, status: "warning" },
  { name: "ALNUA CORE", phase: "Release", progress: 92, status: "success" },
];

export function MockupProjectsView({ department }: MockupProjectsViewProps) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <div className="space-y-4 xl:col-span-2">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {PROJECTS.map((project) => (
            <div
              key={project.name}
              className="rounded-xl border border-bronze-faint bg-obsidian/60 p-4 backdrop-blur-sm transition-all hover:border-bronze/30"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-title text-base font-semibold text-ivoire">{project.name}</p>
                  <p className="text-[11px] text-titane/55">Phase actuelle : {project.phase}</p>
                </div>
                <StatusBadge status={project.status}>
                  {project.status === "active" ? "Actif" : project.status === "warning" ? "Revue" : "Terminé"}
                </StatusBadge>
              </div>

              <div className="mt-4 flex items-center justify-center py-2">
                <RadialProgress value={project.progress} />
              </div>

              <div className="mt-3 flex items-center justify-between text-[10px] text-titane/50">
                <span>IDÉE</span>
                <span>DESIGN</span>
                <span>DEV</span>
                <span>QA</span>
                <span>RELEASE</span>
              </div>
              <div className="mt-1 flex h-1.5 overflow-hidden rounded-full bg-obsidian-2">
                {["IDÉE", "DESIGN", "DEV", "QA", "RELEASE"].map((step, i) => {
                  const active =
                    (project.phase === "IDÉE" && i === 0) ||
                    (project.phase === "Design" && i <= 1) ||
                    (project.phase === "Dev" && i <= 2) ||
                    (project.phase === "QA" && i <= 3) ||
                    (project.phase === "Release" && i <= 4);
                  return (
                    <div
                      key={step}
                      className={cn(
                        "flex-1",
                        active ? "bg-copper" : "bg-obsidian-3",
                        i > 0 && "ml-0.5",
                      )}
                    />
                  );
                })}
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-bronze-faint pt-3">
                <div className="flex -space-x-1.5">
                  {department.agents.slice(0, 3).map((a) => (
                    <div key={a.id} className="rounded-full border border-obsidian">
                      <AgentAvatar agentId={a.id} name={a.name} size={20} />
                    </div>
                  ))}
                </div>
                <button className="text-[11px] text-copper hover:text-copper-light">Ouvrir le projet</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <MockCard title="Résumé des projets">
          <div className="flex items-center justify-center py-2">
            <RadialProgress value={68} size={110} />
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <Metric value="4" label="Actifs" />
            <Metric value="2" label="Validation" />
            <Metric value="1" label="Terminés" />
            <Metric value="1" label="Archivés" />
          </div>
        </MockCard>

        <MockCard title="Métriques globales">
          <div className="space-y-2">
            <MetricRow label="Agents impliqués" value={department.agents.length.toString()} />
            <MetricRow label="Tâches totales" value="325" />
            <MetricRow label="MAJ cette semaine" value="67" />
            <MetricRow label="Projets en avance" value="2" />
          </div>
        </MockCard>
      </div>
    </div>
  );
}

function RadialProgress({ value, size = 96 }: { value: number; size?: number }) {
  const circumference = 2 * Math.PI * 36;
  const dash = (value / 100) * circumference;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="36" fill="none" stroke="#1A1E24" strokeWidth="10" />
        <circle
          cx="50"
          cy="50"
          r="36"
          fill="none"
          stroke="#C08A72"
          strokeWidth="10"
          strokeDasharray={`${dash} ${circumference}`}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <p className="font-title text-lg font-semibold text-ivoire">{value}%</p>
        <p className="text-[9px] text-titane/50">avancement</p>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-bronze-faint bg-obsidian/50 p-2 text-center">
      <p className="font-title text-base font-semibold text-ivoire">{value}</p>
      <p className="text-[9px] uppercase tracking-wider text-titane/45">{label}</p>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2">
      <span className="text-[11px] text-titane/65">{label}</span>
      <span className="font-title text-sm font-semibold text-ivoire">{value}</span>
    </div>
  );
}
