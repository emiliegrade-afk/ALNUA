export const WAITLIST_SOURCES = [
  { id: "instagram", label: "Instagram" },
  { id: "tiktok", label: "TikTok" },
  { id: "bouche_a_oreille", label: "Bouche à oreille" },
  { id: "reddit", label: "Reddit" },
  { id: "autre", label: "Autre" },
] as const;

export const WAITLIST_STATUSES = [
  { id: "waiting", label: "En attente" },
  { id: "notified", label: "Notifiée" },
  { id: "converted", label: "Convertie" },
] as const;

export const WAITLIST_SOURCE_LABELS: Record<string, string> = {
  instagram: "Instagram",
  tiktok: "TikTok",
  bouche_a_oreille: "Bouche à oreille",
  reddit: "Reddit",
  autre: "Autre",
  direct: "Direct",
};

export const WAITLIST_STATUS_LABELS: Record<string, string> = {
  waiting: "En attente",
  notified: "Notifiée",
  converted: "Convertie",
};

export function sourceBadgeStyle(source: string | null): string {
  const map: Record<string, string> = {
    instagram: "border-pink-500/30 bg-pink-500/10 text-pink-300",
    tiktok: "border-cyan-500/30 bg-cyan-500/10 text-cyan-300",
    bouche_a_oreille: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
    reddit: "border-orange-500/30 bg-orange-500/10 text-orange-300",
    autre: "border-copper/20 bg-obsidian/50 text-titanium",
    direct: "border-copper/30 bg-copper/10 text-copper-glow",
  };
  return map[source ?? "direct"] ?? map.autre;
}

export function statusBadgeStyle(status: string): string {
  const map: Record<string, string> = {
    waiting: "border-amber-500/30 bg-amber-500/10 text-amber-300",
    notified: "border-blue-500/30 bg-blue-500/10 text-blue-300",
    converted: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  };
  return map[status] ?? map.waiting;
}

export const WAITLIST_SOURCE_COLORS = [
  "#C08A72",
  "#ec4899",
  "#06b6d4",
  "#22c55e",
  "#f97316",
  "#a78bfa",
];
