"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { C } from "@/app/app-v2/shared";

/** Panel chrome — maquette command center, palette ALNUA (cuivre / obsidienne). */
export function SiegePanel({
  title,
  action,
  className,
  children,
}: {
  title?: string;
  action?: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  return (
    <section
      className={cn(
        "flex flex-col rounded-xl border border-copper/20 bg-obsidian/55 p-4 shadow-[inset_0_1px_0_rgba(224,155,106,0.06)]",
        className,
      )}
    >
      {(title || action) && (
        <div className="mb-3 flex items-center justify-between gap-2">
          {title ? (
            <h2 className="text-[11px] font-medium uppercase tracking-[0.18em] text-titanium/70">
              {title}
            </h2>
          ) : (
            <span />
          )}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function SiegeProgress({ value, className }: { value: number; className?: string }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("h-1.5 w-full overflow-hidden rounded-full bg-obsidian-3", className)}>
      <div
        className="h-full rounded-full bg-gradient-to-r from-copper-dim to-copper"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export function SiegeBadge({
  tone = "copper",
  children,
}: {
  tone?: "copper" | "ok" | "danger" | "muted";
  children: ReactNode;
}) {
  const styles = {
    copper: "border-copper/35 bg-copper/10 text-copper",
    ok: "border-teal/35 bg-teal/10 text-teal",
    danger: "border-danger/40 bg-danger/10 text-danger",
    muted: "border-titanium/25 bg-obsidian-3/80 text-titanium",
  } as const;
  return (
    <span
      className={cn(
        "inline-flex shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide",
        styles[tone],
      )}
    >
      {children}
    </span>
  );
}

export function SiegeQuickLink({
  href,
  label,
  icon,
}: {
  href: string;
  label: string;
  icon?: ReactNode;
}) {
  return (
    <Link
      href={href}
      className="flex min-h-[52px] flex-1 items-center justify-center gap-2 rounded-xl border border-copper/30 bg-copper/[0.06] px-3 py-2.5 text-center text-[12px] text-copper transition hover:border-copper hover:bg-copper/15"
    >
      {icon}
      <span>{label}</span>
    </Link>
  );
}

export function SiegePageHeader({
  title,
  accent,
  subtitle,
  trailing,
}: {
  title: string;
  accent?: string;
  subtitle: string;
  trailing?: ReactNode;
}) {
  const now = new Date();
  const dateLabel = now.toLocaleDateString("fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  const timeLabel = now.toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <header className="flex flex-wrap items-end justify-between gap-3 border-b border-copper/15 pb-4">
      <div>
        <h1 className="text-[24px] leading-[1.05] tracking-[1px] text-ivory">
          <span className="font-bold">{title}</span>
          {accent ? (
            <>
              {" "}
              <span className="font-light tracking-[0.28em] text-titanium">{accent}</span>
            </>
          ) : null}
        </h1>
        <p className="mt-1 text-[12px]" style={{ color: C.dim }}>
          {subtitle}
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <p className="text-right text-[11px] capitalize text-titanium/65">
          {dateLabel}
          <span className="ml-2 text-copper">{timeLabel}</span>
        </p>
        {trailing}
      </div>
    </header>
  );
}

/** Anneau KPI type maquette CEO (cuivre ALNUA). */
export function SiegeRingStat({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="flex flex-col items-start gap-0.5">
      <p className="text-[10px] uppercase tracking-wider text-titanium/55">{label}</p>
      <p className="text-xl font-semibold tabular-nums text-ivory">{value}</p>
      {hint ? <p className="text-[10px] text-copper/80">{hint}</p> : null}
    </div>
  );
}
