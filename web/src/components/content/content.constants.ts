export type PostPlatform =
  | "instagram"
  | "tiktok"
  | "x"
  | "youtube"
  | "linkedin"
  | "website_blog"
  | "discord";
export type PostContentType =
  | "announcement"
  | "teaser"
  | "tutorial"
  | "behind_scenes"
  | "short_video"
  | "lore";

export type PostStatus =
  | "draft"
  | "pending_approval"
  | "approved"
  | "published"
  | "failed"
  | "rejected";

export type StatusTab = "pending_approval" | "approved" | "published" | "all";

// Statuts atteignables par une création manuelle (Content Studio, Phase 33) —
// "published" ne l'est pas : createPost() ne l'accepte pas comme statut
// initial, seul le vrai publisher bot y amène un post.
export type CreatablePostStatus = "draft" | "pending_approval" | "approved";

export const CONTENT_TYPES: { id: PostContentType; label: string }[] = [
  { id: "announcement", label: "Annonce feature" },
  { id: "teaser", label: "Teaser mystère" },
  { id: "behind_scenes", label: "Behind the scenes" },
  { id: "tutorial", label: "Tutoriel court" },
  { id: "short_video", label: "Hype / Engagement" },
  { id: "lore", label: "Lore / Univers" },
];

export const PLATFORMS: { id: PostPlatform; label: string }[] = [
  { id: "instagram", label: "Instagram" },
  { id: "tiktok", label: "TikTok" },
  { id: "x", label: "X" },
  { id: "youtube", label: "YouTube Shorts" },
  { id: "linkedin", label: "LinkedIn" },
  { id: "website_blog", label: "Blog" },
  { id: "discord", label: "Discord" },
];

export type ContentSector = "app" | "gaming" | "robo" | "company";

export const SECTORS: { id: ContentSector; label: string; agent: string }[] = [
  { id: "app", label: "App", agent: "Esmée Diallo" },
  { id: "gaming", label: "Gaming", agent: "Kael Vex" },
  { id: "robo", label: "Robotique", agent: "Mira Solberg" },
  { id: "company", label: "Corporate", agent: "Anouk Gerard" },
];

export const SECTOR_STYLES: Record<ContentSector, string> = {
  app: "bg-naia-muted/50 text-naia-glow ring-naia/30",
  gaming: "bg-wyrdheim-muted/50 text-wyrdheim-glow ring-wyrdheim/30",
  robo: "bg-eve-muted/50 text-eve-glow ring-eve/30",
  company: "bg-violet-500/15 text-violet-300 ring-violet-500/25",
};

export const STATUS_TABS: { id: StatusTab; label: string }[] = [
  { id: "pending_approval", label: "À approuver" },
  { id: "approved", label: "Approuvés" },
  { id: "published", label: "Publiés" },
  { id: "all", label: "Tous" },
];

export const PLATFORM_STYLES: Record<
  PostPlatform,
  { badge: string; label: string }
> = {
  instagram: {
    badge: "bg-pink-500/20 text-pink-300 ring-pink-500/30",
    label: "Instagram",
  },
  tiktok: {
    badge: "bg-red-500/20 text-red-300 ring-red-500/30",
    label: "TikTok",
  },
  x: {
    badge: "bg-sky-500/20 text-sky-300 ring-sky-500/30",
    label: "X",
  },
  youtube: {
    badge: "bg-red-600/25 text-red-400 ring-red-600/35",
    label: "YouTube Shorts",
  },
  linkedin: {
    badge: "bg-blue-600/20 text-blue-300 ring-blue-600/30",
    label: "LinkedIn",
  },
  website_blog: {
    badge: "bg-amber-500/20 text-amber-300 ring-amber-500/30",
    label: "Blog",
  },
  discord: {
    badge: "bg-indigo-500/20 text-indigo-300 ring-indigo-500/30",
    label: "Discord",
  },
};

export const CONTENT_TYPE_LABELS: Record<string, string> = {
  announcement: "Annonce",
  teaser: "Teaser",
  tutorial: "Tutoriel",
  behind_scenes: "Behind the scenes",
  short_video: "Hype",
  lore: "Lore",
};

/* Content Studio (Phase 33, ROADMAP.md) — colonnes Kanban draggables. Seuls
   draft/pending_approval/approved/published sont de vrais statuts atteints
   par une action humaine ; rejected/failed sont produits par le pipeline
   automatique (publisher bot) et restent en lecture seule ailleurs (voir
   content-kanban.tsx) pour ne pas casser published_at si un post est glissé
   directement vers "Publié" sans passer par le vrai publisher. */
export const CONTENT_STUDIO_COLUMNS: { id: PostStatus; label: string; emoji: string }[] = [
  { id: "draft", label: "Brouillon", emoji: "📝" },
  { id: "pending_approval", label: "À approuver", emoji: "⏳" },
  { id: "approved", label: "Approuvé", emoji: "✅" },
  { id: "published", label: "Publié", emoji: "🚀" },
];

export const POST_STATUS_LABELS: Record<PostStatus, string> = {
  draft: "Brouillon",
  pending_approval: "À approuver",
  approved: "Approuvé",
  published: "Publié",
  rejected: "Rejeté",
  failed: "Échoué",
};

export const GLOBAL_PROJECT_ID = "__alnua_global__";

export function projectBadgeClass(branch: string, global?: boolean) {
  if (global) return "bg-violet-500/15 text-violet-300 ring-violet-500/25";
  switch (branch) {
    case "app":
      return "bg-naia-muted/50 text-naia-glow ring-naia/30";
    case "gaming":
      return "bg-wyrdheim-muted/50 text-wyrdheim-glow ring-wyrdheim/30";
    case "robotics":
      return "bg-eve-muted/50 text-eve-glow ring-eve/30";
    default:
      return "bg-violet-500/15 text-violet-300 ring-violet-500/25";
  }
}
