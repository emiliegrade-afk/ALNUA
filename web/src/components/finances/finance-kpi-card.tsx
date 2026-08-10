"use client";

import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Sparkline } from "@/components/console/charts";
import { cn } from "@/lib/utils";

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
  const colorClass = isPositive ? "text-alnua-teal" : "text-alnua-danger";
  const sparkColor = trendColor ?? (isPositive ? "#2DD4BF" : "#F87171");

  return (
    <div
      className={cn(
        "rounded-xl border border-alnua-border bg-alnua-surface p-5 transition-colors hover:border-alnua-cuivre/30",
        className,
      )}
    >
      <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-alnua-titane">
        {title}
      </h3>
      <div className="flex items-end justify-between gap-3">
        <div className="min-w-0">
          <p className="mb-1 font-display text-2xl font-medium text-alnua-ivoire">
            {value}
          </p>
          {change ? (
            <div className={cn("flex items-center text-xs font-medium", colorClass)}>
              <Icon size={14} className="mr-1 shrink-0" aria-hidden />
              <span>{change}</span>
              <span className="ml-2 font-normal text-alnua-titane">
                vs mois dernier
              </span>
            </div>
          ) : (
            <p className="text-xs text-alnua-titane">—</p>
          )}
        </div>
        {trend && trend.length > 1 ? (
          <Sparkline
            data={trend}
            width={80}
            height={40}
            stroke={sparkColor}
            strokeWidth={1.5}
            className="shrink-0 opacity-70"
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
    <tr className="transition-colors hover:bg-alnua-bg/50">
      <td className="w-24 py-3 text-xs text-alnua-titane">{date}</td>
      <td className="py-3 text-alnua-ivoire">{label}</td>
      <td
        className={cn(
          "py-3 text-right font-medium",
          type === "in" ? "text-alnua-teal" : "text-alnua-danger",
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
