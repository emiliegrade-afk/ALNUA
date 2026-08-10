"use client";

import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Sparkline } from "@/components/console/charts";
import { cn } from "@/lib/utils";

/** KPI ouvert — pas de carte individuelle (anti-pâté). */
export function FinanceKpiCard({
  title,
  value,
  change,
  isPositive,
  trend,
  trendColor,
  className,
}: {
  title: string;
  value: string;
  change?: string | null;
  isPositive: boolean;
  trend?: number[];
  trendColor?: string;
  className?: string;
}) {
  const Icon = isPositive ? ArrowUpRight : ArrowDownRight;
  const colorClass = isPositive ? "text-teal" : "text-danger";
  const sparkColor = trendColor ?? (isPositive ? "#2DD4BF" : "#F87171");

  return (
    <div className={cn("finance-kpi-cell flex flex-col", className)}>
      <h3 className="text-[9px] font-medium uppercase tracking-[0.24em] text-titanium">
        {title}
      </h3>
      <p className="finance-kpi-value mt-2.5 font-display text-[1.45rem] font-light leading-none tracking-[-0.02em]">
        {value}
      </p>
      <div className="mt-3 flex items-end justify-between gap-2">
        {change ? (
          <div className={cn("flex min-w-0 items-center text-[10px]", colorClass)}>
            <Icon size={11} className="mr-0.5 shrink-0 opacity-80" aria-hidden />
            <span className="truncate tabular-nums">{change}</span>
          </div>
        ) : (
          <span className="text-[10px] text-titanium/40">—</span>
        )}
        {trend && trend.length > 1 ? (
          <Sparkline
            data={trend}
            width={64}
            height={22}
            stroke={sparkColor}
            strokeWidth={1.6}
            className="shrink-0"
            idSeed={title}
          />
        ) : null}
      </div>
    </div>
  );
}

export function FinanceTransactionRow({
  date,
  label,
  amount,
  type,
}: {
  date: string;
  label: string;
  amount: string;
  type: "in" | "out";
}) {
  return (
    <tr className="transition-colors hover:bg-white/[0.015]">
      <td className="w-20 py-2 text-[11px] tabular-nums text-titanium/65">{date}</td>
      <td className="py-2 text-[12px] text-ivoire/90">{label}</td>
      <td
        className={cn(
          "py-2 text-right text-[12px] font-medium tabular-nums",
          type === "in" ? "text-teal" : "text-danger",
        )}
      >
        {amount}
      </td>
    </tr>
  );
}

/** MoM % — null si pas de base comparable (évite un faux +∞). */
export function pctChange(current: number, previous: number): number | null {
  if (!Number.isFinite(current) || !Number.isFinite(previous)) return null;
  if (previous === 0) return current === 0 ? 0 : null;
  return ((current - previous) / Math.abs(previous)) * 100;
}

export function formatPct(pct: number | null): string | null {
  if (pct == null || !Number.isFinite(pct)) return null;
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

export function formatTxDate(iso: string): string {
  const d = new Date(`${iso.slice(0, 10)}T12:00:00`);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 10);
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
}
