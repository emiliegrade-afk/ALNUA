"use client";

import { Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DEPT_COLORS, type DeptKey } from "@/lib/dept-colors";
import { useCooStore } from "@/store/coo-store";
import { cn } from "@/lib/utils";

export interface AgentCardProps {
  icon?: string;
  name: string;
  role: string;
  branch: DeptKey;
  description: string;
  skills: string[];
  badge?: string;
  status?: "idle" | "working" | "waiting" | "error";
  currentTask?: string;
  /** 0-100. Optional — only the Département workspace's Équipe tab passes it today. */
  utilization?: number;
  /** LLM model slug. Optional — same source as `utilization`. */
  model?: string;
  onClick?: () => void;
  onDelegate?: () => void;
}

const STATUS_LABEL: Record<NonNullable<AgentCardProps["status"]>, string> = {
  idle: "Veille",
  working: "Actif",
  waiting: "En attente",
  error: "Erreur",
};

export function AgentCard({
  icon,
  name,
  role,
  branch,
  description,
  skills,
  badge,
  status = "idle",
  currentTask,
  utilization,
  model,
  onClick,
  onDelegate,
}: AgentCardProps) {
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);
  const openDrawer = useCooStore((s) => s.openDrawer);
  const colors = DEPT_COLORS[branch];

  function handleDelegate() {
    if (onDelegate) {
      onDelegate();
      return;
    }
    setPrefillMessage(`Délègue une tâche à ${name} (${role}) : `);
    openDrawer();
  }

  const statusDot =
    status === "working"
      ? "bg-bronze-bright"
      : status === "error"
        ? "bg-red-400"
        : status === "waiting"
          ? "bg-glow"
          : "bg-titane";

  return (
    <div>
      <article
        className={cn(
          "group relative overflow-hidden rounded-xl border border-bronze-faint bg-obsidian/70 p-4 transition-all hover:border-bronze/50 hover:bg-obsidian sm:p-5",
          onClick && "cursor-pointer",
        )}
        onClick={onClick}
      >
        <div
          className="pointer-events-none absolute -right-10 -top-10 h-24 w-24 rounded-full opacity-0 blur-2xl transition-opacity group-hover:opacity-100"
          style={{ backgroundColor: colors.bg }}
        />

        <div className="relative flex items-start gap-3">
          <div className="relative shrink-0">
            <div
              className="flex h-11 w-11 items-center justify-center rounded-xl border border-bronze-faint bg-obsidian-deep text-lg"
              style={{ boxShadow: `0 0 0 1px ${colors.border}` }}
            >
              {icon ? (
                <span className="text-xl leading-none">{icon}</span>
              ) : (
                <Bot className="h-5 w-5 text-bronze" />
              )}
            </div>
            <span
              className={cn(
                "absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-obsidian",
                statusDot,
                status === "working" && "animate-alnua-pulse",
              )}
            />
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <h3 className="truncate font-title text-base font-semibold text-ivoire">{name}</h3>
                <p className="truncate text-[11px] font-medium uppercase tracking-[0.12em] text-bronze-bright/90">
                  {role}
                </p>
              </div>
              {badge ? (
                <span className="shrink-0 rounded-full border border-bronze-faint bg-bronze/10 px-2 py-0.5 text-[10px] font-medium text-bronze-bright">
                  {badge}
                </span>
              ) : null}
            </div>

            <p className="mt-2 font-body text-sm leading-relaxed text-titane/80">{description}</p>

            <div className="mt-3 flex flex-wrap gap-1.5">
              {skills.map((skill) => (
                <span
                  key={skill}
                  className="rounded-full border border-bronze-faint bg-obsidian-deep/50 px-2 py-0.5 font-body text-[10px] text-titane/70"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="relative mt-4 rounded-lg border border-bronze-faint bg-obsidian-deep/60 px-3 py-2">
          <p className="text-[10px] uppercase tracking-[0.14em] text-titane/45">
            {STATUS_LABEL[status]}
          </p>
          {status === "working" && currentTask ? (
            <p className="mt-0.5 truncate text-xs text-bronze-bright">{currentTask}</p>
          ) : null}
        </div>

        {utilization !== undefined || model ? (
          <div className="relative mt-3 flex items-center justify-between gap-2 text-[10px] text-titane/60">
            {model ? <span className="truncate">{model}</span> : <span />}
            {utilization !== undefined ? (
              <div className="flex min-w-[72px] items-center gap-2">
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-obsidian-deep">
                  <div
                    className="h-full rounded-full bg-bronze"
                    style={{ width: `${Math.max(0, Math.min(100, utilization))}%` }}
                  />
                </div>
                <span className="w-8 shrink-0 text-right tabular-nums">{utilization}%</span>
              </div>
            ) : null}
          </div>
        ) : null}

        <Button
          variant="outline"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            handleDelegate();
          }}
          className="relative mt-4 w-full border-bronze-faint bg-transparent font-body text-titane/80 hover:border-bronze/40 hover:bg-bronze/10 hover:text-ivoire"
        >
          Déléguer une tâche
        </Button>
      </article>
    </div>
  );
}

