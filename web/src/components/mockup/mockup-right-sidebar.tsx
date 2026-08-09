"use client";

import { Activity, TrendingUp, Users } from "lucide-react";
import { useConsoleData } from "@/components/console/console-provider";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { cn } from "@/lib/utils";

function idForName(name: string): string {
  return name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
}

export function MockupRightSidebar() {
  const { activityFeed, stats, activeAgents, totalAgents } = useConsoleData();

  const recentActivity = activityFeed.slice(0, 8);

  return (
    <div className="space-y-5">
      <section>
        <p className="mb-3 text-[9px] uppercase tracking-[0.2em] text-titane/50">
          Activité en temps réel
        </p>
        <div className="space-y-3">
          {recentActivity.length === 0 ? (
            <p className="text-[11px] text-titane/40">Aucune activité récente.</p>
          ) : (
            recentActivity.map((item, idx) => (
              <div key={idx} className="flex gap-2.5">
                <div className="relative mt-0.5 h-6 w-6 shrink-0">
                  <AgentAvatar agentId={idForName(item.agent)} name={item.agent} size={24} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[11px] text-ivoire/90">
                    <span className="font-medium text-bronze-bright">{item.agent}</span>{" "}
                    {item.action}
                  </p>
                  <p className="mt-0.5 text-[10px] text-titane/50">
                    {item.time}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="rounded-xl border border-bronze-faint bg-obsidian/50 p-3">
        <p className="mb-3 text-[9px] uppercase tracking-[0.2em] text-titane/50">
          Métriques globales
        </p>
        <div className="grid grid-cols-2 gap-2">
          <MetricTile icon={Users} value={totalAgents} label="Agents" />
          <MetricTile icon={Activity} value={activeAgents} label="Actifs" />
          <MetricTile icon={TrendingUp} value={`$${stats.costTodayUsd.toFixed(2)}`} label="Coût / jour" />
          <MetricTile icon={Activity} value={stats.apiOnline ? "OK" : "—"} label="Hub" />
        </div>
      </section>

      <section>
        <p className="mb-3 text-[9px] uppercase tracking-[0.2em] text-titane/50">
          Connexions
        </p>
        <div className="flex items-center gap-2 rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-online opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-online" />
          </span>
          <span className="text-[11px] text-ivoire/80">Hub connecté</span>
          <span className="ml-auto text-[10px] text-titane/50">{stats.connectedApps}</span>
        </div>
      </section>
    </div>
  );
}

function MetricTile({
  icon: Icon,
  value,
  label,
}: {
  icon: React.ComponentType<{ className?: string }>;
  value: React.ReactNode;
  label: string;
}) {
  return (
    <div className="rounded-lg border border-bronze-faint bg-obsidian/50 p-2.5">
      <div className="mb-1 flex items-center gap-1.5">
        <Icon className="h-3 w-3 text-copper/70" />
        <span className="text-[9px] uppercase tracking-wider text-titane/50">{label}</span>
      </div>
      <p className={cn("font-title text-sm font-semibold text-ivoire", typeof value === "string" && value.length > 6 && "text-xs")}>
        {value}
      </p>
    </div>
  );
}
