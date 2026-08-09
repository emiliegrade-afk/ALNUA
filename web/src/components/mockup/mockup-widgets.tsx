"use client";

import { cn } from "@/lib/utils";

export function MockCard({
  children,
  className,
  title,
  action,
  noPadding,
  dense,
}: {
  children: React.ReactNode;
  className?: string;
  title?: string;
  action?: React.ReactNode;
  noPadding?: boolean;
  /** Padding / header plus serrés (dashboards dense type Comptabilité). */
  dense?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex flex-col rounded-xl border border-bronze-faint bg-obsidian/60 backdrop-blur-sm transition-all duration-300 hover:border-bronze/30",
        className,
      )}
    >
      {title ? (
        <div
          className={cn(
            "flex shrink-0 items-center justify-between border-b border-bronze-faint",
            dense ? "px-3 py-1.5" : "px-4 py-2.5",
          )}
        >
          <p className="text-[10px] uppercase tracking-[0.18em] text-titane/55">{title}</p>
          {action ? <div>{action}</div> : null}
        </div>
      ) : null}
      <div
        className={cn(
          "min-h-0 flex-1",
          noPadding ? "" : dense ? "p-2.5" : "p-4",
        )}
      >
        {children}
      </div>
    </div>
  );
}

export function KpiCard({
  label,
  value,
  delta,
  deltaType = "positive",
  sparkline,
}: {
  label: string;
  value: string;
  delta?: string;
  deltaType?: "positive" | "negative" | "neutral";
  sparkline?: number[];
}) {
  const max = sparkline ? Math.max(...sparkline, 1) : 1;
  const min = sparkline ? Math.min(...sparkline, 0) : 0;
  const range = max - min || 1;

  return (
    <div className="rounded-xl border border-bronze-faint bg-obsidian/60 p-4 backdrop-blur-sm transition-all duration-300 hover:border-bronze/30">
      <p className="text-[9px] uppercase tracking-[0.18em] text-titane/50">{label}</p>
      <div className="mt-2 flex items-end justify-between gap-2">
        <p className="font-title text-xl font-semibold text-ivoire">{value}</p>
        {delta ? (
          <span
            className={cn(
              "text-[11px] font-medium",
              deltaType === "positive" && "text-online",
              deltaType === "negative" && "text-red-400",
              deltaType === "neutral" && "text-titane/60",
            )}
          >
            {delta}
          </span>
        ) : null}
      </div>
      {sparkline ? (
        <div className="mt-3 flex h-8 items-end gap-0.5">
          {sparkline.map((v, i) => {
            const h = ((v - min) / range) * 100;
            return (
              <div
                key={i}
                className="flex-1 rounded-sm bg-copper/40"
                style={{ height: `${Math.max(15, h)}%` }}
              />
            );
          })}
        </div>
      ) : null}
    </div>
  );
}

export function ProgressBar({
  value,
  className,
  size = "sm",
}: {
  value: number;
  className?: string;
  size?: "sm" | "md";
}) {
  return (
    <div
      className={cn(
        "w-full overflow-hidden rounded-full bg-obsidian-2",
        size === "sm" ? "h-1" : "h-2",
        className,
      )}
    >
      <div
        className="h-full rounded-full bg-copper transition-all duration-500"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

export function StatusBadge({
  children,
  status = "neutral",
}: {
  children: React.ReactNode;
  status?: "active" | "warning" | "neutral" | "success";
}) {
  const classes = {
    active: "border-copper/30 bg-copper/10 text-copper-light",
    warning: "border-yellow-500/30 bg-yellow-500/10 text-yellow-400",
    neutral: "border-bronze-faint bg-obsidian-2 text-titane/70",
    success: "border-online/30 bg-online/10 text-online",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium",
        classes[status],
      )}
    >
      {children}
    </span>
  );
}

export function MiniSparkline({
  data,
  color = "bg-copper",
  height = 32,
}: {
  data: number[];
  color?: string;
  height?: number;
}) {
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;

  return (
    <div className="flex items-end gap-0.5" style={{ height }}>
      {data.map((v, i) => {
        const h = ((v - min) / range) * 100;
        return (
          <div
            key={i}
            className={cn("flex-1 rounded-sm opacity-70", color)}
            style={{ height: `${Math.max(10, h)}%` }}
          />
        );
      })}
    </div>
  );
}
