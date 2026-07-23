"use client";

import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface WidgetProps {
  title: string;
  icon?: LucideIcon;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  delay?: number;
  span?: string;
  /** Stretch body to fill equal-height grid rows */
  fill?: boolean;
}

export function Widget({
  title,
  icon: Icon,
  action,
  children,
  className,
  bodyClassName,
  delay = 0,
  span = "lg:col-span-4",
  fill = false,
}: WidgetProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className={cn(
        "col-span-12 rounded-2xl border border-bronze-faint bg-obsidian/70 overflow-hidden flex flex-col",
        fill && "h-full min-h-0",
        span,
        className,
      )}
    >
      <div className="flex shrink-0 items-center justify-between gap-2 border-b border-bronze-faint bg-obsidian-deep/40 px-4 py-3 sm:px-5">
        <div className="flex items-center gap-2 min-w-0">
          {Icon && <Icon className="h-3.5 w-3.5 text-bronze shrink-0" />}
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-titane/80 truncate">
            {title}
          </h3>
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      <div
        className={cn(
          "p-4 sm:p-5",
          fill && "flex min-h-0 flex-1 flex-col",
          bodyClassName,
        )}
      >
        {children}
      </div>
    </motion.section>
  );
}

/** Compact live badge for widget headers */
export function LiveDot({ label = "live" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-[9px] uppercase tracking-wide text-bronze">
      <span className="relative flex h-1.5 w-1.5">
        <span className="absolute inline-flex h-full w-full rounded-full bg-bronze opacity-75 animate-ping" />
        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-bronze-bright" />
      </span>
      {label}
    </span>
  );
}
