"use client";

import type { AgentStatus } from "@/lib/openroom-api";

/* Palette et primitives visuelles partagées entre page.tsx, tabs.tsx et
   team.tsx — un seul endroit à modifier si la charte change, pas trois. */

export const C = {
  line: "rgba(200,127,78,.16)",
  lineSoft: "rgba(200,127,78,.13)",
  lineStrong: "rgba(200,127,78,.3)",
  copper: "#C87F4E",
  copperLight: "#E8A87C",
  ivory: "#F5F2EA",
  warm: "#C9C0B6",
  muted: "#A79C92",
  dim: "#8C8177",
  faint: "#7A7069",
  online: "#7FC98C",
  onlineSoft: "#8FCB99",
} as const;

/** Charge dérivée du statut : le Hub ne trace pas d'utilisation réelle par
 * agent, on ne fabrique donc pas un pourcentage précis. */
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

/** Couleur par statut réel — la maquette distingue plusieurs états par
 * couleur (vert/ambre/bleu), pas un simple binaire vert/gris. */
export const STATUS_COLOR: Record<AgentStatus["status"], string> = {
  idle: "#7A7069",
  waiting: "#E0A95C",
  working: "#7FC98C",
  error: "#f87171",
};

/** Icône + couleur par nature d'événement (flux d'activité réel du Hub) —
 * la maquette varie la couleur du point par type d'action, pas une seule
 * teinte cuivre partout. Partagé entre le rail d'activité (page.tsx) et le
 * panneau « Tâches récentes » (team.tsx). */
export const KIND_META: Record<string, { icon: string; label: string; color: string }> = {
  ship: { icon: "🚀", label: "Livraison", color: "#7FC98C" },
  decide: { icon: "◈", label: "Décision", color: "#A7ADB5" },
  research: { icon: "◎", label: "Recherche", color: "#D8CFC4" },
  alert: { icon: "⚠", label: "Alerte", color: "#f87171" },
  create: { icon: "✦", label: "Création", color: "#C87F4E" },
};
export const LOAD_LABEL: Record<AgentStatus["status"], string> = {
  idle: "Faible",
  waiting: "Modérée",
  working: "Élevée",
  error: "Bloquée",
};

/** Formatage de l'échéance réelle d'un ticket (`due_date`, Phase 12) —
 * `overdue` sert à colorer la carte en alerte quand la date est dépassée. */
export function formatDueDate(iso: string): { label: string; overdue: boolean } {
  const d = new Date(`${iso}T00:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return {
    label: d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" }),
    overdue: d.getTime() < today.getTime(),
  };
}

/** Anneau de progression — dimensions et dégradé du fichier source. */
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
        stroke="rgba(200,127,78,.15)"
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
        style={{ filter: "drop-shadow(0 0 5px rgba(217,168,143,.6))" }}
      />
    </svg>
  );
}

export function Bar({ value, thick = 3 }: { value: number; thick?: number }) {
  return (
    <span
      className="block min-w-0 flex-1 overflow-hidden rounded-full"
      style={{ height: thick, background: "rgba(200,127,78,.16)" }}
    >
      <span
        className="block h-full rounded-full"
        style={{ width: `${value}%`, background: `linear-gradient(90deg,#8A5230,${C.copperLight})` }}
      />
    </span>
  );
}
