"use client";

import { useEffect, useState } from "react";
import { Loader2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { agentLabel, durationSeconds } from "@/lib/live-cards";
import type { LiveTask, LiveTaskStatus } from "@/lib/live-api";
import { workKind, WORK_LABEL } from "@/lib/live-work";
import { cn } from "@/lib/utils";
import { isActive } from "@/store/live-store";

const STATUS_LABEL: Record<LiveTaskStatus, string> = {
  queued: "En attente",
  running: "En cours",
  done: "Terminée",
  failed: "Échec",
  cancelled: "Annulée",
};

const STATUS_STYLE: Record<LiveTaskStatus, string> = {
  queued: "text-zinc-400",
  running: "text-copper-light",
  done: "text-emerald-400",
  failed: "text-red-400",
  cancelled: "text-zinc-500",
};

interface Props {
  tasks: LiveTask[];
  onCancel: (taskId: string) => void;
}

export function LiveTaskPanel({ tasks, onCancel }: Props) {
  const [now, setNow] = useState(() => Date.now());
  const hasActive = tasks.some(isActive);

  // Tick once a second only while something is running.
  useEffect(() => {
    if (!hasActive) return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [hasActive]);

  return (
    <section aria-label="Tâches" className="flex min-h-0 flex-col gap-2">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-copper-light">
        Tâches
      </h2>
      {tasks.length === 0 ? (
        <p className="text-sm text-zinc-500">
          Aucune tâche. Demande quelque chose à Nadia, elle travaille en arrière-plan.
        </p>
      ) : (
        <ul className="alnua-scroll flex min-h-0 flex-col gap-2 overflow-y-auto pr-1">
          {tasks.map((task) => {
            const seconds = durationSeconds(task, now);
            return (
              <li
                key={task.id}
                className="rounded-lg border border-copper/15 bg-obsidian-2 p-2.5"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="line-clamp-2 text-sm text-ivory">{task.instruction}</p>
                  {isActive(task) && (
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      aria-label={`Annuler : ${task.instruction}`}
                      onClick={() => onCancel(task.id)}
                    >
                      <X />
                    </Button>
                  )}
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs">
                  {task.status === "running" && (
                    <Loader2 className="size-3 animate-spin text-copper-light" />
                  )}
                  <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-zinc-400">
                    {WORK_LABEL[workKind(task)]}
                  </span>
                  <span className={cn("font-medium", STATUS_STYLE[task.status])}>
                    {STATUS_LABEL[task.status]}
                  </span>
                  <span className="text-zinc-500">· {agentLabel(task.agent_id)}</span>
                  {task.file_ids.length > 0 && (
                    <span className="text-zinc-500">
                      · {task.file_ids.length} fichier
                      {task.file_ids.length > 1 ? "s" : ""}
                    </span>
                  )}
                  {seconds !== null && <span className="text-zinc-500">· {seconds} s</span>}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
