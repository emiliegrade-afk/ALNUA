"use client";

import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface BureauPanelProps {
  title?: string;
  icon?: LucideIcon;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  noPadding?: boolean;
}

/** Card surface aligned with Hub dashboard Widgets. */
export function BureauPanel({
  title,
  icon: Icon,
  action,
  children,
  className,
  bodyClassName,
  noPadding = false,
}: BureauPanelProps) {
  return (
    <section
      className={cn(
        "overflow-hidden rounded-2xl border border-bronze-faint bg-obsidian/70",
        className,
      )}
    >
      {title ? (
        <div className="flex items-center justify-between gap-2 border-b border-bronze-faint bg-obsidian-deep/40 px-4 py-3 sm:px-5">
          <div className="flex min-w-0 items-center gap-2">
            {Icon ? <Icon className="h-3.5 w-3.5 shrink-0 text-bronze" /> : null}
            <h3 className="truncate text-[11px] font-semibold uppercase tracking-[0.18em] text-titane/80">
              {title}
            </h3>
          </div>
          {action ? <div className="shrink-0">{action}</div> : null}
        </div>
      ) : null}
      <div className={cn(!noPadding && "p-4 sm:p-5", bodyClassName)}>{children}</div>
    </section>
  );
}
