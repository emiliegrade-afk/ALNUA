"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { ConsoleAgent } from "@/lib/console/types";
import { Brain, Cpu } from "lucide-react";

const STATUS_META: Record<
  ConsoleAgent["status"],
  { label: string; dot: string; text: string; ring: string }
> = {
  active: {
    label: "Actif",
    dot: "bg-bronze-bright",
    text: "text-bronze-bright",
    ring: "ring-bronze/40",
  },
  thinking: {
    label: "Réflexion",
    dot: "bg-glow",
    text: "text-glow",
    ring: "ring-glow/40",
  },
  idle: {
    label: "Veille",
    dot: "bg-titane",
    text: "text-titane",
    ring: "ring-titane/30",
  },
  review: {
    label: "Revue",
    dot: "bg-cuivre",
    text: "text-cuivre",
    ring: "ring-cuivre/40",
  },
};

interface AgentCardProps {
  agent: ConsoleAgent;
  index?: number;
}

export function AgentCard({ agent, index = 0 }: AgentCardProps) {
  const meta = STATUS_META[agent.status];
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-30px" }}
      transition={{ duration: 0.45, delay: (index % 6) * 0.06 }}
      whileHover={{ y: -4 }}
      className="group relative rounded-xl border border-bronze-faint bg-obsidian/70 p-4 sm:p-5 hover:border-bronze/50 hover:bg-obsidian transition-all overflow-hidden"
    >
      {/* glow accent */}
      <div
        className="absolute -top-12 -right-12 h-28 w-28 rounded-full opacity-0 group-hover:opacity-100 blur-2xl transition-opacity"
        style={{ background: agent.hue }}
      />

      <div className="relative flex items-start gap-3">
        {/* Avatar */}
        <div
          className={cn(
            "relative flex h-12 w-12 shrink-0 items-center justify-center rounded-lg ring-1 font-bold text-sm",
            meta.ring
          )}
          style={{
            background: `linear-gradient(135deg, ${agent.hue}22, ${agent.hue}08)`,
            color: agent.hue,
          }}
        >
          {agent.initials}
          <span
            className={cn(
              "absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-obsidian",
              meta.dot,
              agent.status === "active" && "animate-alnua-pulse"
            )}
          />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <h4 className="font-semibold text-ivoire truncate tracking-wide">
              {agent.name}
            </h4>
            <span className={cn("text-[10px] font-medium uppercase tracking-wide", meta.text)}>
              {meta.label}
            </span>
          </div>
          <p className="text-xs text-bronze/90 mt-0.5 truncate">{agent.role}</p>
          <p className="text-[11px] text-titane/60 mt-0.5 truncate">
            {agent.specialty}
          </p>
        </div>
      </div>

      {/* Current task */}
      <div className="relative mt-4 rounded-lg bg-obsidian-deep/70 border border-bronze-faint px-3 py-2.5">
        <div className="flex items-center gap-1.5 mb-1">
          <Brain className="h-3 w-3 text-bronze" />
          <span className="text-[10px] uppercase tracking-[0.15em] text-titane/60">
            Tâche courante
          </span>
        </div>
        <p className="text-xs text-ivoire/85 leading-snug line-clamp-2">
          {agent.task}
        </p>
      </div>

      {/* Footer: model + utilization */}
      <div className="relative mt-3 flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1 text-[10px] text-titane/60">
          <Cpu className="h-3 w-3" />
          {agent.model}
        </span>
        <div className="flex items-center gap-2 min-w-[80px]">
          <div className="h-1.5 flex-1 rounded-full bg-obsidian-deep overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{
                width: `${agent.utilization}%`,
                background: `linear-gradient(90deg, ${agent.hue}, ${agent.hue}99)`,
              }}
            />
          </div>
          <span className="text-[10px] tabular-nums text-titane/70 w-8 text-right">
            {agent.utilization}%
          </span>
        </div>
      </div>
    </motion.div>
  );
}
