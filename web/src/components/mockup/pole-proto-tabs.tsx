"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export type PoleTab = { id: string; label: string };

/** Onglets style maquette (underline cuivre) pour tous les pôles. */
export function PoleProtoTabs({
  tabs,
  active,
  onChange,
}: {
  tabs: PoleTab[];
  active: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="department-tabs" style={{ padding: 0, marginBottom: 10 }}>
      <div className="tabs">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            className={active === t.id ? "active" : undefined}
            onClick={() => onChange(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/** Panneau secondaire rempli (plus de placeholder vide). */
export function PoleFilledPanel({
  title,
  subtitle,
  children,
  onBack,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  onBack?: () => void;
}) {
  return (
    <div className="space-y-3 pb-6">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h2 className="text-[18px] font-medium tracking-wide text-[#e8e2da]">{title}</h2>
          {subtitle ? <p className="mt-1 text-[10px] text-[#6e767f]">{subtitle}</p> : null}
        </div>
        {onBack ? (
          <button type="button" className="outline-btn" onClick={onBack}>
            ← Dashboard
          </button>
        ) : null}
      </div>
      {children}
    </div>
  );
}

export function PoleListCard({
  title,
  rows,
}: {
  title: string;
  rows: { primary: string; secondary?: string; meta?: string; tone?: "ok" | "warn" | "muted" }[];
}) {
  return (
    <section className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
      <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">{title}</p>
      <div className="space-y-1.5">
        {rows.map((r) => (
          <div
            key={r.primary + (r.secondary ?? "")}
            className="flex items-center justify-between gap-2 rounded-md border border-[rgba(255,255,255,0.05)] bg-[#0d141b] px-2.5 py-2"
          >
            <div className="min-w-0">
              <p className="truncate text-[11px] text-[#e8e2da]">{r.primary}</p>
              {r.secondary ? <p className="text-[9px] text-[#6e767f]">{r.secondary}</p> : null}
            </div>
            {r.meta ? (
              <span
                className={cn(
                  "shrink-0 text-[9px]",
                  r.tone === "ok" && "text-[#5ed69a]",
                  r.tone === "warn" && "text-[#e7a85f]",
                  (!r.tone || r.tone === "muted") && "text-[#7e8790]",
                )}
              >
                {r.meta}
              </span>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}

export function PoleStatStrip({
  items,
}: {
  items: { label: string; value: string }[];
}) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-5">
      {items.map((i) => (
        <div
          key={i.label}
          className="rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#0b1118] px-3 py-2.5"
        >
          <p className="text-[16px] font-medium text-[#e8e2da]">{i.value}</p>
          <p className="text-[8px] text-[#6e767f]">{i.label}</p>
        </div>
      ))}
    </div>
  );
}
