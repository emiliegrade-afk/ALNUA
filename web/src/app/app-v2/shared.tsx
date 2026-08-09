"use client";

import type { AgentStatus } from "@/lib/openroom-api";
import { Sparkline } from "@/components/console/charts";

/** Palette charte ALNUA — obsidienne dominante, cuivre rosé en accent léger,
 * titane pour textes secondaires et filets (pas de brun/orange). */
export const C = {
  obsidian: "#0E1014",
  obsidian2: "#13161B",
  obsidian3: "#1A1E24",
  obsidianDeep: "#08090C",
  copper: "#C08A72",
  copperLight: "#D9A88F",
  copperDim: "#8A6050",
  copperRgb: "192,138,114",
  ivory: "#F5F2EA",
  titanium: "#A7ADB5",
  titaniumCold: "#9BA3AC",
  titaniumMuted: "#7A8089",
  titaniumDim: "#5C626A",
  /** Filets structurels — titane, pas cuivre (évite l'effet « brun partout »). */
  line: "rgba(167,173,181,0.12)",
  lineSoft: "rgba(167,173,181,0.08)",
  lineStrong: "rgba(167,173,181,0.22)",
  /** Accents cuivre — bordures actives, icônes, glow discret. */
  copperLine: "rgba(192,138,114,0.24)",
  copperGlow: "rgba(192,138,114,0.32)",
  copperFill: "rgba(192,138,114,0.07)",
  copperFillActive: "rgba(192,138,114,0.11)",
  online: "#7FC98C",
  onlineSoft: "#8FCB99",
  /** Alias legacy — texte secondaire en titane, plus de teinte brune. */
  warm: "#A7ADB5",
  muted: "#9BA3AC",
  dim: "#7A8089",
  faint: "#5C626A",
} as const;

export const DEPT_V2_BG = C.obsidian;
export const ALNUA_STAR_SPARK_MID = C.copperLight;
export const ALNUA_STAR_SPARK_OUTER = C.copper;
export const ALNUA_STAR_GLOW_RGB = C.copperRgb;

export function copperAlpha(alpha: number): string {
  return `rgba(${C.copperRgb},${alpha})`;
}

export function titaniumAlpha(alpha: number): string {
  return `rgba(167,173,181,${alpha})`;
}

export const STATUS_LOAD: Record<AgentStatus["status"], number> = {
  idle: 10,
  waiting: 40,
  working: 78,
  error: 0,
};

export const STATUS_TEXT: Record<AgentStatus["status"], string> = {
  idle: "En veille",
  waiting: "En attente",
  working: "En ligne",
  error: "Erreur",
};

export const STATUS_COLOR: Record<AgentStatus["status"], string> = {
  idle: C.titaniumDim,
  waiting: C.copperLight,
  working: C.online,
  error: "#f87171",
};

export const KIND_META: Record<string, { icon: string; label: string; color: string }> = {
  ship: { icon: "🚀", label: "Livraison", color: C.online },
  decide: { icon: "◈", label: "Décision", color: C.titanium },
  research: { icon: "◎", label: "Recherche", color: C.titaniumCold },
  alert: { icon: "⚠", label: "Alerte", color: "#f87171" },
  create: { icon: "✦", label: "Création", color: C.copperLight },
};

export const LOAD_LABEL: Record<AgentStatus["status"], string> = {
  idle: "Faible",
  waiting: "Modérée",
  working: "Élevée",
  error: "Bloquée",
};

export function formatDueDate(iso: string): { label: string; overdue: boolean } {
  const d = new Date(`${iso}T00:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return {
    label: d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" }),
    overdue: d.getTime() < today.getTime(),
  };
}

export function Ring({ value, size, stroke }: { value: number; size: number; stroke: number }) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const dash = `${((value / 100) * circ).toFixed(2)} ${circ.toFixed(2)}`;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="shrink-0">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={C.lineSoft}
        strokeWidth={stroke}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={C.copper}
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeDasharray={dash}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ filter: `drop-shadow(0 0 5px ${copperAlpha(0.45)})` }}
      />
    </svg>
  );
}

export function KpiTile({
  label,
  value,
  sublabel,
  tone = "default",
  trend,
  trendColor,
}: {
  label: string;
  value: string | number;
  sublabel?: string;
  tone?: "default" | "positive" | "negative";
  trend?: number[];
  trendColor?: string;
}) {
  const color = tone === "positive" ? C.online : tone === "negative" ? "#f87171" : C.ivory;
  return (
    <div
      className="flex-1 rounded-xl border p-3 text-center"
      style={{ borderColor: C.line, background: `${C.obsidian2}CC` }}
    >
      <p className="text-[19px] font-semibold" style={{ color }}>
        {value}
      </p>
      <p className="text-[8.5px]" style={{ color: C.faint }}>
        {label}
      </p>
      {sublabel ? (
        <p className="mt-0.5 text-[9px]" style={{ color: C.dim }}>
          {sublabel}
        </p>
      ) : null}
      {trend && trend.length > 1 ? (
        <Sparkline
          data={trend}
          width={72}
          height={20}
          stroke={trendColor ?? color}
          strokeWidth={1.25}
          className="mx-auto mt-1.5"
          idSeed={label}
        />
      ) : null}
    </div>
  );
}

export function Bar({ value, thick = 3 }: { value: number; thick?: number }) {
  return (
    <span
      className="block min-w-0 flex-1 overflow-hidden rounded-full"
      style={{ height: thick, background: C.lineSoft }}
    >
      <span
        className="block h-full rounded-full"
        style={{
          width: `${value}%`,
          background: `linear-gradient(90deg, ${C.copperDim}, ${C.copperLight})`,
          boxShadow: `0 0 8px ${copperAlpha(0.25)}`,
        }}
      />
    </span>
  );
}
