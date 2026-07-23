"use client";

import { motion } from "framer-motion";
import { GitBranch, Lightbulb, Rocket, ShieldAlert, Sparkles } from "lucide-react";
import { useConsoleData } from "./console-provider";
import { cn } from "@/lib/utils";

const KIND_META = {
  ship: { icon: Rocket, color: "text-bronze-bright", bg: "bg-bronze/15", ring: "ring-bronze/30" },
  decide: { icon: GitBranch, color: "text-cuivre", bg: "bg-cuivre/15", ring: "ring-cuivre/30" },
  research: { icon: Lightbulb, color: "text-glow", bg: "bg-glow/15", ring: "ring-glow/30" },
  alert: { icon: ShieldAlert, color: "text-red-400", bg: "bg-red-500/15", ring: "ring-red-400/30" },
  create: { icon: Sparkles, color: "text-bronze-bright", bg: "bg-bronze/15", ring: "ring-bronze/30" },
} as const;

interface ActivityFeedProps {
  compact?: boolean;
  className?: string;
}

export function ActivityFeed({ compact = false, className }: ActivityFeedProps) {
  const { activityFeed } = useConsoleData();
  return (
    <div className={cn(compact ? "flex h-full min-h-0 flex-col" : "rounded-2xl border border-bronze-faint bg-obsidian/70 overflow-hidden", className)}>
      {!compact && (
        <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-bronze-faint bg-obsidian-deep/50">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full rounded-full bg-bronze opacity-75 animate-ping" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-bronze-bright" />
            </span>
            <h3 className="text-sm font-semibold tracking-wide text-ivoire">
              Flux d&apos;activité — temps réel
            </h3>
          </div>
          <span className="text-[10px] uppercase tracking-[0.2em] text-titane/50 hidden sm:block">
            Synchronisé
          </span>
        </div>
      )}

      <div className={cn(compact ? "flex min-h-0 flex-1 flex-col" : "max-h-[460px] overflow-y-auto mask-fade-y")}>
        <ul className={cn("divide-y divide-bronze-faint", compact && "flex-1 overflow-y-auto alnua-scroll")}>
          {activityFeed.length === 0 ? (
            <li className="flex flex-1 items-center justify-center px-5 py-12 text-center text-sm text-titane/50">
              Aucune activité récente — les agents apparaîtront ici dès qu&apos;ils agissent.
            </li>
          ) : null}
          {activityFeed.map((item, i) => {
            const meta = KIND_META[item.kind];
            const Icon = meta.icon;
            return (
              <motion.li
                key={item.id}
                initial={{ opacity: 0, x: -8 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: (i % 8) * 0.05 }}
                className="flex items-start gap-3 px-5 py-3.5 hover:bg-obsidian-deep/40 transition-colors"
              >
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ring-1",
                    meta.bg,
                    meta.ring
                  )}
                >
                  <Icon className={cn("h-3.5 w-3.5", meta.color)} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-ivoire/90 leading-snug">
                    <span className="font-semibold text-bronze-bright">
                      {item.agent}
                    </span>
                    <span className="text-titane/50 mx-1.5">·</span>
                    <span className="text-[10px] uppercase tracking-wide text-titane/60">
                      {item.dept}
                    </span>
                    <span className="text-titane/70"> {item.action}</span>
                  </p>
                  <span className="text-[10px] text-titane/40 mt-0.5 inline-block">
                    {item.time}
                  </span>
                </div>
              </motion.li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
