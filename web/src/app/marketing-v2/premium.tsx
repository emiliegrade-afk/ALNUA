"use client";

import { Sparkline } from "@/components/console/charts";
import { C } from "../app-v2/shared";

/* Primitives visuelles "premium" — Phase 38, ROADMAP.md. Échelle de la
   maquette d'Emilie (chiffres 27px tabulaires mono, cartes spacieuses,
   badges plateforme circulaires colorés) plutôt que le petit texte cuivre
   monochrome (8-11px) partagé par App/Gaming/Robo/R&D — divergence
   explicitement approuvée pour Marketing/Finances. Volontairement séparé de
   app-v2/shared.tsx (KpiTile, Bar) : ces primitives restent inchangées pour
   les autres départements, pas de risque de régression visuelle ailleurs. */

export const MONO = 'ui-monospace, "SF Mono", "Cascadia Mono", Consolas, monospace';

export function PremiumPanel({
  title,
  action,
  children,
  className,
}: {
  title?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-2xl border p-[18px] ${className ?? ""}`}
      style={{ borderColor: C.line, background: "rgba(19,19,22,.7)" }}
    >
      {title ? (
        <div className="mb-3.5 flex items-center justify-between gap-2">
          <h2 className="text-[13px] font-bold" style={{ color: C.ivory }}>
            {title}
          </h2>
          {action}
        </div>
      ) : null}
      {children}
    </div>
  );
}

export function PremiumKpiTile({
  label,
  value,
  delta,
  deltaTone = "flat",
  caption,
  trend,
  trendColor,
}: {
  label: string;
  value: string | number;
  delta?: string;
  deltaTone?: "pos" | "neg" | "flat";
  caption?: string;
  trend?: number[];
  trendColor?: string;
}) {
  const deltaColor = deltaTone === "pos" ? C.online : deltaTone === "neg" ? "#e8746c" : C.faint;
  const deltaBg =
    deltaTone === "pos"
      ? "rgba(111,207,151,.12)"
      : deltaTone === "neg"
        ? "rgba(232,116,108,.12)"
        : "rgba(255,255,255,.04)";
  return (
    <div className="min-w-[172px] flex-1 rounded-2xl border p-[18px]" style={{ borderColor: C.line, background: "rgba(19,19,22,.7)" }}>
      <div className="flex items-start justify-between gap-2">
        <span className="text-[10.5px] tracking-[.6px]" style={{ color: C.muted }}>
          {label}
        </span>
        {delta ? (
          <span
            className="shrink-0 rounded-md px-[7px] py-[3px] text-[10.5px] font-semibold"
            style={{ fontFamily: MONO, color: deltaColor, background: deltaBg }}
          >
            {delta}
          </span>
        ) : null}
      </div>
      <p className="mt-2.5 text-[27px] font-semibold leading-none tracking-[-.5px]" style={{ fontFamily: MONO, color: C.ivory }}>
        {value}
      </p>
      {caption ? (
        <p className="mt-[5px] text-[10px]" style={{ color: C.faint }}>
          {caption}
        </p>
      ) : null}
      {trend && trend.length > 1 ? (
        <Sparkline
          data={trend}
          width={200}
          height={46}
          stroke={trendColor ?? C.copperLight}
          strokeWidth={2}
          className="mt-2.5 w-full"
          idSeed={label}
        />
      ) : (
        <div className="mt-2.5 h-[46px]" />
      )}
    </div>
  );
}

const PLATFORM_BADGE: Record<string, { bg: string; color?: string; glyph: string; border?: string }> = {
  instagram: { bg: "linear-gradient(135deg, #f9c04a, #e34a8c 55%, #7048d8)", glyph: "◆" },
  meta: { bg: "linear-gradient(135deg, #f9c04a, #e34a8c 55%, #7048d8)", glyph: "f" },
  tiktok: { bg: "#0a0a0c", color: "#4de3d1", border: "rgba(255,255,255,.18)", glyph: "♪" },
  youtube: { bg: "#e64c3f", glyph: "▶" },
  linkedin: { bg: "#0a66c2", glyph: "in" },
  google: { bg: "linear-gradient(135deg, #4285f4, #34a853 40%, #fbbc05 70%, #ea4335)", color: "#1a1108", glyph: "G" },
  x: { bg: "#0a0a0c", border: "rgba(255,255,255,.18)", glyph: "✕" },
  discord: { bg: "#5865f2", glyph: "◈" },
  website_blog: { bg: "#3a332c", glyph: "◉" },
};

export function PlatformBadge({ platform, size = 34 }: { platform: string; size?: number }) {
  const style = PLATFORM_BADGE[platform] ?? { bg: "rgba(192,138,114,.15)", color: C.copperLight, glyph: "•" };
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-full text-[13px] font-bold"
      style={{
        width: size,
        height: size,
        background: style.bg,
        color: style.color ?? "#fff",
        border: style.border ? `1px solid ${style.border}` : undefined,
        fontSize: size * 0.38,
      }}
    >
      {style.glyph}
    </div>
  );
}

export function FunnelBars({
  stages,
}: {
  stages: { label: string; value: number }[];
}) {
  const max = Math.max(1, ...stages.map((s) => s.value));
  return (
    <div className="flex flex-col gap-2.5">
      {stages.map((s, i) => {
        const widthPct = Math.max(6, Math.round((s.value / max) * 100));
        const prev = i > 0 ? stages[i - 1].value : null;
        const rate = prev && prev > 0 ? Math.round((s.value / prev) * 100) : null;
        return (
          <div key={s.label} className="flex items-center gap-2.5">
            <span className="w-[82px] shrink-0 text-[11px]" style={{ color: C.muted }}>
              {s.label}
            </span>
            <div className="h-7 flex-1 rounded-md" style={{ background: "rgba(255,255,255,.03)" }}>
              <div
                className="flex h-full items-center justify-end rounded-md px-2.5 text-[11.5px] font-semibold"
                style={{
                  width: `${widthPct}%`,
                  background: "linear-gradient(90deg, rgba(192,138,114,.55), rgba(232,168,124,.9))",
                  color: "#1a1108",
                  fontFamily: MONO,
                }}
              >
                {s.value.toLocaleString("fr-FR")}
              </div>
            </div>
            <span className="w-9 shrink-0 text-right text-[10px]" style={{ color: C.faint, fontFamily: MONO }}>
              {rate != null ? `${rate}%` : ""}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function StatusPill({ tone, children }: { tone: "done" | "progress" | "scheduled"; children: React.ReactNode }) {
  const map = {
    done: { color: C.online, bg: "rgba(111,207,151,.12)" },
    progress: { color: "#8fb3e8", bg: "rgba(143,179,232,.12)" },
    scheduled: { color: C.copperLight, bg: "rgba(192,138,114,.12)" },
  } as const;
  const s = map[tone];
  return (
    <span className="shrink-0 rounded-full px-[7px] py-[2px] text-[8.5px] font-semibold" style={{ color: s.color, background: s.bg }}>
      {children}
    </span>
  );
}
