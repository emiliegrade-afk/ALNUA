"use client";

import type { AgentStatus } from "@/lib/openroom-api";
import { Sparkline } from "@/components/console/charts";

/** Palette charte ALNUA — brand board maquettes (obsidienne / titane métal / cuivre). */
export const C = {
  void: "#000000",
  obsidian: "#0E1014",
  obsidian2: "#16181D",
  obsidian3: "#1A1E24",
  obsidianDeep: "#050507",
  border: "#2A2E38",
  copper: "#E09B6A",
  copperLight: "#F5C9A4",
  copperDim: "#B86E45",
  copperRgb: "224,155,106",
  ivory: "#F5F2EA",
  /** Brand board Titane — métal froid (#A7ADB5), jamais olive #A7ADB5. */
  titanium: "#B8BDC4",
  titaniumCold: "#E2E5E9",
  titaniumMuted: "#8A9098",
  titaniumDim: "#6D737C",
  titaniumRgb: "184,189,196",
  /** Filets structurels — titane métal. */
  line: "rgba(167,173,181,0.14)",
  lineSoft: "rgba(167,173,181,0.09)",
  lineStrong: "rgba(167,173,181,0.26)",
  /** Accents cuivre poli — bordures actives, icônes, glow Jarvis. */
  copperLine: "rgba(224,155,106,0.42)",
  copperGlow: "rgba(224,155,106,0.65)",
  copperFill: "rgba(224,155,106,0.12)",
  copperFillActive: "rgba(224,155,106,0.20)",
  teal: "#2DD4BF",
  danger: "#F87171",
  online: "#2DD4BF",
  onlineSoft: "#5EEAD4",
  /** Alias legacy — texte secondaire en titane. */
  warm: "#A7ADB5",
  muted: "#8A9098",
  dim: "#6D737C",
  faint: "#555B64",
} as const;

export const DEPT_V2_BG = C.void;
export const ALNUA_STAR_SPARK_MID = C.copperLight;
export const ALNUA_STAR_SPARK_OUTER = C.copper;
export const ALNUA_STAR_GLOW_RGB = C.copperRgb;

export function copperAlpha(alpha: number): string {
  return `rgba(${C.copperRgb},${alpha})`;
}

export function titaniumAlpha(alpha: number): string {
  return `rgba(${C.titaniumRgb},${alpha})`;
}

/**
 * @deprecated Cosmetic load % — prefer `resolveAgentLoad` (real progress / runId).
 * Kept as 0-map so rings don't invent activity when idle.
 */
export const STATUS_LOAD: Record<AgentStatus["status"], number> = {
  idle: 0,
  waiting: 0,
  working: 0,
  error: 0,
};

/** Real load: backend progress only. No fake idle→10% mapping (DEC-021). */
export function resolveAgentLoad(agent?: {
  status?: AgentStatus["status"];
  progress?: number | null;
}): number {
  if (agent?.progress != null && Number.isFinite(agent.progress)) {
    return Math.min(100, Math.max(0, Number(agent.progress)));
  }
  return 0;
}

export function agentTaskLabel(agent?: {
  currentTask?: string | null;
  runId?: string | null;
  taskId?: string | null;
  recipeId?: string | null;
}): string | null {
  if (agent?.currentTask) return agent.currentTask;
  if (agent?.runId) return `run ${agent.runId.slice(0, 12)}`;
  if (agent?.taskId) return `task ${String(agent.taskId).slice(0, 12)}`;
  if (agent?.recipeId) return agent.recipeId;
  return null;
}

export const STATUS_TEXT: Record<AgentStatus["status"], string> = {
  idle: "En veille",
  waiting: "En attente",
  working: "En ligne",
  error: "Erreur",
};

/** Sidebar / card chip: real task label, else real %, else status text. */
export function agentLoadChip(
  agent?: {
    status?: AgentStatus["status"];
    progress?: number | null;
    currentTask?: string | null;
    runId?: string | null;
    taskId?: string | null;
    recipeId?: string | null;
  },
  fallbackStatus: AgentStatus["status"] = "idle",
): string {
  const label = agentTaskLabel(agent);
  if (label) return label.length > 22 ? `${label.slice(0, 20)}…` : label;
  const load = resolveAgentLoad(agent);
  if (load > 0) return `${load}%`;
  return STATUS_TEXT[agent?.status ?? fallbackStatus];
}

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
      style={{ borderColor: "rgba(167,173,181,0.18)", background: "#000000" }}
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
