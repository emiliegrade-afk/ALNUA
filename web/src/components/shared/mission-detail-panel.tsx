"use client";

import { useMemo, useState } from "react";
import { Bars } from "@/components/console/charts";
import { getAgentsForBureau, type BureauKey } from "@/lib/agent-bureau";
import type { TicketWithProject } from "@/lib/tickets";
import { cn } from "@/lib/utils";

interface MissionDetailPanelProps {
  bureau: BureauKey;
  tickets: TicketWithProject[];
}

const TASK_STATUS_LABEL: Record<string, string> = {
  done: "Terminée",
  in_review: "En cours",
  in_progress: "En cours",
  open: "À venir",
  wont_fix: "Abandonnée",
};

const TASK_STATUS_STYLE: Record<string, string> = {
  done: "text-emerald-300",
  in_review: "text-blue-300",
  in_progress: "text-blue-300",
  open: "text-titane/60",
  wont_fix: "text-zinc-400",
};

/**
 * Project-level detail below the Kanban — "MISSION EN COURS" from the
 * reference mockup, built from real tickets grouped by project (task list,
 * progress %, team). No per-project velocity/bug-rate endpoint exists yet,
 * so the analytics half uses the same real ticket counts the board already
 * has (status breakdown), not invented time-series.
 */
export function MissionDetailPanel({ bureau, tickets }: MissionDetailPanelProps) {
  const projectGroups = useMemo(() => {
    const byProject = new Map<string, { name: string; tickets: TicketWithProject[] }>();
    for (const t of tickets) {
      const key = t.project_id;
      if (!byProject.has(key)) byProject.set(key, { name: t.project_name ?? "Projet", tickets: [] });
      byProject.get(key)!.tickets.push(t);
    }
    return Array.from(byProject.entries()).map(([id, v]) => ({ id, ...v }));
  }, [tickets]);

  const [selectedProjectId, setSelectedProjectId] = useState(projectGroups[0]?.id);
  const project = projectGroups.find((p) => p.id === selectedProjectId) ?? projectGroups[0];
  const teamAvatars = getAgentsForBureau(bureau).slice(0, 5);

  if (!project) {
    return (
      <div className="rounded-xl border border-bronze-faint bg-obsidian/50 px-6 py-8 text-center text-sm text-titane/60">
        Aucune mission en cours — les tickets apparaîtront ici une fois créés.
      </div>
    );
  }

  const done = project.tickets.filter((t) => t.status === "done").length;
  const progress = Math.round((done / project.tickets.length) * 100);
  const statusCounts = ["open", "in_progress", "in_review", "done"].map((s) => ({
    label: TASK_STATUS_LABEL[s],
    value: project.tickets.filter((t) => t.status === s).length,
  }));

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
      <div className="rounded-xl border border-bronze-faint bg-obsidian/70 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="label-caps">Projet</p>
            <h3 className="font-title text-lg font-semibold text-ivoire">{project.name}</h3>
          </div>
          {projectGroups.length > 1 ? (
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="rounded-lg border border-bronze-faint bg-obsidian-deep/60 px-2 py-1 text-xs text-titane/80"
            >
              {projectGroups.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          ) : null}
        </div>

        <div className="mt-3">
          <div className="mb-1 flex justify-between text-xs text-titane/60">
            <span>Progression</span>
            <span>{progress}%</span>
          </div>
          <div className="h-1.5 rounded-full bg-obsidian-3">
            <div
              className="h-full rounded-full bg-bronze transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="mt-4 flex -space-x-2">
          {teamAvatars.map((a) => (
            <span
              key={a.id}
              title={a.name}
              className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-obsidian bg-obsidian-deep text-sm"
            >
              {a.icon}
            </span>
          ))}
        </div>

        <p className="mt-4 label-caps">Tickets</p>
        <ul className="mt-2 max-h-60 divide-y divide-bronze-faint overflow-y-auto">
          {project.tickets.map((t) => (
            <li key={t.id} className="flex items-center justify-between gap-3 py-2">
              <span className="truncate text-sm text-ivoire/85">{t.title}</span>
              <span className={cn("shrink-0 text-xs font-medium", TASK_STATUS_STYLE[t.status])}>
                {TASK_STATUS_LABEL[t.status] ?? t.status}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-xl border border-bronze-faint bg-obsidian/70 p-4">
        <p className="label-caps mb-3">Répartition</p>
        <Bars data={statusCounts} height={140} color="#C08A72" />
      </div>
    </div>
  );
}
