import type { PartnerStatus, PartnerType } from "@/lib/partnerships-api";

export const PARTNER_TYPES: { id: PartnerType | string; label: string; emoji: string }[] = [
  { id: "influencer", label: "Influenceuse", emoji: "👤" },
  { id: "creator", label: "Créatrice", emoji: "✨" },
  { id: "brand", label: "Marque", emoji: "🏷️" },
  { id: "affiliate", label: "Affilié(e)", emoji: "🔗" },
  { id: "investor", label: "Investisseur", emoji: "💼" },
  { id: "distributor", label: "Distributeur", emoji: "📦" },
  { id: "press", label: "Presse", emoji: "📰" },
];

export const PUBLIC_REQUEST_TYPES = [
  { id: "influencer", label: "Créatrice / Influenceuse", emoji: "👤" },
  { id: "brand", label: "Marque", emoji: "🏷️" },
  { id: "affiliate", label: "Affilié(e)", emoji: "🔗" },
  { id: "other", label: "Autre", emoji: "💬" },
] as const;

export const PARTNER_STATUSES: { id: PartnerStatus; label: string }[] = [
  { id: "prospect", label: "Prospect" },
  { id: "contacted", label: "Contacté(e)" },
  { id: "in_discussion", label: "En discussion" },
  { id: "agreement", label: "Accord" },
  { id: "active", label: "Actif" },
  { id: "paused", label: "En pause" },
  { id: "declined", label: "Décliné" },
];

export const INTERACTION_TYPES = [
  { id: "email", label: "Email", icon: "✉️" },
  { id: "dm", label: "DM", icon: "💬" },
  { id: "call", label: "Appel", icon: "📞" },
  { id: "meeting", label: "Réunion", icon: "🤝" },
  { id: "contract_sent", label: "Contrat envoyé", icon: "📤" },
  { id: "contract_signed", label: "Contrat signé", icon: "✅" },
] as const;

export const AUDIENCE_BUCKETS = [
  "< 1k",
  "1k-10k",
  "10k-100k",
  "100k+",
] as const;

export const PROJECT_OPTIONS = [
  "Naïa",
  "Wyrdheim",
  "Eve",
  "ALNUA Global",
] as const;

export const REQUEST_STATUSES = [
  { id: "new", label: "Nouveau" },
  { id: "reviewed", label: "Lu" },
  { id: "converted", label: "Converti" },
  { id: "declined", label: "Décliné" },
] as const;

const TYPE_COLORS: Record<string, string> = {
  influencer: "bg-violet-500/20 text-violet-300 border-violet-500/30",
  creator: "bg-violet-500/20 text-violet-300 border-violet-500/30",
  brand: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  affiliate: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  investor: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  distributor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
  press: "bg-pink-500/20 text-pink-300 border-pink-500/30",
};

const STATUS_COLORS: Record<string, string> = {
  prospect: "bg-zinc-500/20 text-zinc-300 border-zinc-500/30",
  contacted: "bg-sky-500/20 text-sky-300 border-sky-500/30",
  in_discussion: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  agreement: "bg-indigo-500/20 text-indigo-300 border-indigo-500/30",
  active: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  paused: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  declined: "bg-zinc-600/20 text-zinc-400 border-zinc-600/30",
  new: "bg-red-500/20 text-red-300 border-red-500/30",
  reviewed: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  converted: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
};

export function typeBadgeStyle(type: string): string {
  return TYPE_COLORS[type] ?? "bg-white/10 text-ivory/80 border-white/10";
}

export function statusBadgeStyle(status: string): string {
  return STATUS_COLORS[status] ?? "bg-white/10 text-ivory/80 border-white/10";
}

export function partnerTypeLabel(type: string): string {
  return PARTNER_TYPES.find((t) => t.id === type)?.label ?? type;
}

export function partnerStatusLabel(status: string): string {
  return PARTNER_STATUSES.find((s) => s.id === status)?.label ?? status;
}

/** Deterministic avatar color from name */
export function avatarColor(name: string): string {
  const palette = [
    "bg-violet-600",
    "bg-blue-600",
    "bg-emerald-600",
    "bg-amber-600",
    "bg-rose-600",
    "bg-cyan-600",
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return palette[Math.abs(hash) % palette.length];
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}
