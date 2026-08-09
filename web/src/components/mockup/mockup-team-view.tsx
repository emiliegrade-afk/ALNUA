"use client";

import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { ConsoleDepartment } from "@/lib/console/types";
import { cn } from "@/lib/utils";
import { MockCard, ProgressBar, StatusBadge } from "./mockup-widgets";

interface MockupTeamViewProps {
  department: ConsoleDepartment;
}

export function MockupTeamView({ department }: MockupTeamViewProps) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <div className="space-y-4 xl:col-span-2">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {department.agents.map((agent) => (
            <div
              key={agent.id}
              className="rounded-xl border border-bronze-faint bg-obsidian/60 p-4 backdrop-blur-sm transition-all hover:border-bronze/30"
            >
              <div className="flex items-start gap-3">
                <div className="relative">
                  <AgentAvatar agentId={agent.id} name={agent.name} size={48} />
                  <span
                    className={cn(
                      "absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border border-obsidian",
                      agent.status === "active" && "bg-online",
                      agent.status === "thinking" && "bg-copper",
                      agent.status === "idle" && "bg-titane/50",
                      agent.status === "review" && "bg-red-400",
                    )}
                  />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-ivoire">{agent.name}</p>
                  <p className="text-[11px] text-titane/55">{agent.role}</p>
                  <p className="mt-1 text-[10px] text-titane/45">{agent.specialty}</p>
                </div>
              </div>
              <div className="mt-3 space-y-1.5">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="text-titane/55">Charge</span>
                  <span className="text-copper">{agent.utilization}%</span>
                </div>
                <ProgressBar value={agent.utilization} />
              </div>
              <div className="mt-3 flex items-center justify-between">
                <StatusBadge status={agent.status === "active" ? "active" : "neutral"}>
                  {agent.status === "active" ? "En ligne" : agent.status === "thinking" ? "Réflexion" : agent.status === "review" ? "Revue" : "En veille"}
                </StatusBadge>
                <p className="truncate text-[10px] text-titane/45 max-w-[60%]">{agent.task}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <MockCard title="Charge d'équipe">
          <div className="space-y-3">
            {department.agents.slice(0, 5).map((a) => (
              <div key={a.id} className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-ivoire/80">{a.name}</span>
                  <span className="text-copper">{a.utilization}%</span>
                </div>
                <ProgressBar value={a.utilization} />
              </div>
            ))}
          </div>
        </MockCard>

        <MockCard title="Compétences principales">
          <div className="flex flex-wrap gap-1.5">
            {["React", "TypeScript", "Python", "FastAPI", "Supabase", "Tailwind", "Godot", "n8n"].map((skill) => (
              <span
                key={skill}
                className="rounded-full border border-bronze-faint bg-obsidian-2 px-2 py-1 text-[10px] text-titane/70"
              >
                {skill}
              </span>
            ))}
          </div>
        </MockCard>
      </div>
    </div>
  );
}
